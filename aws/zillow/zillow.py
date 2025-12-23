import boto3
import json
import os
import psycopg2
from psycopg2.extras import execute_batch
from typing import Dict, Optional, List

from simple_crawler import SimpleCrawler


class Zillow(SimpleCrawler):
    CITIES = ["Collingswood", "Haddonfield", "Haddon_Township"]

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
            })

        return homes

    def sync_sold(self, data: Dict):
        results = self.fetch_recently_sold(data)
        parsed_results = self.parse_recently_sold(results)
        self._save_to_database(parsed_results)

    def _get_db_connection(self):
        """Create database connection from environment variables"""
        return psycopg2.connect(
            dbname=os.environ.get("DB_NAME", "groceries"),
            user=os.environ["DB_USER"],
            password=os.environ["DB_PASSWORD"],
            host=os.environ["DB_HOST"],
            port=os.environ.get("DB_PORT", "5432")
        )

    def _save_to_database(self, homes: List[Dict]):
        """
        Insert homes into database, skip duplicates.
        Uses ON CONFLICT to handle duplicates efficiently.
        """
        if not homes:
            print(f"No homes to save for {self.city}")
            return

        conn = None
        try:
            conn = self._get_db_connection()
            cur = conn.cursor()

            # Insert query with ON CONFLICT to skip duplicates
            # Using address + date_sold as the duplicate check
            insert_query = """
                INSERT INTO homes (
                    url, sold_price, raw_sold_price,
                    address_city, address_street, address_state, address_zipcode,
                    date_sold, bedrooms, bathrooms, sqft,
                    days_on_market, type, zestimate,
                    lot_size, lot_size_unit, tax_assessment
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                )
                ON CONFLICT (address_city, address_street, address_state, date_sold) DO NOTHING
            """

            # Flatten the data for batch insert
            values = []
            for home in homes:
                values.append((
                    home.get('url'),
                    home.get('sold_price'),
                    home.get('raw_sold_price'),
                    home.get('address', {}).get('city'),
                    home.get('address', {}).get('street'),
                    home.get('address', {}).get('state'),
                    home.get('address', {}).get('zipcode'),
                    home.get('date_sold'),
                    home.get('bedrooms'),
                    home.get('bathrooms'),
                    home.get('sqft'),
                    home.get('days_on_market'),
                    home.get('type'),
                    home.get('zestimate'),
                    home.get('lot_size'),
                    home.get('lot_size_unit'),
                    home.get('tax_assessment')
                ))

            # Batch insert for efficiency
            execute_batch(cur, insert_query, values)
            conn.commit()

            inserted_count = cur.rowcount
            print(f"Processed {len(homes)} homes for {self.city}, inserted {inserted_count} new records")

        except Exception as e:
            if conn:
                conn.rollback()
            print(f"Error saving to database for {self.city}: {e}")
            raise
        finally:
            if conn:
                cur.close()
                conn.close()

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
