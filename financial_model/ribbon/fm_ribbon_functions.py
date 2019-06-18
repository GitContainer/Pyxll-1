from pyxll import xl_app, reload, xl_macro
import pydevd
import logging
from generic_fns import (
    get_cached_object,
    set_formula,
    get_value,
    file_picker,
    ParametersParser,
    file_saver,
    load_user_zones,
    to_df,
)
from generic_ui import load_config_xl
from fm_ui import create_fm_data_manager
from fm_data_manager import FMDataManager


_log = logging.getLogger(__name__)

try:
    from win32api import MessageBox
except ImportError:
    _log.warning("*** win32api could not be imported.                ***")
    _log.warning("*** Some of the ribbon examples will not work.     ***")
    _log.warning("*** to fix this, install the pywin32 extensions.   ***")


@xl_macro(shortcut="Ctrl+Shift+R")
def fm_reload(trigger):
    reload()


def pycharm_connect(trigger):
    logging.info("Connecting to Pycharm")
    pydevd.settrace(
        "localhost", port=5000, suspend=False, stdoutToServer=True, stderrToServer=True
    )
    logging.info("Connected to Pycharm")


def pycharm_reconnect(trigger):
    logging.info("Connecting to Pycharm")
    pydevd.connected = False
    pydevd.settrace(
        "localhost", port=5000, suspend=False, stdoutToServer=True, stderrToServer=True
    )
    logging.info("Connected to Pycharm")


@xl_macro(shortcut="Ctrl+Shift+C")
def load_config(trigger):
    logging.info("Loading Configuration")
    set_formula("data_obj_cfg", fn=load_config_xl)


@xl_macro(shortcut="Ctrl+Shift+L")
def load_session(trigger):
    xl = xl_app()
    cfg = get_cached_object(get_value("data_obj_cfg", xl=xl))  # type: ParametersParser
    backup_file = file_picker(
        "Load Session", path=cfg["PROJECT"]["BACKUP"] + "/*" + cfg["PROJECT"]["format"]
    )

    if backup_file is None:
        return

    logging.info(f"Loading Session {backup_file}")
    set_formula(
        "data_obj_manager", fn=create_fm_data_manager, args=f'"{backup_file}"', xl=xl
    )

    data_manager = get_cached_object(
        get_value("data_obj_manager")
    )  # type: FMDataManager
    data_manager.check_compatibility()
    load_user_zones(xl=xl)


@xl_macro(shortcut="Ctrl+Shift+S")
def save_as_session(trigger):
    xl = xl_app()
    cfg = get_cached_object(get_value("data_obj_cfg", xl=xl))  # type: ParametersParser
    save_file = file_saver(
        "Save Session", path=cfg["PROJECT"]["named"] + "/*" + cfg["PROJECT"]["format"]
    )

    if save_file is None:
        return

    save_file = save_file + cfg["PROJECT"]["format"]
    data_manager = get_cached_object(
        get_value("data_obj_manager")
    )  # type: FMDataManager
    data_manager.save_as_db(save_file)

    logging.info(f"Saving Session as {save_file}")


@xl_macro(shortcut="Ctrl+Shift+G")
def get_data(trigger):
    logging.info("Getting Data")
    xl = xl_app()
    set_formula("data_obj_manager", fn=create_fm_data_manager, xl=xl)

    data_manager = get_cached_object(
        get_value("data_obj_manager")
    )  # type: FMDataManager

    assets = to_df(get_value("project_state_assets", xl=xl))
    type_curves = to_df(get_value("type_curves", xl=xl))
    section_assumptions = to_df(get_value("section_assumptions", xl=xl))

    data_manager.set_new_session(
        assets=assets, type_curves=type_curves, section_assumptions=section_assumptions
    )
    data_manager.data_formatter.project_state_assets(xl=xl)
    data_manager.data_formatter.project_parameters(xl=xl)
