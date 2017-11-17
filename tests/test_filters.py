import pytest

from qsq.exceptions import FilterError
from qsq.filters import json_filter


@pytest.fixture
def json_data():
    return {
        'name': 'foobar',
        'age': 42,
        'fruits': ['apple', 'kiwi']
    }


def test_simple_filter(json_data):
    results = json_filter('name', json_data)
    assert results == 'foobar'


@pytest.mark.parametrize('expr', ['', None, []])
def test_missing_expr_filter(expr, json_data):
    results = json_filter(expr, json_data)
    assert results == json_data


@pytest.mark.parametrize('data', ['', None, []])
def test_missing_data_filter(data):
    results = json_filter('age', data)
    assert results == []


def test_filter_error_with_invalid_expr(json_data):
    with pytest.raises(FilterError):
        json_filter('?', json_data)
