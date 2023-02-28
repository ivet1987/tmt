import logging
from typing import List, Optional

import _pytest.logging
import click
import pytest

from tmt.log import (DebugLevelFilter, Logger, QuietnessFilter,
                     VerbosityLevelFilter)

from . import assert_log


def _exercise_logger(
        caplog: _pytest.logging.LogCaptureFixture,
        logger: Logger,
        indent_by: str = '',
        labels: Optional[List[str]] = None) -> None:
    labels = labels or []

    if labels:
        prefix = ''.join(
            click.style(f'[{label}]', fg='cyan') for label in labels
            ) + ' '

    else:
        prefix = ''

    prefix = f'{indent_by}{prefix}'

    caplog.clear()

    logger.print('this is printed')
    logger.debug('this is a debug message')
    logger.verbose('this is a verbose message')
    logger.info('this is just an info')
    logger.warn('this is a warning')
    logger.fail('this is a failure')

    assert_log(
        caplog,
        message=f'{prefix}this is printed',
        details_key='this is printed',
        details_logger_labels=labels,
        levelno=logging.INFO)
    assert_log(
        caplog,
        message=f'{prefix}this is a debug message',
        details_key='this is a debug message',
        details_logger_labels=labels,
        levelno=logging.DEBUG)
    assert_log(
        caplog,
        message=f'{prefix}this is a verbose message',
        details_key='this is a verbose message',
        details_logger_labels=labels,
        levelno=logging.INFO)
    assert_log(
        caplog,
        message=f'{prefix}this is just an info',
        details_key='this is just an info',
        details_logger_labels=labels,
        levelno=logging.INFO)
    assert_log(
        caplog,
        message=f'{prefix}{click.style("warn", fg="yellow")}: this is a warning',
        details_key='warn',
        details_value='this is a warning',
        details_logger_labels=labels,
        levelno=logging.WARN)
    assert_log(
        caplog,
        message=f'{prefix}{click.style("fail", fg="red")}: this is a failure',
        details_key='fail',
        details_value='this is a failure',
        details_logger_labels=labels,
        levelno=logging.ERROR)


def test_sanity(caplog: _pytest.logging.LogCaptureFixture, root_logger: Logger) -> None:
    _exercise_logger(caplog, root_logger)


def test_creation(caplog: _pytest.logging.LogCaptureFixture, root_logger: Logger) -> None:
    logger = Logger.create()
    assert logger._logger.name == 'tmt'

    actual_logger = logging.Logger('3rd-party-app-logger')
    logger = Logger.create(actual_logger)
    assert logger._logger is actual_logger


def test_descend(caplog: _pytest.logging.LogCaptureFixture, root_logger: Logger) -> None:
    deeper_logger = root_logger.descend().descend().descend()

    _exercise_logger(caplog, deeper_logger, indent_by='            ')


@pytest.mark.parametrize(
    ('logger_verbosity', 'message_verbosity', 'filter_outcome'),
    [
        # (
        #   logger verbosity - corresponds to -v, -vv, -vvv CLI options,
        #   message verbosity - `level` parameter of `verbosity(...)` call,
        #   expected outcome of `VerbosityLevelFilter.filter()` - returns integer!
        # )
        (0, 1, 0),
        (1, 1, 1),
        (2, 1, 1),
        (3, 1, 1),
        (4, 1, 1),
        (0, 2, 0),
        (1, 2, 0),
        (2, 2, 1),
        (3, 2, 1),
        (4, 2, 1),
        (0, 3, 0),
        (1, 3, 0),
        (2, 3, 0),
        (3, 3, 1),
        (4, 3, 1),
        (0, 4, 0),
        (1, 4, 0),
        (2, 4, 0),
        (3, 4, 0),
        (4, 4, 1)
        ]
    )
def test_verbosity_filter(
        logger_verbosity: int,
        message_verbosity: int,
        filter_outcome: int
        ) -> None:
    filter = VerbosityLevelFilter()

    assert filter.filter(logging.makeLogRecord({
        'levelno': logging.INFO,
        'details': {
            'logger_verbosity_level': logger_verbosity,
            'message_verbosity_level': message_verbosity
            }
        })) == filter_outcome


@pytest.mark.parametrize(
    ('logger_debug', 'message_debug', 'filter_outcome'),
    [
        # (
        #   logger debug level - corresponds to -d, -dd, -ddd CLI options,
        #   message debug level - `level` parameter of `debug(...)` call,
        #   expected outcome of `DebugLevelFilter.filter()` - returns integer!
        # )
        (0, 1, 0),
        (1, 1, 1),
        (2, 1, 1),
        (3, 1, 1),
        (4, 1, 1),
        (0, 2, 0),
        (1, 2, 0),
        (2, 2, 1),
        (3, 2, 1),
        (4, 2, 1),
        (0, 3, 0),
        (1, 3, 0),
        (2, 3, 0),
        (3, 3, 1),
        (4, 3, 1),
        (0, 4, 0),
        (1, 4, 0),
        (2, 4, 0),
        (3, 4, 0),
        (4, 4, 1)
        ]
    )
def test_debug_filter(
        logger_debug: int,
        message_debug: int,
        filter_outcome: int
        ) -> None:
    filter = DebugLevelFilter()

    assert filter.filter(logging.makeLogRecord({
        'levelno': logging.DEBUG,
        'details': {
            'logger_debug_level': logger_debug,
            'message_debug_level': message_debug
            }
        })) == filter_outcome


@pytest.mark.parametrize(
    ('levelno', 'filter_outcome'),
    [
        # (
        #   log message level,
        #   expected outcome of `QietnessFilter.filter()` - returns integer!
        # )
        (logging.DEBUG, 0),
        (logging.INFO, 0),
        (logging.WARNING, 1),
        (logging.ERROR, 1),
        (logging.CRITICAL, 1)
        ]
    )
def test_quietness_filter(levelno: int, filter_outcome: int) -> None:
    filter = QuietnessFilter()

    assert filter.filter(logging.makeLogRecord({
        'levelno': levelno
        })) == filter_outcome


def test_labels(caplog: _pytest.logging.LogCaptureFixture, root_logger: Logger) -> None:
    _exercise_logger(caplog, root_logger, labels=[])

    root_logger.labels += ['foo']

    _exercise_logger(caplog, root_logger, labels=['foo'])

    root_logger.labels += ['bar']

    _exercise_logger(caplog, root_logger, labels=['foo', 'bar'])