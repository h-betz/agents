import json
import time
from random import randint
from db_api import DBAPI
from local.zillow.zillow import Zillow


def backfill(zillow, zpid, **kwargs):
    headers = {
        'accept': '*/*',
        'accept-language': 'en-US,en;q=0.9',
        'client-id': 'not-for-sale-sub-app-browser-client',
        'content-type': 'application/json',
        'priority': 'u=1, i',
        'referer': kwargs.get("url"),
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
    try:
        response = zillow.get("https://www.zillow.com/graphql/", params=params, headers=headers)
        if response.status_code != 200:
            raise Exception(response.text)
        data = response.json()
        home_info = data.get("data").get("property")
        sqft = home_info.get("livingArea")
        beds = home_info.get("bedrooms")
        baths = home_info.get("bathrooms")

        return {
            "sqft": sqft, #daysOnZillow
            "beds": beds,
            "baths": baths,
        }
    except Exception as e:
        print()


def get_records_missing_bed_bath():
    """Query database for records where bedrooms or bathrooms are null."""
    query = """
        SELECT zpid, url FROM homes
        WHERE bedrooms IS NULL OR bathrooms IS NULL
    """
    with DBAPI(dbname="homelander") as db:
        db.cursor.execute(query)
        return db.cursor.fetchall()


def update_record(zpid, sqft, beds, baths):
    """Update a home record with sqft, bedrooms, and bathrooms."""
    query = """
        UPDATE homes
        SET sqft = %s, bedrooms = %s, bathrooms = %s
        WHERE zpid = %s
    """
    with DBAPI(dbname="homelander") as db:
        db.cursor.execute(query, (sqft, beds, baths, zpid))
        return db.cursor.rowcount


if __name__ == "__main__":
    """
    Need to query the database for the records that have the bed and bathrooms as null
    and call backfill. We then need to update their record in the database with the
    new data: sqft, bedrooms, bathrooms
    """
    zillow, _ = Zillow.for_city("Moorestown")

    # Get records missing bed/bath data
    records = get_records_missing_bed_bath()
    print(f"Found {len(records)} records missing bed/bath data")

    for zpid, url in records:
        print(f"Processing zpid: {zpid}")
        try:
            time.sleep(randint(1, 3))
            data = backfill(zillow, zpid, url=url)

            if data:
                updated = update_record(zpid, data.get('sqft'), data.get('beds'), data.get('baths'))
                if updated:
                    print(f"  -> Updated: sqft={data.get('sqft')}, beds={data.get('beds')}, baths={data.get('baths')}")
                else:
                    print(f"  -> No rows updated")
            else:
                print(f"  -> Backfill returned no data")

        except Exception as e:
            print(f"  -> Error: {e}")