import json
import pkgutil
import re
import warnings


def read_json(filename: str) -> dict:
    data = pkgutil.get_data(__name__, filename)
    if data is None:
        msg = f"didn't find config file {filename}"
        raise FileNotFoundError(msg)

    return dict(json.loads(data.decode("utf8")))


def compile_list(rules: dict, key: str, provider_name: str) -> None:
    result = []
    for pattern in rules.get(key, []):
        try:
            compiled = re.compile(pattern, flags=re.IGNORECASE)
        except re.error as exc:
            msg = (
                f"{exc!r}. "
                f"Could not compile the regex {pattern!r} in {key!r} section "
                f"of {provider_name!r}. Skipping"
            )
            warnings.warn(msg, stacklevel=2)
        else:
            result.append(compiled)
    rules[key] = result


def compile_patterns(all_rules: dict) -> None:
    for provider_name, rules in all_rules["providers"].items():
        rules["urlPattern"] = re.compile(
            rules["urlPattern"], flags=re.IGNORECASE
        )
        rules["rules"] = [
            re.compile(f"^{r}$", flags=re.IGNORECASE)
            for r in rules.get("rules", [])
        ]
        for key in [
            "referralMarketing",
            "exceptions",
            "rawRules",
            "redirections",
        ]:
            compile_list(rules, key, provider_name)


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

    compile_patterns(clear_urls_rules)
    return clear_urls_rules
