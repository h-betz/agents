import logging
import requests
import sys
import time
import traceback
from typing import Dict
from urllib.parse import urljoin

from crawler.utils.xpath_utils import bind_custom_html_element


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)


class Crawler(requests.Session):

    def __init__(self):
        super().__init__()
        self.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36"
            }
        )

    def load_cookies(self, cookies: Dict):
        for cookie_name, cookie_value in cookies.items():
            self.cookies.set(cookie_name, cookie_value)

    def save_cookies(self, filepath: str):
        pass

    def get(self, url, max_retries=3, **kwargs):
        for attempt in range(max_retries):
            try:
                # Exponential backoff: wait before retry (skip on first attempt)
                if attempt > 0:
                    sleep_time = 2**attempt  # 2, 4, 8 seconds
                    logger.warning(
                        f"Retry {attempt}/{max_retries} for {url} after {sleep_time}s"
                    )
                    time.sleep(sleep_time)

                raw_response = super().get(url, **kwargs)
                logger.info(f"Response from {url}: {raw_response.status_code}")

                if raw_response.status_code >= 400:
                    raise Exception(f"HTTP {raw_response.status_code} error")

                response = bind_custom_html_element(raw_response)
                return response
            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt failed
                    logger.error(
                        f"Failed to request {url} after {max_retries} attempts"
                    )
                    logger.error(traceback.format_exc())
                    raise  # Re-raise the exception

                logger.warning(f"Attempt {attempt + 1} failed for {url}: {e}")
        # Should never reach here, but just in case
        raise Exception(f"Failed to fetch {url} after {max_retries} retries")

    def post(self, url, max_retries=3, **kwargs):
        """POST request with retry logic and exponential backoff."""
        for attempt in range(max_retries):
            try:
                # Exponential backoff: wait before retry (skip on first attempt)
                if attempt > 0:
                    sleep_time = 2**attempt  # 2, 4, 8 seconds
                    logger.warning(
                        f"Retry {attempt}/{max_retries} for POST {url} after {sleep_time}s"
                    )
                    time.sleep(sleep_time)

                raw_response = super().post(url, **kwargs)
                logger.info(f"POST response from {url}: {raw_response.status_code}")

                if raw_response.status_code >= 400:
                    raise Exception(f"HTTP {raw_response.status_code} error")

                response = bind_custom_html_element(raw_response)
                return response
            except Exception as e:
                if attempt == max_retries - 1:
                    # Last attempt failed
                    logger.error(
                        f"Failed POST request to {url} after {max_retries} attempts"
                    )
                    logger.error(traceback.format_exc())
                    raise  # Re-raise the exception

                logger.warning(f"POST attempt {attempt + 1} failed for {url}: {e}")
        # Should never reach here, but just in case
        raise Exception(f"Failed to POST {url} after {max_retries} retries")

    def submit(self, page, form_selector=".//form", additional_data=None, **kwargs):
        """
        Submit a form from a page.

        Args:
            page: The page element containing the form
            form_selector: XPath selector for the form (default: ".//form" for first form)
            additional_data: Dictionary of additional form data to include/override
            **kwargs: Additional arguments to pass to the POST/GET request

        Returns:
            Response from form submission

        Example:
            response = crawler.submit_form(page)
            response = crawler.submit_form(page, ".//form[@name='login']", {"username": "user"})
        """
        # Find the form
        form = page.first(form_selector)

        # Get form action and method
        form_action = form.get("action") or ""
        form_method = (form.get("method") or "get").lower()

        # Build full URL from relative or absolute action
        submit_url = urljoin(str(page.url), form_action)

        # Extract form data from input fields
        form_data = form.data()

        # Merge with additional data if provided
        if additional_data:
            form_data.update(additional_data)

        # Submit the form using the appropriate HTTP method
        if form_method == "post":
            return self.post(submit_url, data=form_data, **kwargs)
        else:
            return self.get(submit_url, params=form_data, **kwargs)
