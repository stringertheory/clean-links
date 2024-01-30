import json


def read_config(
    additional_config_filename: str = "clean_links/clearurls_config.json"
) -> dict:
    with open("clean_links/clearurls.json") as infile:
        clear_urls_rules = dict(json.load(infile))

    with open(additional_config_filename) as infile:
        additional_rules = json.load(infile)

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
