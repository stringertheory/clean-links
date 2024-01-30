import logging
from typing import Union

import requests
from urllib3.exceptions import InsecureRequestWarning

# suppress warning about that's given when using verify=False
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

__packagename__ = "CleanLinks"
__version__ = "0.01"
__url__ = "https://github.com/stringertheory/clean-links"

USER_AGENT = f"{__packagename__}/{__version__} ({__url__})"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HEADERS = {
    "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": USER_AGENT,
}


def get_last_url_from_exception(exc: Exception) -> Union[str, None]:
    result = None

    try:
        if exc.response and exc.response.url:
            result = exc.response.url
        elif exc.request:
            result = exc.request.url
    except Exception as exc:
        logging.exception("exception occurred while getting last url")

    return result


def unshorten_url(
    url: str, timeout: int = 9, verify: bool = False, headers: dict = HEADERS
) -> dict:
    with requests.Session() as session:
        try:
            response = session.head(
                url,
                allow_redirects=True,
                timeout=timeout,
                headers=headers,
                verify=verify,
            )
        except Exception as exc:
            return {
                "url": url,
                "resolved": get_last_url_from_exception(exc),
                "status": None,
                "exception": f"{type(exc).__name__}: {exc}",
            }
        else:
            return {
                "url": url,
                "resolved": response.url,
                "status": response.status_code,
                "exception": None,
            }


def main() -> None:
    url = "https://trib.al/5m7fAg3"
    url = "https://www.bloomberg.com/news/articles/2024-01-24/cryptocurrency-ai-electricity-demand-seen-doubling-in-three-years?cmpid%3D=socialflow-twitter-tech&utm_content=tech&utm_medium=social&utm_campaign=socialflow-organic&utm_source=twitter"
    url = "https://tinyurl.com/yc2ft9m5"
    url = "https://bit.ly/3C4WXQ9"
    # url = 'https://tinyurl.com/NewwAlemAndKibrom'
    url = "https://hubs.la/Q01HRjhm0"

    print(unshorten_url(url))


if __name__ == "__main__":
    main()
