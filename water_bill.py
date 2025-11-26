from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os

load_dotenv()

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://wipp.edmundsassoc.com/Wipp0322/")
    page.wait_for_load_state('networkidle')
    print(page.title())
    browser.close()


def login():
    browser = p.chromium.launch()
    page = browser.new_page()
    page.goto("https://wipp.edmundsassoc.com/Wipp0322/")
    page.wait_for_load_state('networkidle')
    print(page.title())
    browser.close()