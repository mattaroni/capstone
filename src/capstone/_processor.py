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

import datetime
from dataclasses import dataclass

# external libraries
import asent
import spacy
from asent.data_classes import DocPolarityOutput

# local modules
from log_settings import logger

_POTENTIAL_DATE_FORMATS: list[str] = ['%B %d, %Y', '%d-%b-%y', '%b %d, %Y']


@dataclass(frozen=True)
class Article:
    title: str
    subject: str
    date: str
    is_true: int # for compatibility with SQLite: 1 = True, 0 = False
    negativity: float
    neutrality: float
    positivity: float
    compound_sentiment: float
    sentence_count: int


@dataclass(frozen=True)
class Token:
    article_id: int
    orth: str
    lemma: str
    pos: str
    tag: str
    dep: str
    head: str
    prefix: str
    suffix: str


def _parse_date_to_iso_format(date_string: str) -> str:
    global _POTENTIAL_DATE_FORMATS

    for date_format in _POTENTIAL_DATE_FORMATS:
        try:
            date = datetime.date.strptime(date_string, date_format)
        except ValueError as err:
            last_error = err
            continue

        return str(date)

    raise last_error


def _simplify_spacy_token(token: spacy.tokens.Token, index: int) -> Token:
    return Token(
        index,
        token.text,
        token.lemma_,
        token.pos_,
        token.tag_,
        token.dep_,
        token.head.text,
        token.prefix_,
        token.suffix_,
    )


class ArticleProcessor:
    _LANGUAGE_MODEL = 'en_core_web_sm'
    _PIPES = ('sentencizer', 'asent_en_v1')

    def __init__(self) -> None:
        self._nlp = spacy.load(self._LANGUAGE_MODEL)

        for pipe in self._PIPES:
            self._nlp.add_pipe(pipe)

    def process(self,
        index: int,
        title: str,
        text: str,
        subject: str,
        date: str,
        is_true: bool,
    ) -> tuple[Article, list[Token]]:
        doc = self._nlp(text)
        polarity: DocPolarityOutput = doc._.polarity

        article = Article(
            title,
            subject,
            _parse_date_to_iso_format(date),
            int(is_true),
            polarity.negative,
            polarity.neutral,
            polarity.positive,
            polarity.compound,
            polarity.n_sentences,
        )

        tokens = [_simplify_spacy_token(token, index) for token in iter(doc)]

        return (article, tokens)
