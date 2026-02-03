from curl_cffi.requests import Session
from typing import Dict

class SimpleCrawler(Session):

    def __init__(self, impersonate="chrome"):
        super().__init__(impersonate=impersonate)
        self.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
            }
        )

    def load_cookies(self, cookies: Dict):
        for cookie_name, cookie_value in cookies.items():
            self.cookies.set(cookie_name, cookie_value)
