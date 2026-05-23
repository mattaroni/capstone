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

from pathlib import Path
from sqlite3 import OperationalError
from statistics import mean, NormalDist

# third-party libraries
import numpy
from matplotlib import pyplot

# local modules
from corpora import Corpus
from isot_tools import iter_isot_dataset
from log_settings import logger, setup_logging

type Sentiment = tuple[list[float], list[float], list[float]]

# constants
ISOT_DATABASE_URL = 'https://onlineacademiccommunity.uvic.ca/isot/wp-content/uploads/sites/7295/2023/03/News-_dataset.zip'
CORPUS_PATH = 'data/corpus.db'
SCRIPT_PATH = 'src/capstone/config/setup_corpus.sql'
TRUE_CSV_PATH = 'data/True.csv'
FAKE_CSV_PATH = 'data/Fake.csv'


def _list_word_frequency(words: list[str]) -> list[tuple[str, int]]:
    unique_words = set(words)
    stats: list[tuple[str, int]] = []

    for word in unique_words:
        count = words.count(word)
        stats.append((word, count))

    return stats


def get_sentiment() -> tuple[Sentiment, Sentiment]:
    with Corpus(CORPUS_PATH) as corpus:
        sentiment_true = corpus.fetch_data('articles', [
            'positivity', 'neutrality', 'negativity',
        ], 'is_true == 1')

        sentiment_fake = corpus.fetch_data('articles', [
            'positivity', 'neutrality', 'negativity',
        ], 'is_true == 0')

    data_true = list(zip(*sentiment_true))
    data_fake = list(zip(*sentiment_fake))

    return (data_true, data_fake)

def print_sentiment() -> None:
    data_true, data_fake = get_sentiment()

    normal_dist_positive_true = NormalDist.from_samples(data_true[0])
    normal_dist_neutral_true = NormalDist.from_samples(data_true[1])
    normal_dist_negative_true = NormalDist.from_samples(data_true[2])

    normal_dist_positive_fake = NormalDist.from_samples(data_fake[0])
    normal_dist_neutral_fake = NormalDist.from_samples(data_fake[1])
    normal_dist_negative_fake = NormalDist.from_samples(data_fake[2])

    normal_distributions = [ # data, label
        [normal_dist_positive_true, 'true, positive'],
        [normal_dist_neutral_true, 'true, neutral'],
        [normal_dist_negative_true, 'true, negative'],
        [normal_dist_positive_fake, 'fake, positive'],
        [normal_dist_neutral_fake, 'fake, neutral'],
        [normal_dist_negative_fake, 'fake, negative'],
    ]

    for data, label in normal_distributions:
        print(label)

        q1, mean, q3 = data.quantiles(4)

        print('Q1', q1)
        print('Q2/MEAN:', mean)
        print('Q3:', q3)
        print('STDEV:', data.stdev)
        print('MEDIAN:', data.median)
        print('MODE:', data.mode)
        print() # separate printed sections


def chart_sentiment() -> None:
    data_true, data_fake = get_sentiment()

    pyplot.style.use('_mpl-gallery')

    fig, axs = pyplot.subplots(nrows=1, ncols=2, figsize=(9, 4))

    for ax, title, data in zip(axs, ['true', 'fake'], [data_true, data_fake]):
        ax.boxplot(
            data,
            widths=1.5,
            patch_artist=True,
            showmeans=False,
            showfliers=False,
            medianprops={
                "color": "white",
                "linewidth": 0.5,
            },
            boxprops={
                "facecolor": "C0",
                "edgecolor": "white",
                "linewidth": 0.5,
            },
            whiskerprops={
                "color": "C0",
                "linewidth": 1.5,
            },
            capprops={
                "color": "C0",
                "linewidth": 1.5,
            },
        )

        ax.set_title(title)

        ax.set(
            xlim=(0, 4),
            xticks=numpy.arange(1, 4),
            ylim=(0, 1),
            # yticks=numpy.arange(0, 1),
        )

    pyplot.show()


