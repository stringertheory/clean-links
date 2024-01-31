import json
import pkgutil


def read_config(
    additional_config_filename: str = "clearurls_config.json",
) -> dict:
    data = pkgutil.get_data(__name__, "clearurls.json").decode("utf8")
    clear_urls_rules = dict(json.loads(data))

    data = pkgutil.get_data(__name__, additional_config_filename).decode("utf8")
    additional_rules = dict(json.loads(data))

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
