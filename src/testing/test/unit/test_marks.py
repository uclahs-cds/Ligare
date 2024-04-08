from pytest import Pytester


def test__mark_category(pytester: Pytester):
    _ = pytester.makepyfile(
        conftest="""
        from BL_Python.testing.markers import pytest_addoption, pytest_collection_modifyitems, pytest_configure
    """
    )
    _ = pytester.makepyfile("""
        import pytest

        @pytest.mark.category("foo")
        @pytest.mark.issue("GH123")
        def test__foo():
            assert True

        @pytest.mark.category("bar")
        def test__bar():
            assert True
    """)

    result = pytester.runpytest(
        # for some reason pytest is discovering
        # all the tests ... maybe the hook isn't
        # called? maybe inline_run() can help.
        "-s",
        "-v",
        "-p",
        "BL_Python.testing.markers",
        "--mark-issue='GH123'",
    )
    # result.assert_outcomes(passed=1)
    pass


# @pytest.mark.category("bar")
# @pytest.mark.issue("GH456")
# def test__bar():
#    pass
#
#
# @pytest.mark.category("baz")
# @pytest.mark.issue("GH789")
# def test__baz():
#    x = 1 / 0
#
