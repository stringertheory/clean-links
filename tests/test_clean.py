from clean_links.clean import clean_url


def test_utm():
    result = clean_url("https://example.com/?utm_source=yomama")
    assert result == "https://example.com/"


def test_amazon():
    url = "https://www.amazon.com/Kobo-Glare-Free-Touchscreen-ComfortLight-Adjustable/dp/B0BCXLQNCC/ref=pd_ci_mcx_mh_mcx_views_0?pd_rd_w=Dx5dF&content-id=amzn1.sym.225b4624-972d-4629-9040-f1bf9923dd95%3Aamzn1.symc.40e6a10e-cbc4-4fa5-81e3-4435ff64d03b&pf_rd_p=225b4624-972d-4629-9040-f1bf9923dd95&pf_rd_r=A7JSDJGYR33BN5GRCV7V&pd_rd_wg=xW6Yf&pd_rd_r=4b8a3532-9e28-4857-a929-5e572d2c765f&pd_rd_i=B0BCXLQNCC"
    result = clean_url(url)
    assert (
        result
        == "https://www.amazon.com/Kobo-Glare-Free-Touchscreen-ComfortLight-Adjustable/dp/B0BCXLQNCC"
    )


def test_ok_query_params():
    url = "https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1144182"
    result = clean_url(url)
    assert result == url
