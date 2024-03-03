from __future__ import annotations

import typing

import pytest

from esbonio import server
from esbonio.server.features.log import LoggerConfiguration
from esbonio.server.features.log import LoggingConfig

if typing.TYPE_CHECKING:
    from typing import Dict


SERVER = server.EsbonioLanguageServer


@pytest.mark.parametrize(
    "config,expected",
    [
        (  # Check the defaults
            LoggingConfig(),
            dict(
                version=1,
                disable_existing_loggers=True,
                formatters=dict(
                    fmt01=dict(format="[%(name)s] %(message)s"),
                    fmt02=dict(format="%(message)s"),
                ),
                handlers=dict(
                    stderr01={
                        "class": "logging.StreamHandler",
                        "level": "DEBUG",
                        "formatter": "fmt01",
                        "stream": "ext://sys.stderr",
                    },
                    stderr02={
                        "class": "logging.StreamHandler",
                        "level": "DEBUG",
                        "formatter": "fmt02",
                        "stream": "ext://sys.stderr",
                    },
                ),
                loggers=dict(
                    esbonio=dict(
                        level="ERROR",
                        propagate=False,
                        handlers=["stderr01"],
                    ),
                    sphinx=dict(
                        level="INFO",
                        propagate=False,
                        handlers=["stderr02"],
                    ),
                ),
            ),
        ),
        (  # It should be possible to override the base logging level
            LoggingConfig(level="debug"),
            dict(
                version=1,
                disable_existing_loggers=True,
                formatters=dict(
                    fmt01=dict(format="[%(name)s] %(message)s"),
                    fmt02=dict(format="%(message)s"),
                ),
                handlers=dict(
                    stderr01={
                        "class": "logging.StreamHandler",
                        "level": "DEBUG",
                        "formatter": "fmt01",
                        "stream": "ext://sys.stderr",
                    },
                    stderr02={
                        "class": "logging.StreamHandler",
                        "level": "DEBUG",
                        "formatter": "fmt02",
                        "stream": "ext://sys.stderr",
                    },
                ),
                loggers=dict(
                    esbonio=dict(
                        level="DEBUG",
                        propagate=False,
                        handlers=["stderr01"],
                    ),
                    sphinx=dict(
                        level="INFO",
                        propagate=False,
                        handlers=["stderr02"],
                    ),
                ),
            ),
        ),
        (  # It should be possible to override the base log format
            LoggingConfig(format="%(message)s"),
            dict(
                version=1,
                disable_existing_loggers=True,
                formatters=dict(
                    fmt01=dict(format="%(message)s"),
                ),
                handlers=dict(
                    stderr01={
                        "class": "logging.StreamHandler",
                        "level": "DEBUG",
                        "formatter": "fmt01",
                        "stream": "ext://sys.stderr",
                    },
                ),
                loggers=dict(
                    esbonio=dict(
                        level="ERROR",
                        propagate=False,
                        handlers=["stderr01"],
                    ),
                    sphinx=dict(
                        level="INFO",
                        propagate=False,
                        handlers=["stderr01"],
                    ),
                ),
            ),
        ),
        (  # User should be able to re-direct output to ``window/logMessages``
            LoggingConfig(stderr=False, window=True),
            dict(
                version=1,
                disable_existing_loggers=True,
                formatters=dict(
                    fmt01=dict(format="[%(name)s] %(message)s"),
                    fmt02=dict(format="%(message)s"),
                ),
                handlers=dict(
                    window01={
                        "()": "esbonio.server.features.log.WindowLogMessageHandler",
                        "level": "DEBUG",
                        "formatter": "fmt01",
                        "server": SERVER,
                    },
                    window02={
                        "()": "esbonio.server.features.log.WindowLogMessageHandler",
                        "level": "DEBUG",
                        "formatter": "fmt02",
                        "server": SERVER,
                    },
                ),
                loggers=dict(
                    esbonio=dict(
                        level="ERROR",
                        propagate=False,
                        handlers=["window01"],
                    ),
                    sphinx=dict(
                        level="INFO",
                        propagate=False,
                        handlers=["window02"],
                    ),
                ),
            ),
        ),
        (  # User should be able to re-direct output to a file
            LoggingConfig(stderr=False, filepath="esbonio.log"),
            dict(
                version=1,
                disable_existing_loggers=True,
                formatters=dict(
                    fmt01=dict(format="[%(name)s] %(message)s"),
                    fmt02=dict(format="%(message)s"),
                ),
                handlers=dict(
                    file01={
                        "class": "logging.FileHandler",
                        "level": "DEBUG",
                        "formatter": "fmt01",
                        "filename": "esbonio.log",
                    },
                    file02={
                        "class": "logging.FileHandler",
                        "level": "DEBUG",
                        "formatter": "fmt02",
                        "filename": "esbonio.log",
                    },
                ),
                loggers=dict(
                    esbonio=dict(
                        level="ERROR",
                        propagate=False,
                        handlers=["file01"],
                    ),
                    sphinx=dict(
                        level="INFO",
                        propagate=False,
                        handlers=["file02"],
                    ),
                ),
            ),
        ),
        (  # User should be able to log to everything if they so desired
            LoggingConfig(stderr=True, window=True, filepath="esbonio.log"),
            dict(
                version=1,
                disable_existing_loggers=True,
                formatters=dict(
                    fmt01=dict(format="[%(name)s] %(message)s"),
                    fmt02=dict(format="%(message)s"),
                ),
                handlers=dict(
                    file01={
                        "class": "logging.FileHandler",
                        "level": "DEBUG",
                        "formatter": "fmt01",
                        "filename": "esbonio.log",
                    },
                    stderr02={
                        "class": "logging.StreamHandler",
                        "level": "DEBUG",
                        "formatter": "fmt01",
                        "stream": "ext://sys.stderr",
                    },
                    window03={
                        "()": "esbonio.server.features.log.WindowLogMessageHandler",
                        "level": "DEBUG",
                        "formatter": "fmt01",
                        "server": SERVER,
                    },
                    file04={
                        "class": "logging.FileHandler",
                        "level": "DEBUG",
                        "formatter": "fmt02",
                        "filename": "esbonio.log",
                    },
                    stderr05={
                        "class": "logging.StreamHandler",
                        "level": "DEBUG",
                        "formatter": "fmt02",
                        "stream": "ext://sys.stderr",
                    },
                    window06={
                        "()": "esbonio.server.features.log.WindowLogMessageHandler",
                        "level": "DEBUG",
                        "formatter": "fmt02",
                        "server": SERVER,
                    },
                ),
                loggers=dict(
                    esbonio=dict(
                        level="ERROR",
                        propagate=False,
                        handlers=["file01", "stderr02", "window03"],
                    ),
                    sphinx=dict(
                        level="INFO",
                        propagate=False,
                        handlers=["file04", "stderr05", "window06"],
                    ),
                ),
            ),
        ),
        (  # The user should be able to customize an individual logger.
            LoggingConfig(
                config={"esbonio.Configuration": LoggerConfiguration(level="info")},
            ),
            dict(
                version=1,
                disable_existing_loggers=True,
                formatters=dict(
                    fmt01=dict(format="[%(name)s] %(message)s"),
                    fmt02=dict(format="%(message)s"),
                ),
                handlers=dict(
                    stderr01={
                        "class": "logging.StreamHandler",
                        "level": "DEBUG",
                        "formatter": "fmt01",
                        "stream": "ext://sys.stderr",
                    },
                    stderr02={
                        "class": "logging.StreamHandler",
                        "level": "DEBUG",
                        "formatter": "fmt02",
                        "stream": "ext://sys.stderr",
                    },
                ),
                loggers={
                    "esbonio": dict(
                        level="ERROR",
                        propagate=False,
                        handlers=["stderr01"],
                    ),
                    "esbonio.Configuration": dict(
                        level="INFO",
                        propagate=False,
                        handlers=["stderr01"],
                    ),
                    "sphinx": dict(
                        level="INFO",
                        propagate=False,
                        handlers=["stderr02"],
                    ),
                },
            ),
        ),
    ],
)
def test_logging_config(config: LoggingConfig, expected: Dict):
    """Ensure that we can convert the user's config into the config we can pass to the
    ``logging.config`` module correctly."""

    # SERVER in this case is a class, at runtime this will be an actual instance.
    assert config.to_logging_config(SERVER) == expected
