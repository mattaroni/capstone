# Copyright 2026 Matthew Marshall
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import annotationlib
from collections.abc import Callable
from functools import partial

# local modules
from _processor import Article, Token


def _double_apostrophes(value: str | int | float) -> str | int | float:
    if isinstance(value, str):
        value = value.replace("'", "''")

    return value


def _remove_backslashes(value: str) -> str:
    return value.replace('\\', '')


def _to_sqlite_value_expr(processed_data: Article | Token) -> str:
    values = vars(processed_data).values()
    values = map(_double_apostrophes, values)
    values = map(repr, values)
    values = map(_remove_backslashes, values)
    return ', '.join(values)


def make_insert_command_factory(
    table_name: str,
    expected_class: type[Article | Token],
) -> Callable[[Article | Token], str]:
    columns = annotationlib.get_annotations(expected_class)
    joined_columns = ', '.join(columns)
    template = f'INSERT INTO {table_name} ({joined_columns}) VALUES ({{}});'

    def make_insert_command(data: Article | Token) -> str:
        values = _to_sqlite_value_expr(data)
        return template.format(values)

    return make_insert_command
