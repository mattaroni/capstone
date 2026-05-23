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
import pathlib
import zipfile
from collections.abc import Generator
from typing import IO

# third-party libraries
import requests

# local modules
from log_settings import logger

CHUNK_SIZE = 10 * 1024
FAKE_NEWS_CSV = 'Fake.csv'
TRUE_NEWS_CSV = 'True.csv'


def _download_zip_file(url: str) -> pathlib.Path:
    """Downloads a zip file from the internet to the working directory.

    Args:
        url (str): Web URL to an online zip file.

    Returns:
        pathlib.Path: Filepath to the downloaded zip file.
    """

    global CHUNK_SIZE

    zip_file_name = url[url.rfind('/')+1:]
    zip_file_path = pathlib.Path(zip_file_name)

    with requests.get(url, stream=True) as response:
        with open(zip_file_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                file.write(chunk)

    return zip_file_path


def _iter_zipped_isot_file(
    zip_file_path: pathlib.Path,
    filename: str,
    is_true: bool,
) -> Generator[dict[str, str]]:
    zipped_file_path = zipfile.Path(zip_file_path, filename)

    with zipped_file_path.open() as file:
        reader = csv.DictReader(file) # NOTE: May fail

        for article in reader:
            for field in ['title', 'date']:
                article[field] = article[field].strip()

            article['is_true'] = is_true

            yield article


def iter_isot_dataset(url: str) -> Generator[dict[str, str]]:
    global FAKE_NEWS_CSV, TRUE_NEWS_CSV

    logger.info('downloading ISOT fake news dataset...')

    zip_file_path = _download_zip_file(url)
    logger.log(25, 'dataset downloaded!')

    for article in _iter_zipped_isot_file(zip_file_path, TRUE_NEWS_CSV, True):
        yield article

    for article in _iter_zipped_isot_file(zip_file_path, FAKE_NEWS_CSV, False):
        yield article

    zip_file_path.unlink()
    logger.debug('removed zip file for ISOT fake news dataset')





