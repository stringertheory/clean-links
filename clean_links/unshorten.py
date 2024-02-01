import contextlib
import warnings
from itertools import zip_longest
from typing import Generator, Union

import requests
import urllib3

HEADERS = {
    "accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/avif,image/webp,image/apng,*/*;"
        "q=0.8,application/signed-exchange;v=b3;q=0.7"
    ),
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "en-US,en;q=0.9",
    "sec-fetch-dest": "document",
    "sec-fetch-mode": "navigate",
    "sec-fetch-site": "same-origin",
    "sec-fetch-user": "?1",
    "upgrade-insecure-requests": "1",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}


@contextlib.contextmanager
def _disable_ssl_warnings() -> Generator:
    with warnings.catch_warnings():
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        yield None


def _send(
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


def _request_redirect_chain(
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
    next_prepped = _send(session, prepped, history, verify, timeout)
    while next_prepped:
        next_prepped = _send(session, next_prepped, history, verify, timeout)

    return history


def _format_exception(exc: Union[Exception, None]) -> Union[str, None]:
    if exc is None:
        return None
    else:
        return f"{type(exc).__name__}: {exc}"


def unshorten_url(
    url: str, timeout: float = 9, verify: bool = False, headers: dict = HEADERS
) -> dict:
    with requests.Session() as session, _disable_ssl_warnings():
        exception = None
        try:
            history = _request_redirect_chain(
                session, url, verify, timeout, headers, "HEAD"
            )
        except requests.exceptions.RequestException as exc:
            exception = exc
            history = getattr(exc, "history", {})
            if not history or not history["requests"]:
                raise

        pairs = list(zip_longest(history["requests"], history["responses"]))
        for req, res in pairs:
            if res is not None and req.url != res.url:
                msg = (
                    "something's wrong. "
                    "url of request and response don't match."
                )
                raise ValueError(msg)

        last_request, last_response = pairs[-1]

        return {
            "url": url,
            "resolved": last_request.url,
            "status": last_response.status_code if last_response else None,
            "exception": _format_exception(exception),
            "request_history": [r.url for r in history["requests"]],
            "response_history": [r.status_code for r in history["responses"]],
        }


if __name__ == "__main__":
    result = unshorten_url("https://dingle.berries/")
    print(result)
