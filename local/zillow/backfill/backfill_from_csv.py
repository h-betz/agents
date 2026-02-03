import csv
import json
import re
import time
from random import randint
from datetime import datetime
from db_api import DBAPI
from local.zillow.zillow import Zillow


def backfill(zillow, zpid, **kwargs):
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'client-id': 'not-for-sale-sub-app-browser-client',
        'content-type': 'application/json',
        'priority': 'u=1, i',
        'referer': "https://www.zillow.com/homedetails/479-N-Church-St-Moorestown-NJ-08057/38128371_zpid/",
        'sec-ch-ua': '"Google Chrome";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"macOS"',
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36',
        'x-z-enable-oauth-conversion': 'true',
    }
    variables = {
        "zpid": zpid,
        "altId": None,
        "deviceType": "desktop",
        "deviceTypeV2": "WEB_DESKTOP",
        "useOmpV2": True,
        "includeLastSoldListing": False
    }
    params = {
        'extensions': '{"persistedQuery":{"version":1,"sha256Hash":"4dae43213dc50a3fe01c15455df088f46f37ef86aa0af63b24bf0331de593bdc"}}',
        'variables': json.dumps(variables),
    }
    """
    Looking for the following fields:
    - Tax Assessment
    - Days on Market
    - zestimate
    """
    try:
        response = zillow.get("https://www.zillow.com/graphql/", params=params, headers=headers)
        if response.status_code != 200:
            raise Exception(response.text)
        data = response.json()
        home_info = data.get("data").get("property")
        lot_area_unit = home_info.get("lotAreaUnit")
        tax_history = home_info.get("taxHistory") or []
        tax_assessment = tax_history[0].get("value") if tax_history else None

        return {
            "days_on_market": home_info.get("daysOnZillow"), #daysOnZillow
            "type": home_info.get("homeType"),
            "zestimate": home_info.get("zestimate"),
            "lot_size": home_info.get("lotAreaValue"),
            "lot_size_unit": lot_area_unit.lower() if lot_area_unit else None,
            "tax_assessment": tax_assessment,
            "price_history": home_info.get("priceHistory"),
        }
    except Exception as e:
        print()


def extract_zpid(url):
    """Extract zpid from a Zillow URL."""
    if not url or 'zillow.com' not in url:
        return None
    match = re.search(r'/(\d+)_zpid', url)
    return int(match.group(1)) if match else None


def zpid_exists(zpid):
    """Check if a zpid already exists in the database."""
    query = "SELECT 1 FROM homes WHERE zpid = %s LIMIT 1"
    with DBAPI(dbname="homelander") as db:
        result = db.execute(query, (zpid,))
        return result is not None


def parse_sold_date(date_str):
    """Parse sold date from MM/DD/YYYY format to Unix timestamp in milliseconds."""
    if not date_str:
        return None
    try:
        dt = datetime.strptime(date_str, "%m/%d/%Y")
        return int(dt.timestamp() * 1000)
    except ValueError:
        return None


def parse_float(value):
    """Safely parse a float value."""
    if not value:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def parse_int(value):
    """Safely parse an int value."""
    if not value:
        return None
    try:
        return int(float(value))
    except ValueError:
        return None


def save_home_to_database(home):
    """Insert a single home into the database."""
    try:
        insert_query = """
            INSERT INTO homes (
                url, sold_price, raw_sold_price,
                address_city, address_street, address_state, address_zipcode,
                date_sold, bedrooms, bathrooms, sqft,
                days_on_market, type, zestimate,
                lot_size, lot_size_unit, tax_assessment, zpid
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (address_city, address_street, address_state, date_sold) DO NOTHING
            RETURNING zpid
        """

        values = (
            home.get('url'),
            home.get('sold_price'),
            home.get('raw_sold_price'),
            home.get('address_city'),
            home.get('address_street'),
            home.get('address_state'),
            home.get('address_zipcode'),
            home.get('date_sold'),
            home.get('bedrooms'),
            home.get('bathrooms'),
            home.get('sqft'),
            home.get('days_on_market'),
            home.get('type'),
            home.get('zestimate'),
            home.get('lot_size'),
            home.get('lot_size_unit'),
            home.get('tax_assessment'),
            home.get('zpid')
        )

        with DBAPI(dbname="homelander") as db:
            result = db.execute_with_returning(insert_query, values)
            if result:
                print(f"  -> Inserted home: {home.get('address_street')}")
                return True
            else:
                print(f"  -> Home already exists: {home.get('address_street')}")
                return False

    except Exception as e:
        print(f"  -> Error saving home: {e}")
        raise


