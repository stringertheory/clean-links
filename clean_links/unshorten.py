import contextlib
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


def send(
    session: requests.Session,
    prepped: requests.PreparedRequest,
    history: dict,
    verify: bool,
    timeout: float,
) -> Union[requests.PreparedRequest, None]:
    history["requests"].append(prepped)
    try:
        response = session.send(
            prepped, allow_redirects=False, verify=verify, timeout=timeout
        )
    except requests.exceptions.RequestException as exc:
        exc.history = history
        raise
    else:
        history["responses"].append(response)

    return response.next


def request_redirect_chain(
    session: requests.Session,
    url: str,
    verify: bool,
    timeout: float,
    headers: dict,
    method: str = "HEAD",
) -> dict:
    history: dict = {
        "requests": [],
        "responses": [],
    }

    # prepare initial request
    request = requests.Request(method, url, headers=headers)
    prepped = session.prepare_request(request)

    # send and follow the redirect chain, filling in the history
    next_prepped = send(session, prepped, history, verify, timeout)
    while next_prepped:
        next_prepped = send(session, next_prepped, history, verify, timeout)

    return history


def format_exception(exc: Union[Exception, None]) -> Union[str, None]:
    if exc is None:
        return None
    else:
        return f"{type(exc).__name__}: {exc}"


def unshorten_url(
    url: str, timeout: float = 9, verify: bool = False, headers: dict = HEADERS
) -> dict:
    with requests.Session() as session, disable_ssl_warnings():
        exception = None
        try:
            history = request_redirect_chain(
                session, url, verify, timeout, headers, "HEAD"
            )
        except requests.exceptions.RequestException as exc:
            exception = exc
            history = getattr(exc, "history", {})
            if not history or not history["responses"]:
                raise

        response = history["responses"][-1]
        return {
            "url": url,
            "resolved": response.url,
            "status": response.status_code,
            "exception": format_exception(exception),
            "request_history": [r.url for r in history["requests"]],
            "response_history": [r.status_code for r in history["responses"]],
        }
