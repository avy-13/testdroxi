import pytest

from main import gmail_login


@pytest.fixture
def example_of_injected_item():
    return {'a': 1}


def test_gmail_login(example_of_injected_item: dict[str, int]):
    creds = gmail_login()

    assert len(creds.client_id) > 0
    # assert creds.token_uri == "https://oauth2.googleapis.com/token"

    assert example_of_injected_item.get('b', None) is None
    assert example_of_injected_item.get('a', None) == 1


def test_simple(example_of_injected_item):

    example_of_injected_item['b'] = 10
    example_of_injected_item['a'] += 1

    assert example_of_injected_item['a'] == 2


def exception_raising_func():
    raise ValueError("Exception 123 raised")


def test_match():
    with pytest.raises(ValueError, match=r".* 123 .*"):
        exception_raising_func()
