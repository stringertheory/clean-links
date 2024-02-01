from clean_links import normalize_url


def test_simple():
    norm1 = normalize_url("https://example.com/")
    norm2 = normalize_url("https://example.com/?utm_source=yomama")
    assert "https://example.com/" == norm1 == norm2


def test_nonexistant():
    # dingle.berries is not actually a website
    norm1 = normalize_url("https://dingle.berries/")

    # https://bit.ly/dberry redirects to
    # https://dingle.berries/?utm_medium=dingle&utm_campaign=berries...
    norm2 = normalize_url("https://bit.ly/dberry")

    assert "https://dingle.berries/" == norm1 == norm2
