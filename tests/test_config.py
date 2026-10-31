import pytest

from clean_links import config

real_read_json = config.read_json


def _with_upstream_renamed(monkeypatch, old, new):
    """Simulate a ClearURLs refresh that renamed provider ``old``."""

    def fake_read_json(filename):
        data = real_read_json(filename)
        if filename == "clearurls.json":
            providers = data["providers"]
            providers[new] = providers.pop(old)
        return data

    monkeypatch.setattr(config, "read_json", fake_read_json)


def test_shipped_overlay_matches_vendored_rules():
    # Fails loudly after `make update-clearurls` if upstream renamed a
    # provider that clearurls_config.json extends.
    config.read_config()


def test_renamed_upstream_provider_names_the_entry(monkeypatch):
    _with_upstream_renamed(monkeypatch, "etsy.com", "etsy")
    with pytest.raises(ValueError, match=r"'etsy\.com'.*no urlPattern"):
        config.read_config()


def test_new_provider_with_its_own_pattern_is_fine():
    # wsj isn't a ClearURLs provider; it brings its own urlPattern.
    rules = config.read_config()
    assert rules["providers"]["wsj"]["urlPattern"].match(
        "https://www.wsj.com/articles/x"
    )
