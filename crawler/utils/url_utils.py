import codecs

def decode_url(encoded_url):
    """
    Decode a JavaScript/Unicode escaped URL.

    Handles escape sequences like \\x3A (:), \\x2F (/), etc.
    Common in JavaScript-embedded URLs and AJAX responses.

    Args:
        encoded_url: URL string with \\xHH escape sequences

    Returns:
        Decoded URL string

    Example:
        encoded = 'https\\x3A\\x2F\\x2Fexample.com\\x2Fpath'
        decoded = Crawler.decode_url(encoded)
        # Returns: 'https://example.com/path'
    """
    return codecs.decode(encoded_url, 'unicode_escape')