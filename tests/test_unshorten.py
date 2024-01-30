import pytest

from clean_links.unshorten import unshorten_url


# cassettes/{module_name}/test_single.yaml will be used
@pytest.mark.vcr
def test_unchanged():
    url = "https://example.com/"
    result = unshorten_url(url)
    assert result == {
        "url": url,
        "resolved": "https://example.com/",
        "status": 200,
        "exception": None,
    }


@pytest.mark.vcr
def test_single_redirect():
    url = "https://trib.al/5m7fAg3"
    result = unshorten_url(url)
    assert result == {
        "url": url,
        "resolved": "https://www.bloomberg.com/news/articles/2024-01-24/cryptocurrency-ai-electricity-demand-seen-doubling-in-three-years?cmpid%3D=socialflow-twitter-tech&utm_content=tech&utm_medium=social&utm_campaign=socialflow-organic&utm_source=twitter",
        "status": 200,
        "exception": None,
    }


@pytest.mark.vcr
def test_multiple_redirect():
    url = "https://hubs.la/Q01HRjhm0"
    result = unshorten_url(url)
    print(result)
    assert result == {
        "url": url,
        "resolved": "https://app.east.mentorspaces.com/#!/orgs/6aab4989-2bd1-7ec9-6e3f-56f3128815c8/?utm_content=242450506&utm_medium=social&utm_source=twitter&hss_channel=tw-18419094&_branch_match_id=1280732352261121106&utm_campaign=fall-recruiting&_branch_referrer=H4sIAAAAAAAAAx3KUQqEIBAA0Nv0V1rYsgXSUcJmB5R0FGek61f7%2B3hepPCqVEKSXLk4QB5cKUMMdCriA7cmaYdM8gw7mcnMetaf7tWEv9CS5QzBxb9wbhXQyhVEsHaeeQfviDA%2B1o9fMy56MTdcnGABdQAAAA%3D%3D",
        "status": 200,
        "exception": None,
    }


@pytest.mark.vcr
def test_expired_certificate_ignore():
    url = "https://expired.badssl.com/"
    result = unshorten_url(url, verify=False)
    assert result == {
        "url": url,
        "resolved": "https://expired.badssl.com/",
        "status": 200,
        "exception": None,
    }


def test_expired_certificate_verify():
    url = "https://expired.badssl.com/"
    result = unshorten_url(url, verify=True)
    assert result["url"] == "https://expired.badssl.com/"
    assert result["resolved"] == "https://expired.badssl.com/"
    assert result["status"] is None
    assert result["exception"].startswith("SSLError:")
