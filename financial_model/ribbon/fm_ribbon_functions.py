from operator import and_

import pandas as pd
from pyxll import xl_app, reload, xl_macro
import pydevd
import logging

from scipy.optimize import minimize
import numpy as np

from fm_orm import Well_Oneline, Section_Assumption, Section_Well, Project_State_Asset
from form_norm import form_norm
from generic_fns import (
    get_cached_object,
    set_formula,
    get_value,
    file_picker,
    ParametersParser,
    file_saver,
    load_user_zones,
    to_df,
    copy_df_xl,
    get_address,
    add_xl_app,
    copy_np_xl,
    set_value,
)
from generic_type_hints import w32
from generic_ui import load_config_xl
from fm_ui import create_fm_data_manager, read_project_settings, set_default_formulae
from fm_data_manager import FMDataManager
from mod_arps import modarps_rmse

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

    set_formula(
        "data_obj_manager", fn=create_fm_data_manager, args=f'"{backup_file}"', xl=xl
    )

    data_manager = get_cached_object(
        get_value("data_obj_manager")
    )  # type: FMDataManager
    data_manager.check_compatibility()

    load_user_zones(xl=xl)
    set_formation_normalizer(xl=xl)
    set_producing_sections(xl=xl)


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
    external_settings = read_project_settings(string="sett_", xl=xl)

    data_manager.set_new_session(
        external_settings=external_settings,
        assets=assets,
        type_curves=type_curves,
        section_assumptions=section_assumptions,
    )
    data_manager.data_formatter.project_state_assets(xl=xl)
    data_manager.data_formatter.project_parameters(xl=xl)


@xl_macro
def normalize_formation(trigger):
    logging.info("Normalizing Formation")
    xl = xl_app()
    dm = get_cached_object(get_value("data_obj_manager"))  # type: FMDataManager

    data = (
        dm.session.query(
            Well_Oneline.api,
            Well_Oneline.well_name,
            Well_Oneline.well_number,
            Well_Oneline.well_str,
            Well_Oneline.operator_name,
            Well_Oneline.formation,
            Section_Assumption.formation_1,
            Section_Assumption.formation_2,
        )
        .join(Section_Well)
        .join(Project_State_Asset)
        .join(Section_Assumption)
        .all()
    )

    df = pd.DataFrame(data)

    # This line added in case a multi unit well lying in two different sections have two different
    # section assumptions

    df = df.drop_duplicates(["api"]).reset_index(drop=True)

    str_columns = [
        "well_name",
        "well_number",
        "operator_name",
        "formation",
        "formation_1",
        "formation_2",
    ]

    string_array = df.loc[:, str_columns].values.transpose().astype("unicode")

    formation = form_norm(string_array)

    df["norm_formation"] = formation

    formation_columns = [
        "api",
        "well_str",
        "operator_name",
        "formation",
        "formation_1",
        "formation_2",
        "norm_formation",
    ]
    df = df.loc[:, formation_columns]

    with dm.session_scope() as session:
        for i, row in df.iterrows():
            selected_well = (
                session.query(Well_Oneline).filter(Well_Oneline.api == row["api"]).one()
            )  # type: Well_Oneline
            selected_well.norm_formation = row.norm_formation

    set_formation_normalizer()


@add_xl_app
def set_formation_normalizer(xl: w32 = None):
    dm = get_cached_object(get_value("data_obj_manager", xl=xl))

    data = (
        dm.session.query(
            Well_Oneline.api,
            Well_Oneline.well_str,
            Well_Oneline.operator_name,
            Well_Oneline.formation,
            Section_Assumption.formation_1,
            Section_Assumption.formation_2,
            Well_Oneline.norm_formation,
        )
        .join(Section_Well)
        .join(Project_State_Asset)
        .join(Section_Assumption)
        .all()
    )

    df = pd.DataFrame(data)

    copy_df_xl(
        df=df,
        sheet="Formation",
        name="formation_state_normalizer",
        copy_columns=False,
        xl=xl,
    )

    dm.data_formatter.formation_state_normalizer()


@xl_macro
def decline_wells(trigger):
    """
    TODO: Optimize this function. Take a longer time for lots of sections.
    :param trigger:
    :return:
    """
    logging.info("Declining Wells")
    xl = xl_app()

    dm = get_cached_object(get_value("data_obj_manager", xl=xl))  # type: FMDataManager
    df = dm["monthlies"]
    api_list = df.api.unique()

    oil_list, gas_list = run_arps(df, api_list, dm.get_initial_guess(), dm.get_bounds())

    with dm.session_scope() as session:
        for i, selected_api in enumerate(api_list):
            selected_well = (
                session.query(Well_Oneline)
                .filter(Well_Oneline.api == str(selected_api))
                .one()
            )  # type: Well_Oneline

            selected_well.ip_final_oil = oil_list[i][0]
            selected_well.di_oil = oil_list[i][1]
            selected_well.dmin_oil = oil_list[i][2]
            selected_well.b_oil = oil_list[i][3]
            selected_well.ip_oil_idx = oil_list[i][4]

            selected_well.ip_final_gas = gas_list[i][0]
            selected_well.di_gas = gas_list[i][1]
            selected_well.dmin_gas = gas_list[i][2]
            selected_well.b_gas = gas_list[i][3]
            selected_well.ip_gas_idx = oil_list[i][4]

            # selected_well.well_type = "Declined"

    logging.info(f"Declined {api_list.shape[0]} wells")
    set_producing_sections(xl=xl)


def run_arps(df, api_list, initial_guess, bounds):

    oil_list = [None] * api_list.shape[0]
    gas_list = [None] * api_list.shape[0]

    for i, api in enumerate(api_list):
        test_df = df.query("api == @api")

        for product in ["oil", "gas"]:
            well_initial_guess = initial_guess.copy()
            well_bounds = bounds.copy()

            stream = test_df[product].values
            ip_start_idx = np.argmax(stream)
            decline_stream = stream[ip_start_idx:]
            actual = decline_stream.reshape(-1, 1)
            well_initial_guess[0] = well_initial_guess[0] * decline_stream[0]
            well_bounds[0] = (
                well_bounds[0][0] * decline_stream[0],
                well_bounds[0][1] * decline_stream[0],
            )

            result = minimize(
                modarps_rmse,
                x0=well_initial_guess,
                args=actual,
                method="L-BFGS-B",
                bounds=well_bounds,
                options={"maxiter": 1000, "eps": 0.0001},
            )

            result_pars = result.x.tolist()
            result_pars.append(int(ip_start_idx))

            if product == "oil":
                oil_list[i] = result_pars
            else:
                gas_list[i] = result_pars

    return oil_list, gas_list


@add_xl_app
def set_producing_sections(xl=None):
    dm = get_cached_object(get_value("data_obj_manager", xl=xl))
    sections = np.unique(
        np.array(
            dm.session.query(Section_Well.trsm_heh)
            .join(Well_Oneline)
            .filter(Well_Oneline.well_type == "PDP")
            .all()
        )
    )

    copy_np_xl(sections, "Helper", "fm_fn_producing_sections", xl=xl)
    set_value("fm_fn_producing_section", sections[0])
