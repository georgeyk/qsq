# -*- coding: utf-8 -*-

from pprint import pformat
import json

import jmespath
from jmespath.exceptions import JMESPathError

from .exceptions import FilterError


def json_filter(expr, data):
    if not expr:
        return data
    if not data:
        return []

    try:
        return jmespath.search(expr, data)
    except JMESPathError as exc:
        raise FilterError('Invalid filter: {}'.format(exc))
