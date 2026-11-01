# Contributing to `clean-links`

Contributions are welcome, and they are greatly appreciated!
Every little bit helps, and credit will always be given.

You can contribute in many ways:

# Types of Contributions

## Report Bugs

Report bugs at https://github.com/stringertheory/clean-links/issues

If you are reporting a bug, please include:

- Your operating system name and version.
- Any details about your local setup that might be helpful in troubleshooting.
- Detailed steps to reproduce the bug.

## Fix Bugs

Look through the GitHub issues for bugs.
Anything tagged with "bug" and "help wanted" is open to whoever wants to implement a fix for it.

## Implement Features

Look through the GitHub issues for features.
Anything tagged with "enhancement" and "help wanted" is open to whoever wants to implement it.

## Write Documentation

Cookiecutter PyPackage could always use more documentation, whether as part of the official docs, in docstrings, or even on the web in blog posts, articles, and such.

## Submit Feedback

The best way to send feedback is to file an issue at https://github.com/stringertheory/clean-links/issues.

If you are proposing a new feature:

- Explain in detail how it would work.
- Keep the scope as narrow as possible, to make it easier to implement.
- Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

# Get Started!

Ready to contribute? Here's how to set up `clean-links` for local development.
Please note this documentation assumes you already have `poetry` and `Git` installed and ready to go.

1. Fork the `clean-links` repo on GitHub.

2. Clone your fork locally:

```bash
cd <directory_in_which_repo_should_be_created>
git clone git@github.com:YOUR_NAME/clean-links.git
```

3. Now we need to install the environment. Navigate into the directory

```bash
cd clean-links
```

If you are using `pyenv`, select a version to use locally. (See installed versions with `pyenv versions`)

```bash
pyenv local <x.y.z>
```

Then, install and activate the environment with:

```bash
poetry install
poetry shell
```

4. Install pre-commit to run linters/formatters at commit time:

```bash
poetry run pre-commit install
```

5. Create a branch for local development:

```bash
git checkout -b name-of-your-bugfix-or-feature
```

Now you can make your changes locally.

6. Don't forget to add test cases for your added functionality to the `tests` directory.

7. When you're done making changes, check that your changes pass the formatting tests.

```bash
make check
```

Now, validate that all unit tests are passing:

```bash
make test
```

9. Before raising a pull request you should also run tox.
   This will run the tests across different versions of Python:

```bash
tox
```

This requires you to have multiple versions of python installed.
This step is also triggered in the CI/CD pipeline, so you could also choose to skip this step locally.

10. Commit your changes and push your branch to GitHub:

```bash
git add .
git commit -m "Your detailed description of your changes."
git push origin name-of-your-bugfix-or-feature
```

11. Submit a pull request through the GitHub website.

# Cleaning rules

Which query parameters get stripped is decided by two files in `clean_links/`:

- **`clearurls.json`** is a vendored copy of the upstream
  [ClearURLs](https://gitlab.com/ClearURLs/ClearUrls) ruleset. Don't edit it
  by hand. Refresh it with:

  ```bash
  make update-clearurls
  git diff clean_links/clearurls.json   # review what upstream changed
  make test
  ```

- **`clearurls_config.json`** holds this project's own rules, layered on top
  of the vendored file when the package is imported. An entry that names an
  existing ClearURLs provider adds to that provider's `rules` (other keys,
  such as `urlPattern`, replace upstream's). An entry with a new name creates
  a new provider and must include its own `urlPattern`.

If a refresh renames or removes a provider that `clearurls_config.json`
extends, importing the package fails with a `ValueError` naming the entry.
Rename the entry to the provider's new name (or give it a `urlPattern`).

## Adding a rule

The project's rule of thumb: wrongly merging two different pages is worse
than failing to merge two copies of the same page. So only add a parameter
when it is purely tracking and never changes what the page shows.

- Rules are regexes matched against the whole parameter name,
  case-insensitively. Prefer exact names (`gbraid`) or closed lists
  (`pk_(?:campaign|source)`) over open wildcards.
- Put a name in `globalRules` only if it is unambiguous on every site. Names
  that are tracking on one site but could mean something elsewhere (`ref`,
  `source`, `s`) belong under that site's provider.
- A new provider's `urlPattern` should end at the domain, e.g. (as written in the JSON)
  `^https?://(?:[a-z0-9-]+\\.)*?example\\.com(?:[:/?#]|$)`, so lookalike
  hosts such as `example.com.evil.org` don't match.
- Add tests to `tests/test_clean.py`: one showing the parameter is stripped
  where it should be, and one showing it is kept elsewhere.

Useful sources for candidate parameters are upstream ClearURLs and Firefox's
"Copy Clean Link" lists
(`toolkit/components/antitracking/StripOnShareLists` in mozilla-central).
Firefox's lists are tuned for links a person sees and can fix, so check each
name before adopting it rather than importing them wholesale.

Rule changes apply to already-cached links straight away: the cache stores
where each link ends up, and the key is recomputed on every lookup.

# Pull Request Guidelines

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests.

2. If the pull request adds functionality, the docs should be updated.
   Put your new functionality into a function with a docstring, and add the feature to the list in `README.md`.
