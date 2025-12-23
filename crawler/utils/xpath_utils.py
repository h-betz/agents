import types

from lxml import html
from lxml.html import HtmlElement
from requests import Response

from crawler.utils.default_html_element import DefaultHtmlElement


# Cache custom functions to avoid repeated dir() calls
_CUSTOM_FUNCTIONS = None


def _get_custom_functions():
    """Get cached list of custom functions from DefaultHtmlElement."""
    global _CUSTOM_FUNCTIONS
    if _CUSTOM_FUNCTIONS is None:
        _CUSTOM_FUNCTIONS = {
            name: getattr(DefaultHtmlElement, name)
            for name in dir(DefaultHtmlElement)
            if not name.startswith("__") and callable(getattr(DefaultHtmlElement, name))
        }
    return _CUSTOM_FUNCTIONS


def map_lxml_html_to_custom_html_element(element: HtmlElement) -> HtmlElement:
    """Bind custom methods from DefaultHtmlElement to an lxml HtmlElement."""
    custom_functions = _get_custom_functions()
    existing_functions = set(dir(element))

    for func_name, func in custom_functions.items():
        if func_name not in existing_functions:
            # Bind custom function as a method
            element.__dict__[func_name] = types.MethodType(func, element)

    return element


def bind_custom_html_element(raw_html: Response) -> HtmlElement:
    element = html.fromstring(raw_html.content)
    element.status_code = raw_html.status_code
    element.url = raw_html.url
    element.headers = raw_html.headers
    element.content = raw_html.content
    try:
        element._json = raw_html.json()
    except Exception:
        element._json = {}

    return map_lxml_html_to_custom_html_element(element)
