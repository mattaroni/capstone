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

import atexit
import logging
import logging.config
import tomllib
from datetime import datetime, UTC
from functools import partial
from logging import Formatter, Logger, LogRecord
from logging.handlers import QueueHandler
from pathlib import Path
from typing_extensions import override

CONFIG_PATH = 'src/capstone/config/logging_config.toml'
LOG_LEVEL_SUCCESS_NUMBER = 25

logger = logging.getLogger()


def _stylize(ansi: str, text: str) -> str:
    """Generates a stylized version of a text with the ANSI escape code.

    Args:
        ansi (str): The *n* value of an ANSI escape code, which will be used
            to stylize the text.
        text (str): The text to create a stylized version of.

    Returns:
        str: A version of the text that is stylized with the ANSI escape code.
    """

    return f'\x1b[{ansi}m{text}\x1b[0m'


_subtle_text = partial(_stylize, '2;3')
_green_text = partial(_stylize, '32')
_yellow_text = partial(_stylize, '33')
_red_text = partial(_stylize, '31')
_red_background = partial(_stylize, '31;7')


class PrettyFormatter(Formatter):
    def __init__(self, timefmt: str = '%H:%M:%S') -> None:
        dim_text = lambda text: _stylize('2', text)

        super().__init__('%(asctime)s %(message)s', dim_text(timefmt))

    @override
    def formatMessage(self, record: LogRecord) -> str:
        global LOG_LEVEL_SUCCESS_NUMBER

        match record.levelno:
            case 10:
                record.message = _subtle_text(record.message)
            case 20:
                pass
            case 30:
                message_text = f'[WARNING]: {record.message}'
                record.message = _yellow_text(message_text)
            case 40:
                record.message = _red_text(f'[ERROR]: {record.message}')
            case 50:
                message_text = f' CRITICAL ERROR - {record.message} '
                record.message = _red_background(message_text)
            case LOG_LEVEL_SUCCESS_NUMBER:
                record.message = _green_text(f'✓ {record.message}')

        return super().formatMessage(record)


class DetailedFormatter(Formatter):
    def __init__(self, fmt: str) -> str:
        super().__init__(fmt, style='{')

    @override
    def formatTime(self, record: LogRecord, datefmt: str | None = None) -> str:
        timestamp = datetime.fromtimestamp(record.created, UTC)
        return timestamp.strftime('%Y-%m-%dT%H:%M:%SZ')


def setup_logging() -> None:
    global CONFIG_PATH, LOG_LEVEL_SUCCESS_NUMBER

    with open(CONFIG_PATH, 'rb') as file:
        config = tomllib.load(file)

    logfile_path = config['handlers']['file']['filename']
    Path(logfile_path).parent.mkdir(parents=True, exist_ok=True)

    logging.config.dictConfig(config)
    logging.addLevelName(LOG_LEVEL_SUCCESS_NUMBER, 'SUCCESS')
    queue_handler = logging.getHandlerByName('queue_handler')

    if queue_handler is not None:
        queue_handler.listener.start()
        atexit.register(queue_handler.listener.stop)


if __name__ == '__main__':
    setup_logging()

    logger.debug('lorem ipsum dolor sit amet')
    logger.info('lorem ipsum dolor sit amet')
    logger.log(25, 'lorem ipsum dolor sit amet')
    logger.warning('lorem ipsum dolor sit amet')
    logger.error('lorem ipsum dolor sit amet')
    logger.critical('lorem ipsum dolor sit amet')
