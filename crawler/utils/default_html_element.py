from typing import Dict, List

from lxml.html import HtmlElement


class DefaultHtmlElement:
    """Mixin class providing custom methods for HtmlElement instances."""

    def content(self) -> str:
        """Get the text content of the element, stripped of whitespace."""
        text = self.text_content()
        return (text or "").strip()

    def _get_element(self, path: str, index: int = 0) -> HtmlElement:
        """
        Get an element by xpath and index.

        Args:
            path: XPath query string
            index: Index of element to retrieve (0 for first, -1 for last)

        Returns:
            HtmlElement with is_empty attribute set
        """
        # Import here to avoid circular import
        from crawler.utils.xpath_utils import map_lxml_html_to_custom_html_element

        elements = self.xpath(path)
        if not elements:
            element = map_lxml_html_to_custom_html_element(HtmlElement())
            element.is_empty = True
            return element

        element = map_lxml_html_to_custom_html_element(elements[index])
        element.is_empty = False
        return element

    def first(self, path: str) -> HtmlElement:
        """Get the first element matching the xpath."""
        return self._get_element(path, index=0)

    def last(self, path: str) -> HtmlElement:
        """Get the last element matching the xpath."""
        return self._get_element(path, index=-1)

    def elements(self, path: str) -> List[HtmlElement]:
        """Get all elements matching the xpath."""
        # Import here to avoid circular import
        from crawler.utils.xpath_utils import map_lxml_html_to_custom_html_element

        elements = self.xpath(path)
        result = []
        for element in elements:
            element = map_lxml_html_to_custom_html_element(element)
            element.is_empty = False
            result.append(element)
        return result

    def json(self) -> Dict:
        """Get JSON data attached to this element (from response)."""
        return getattr(self, "_json", {})

    def data(self) -> Dict[str, str]:
        """Extract form data from input elements."""
        _data = {}
        for field in self.elements(".//input"):
            name = field.get("name")
            value = field.get("value")
            if name:  # Only add if name exists
                _data[name] = value
        return _data
