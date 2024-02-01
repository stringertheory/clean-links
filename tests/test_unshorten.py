import pytest
import requests

from clean_links.unshorten import unshorten_url


def test_missing_schema():
    url = "Ceci n'est pas une URL"
    with pytest.raises(requests.exceptions.MissingSchema):
        unshorten_url(url)


def test_not_an_address():
    url = "https://dingle.berries/"
    result = unshorten_url(url)
    assert result["url"] == url
    assert result["resolved"] == url
    assert result["status"] is None
    assert result["exception"].startswith("ConnectionError")
    assert result["request_history"] == [url]
    assert result["response_history"] == []


@pytest.mark.vcr
def test_unchanged():
    url = "https://example.com/"
    result = unshorten_url(url)
    assert result == {
        "url": url,
        "resolved": "https://example.com/",
        "status": 200,
        "exception": None,
        "request_history": ["https://example.com/"],
        "response_history": [200],
    }


@pytest.mark.vcr
def test_single_redirect():
    url = "https://trib.al/5m7fAg3"
    result = unshorten_url(url)
    resolved = "https://www.bloomberg.com/news/articles/2024-01-24/cryptocurrency-ai-electricity-demand-seen-doubling-in-three-years?cmpid%3D=socialflow-twitter-tech&utm_content=tech&utm_medium=social&utm_campaign=socialflow-organic&utm_source=twitter"
    assert result == {
        "url": url,
        "resolved": resolved,
        "status": 200,
        "exception": None,
        "request_history": [url, resolved],
        "response_history": [301, 200],
    }


@pytest.mark.vcr
def test_multiple_redirect():
    url = "https://hubs.la/Q01HRjhm0"
    result = unshorten_url(url)
    resolved = "https://app.east.mentorspaces.com/#!/orgs/6aab4989-2bd1-7ec9-6e3f-56f3128815c8/?utm_content=242450506&utm_medium=social&utm_source=twitter&hss_channel=tw-18419094&_branch_match_id=1280732352261121106&utm_campaign=fall-recruiting&_branch_referrer=H4sIAAAAAAAAAx3KUQqEIBAA0Nv0V1rYsgXSUcJmB5R0FGek61f7%2B3hepPCqVEKSXLk4QB5cKUMMdCriA7cmaYdM8gw7mcnMetaf7tWEv9CS5QzBxb9wbhXQyhVEsHaeeQfviDA%2B1o9fMy56MTdcnGABdQAAAA%3D%3D"
    assert result == {
        "url": url,
        "resolved": resolved,
        "status": 200,
        "exception": None,
        "request_history": [
            url,
            "https://mentorspaces.app.link/nsbe?utm_content=242450506&utm_medium=social&utm_source=twitter&hss_channel=tw-18419094",
            "https://app.east.mentorspaces.com/orgs/6aab4989-2bd1-7ec9-6e3f-56f3128815c8/?utm_content=242450506&utm_medium=social&utm_source=twitter&hss_channel=tw-18419094&_branch_match_id=1280732352261121106&utm_campaign=fall-recruiting&_branch_referrer=H4sIAAAAAAAAAx3KUQqEIBAA0Nv0V1rYsgXSUcJmB5R0FGek61f7%2B3hepPCqVEKSXLk4QB5cKUMMdCriA7cmaYdM8gw7mcnMetaf7tWEv9CS5QzBxb9wbhXQyhVEsHaeeQfviDA%2B1o9fMy56MTdcnGABdQAAAA%3D%3D",
            "http://app.east.mentorspaces.com/#!/orgs/6aab4989-2bd1-7ec9-6e3f-56f3128815c8/?utm_content=242450506&utm_medium=social&utm_source=twitter&hss_channel=tw-18419094&_branch_match_id=1280732352261121106&utm_campaign=fall-recruiting&_branch_referrer=H4sIAAAAAAAAAx3KUQqEIBAA0Nv0V1rYsgXSUcJmB5R0FGek61f7%2B3hepPCqVEKSXLk4QB5cKUMMdCriA7cmaYdM8gw7mcnMetaf7tWEv9CS5QzBxb9wbhXQyhVEsHaeeQfviDA%2B1o9fMy56MTdcnGABdQAAAA%3D%3D",
            resolved,
        ],
        "response_history": [301, 307, 301, 301, 200],
    }


@pytest.mark.vcr
def test_expired_certificate_ignore():
    url = "https://expired.badssl.com/"
    result = unshorten_url(url, verify=False)
    resolved = "https://expired.badssl.com/"
    assert result == {
        "url": url,
        "resolved": resolved,
        "status": 200,
        "exception": None,
        "request_history": [url],
        "response_history": [200],
    }


@pytest.mark.vcr
def test_resolve_to_mailto():
    url = "https://tinyurl.com/NewwAlemAndKibrom"
    result = unshorten_url(url)
    assert result["url"] == url
    assert result["resolved"].startswith("mailto:center@moi.gov.eg")
    assert result["status"] is None
    assert result["exception"].startswith("InvalidSchema: No connection adap")
    assert result["request_history"][0] == url
    assert result["request_history"][1].startswith("mailto:center@moi.gov.eg")
    assert result["response_history"] == [301]


@pytest.mark.vcr
def test_invalid_url_in_redirect_chain():
    """What should this actually do?

    Throw error like if it was an invalid URL to begin with?

    Or should it return the last valid URL in the redirect chain?

    I think the last URL in the chain..

    """
    url = "https://ctt.ec/5kum7+"
    result = unshorten_url(url)
    resolved = "http://"
    assert result == {
        "url": url,
        "resolved": resolved,
        "status": None,
        "exception": "InvalidURL: No host specified.",
        "request_history": [url, "https://clicktotweet.com/5kum7+", "http://"],
        "response_history": [301, 302],
    }


# def test_expired_certificate_verify():
#     url = "https://expired.badssl.com/"
#     result = unshorten_url(url, verify=True)
#     assert result["url"] == "https://expired.badssl.com/"
#     assert result["resolved"] == "https://expired.badssl.com/"
#     assert result["status"] is None
#     assert result["exception"].startswith("SSLError:")
