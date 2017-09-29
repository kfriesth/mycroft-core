# Copyright 2016 Mycroft AI, Inc.
#
# This file is part of Mycroft Core.
#
# Mycroft Core is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Mycroft Core is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Mycroft Core.  If not, see <http://www.gnu.org/licenses/>.
import inspect
import logging
import sys

from os.path import isfile

from mycroft.util.json_helper import load_commented_json


def getLogger(name="MYCROFT"):
    """Depreciated. Use LOG instead"""
    return logging.getLogger(name)


def _make_log_method(fn):
    @classmethod
    def method(cls, *args, **kwargs):
        cls._log(fn, *args, **kwargs)

    method.__func__.__doc__ = fn.__doc__
    return method


class LOG:
    """
    Custom logger class that acts like logging.Logger
    The logger name is automatically generated by the module of the caller

    Usage:
        LOG.debug('My message: %s', debug_str)
        LOG('custom_name').debug('Another message')
    """

    _custom_name = None
    handler = None
    level = None

    # Copy actual logging methods from logging.Logger
    # Usage: LOG.debug(message)
    debug = _make_log_method(logging.Logger.debug)
    info = _make_log_method(logging.Logger.info)
    warning = _make_log_method(logging.Logger.warning)
    error = _make_log_method(logging.Logger.error)
    exception = _make_log_method(logging.Logger.exception)

    @classmethod
    def init(cls):
        sys_config = '/etc/mycroft/mycroft.conf'
        config = load_commented_json(sys_config) if isfile(sys_config) else {}
        cls.level = logging.getLevelName(config.get('log_level', 'DEBUG'))
        fmt = '%(asctime)s.%(msecs)03d - ' \
              '%(name)s - %(levelname)s - %(message)s'
        datefmt = '%H:%M:%S'
        formatter = logging.Formatter(fmt, datefmt)
        cls.handler = logging.StreamHandler(sys.stdout)
        cls.handler.setFormatter(formatter)
        cls.create_logger('')  # Enables logging in external modules

    @classmethod
    def create_logger(cls, name):
        l = logging.getLogger(name)
        l.propagate = False
        l.addHandler(cls.handler)
        l.setLevel(cls.level)
        return l

    def __init__(self, name):
        LOG._custom_name = name

    @classmethod
    def _log(cls, func, *args, **kwargs):
        if cls._custom_name is not None:
            name = cls._custom_name
            cls._custom_name = None
        else:
            # Stack:
            # [0] - _log()
            # [1] - debug(), info(), warning(), or error()
            # [2] - caller
            stack = inspect.stack()

            # Record:
            # [0] - frame object
            # [1] - filename
            # [2] - line number
            # [3] - function
            # ...
            record = stack[2]
            mod = inspect.getmodule(record[0])
            module_name = mod.__name__ if mod else ''
            name = module_name + ':' + record[3] + ':' + str(record[2])
        func(cls.create_logger(name), *args, **kwargs)

LOG.init()
