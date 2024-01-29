import logging
import re
from urllib.parse import parse_qs, urlencode, urlsplit

from clean_links.config import read_config
from clean_links.unshorten import unshorten_url

clear_urls_rules = read_config()


def query_string(url: str, rules: list) -> str:
    split = urlsplit(url)
    params = parse_qs(split.query)

    delete_keys = {None, ""}
    for rule in rules:
        for key in params:
            if re.match("^" + rule + "$", key, flags=re.IGNORECASE):
                delete_keys.add(key)

    for delete_key in delete_keys:
        params.pop(delete_key, "")  # type: ignore[arg-type]

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


def clear_url(
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


def main() -> None:
    url = "https://www.amazon.com/Kobo-Glare-Free-Touchscreen-ComfortLight-Adjustable/dp/B0BCXLQNCC/ref=pd_ci_mcx_mh_mcx_views_0?pd_rd_w=Dx5dF&content-id=amzn1.sym.225b4624-972d-4629-9040-f1bf9923dd95%3Aamzn1.symc.40e6a10e-cbc4-4fa5-81e3-4435ff64d03b&pf_rd_p=225b4624-972d-4629-9040-f1bf9923dd95&pf_rd_r=A7JSDJGYR33BN5GRCV7V&pd_rd_wg=xW6Yf&pd_rd_r=4b8a3532-9e28-4857-a929-5e572d2c765f&pd_rd_i=B0BCXLQNCC"

    url = "https://trib.al/5m7fAg3"
    # url = "https://tinyurl.com/yc2ft9m5"
    # url = "https://bit.ly/3C4WXQ9"
    # url = 'https://tinyurl.com/NewwAlemAndKibrom'
    # url = "https://hubs.la/Q01HRjhm0"
    # url = "https://buff.ly/3Omwkwd"
    # url = "https://bit.ly/48RtRlw"
    # url = "https://srv.buysellads.com/ads/long/x/TCHU7KSHTTTTTTH6NPRNPTTTTTTFNZMBKWTTTTTTA4RZC7VTTTTTTBZI5HINWLB6G3DIEMS4PABU5AIEQQY6BADG2HUT"
    # url = "https://buff.ly/2RjYjMt"

    print(url)
    print()
    resolved = unshorten_url(url).get("resolved", "")
    print(resolved)
    print()
    clear = clear_url(resolved)  # , keep_query=False, keep_fragment=False)
    print(clear)
    # print(url)
    # original, resolved, status = resolve_url(url, 10)
    # print(original)
    # print(resolved)


if __name__ == "__main__":
    main()
