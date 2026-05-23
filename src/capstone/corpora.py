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

import csv
import datetime
import sqlite3
from collections.abc import Generator, Iterable
from contextlib import contextmanager
from functools import partial
from pathlib import Path
from typing import Self

# third-party modules
from asent.data_classes import DocPolarityOutput
from spacy.tokens import Token

# local modules
from log_settings import logger # TODO: actually use
from _processor import Article, Token, ArticleProcessor
from _sqlite_tools import make_insert_command_factory

_get_sql_insert_article = make_insert_command_factory('articles', Article)
_get_sql_insert_token_true = make_insert_command_factory('tokens_true', Token)
_get_sql_insert_token_fake = make_insert_command_factory('tokens_fake', Token)


# testing

class Corpus:
    def __init__(self, database: str, setup_script: str | None = None) -> None:
        self._database = database
        self._processor = ArticleProcessor()

        if setup_script:
            with open(setup_script) as file:
                self._setup_script = file.read()
        else:
            self._setup_script = None

        # defaults
        self._article_count = 0
        self._connection: sqlite3.Connection | None = None

    def add_article(
        self,
        title: str,
        text: str,
        subject: str,
        date: str,
        is_true: bool,
    ) -> None:
        error_message = 'failed to add article: "{}"'
        self._article_count += 1

        try:
            article, tokens = self._processor.process(
                self._article_count,
                title.lstrip(),
                text,
                subject,
                date.rstrip(),
                is_true,
            )
        except ValueError as err:
            logger.debug(f'corpus fed invalid date value: {date}')
            logger.error(error_message.format(title))
            self._article_count -= 1
            return None

        commands = [_get_sql_insert_article(article)]

        if is_true:
            get_sql_insert_token = _get_sql_insert_token_true
        else:
            get_sql_insert_token = _get_sql_insert_token_fake

        for token in tokens:
            commands.append(get_sql_insert_token(token))

        with self._open_cursor() as cursor:
            for command in commands:
                try:
                    cursor.execute(command)
                except sqlite3.OperationalError as err:
                    logger.debug(f'sql command failed: {command}')
                    logger.error(error_message.format(title))
                    self._connection.rollback()
                    self._article_count -= 1
                    return None

        self._connection.commit()
        logger.info(f'added article {self._article_count}: "{title}"')

    def fetch_data(
        self,
        table: str,
        columns: list[str],
        condition: str | None = None,
    ) -> list[tuple[str | int | float]]:
        command = f"SELECT {', '.join(columns)} FROM {table}"

        if condition:
            command = f'{command} WHERE {condition}'

        with self._open_cursor() as cursor:
            results = cursor.execute(command).fetchall()

        return results

    @contextmanager
    def _open_cursor(self) -> Generator[sqlite3.Cursor]:
        if not self._connection:
            raise ConnectionError('corpus not connected to database file')

        cursor = self._connection.cursor()

        try:
            yield cursor
        finally:
            cursor.close()

    def __enter__(self) -> Self:
        self._connection = sqlite3.connect(self._database)

        with self._open_cursor() as cursor:
            if self._setup_script:
                cursor.executescript(self._setup_script)
                self._setup_script = None

            results = cursor.execute('SELECT id FROM articles').fetchall()
            self._article_count = int(results[-1][0]) if results else 0

        return self

    def __exit__(self, *exc_details) -> None:
        self._connection.close()
        self._connection = None


# def build_corpus(
#     filepath: Path,
#     setup_script: str,
#     *csv_files: str,
# ) -> None:
#     with open(setup_script) as file:
#         corpus = Corpus(filepath, file.read())

#     try:
#         parse_csv_to_corpus(corpus, true_csv, True)
#         parse_csv_to_corpus(corpus, fake_csv, False)
#         logger.log(25, 'successfully built corpus!')
#     except sqlite3.Error as err:
#         logger.exception(err)
#         logger.critical('failed to build corpus')
#     finally:
#         corpus.close()


# @contextmanager
# def open_corpus(filepath: str) -> Generator[Corpus]:
#     corpus = Corpus(filepath)

#     try:
#         yield corpus
#     except sqlite3.OperationalError as err:
#         logger.error(err)
#     finally:
#         corpus.close()