def get_overall_lexical_diversity() -> tuple[float, float]:
    fields = ['lemma']

    # the words have to be *content* words
    condition = "pos IN ('PROPN', 'NOUN', 'ADJ', 'VERB', 'ADV')"

    with Corpus(CORPUS_PATH) as corpus:
        content_words_true = corpus.fetch_data(
            'tokens_true',
            fields,
            condition,
        )

        content_words_fake = corpus.fetch_data(
            'tokens_fake',
            fields,
            condition,
        )

    count_total_true = len(content_words_true)
    count_total_fake = len(content_words_fake)

    count_unique_true = len(set(content_words_true))
    count_unique_fake = len(set(content_words_fake))

    lexical_diversity_true = count_unique_true / count_total_true
    lexical_diversity_fake = count_unique_fake / count_total_fake

    return (lexical_diversity_true, lexical_diversity_fake)


# lexical diversity of the total set of content words of all collected articles
def print_overall_lexical_diversity() -> None:
    results = get_overall_lexical_diversity()
    lexical_diversity_true, lexical_diversity_fake = results

    print('overall lexical diversity:')
    print('TRUE:', lexical_diversity_true)
    print('FAKE:', lexical_diversity_fake)


# mean value of an articles lexical diversity
def get_mean_lexical_diversity() -> tuple[float, float]:
    lex_div_condition = "pos IN ('PROPN', 'NOUN', 'ADJ', 'VERB', 'ADV')"

    with Corpus(CORPUS_PATH) as corpus:
        table_and_field = ['articles', ['id']]
        article_ids_true = corpus.fetch_data(*table_and_field, 'is_true = 1')
        article_ids_fake = corpus.fetch_data(*table_and_field, 'is_true = 0')

        article_ids_true = [x[0] for x in article_ids_true]
        article_ids_fake = [x[0] for x in article_ids_fake]

        lexical_diversity_true = []
        lexical_diversity_fake = []

        for article_id in article_ids_true:
            content_words = corpus.fetch_data(
                'tokens_true',
                ['lemma'],
                f'{lex_div_condition} AND article_id = {article_id}',
            )

            total_words = len(content_words)
            unique_words = len(set(content_words))
            lexical_diversity = unique_words / total_words

            print(f'true article #{article_id}, lexical diversity:', lexical_diversity)
            lexical_diversity_true.append(lexical_diversity)

        for article_id in article_ids_fake:
            content_words = corpus.fetch_data(
                'tokens_fake',
                ['lemma'],
                f'{lex_div_condition} AND article_id = {article_id}',
            )

            total_words = len(content_words)
            unique_words = len(set(content_words))
            lexical_diversity = unique_words / total_words

            print(f'fake article #{article_id}, lexical diversity:', lexical_diversity)
            lexical_diversity_fake.append(unique_words / total_words)

    mean_lexical_diversity_true = mean(lexical_diversity_true)
    mean_lexical_diversity_fake = mean(lexical_diversity_fake)

    return (mean_lexical_diversity_true, mean_lexical_diversity_fake)


def print_mean_lexical_diversity() -> None:
    results = get_mean_lexical_diversity()
    mean_lexical_diversity_true, mean_lexical_diversity_fake = results

    print('mean lexical diversity:')
    print('TRUE:', mean_lexical_diversity_true)
    print('FAKE:', mean_lexical_diversity_fake)


def main() -> None:
    setup_logging()

    if not Path(CORPUS_PATH).exists():
        with Corpus(CORPUS_PATH, SCRIPT_PATH) as corpus:
            logger.info("initialized corpus file")

            for article in iter_isot_dataset(ISOT_DATABASE_URL):
                corpus.add_article(**article)

    print_sentiment()
    chart_sentiment()
    print_overall_lexical_diversity()


if __name__ == '__main__':
    main()
