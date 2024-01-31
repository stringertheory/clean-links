import logging
import re
from urllib.parse import parse_qs, urlencode, urlsplit

from clean_links.config import read_config

clear_urls_rules = read_config()


def query_string(url: str, rules: list) -> str:
    split = urlsplit(url)
    params = parse_qs(split.query)

    delete_keys = {""}
    for rule in rules:
        for key in params:
            if re.match("^" + rule + "$", key, flags=re.IGNORECASE):
                delete_keys.add(key)

    for delete_key in delete_keys:
        params.pop(delete_key, None)

    params_string = urlencode(params, doseq=True)

    if params_string:
        return split.path + "?" + params_string
    else:
        return split.path


def match_provider(provider: str, url: str, rules: dict) -> bool:
    match_url = re.match(rules["urlPattern"], url)
    match_exception = None
    for exception_pattern in rules["exceptions"]:
        try:
            match_exception = re.match(exception_pattern, url)
        except Exception:
            logging.exception(
                f"something's wrong with regex {exception_pattern!r} "
                f"for provider {provider!r}."
            )

        if match_exception:
            break
    return bool(match_url and not match_exception)


def clean_url(
    url: str, keep_query: bool = True, keep_fragment: bool = True
) -> str:
    for provider_name, rules in clear_urls_rules["providers"].items():
        if match_provider(provider_name, url, rules):
            for rule in rules["rawRules"]:
                url = re.sub(rule, "", url, flags=re.IGNORECASE)

            split = urlsplit(url)
            if keep_query:
                full_path = query_string(url, rules["rules"])
            else:
                full_path = split.path

            relative = full_path
            if keep_fragment:
                fragment_path = query_string(split.fragment, rules["rules"])
                if fragment_path:
                    relative += "#" + fragment_path

            url = f"{split.scheme}://{split.netloc}{relative}"

    return url
