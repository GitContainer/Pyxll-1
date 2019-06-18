import logging

import pydevd

_log = logging.getLogger(__name__)

try:
    from win32api import MessageBox
except ImportError:
    _log.warning("*** win32api could not be imported.                ***")
    _log.warning("*** Some of the ribbon examples will not work.     ***")
    _log.warning("*** to fix this, install the pywin32 extensions.   ***")


def pycharm_connect(button):
    logging.info("Connecting to Pycharm")
    pydevd.settrace(
        "localhost", port=5000, suspend=False, stdoutToServer=True, stderrToServer=True
    )
    logging.info("Connected to Pycharm")


def pycharm_reconnect(button):
    logging.info("Connecting to Pycharm")
    pydevd.connected = False
    pydevd.settrace(
        "localhost", port=5000, suspend=False, stdoutToServer=True, stderrToServer=True
    )
    logging.info("Connected to Pycharm")
