import boto3
import csv
import io
import json
import os
import time
from typing import Dict, Optional, List

from crawler.simple_crawler import SimpleCrawler


def _csv_str(value) -> str:
    return "" if value is None else str(value)


class Zillow(SimpleCrawler):
    CITIES = ["Collingswood", "Haddonfield", "Haddon_Township", "Moorestown"]

    HOMES_CSV_FIELDS = [
        "url", "sold_price", "raw_sold_price",
        "address_city", "address_street", "address_state", "address_zipcode",
        "date_sold", "bedrooms", "bathrooms", "sqft",
        "days_on_market", "type", "zestimate",
        "lot_size", "lot_size_unit", "tax_assessment", "zpid",
    ]
    HOMES_DEDUP_FIELDS = ("address_city", "address_street", "address_state", "date_sold")

    def __init__(self, s3_bucket: Optional[str] = None, s3_prefix: Optional[str] = None):
        super(Zillow, self).__init__()
        self.headers.update({
            'accept': '*/*',
            'accept-language': 'en-US,en;q=0.9',
            'content-type': 'application/json',
            'origin': 'https://www.zillow.com',
            'priority': 'u=1, i',
            'referer': 'https://www.zillow.com',
        })
        self.city = ""
        self.s3_bucket = s3_bucket or os.getenv('ZILLOW_S3_BUCKET')
        self.s3_prefix = s3_prefix or os.getenv('ZILLOW_S3_PREFIX', '../../crawler/session_data')
        self._s3_client = None

    def fetch_recently_sold(self, data: Dict):
        url = "https://www.zillow.com/async-create-search-page-state"
        time.sleep(1)
        response = self.put(url, json=data)
        if response.status_code != 200:
            raise Exception(f"Request to {url} failed with status code {response.status_code}")
        results = response.json()
        if results.get("cat1").get("searchList").get("totalPages") > 1:
            raise Exception(f"Too many results for {self.city}")
        return response.json()

    def parse_recently_sold(self, data: Dict):
        search_result = data.get("cat1")
        results = search_result.get("searchResults")
        list_results = results.get("listResults")
        homes = []
        for result in list_results:
            home_info = result.get("hdpData").get("homeInfo")
            homes.append({
                "url": result.get("detailUrl"),
                "sold_price": result.get("soldPrice"),
                "raw_sold_price": result.get("price") or result.get("unformattedPrice"),
                "address": {
                    "city": result.get("addressCity"),
                    "street": result.get("addressStreet"),
                    "state": result.get("addressState"),
                    "zipcode": result.get("addressZipcode"),
                },
                "date_sold": home_info.get("dateSold"),
                "bathrooms": result.get("bathrooms"),
                "bedrooms": result.get("bedrooms"),
                "sqft": result.get("livingArea"),
                "days_on_market": home_info.get("daysOnZillow"),
                "type": home_info.get("homeType"),
                "zestimate": home_info.get("zestimate"),
                "lot_size": home_info.get("lotAreaValue"),
                "lot_size_unit": home_info.get("lotAreaUnit"),
                "tax_assessment": home_info.get("taxAssessedValue"),
                "zpid": home_info.get("zpid"),
            })

        return homes

    def sync_sold(self, data: Dict):
        results = self.fetch_recently_sold(data)
        parsed_results = self.parse_recently_sold(results)
        new_zpids = self._save_to_csv(parsed_results)

        # Send new zpids to SQS for price history fetching
        if new_zpids:
            self._send_to_sqs(new_zpids)

    def _send_to_sqs(self, zpids: List[int]):
        """Send zpids to SQS queue for price history fetching"""
        queue_url = os.environ.get('PRICE_HISTORY_QUEUE_URL')

        if not queue_url:
            print("Warning: PRICE_HISTORY_QUEUE_URL not set, skipping SQS messages")
            return

        try:
            sqs = boto3.client('sqs')

            for zpid in zpids:
                message_body = json.dumps({'zpid': zpid})
                sqs.send_message(
                    QueueUrl=queue_url,
                    MessageBody=message_body
                )
                print(f"Sent zpid {zpid} to SQS queue")

            print(f"Successfully sent {len(zpids)} messages to SQS")

        except Exception as e:
            print(f"Error sending messages to SQS: {e}")
            # Don't raise - SQS failure shouldn't break the scraper

    @property
    def homes_csv_key(self) -> str:
        """Path (S3 key or local path) of the homes CSV file"""
        if self.s3_bucket:
            return f"{self.s3_prefix}/homes.csv"
        return "data/homes.csv"

    def _read_csv_rows(self, key_or_path: str) -> List[Dict]:
        """Read existing CSV rows from S3 or local disk"""
        if self.s3_bucket:
            try:
                response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=key_or_path)
            except self.s3_client.exceptions.NoSuchKey:
                return []
            content = response['Body'].read().decode('utf-8')
            return list(csv.DictReader(io.StringIO(content)))
        else:
            if not os.path.exists(key_or_path):
                return []
            with open(key_or_path, newline="") as f:
                return list(csv.DictReader(f))

    def _write_csv_rows(self, key_or_path: str, fieldnames: List[str], rows: List[Dict]):
        """Write CSV rows to S3 or local disk"""
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

        if self.s3_bucket:
            self.s3_client.put_object(Bucket=self.s3_bucket, Key=key_or_path, Body=buffer.getvalue().encode('utf-8'))
        else:
            os.makedirs(os.path.dirname(key_or_path) or ".", exist_ok=True)
            with open(key_or_path, "w", newline="") as f:
                f.write(buffer.getvalue())

    def _save_to_csv(self, homes: List[Dict]) -> List[int]:
        """
        Append homes to the CSV file, skip duplicates.
        Returns list of zpids for newly added homes.
        """
        if not homes:
            print(f"No homes to save for {self.city}")
            return []

        csv_key = self.homes_csv_key
        rows = self._read_csv_rows(csv_key)
        existing_keys = {tuple(row.get(f, "") for f in self.HOMES_DEDUP_FIELDS) for row in rows}

        new_zpids = []
        for home in homes:
            row = {
                "url": _csv_str(home.get('url')),
                "sold_price": _csv_str(home.get('sold_price')),
                "raw_sold_price": _csv_str(home.get('raw_sold_price')),
                "address_city": _csv_str(home.get('address', {}).get('city')),
                "address_street": _csv_str(home.get('address', {}).get('street')),
                "address_state": _csv_str(home.get('address', {}).get('state')),
                "address_zipcode": _csv_str(home.get('address', {}).get('zipcode')),
                "date_sold": _csv_str(home.get('date_sold')),
                "bedrooms": _csv_str(home.get('bedrooms')),
                "bathrooms": _csv_str(home.get('bathrooms')),
                "sqft": _csv_str(home.get('sqft')),
                "days_on_market": _csv_str(home.get('days_on_market')),
                "type": _csv_str(home.get('type')),
                "zestimate": _csv_str(home.get('zestimate')),
                "lot_size": _csv_str(home.get('lot_size')),
                "lot_size_unit": _csv_str(home.get('lot_size_unit')),
                "tax_assessment": _csv_str(home.get('tax_assessment')),
                "zpid": _csv_str(home.get('zpid')),
            }
            key = tuple(row[f] for f in self.HOMES_DEDUP_FIELDS)
            if key in existing_keys:
                continue
            rows.append(row)
            existing_keys.add(key)
            new_zpids.append(home.get('zpid'))

        if new_zpids:
            self._write_csv_rows(csv_key, self.HOMES_CSV_FIELDS, rows)
        print(f"Processed {len(homes)} homes for {self.city}, inserted {len(new_zpids)} new records")
        return new_zpids

    @property
    def s3_client(self):
        """Lazy load S3 client"""
        if self._s3_client is None and self.s3_bucket:
            self._s3_client = boto3.client('s3')
        return self._s3_client

    def _load_session_data(self, city: str) -> dict:
        """Load session data from S3 or local file system"""
        filename = f"{city.lower()}.json"

        if self.s3_bucket:
            # Load from S3
            s3_key = f"{self.s3_prefix}/{filename}"
            response = self.s3_client.get_object(Bucket=self.s3_bucket, Key=s3_key)
            return json.loads(response['Body'].read().decode('utf-8'))
        else:
            # Load from local file system
            with open(f"session_data/{filename}") as f:
                return json.load(f)

    @classmethod
    def for_city(cls, city: str, s3_bucket: Optional[str] = None, s3_prefix: Optional[str] = None):
        """Factory method to create a crawler for a specific city"""
        instance = cls(s3_bucket=s3_bucket, s3_prefix=s3_prefix)
        instance.city = city
        session_data = instance._load_session_data(city)
        instance.load_cookies(session_data.get("cookies"))
        request_data = session_data.get("data")
        return instance, request_data

    def run(self, search_data: Dict):
        self.sync_sold(search_data)

    @classmethod
    def run_all(cls, s3_bucket: Optional[str] = None, s3_prefix: Optional[str] = None):
        """Run scraper for all cities"""
        for city in cls.CITIES:
            crawler, search_data = cls.for_city(city, s3_bucket=s3_bucket, s3_prefix=s3_prefix)
            crawler.run(search_data)


if __name__ == '__main__':
    Zillow.run_all()
