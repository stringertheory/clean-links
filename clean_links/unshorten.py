import contextlib
import logging
import warnings
from typing import Generator, Union

import requests
import urllib3

from clean_links import __version__

USER_AGENT = f"clean-links/{__version__}"
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


@contextlib.contextmanager
def disable_ssl_warnings() -> Generator:
    with warnings.catch_warnings():
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        yield None


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
    with requests.Session() as session, disable_ssl_warnings():
        try:
            response = session.head(
                url,
                allow_redirects=True,
                timeout=timeout,
                headers=headers,
                verify=verify,
            )
        except requests.exceptions.MissingSchema:
            raise
        except requests.exceptions.InvalidURL:
            raise
        except requests.exceptions.InvalidSchema as exc:
            msg = str(exc)
            if msg.startswith("No connection adapters were found"):
                resolved = msg[39:-1]
                return {
                    "url": url,
                    "resolved": resolved,
                    "status": None,
                    "exception": f"{type(exc).__name__}: {exc}",
                }
            else:
                raise
        except requests.exceptions.RequestException as exc:
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
    url = "https://expired.badssl.com/"
    url = "https://tinyurl.com/NewwAlemAndKibrom"

    print(unshorten_url(url, verify=True))


if __name__ == "__main__":
    main()
