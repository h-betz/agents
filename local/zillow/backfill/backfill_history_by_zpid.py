import json
import os
import random
import sys
import time

# Add project root and parent directory to path for imports
project_root = os.path.join(os.path.dirname(__file__), "..", "..", "..")
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from local.zillow.zillow import Zillow
from db_api import DBAPI

COOKIES_PATH = os.path.join(os.path.dirname(__file__), "..", "session_data", "cookies.json")


def get_zpids_to_backfill():
    """Query zpids from homes table that don't have price history yet"""
    query = """
        SELECT DISTINCT h.zpid
        FROM homes h
        LEFT JOIN price_history ph ON h.zpid = ph.zpid
        WHERE ph.zpid IS NULL AND h.zpid IS NOT NULL
    """
    with DBAPI(dbname="homelander") as db:
        db.cursor.execute(query)
        results = db.cursor.fetchall()
        return [row[0] for row in results]


def main():
    zpids = get_zpids_to_backfill()
    print(f"Found {len(zpids)} zpids to backfill")

    # Load cookies from cookies.json
    with open(COOKIES_PATH) as f:
        cookies = json.load(f)

    zillow = Zillow()
    zillow.load_cookies(cookies)

    for zpid in zpids:
        time.sleep(random.randint(1, 3))
        records = zillow.get_property_pricing_history(zpid)
        zillow.save_price_history(records)


if __name__ == "__main__":
    main()
