"""
Support for selecting tests based on the value of custom marks.

Tests can be marked as follows:

```
@pytest.mark.category("my-category")
def test_foo():
    pass

@pytest.mark.issue("GH123")
def test_bar():
    pass
```

On the command like, these are used as follows:
```
pytest --mark-issue="GH123"
# specify several values with spaces and commas
pytest --mark-issue="GH123 GH456,GH789"
pytest --mark-category="issue"
pytest --mark-category="foo"
pytest --mark-category="issue foo"
pytest --mark-issue="GH123" --mark-category="bar,baz"
```

Note that specifying both mark options is an _or_ filter. Any tests
with any matching marks are included.
Specifying `--mark-issue` or `--mark-category` multiple times will
only search for marks matching the last instance of its use.
"""

import logging
import re

import _pytest.config
import _pytest.main
import _pytest.python

_MARKER_FILTER_OPTION_PREFIX = "--mark-"
_MARKER_FILTER_OPTION_ISSUE = "issue"
_MARKER_FILTER_OPTION_CATEGORY = "category"
_MARKER_FILTER_OPTIONS = [_MARKER_FILTER_OPTION_ISSUE, _MARKER_FILTER_OPTION_CATEGORY]


def pytest_configure(config: _pytest.config.Config):
    config.addinivalue_line(
        "markers",
        f"{_MARKER_FILTER_OPTION_ISSUE}(...): GitHub issue related to the marked test. Must have a value when specified. Can be specified multiple times.",
    )
    config.addinivalue_line(
        "markers",
        f"{_MARKER_FILTER_OPTION_CATEGORY}(...): Arbitrary category of the marked test. Must have a value when specified. Can be specified multiple times.",
    )


# https://stackoverflow.com/a/67201943
def pytest_addoption(
    parser: _pytest.main.Parser,  # pyright: ignore[reportPrivateImportUsage]
):
    parser.addoption(
        f"{_MARKER_FILTER_OPTION_PREFIX}{_MARKER_FILTER_OPTION_ISSUE}",
        action="store",
        help="Specify specific issues to filter for.",
    )
    parser.addoption(
        f"{_MARKER_FILTER_OPTION_PREFIX}{_MARKER_FILTER_OPTION_CATEGORY}",
        action="store",
        help="Specify specific categories to filter for.",
    )


def _pytest_collection_modifyitems_collect_custom_marks(
    items: list[_pytest.python.Function],
):
    """Add custom mark values to properties of tests"""

    for item in items:
        issue_category_set = False
        for marker in item.iter_markers(name=_MARKER_FILTER_OPTION_CATEGORY):
            if not marker.args:
                raise ValueError(
                    f"""No category given for "{_MARKER_FILTER_OPTION_CATEGORY}" marker for test {item.name}"""
                )
            for category in marker.args:
                item.user_properties.append((_MARKER_FILTER_OPTION_CATEGORY, category))

        for marker in item.iter_markers(name=_MARKER_FILTER_OPTION_ISSUE):
            if not issue_category_set:
                if not marker.args:
                    raise ValueError(
                        f"""No issue number given for "{_MARKER_FILTER_OPTION_ISSUE}" marker for test {item.name}"""
                    )
                item.user_properties.append((
                    _MARKER_FILTER_OPTION_CATEGORY,
                    _MARKER_FILTER_OPTION_ISSUE,
                ))
                issue_category_set = True

            for issue in marker.args:
                item.user_properties.append((_MARKER_FILTER_OPTION_ISSUE, issue))


def _pytest_collection_modifyitems_add_custom_marks(
    config: _pytest.config.Config,
    items: list[_pytest.python.Function],
):
    """filter tests to execute the the value supplied for that mark"""

    new_items: set[_pytest.python.Function] = set()
    for marker_filter_option in _MARKER_FILTER_OPTIONS:
        marker_filter = config.getoption(
            f"{_MARKER_FILTER_OPTION_PREFIX}{marker_filter_option}"
        )
        if marker_filter is not None:
            if not marker_filter or isinstance(marker_filter, _pytest.config.Notset):
                raise Exception(
                    f"Empty {_MARKER_FILTER_OPTION_PREFIX}{marker_filter_option} parameter given. Must specify a value."
                )

            filter_values: set[str] = set(re.split(r"\s+|,+", marker_filter))
            for item in items:
                marker = item.get_closest_marker(marker_filter_option)
                if marker and marker.args and marker.args[0] in filter_values:
                    # Add unique tests that contain the value for the marker
                    new_items.add(item)

    if new_items:
        logger = logging.getLogger()
        logger.info(f"\nselected {len(new_items)} tests from marker filters")
        items[:] = list(new_items)


def pytest_collection_modifyitems(
    session: _pytest.main.Session,
    config: _pytest.config.Config,
    items: list[_pytest.python.Function],
):
    _pytest_collection_modifyitems_collect_custom_marks(items)

    _pytest_collection_modifyitems_add_custom_marks(config, items)
