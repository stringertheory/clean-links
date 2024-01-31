import json
import pkgutil


def read_json(filename: str) -> dict:
    data = pkgutil.get_data(__name__, filename)
    if data is None:
        msg = f"didn't find config file {filename}"
        raise FileNotFoundError(msg)

    return dict(json.loads(data.decode("utf8")))


def read_config(
    additional_config_filename: str = "clearurls_config.json",
) -> dict:
    clear_urls_rules = read_json("clearurls.json")
    additional_rules = read_json(additional_config_filename)

    for provider_name, rules in additional_rules["providers"].items():
        provider = clear_urls_rules["providers"].get(provider_name)
        if not provider:
            clear_urls_rules["providers"][provider_name] = {
                "urlPattern": None,
                "completeProvider": False,
                "rules": [],
                "referralMarketing": [],
                "exceptions": [],
                "rawRules": [],
                "redirections": [],
                "forceRedirection": False,
            }
            provider = clear_urls_rules["providers"][provider_name]

        for key, value in rules.items():
            if key in ["rules"]:
                provider[key].extend(value)
            else:
                provider[key] = value

    return clear_urls_rules