def save_price_history(zpid, price_history):
    """Save price history records to database."""
    if not price_history:
        print(f"  -> No price history records to save")
        return

    try:
        insert_query = """
            INSERT INTO price_history (
                zpid, price, time, date,
                price_per_sq_ft, price_change_rate, event
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s
            )
            ON CONFLICT (zpid, time, event) DO NOTHING
        """

        values = []
        for record in price_history:
            values.append((
                zpid,
                record.get('price'),
                record.get('time'),
                record.get('date'),
                record.get('pricePerSquareFoot'),
                record.get('priceChangeRate'),
                record.get('event')
            ))

        with DBAPI(dbname="homelander") as db:
            inserted_count = db.execute_batch(insert_query, values)
            print(f"  -> Processed {len(price_history)} price history records, inserted {inserted_count} new records")

    except Exception as e:
        print(f"  -> Error saving price history: {e}")
        raise


def process_csv(csv_path):
    """Process CSV file and call backfill for each Zillow record."""
    zillow, _ = Zillow.for_city("Moorestown")
    results = []

    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            url = row.get('Link', '')
            zpid = extract_zpid(url)

            if zpid is None:
                print(f"Skipping non-Zillow URL: {row.get('Address', 'Unknown')}")
                continue

            print(f"Processing: {row.get('Address', 'Unknown')} (zpid: {zpid})")

            # Check if record already exists before making API call
            if zpid_exists(zpid):
                print(f"  -> Skipping existing record (zpid: {zpid})")
                continue

            try:
                # Fetch additional data from Zillow API
                time.sleep(randint(1, 3))
                api_data = backfill(zillow, zpid, url=url)

                # Build the home record combining CSV data and API data
                home = {
                    'url': url,
                    'sold_price': row.get('Sold Price', ''),
                    'raw_sold_price': parse_int(row.get('Sold Price', '').replace(',', '')),
                    'address_city': 'Moorestown',
                    'address_street': row.get('Address', ''),
                    'address_state': 'NJ',
                    'address_zipcode': '08057',
                    'date_sold': parse_sold_date(row.get('Sold Date', '')),
                    'bedrooms': parse_int(row.get('Beds', '')),
                    'bathrooms': parse_float(row.get('Baths', '')),
                    'sqft': parse_int(row.get('Sqft', '')),
                    'days_on_market': api_data.get('days_on_market'),
                    'type': api_data.get('type'),
                    'zestimate': api_data.get('zestimate'),
                    'lot_size': api_data.get('lot_size') or parse_float(row.get('Lot Size', '')),
                    'lot_size_unit': api_data.get('lot_size_unit', 'sqft'),
                    'tax_assessment': api_data.get('tax_assessment'),
                    'zpid': zpid
                }

                # Save home to database
                save_home_to_database(home)

                # Save price history
                price_history = api_data.get('price_history', [])
                if price_history:
                    save_price_history(zpid, price_history)

                results.append({'address': row.get('Address', ''), 'zpid': zpid, 'success': True})

            except Exception as e:
                print(f"  -> Error: {e}")
                results.append({'address': row.get('Address', ''), 'zpid': zpid, 'error': str(e)})

    return results


if __name__ == "__main__":
    import os
    csv_path = os.path.join(os.path.dirname(__file__), '../session_data', 'Comps - Home.csv')
    results = process_csv(csv_path)
