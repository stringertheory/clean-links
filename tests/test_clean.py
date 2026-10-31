import pytest

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


# Tracking parameters adopted from Firefox's strip-on-share lists
# (toolkit/components/antitracking/StripOnShareLists). Only pure tracking
# IDs were taken; names that can carry content (e.g. ``var``, ``adid``,
# TikTok ``q``/``t``) were deliberately left out — a False merge is worse
# than a False split.

GLOBAL_TRACKERS = [
    "gbraid",
    "wbraid",
    "gclsrc",
    "gad_source",
    "gad_campaignid",
    "ttclid",
    "li_fat_id",
    "ScCid",
    "epik",
    "_branch_match_id",
    "_hsmi",
    "hsa_cam",
    "pk_campaign",
    "matomo_source",
    "piwik_kwd",
    "trk_contact",
    "at_medium",
    "s_kwcid",
]


@pytest.mark.parametrize("param", GLOBAL_TRACKERS)
def test_global_trackers_stripped_everywhere(param):
    url = f"https://example.com/article?id=7&{param}=abc"
    assert clean_url(url) == "https://example.com/article?id=7"


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        (
            "https://www.amazon.com/dp/B0BCXLQNCC?hvadid=1&hvdev=c",
            "https://www.amazon.com/dp/B0BCXLQNCC",
        ),
        (
            "https://www.ebay.com/itm/123?mkcid=1&mkevt=1&campid=5",
            "https://www.ebay.com/itm/123",
        ),
        (
            "https://www.bbc.com/news/x?ns_source=tw&ns_mchannel=social",
            "https://www.bbc.com/news/x",
        ),
        (
            "https://www.etsy.com/listing/1/thing?ref=shop_home",
            "https://www.etsy.com/listing/1/thing",
        ),
        (
            "https://www.reddit.com/r/python/comments/abc/?ref=share",
            "https://www.reddit.com/r/python/comments/abc/",
        ),
        (
            "https://www.tiktok.com/@u/video/1?share_app_id=1&sender_device=pc",
            "https://www.tiktok.com/@u/video/1",
        ),
        (
            "https://www.wsj.com/articles/x?reflink=desktopwebshare",
            "https://www.wsj.com/articles/x",
        ),
        (
            "https://edition.cnn.com/2026/10/31/x/index.html?ref=yo",
            "https://edition.cnn.com/2026/10/31/x/index.html",
        ),
        (
            "https://en.wikipedia.org/wiki/URL?wprov=sfla1",
            "https://en.wikipedia.org/wiki/URL",
        ),
        (
            "https://www.twitch.tv/x?tt_medium=redt&tt_content=post",
            "https://www.twitch.tv/x",
        ),
        (
            "https://www.bloomberg.com/news/x?srnd=homepage&sref=abc",
            "https://www.bloomberg.com/news/x",
        ),
    ],
)
def test_site_scoped_trackers_stripped(url, expected):
    assert clean_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        # Site-scoped names stay put on other sites.
        "https://example.com/a?ref=main",
        "https://example.com/a?source=feed",
        "https://example.com/a?wprov=x",
        # Lookalike hosts don't inherit a site's rules.
        "https://wsj.com.example.org/a?reflink=x",
        "https://notcnn.com/a?ref=x",
        # Firefox strips these, but they can carry content.
        "https://example.com/a?var=blue",
        "https://example.com/listing?adid=123",
        "https://www.tiktok.com/search?q=cats&t=1",
        "https://www.amazon.com/dp/B0BCXLQNCC?psc=1",
    ],
)
def test_content_bearing_params_kept(url):
    assert clean_url(url) == url
