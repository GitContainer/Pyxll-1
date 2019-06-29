import logging
from operator import and_

import pandas as pd
import numpy as np
import pytest
from pyxll import xl_func, xl_on_close, xl_app, xl_on_reload, xl_macro

from fm_orm import Well_Oneline, Project_State_Asset, Section_Well
from generic_exceptions import Win32COMCacheException
from generic_fns import (
    get_value,
    to_df,
    set_formula,
    clear_list,
    clear_user_zones,
    get_cached_object,
    message_box,
    clear_win32com_cache,
    set_value,
    ParametersParser,
    add_xl_app,
    get_names_with_string,
    copy_df_xl,
    copy_np_xl,
)
from generic_ui import (
    create_source_connector,
    create_query_manager,
    load_config_xl,
    load_module_xml,
)

from fm_data_manager import FMDataManager
from fm_data_loader import FMDataLoader
from fm_data_formatter import FMDataFormatter


@xl_func(volatile=False)
def create_fm_data_manager(restore=None):
    """
    Creates a fm data manager using the xl instance passed.

    WARNING! dont change the wrapper order.
    :param restore:
    :param xl:
    :return:
    """
    xl = xl_app()
    assets = to_df(get_value("project_state_assets", xl=xl))

    if (assets.shape[0] == 0) and restore is None:
        message_box("Provide at least a section to start the analysis")
        return

    cfg = get_cached_object(get_value("data_obj_cfg"))
    source_connector = create_source_connector(xl=xl)
    query_manager = create_query_manager(xl=xl)

    data_loader = FMDataLoader()
    data_formatter = FMDataFormatter()

    dm = FMDataManager(
        cfg=cfg,
        qm=query_manager,
        sc=source_connector,
        dl=data_loader,
        df=data_formatter,
        restore=restore,
    )
    return dm


@xl_func
def ribbon_on_tab_select(tab, xl=None):
    pass


@xl_func
@xl_on_close
def ui_closure():
    xl = xl_app()
    # message_box(
    #     "WARNING! Closing the excel will clear all the session data from the template. Make sure to save the session."
    # )
    clear_list(containing_string="fm_fn", xl=xl)
    clear_list(containing_string="obj", xl=xl)
    clear_user_zones(containing_string="state", xl=xl)


@xl_on_reload
def ui_reload(trigger):
    ui_closure()
    ui_initiation()


def set_default_values(defaults: dict):
    for key, value in defaults.items():
        set_value(key, value)


def set_default_formulae(defaults: dict, xl):
    for key, value in defaults.items():
        xl.Range(key).Formula = "=" + value


@add_xl_app
@xl_func
def reset_defaults(xl=None):
    xl.ScreenUpdating = False
    try:
        logging.info("Resetting Defaults")
        cfg = get_cached_object(get_value("data_obj_cfg"))  # type: ParametersParser

        set_default_values(cfg["DEFAULTS_VALUES"])
        set_default_formulae(cfg["DEFAULTS_FORMULAE"], xl=xl)
    finally:
        xl.ScreenUpdating = True


@add_xl_app
@xl_func
def read_project_settings(string: str = "sett_", xl=None) -> pd.DataFrame:
    settings_names = get_names_with_string(pattern=string, xl=xl)
    settings_values = [str(get_value(setting, xl=xl)) for setting in settings_names]

    settings = dict(name=settings_names, value=settings_values)
    settings_df = pd.DataFrame(settings)
    return settings_df


@xl_macro
def ui_initiation():
    try:
        xl = xl_app()
    except AttributeError:
        clear_win32com_cache()
        raise Win32COMCacheException

    set_formula("data_obj_cfg", fn=load_config_xl, xl=xl)
    reset_defaults(xl=xl)

    load_module_xml("session", xl=xl)
    load_module_xml("project", xl=xl)
    load_module_xml("tools", xl=xl)


@xl_macro
def set_producing_section_wells():
    xl = xl_app()
    dm = get_cached_object(get_value("data_obj_manager", xl=xl))
    selected_section = get_value("fm_fn_producing_section", xl=xl)

    wells = np.unique(
        np.array(
            dm.session.query(Well_Oneline.well_str)
            .join(Section_Well)
            .filter(
                and_(
                    Well_Oneline.well_type == "PDP",
                    Section_Well.trsm_heh == selected_section,
                )
            )
            .all()
        )
    )

    clear_list(containing_string="fm_fn_producing_section_wells", xl=xl)
    copy_np_xl(array=wells, sheet="Helper", name="fm_fn_producing_section_wells", xl=xl)


@xl_macro
def set_dca_pars():
    xl = xl_app()
    dm = get_cached_object(get_value("data_obj_manager", xl=xl))
    selected_well = get_value("fm_fn_producing_well_name", xl=xl)

    dca_pars_oil = pd.DataFrame(
        dm.session.query(
            Well_Oneline.ip_final_oil,
            Well_Oneline.di_oil,
            Well_Oneline.b_oil,
            Well_Oneline.dmin_oil,
            Well_Oneline.ip_oil_idx,
        )
        .filter(Well_Oneline.well_str == selected_well)
        .all()
    )
    dca_pars_oil.columns = ["IP", "De", "B", "Dmin", "Max IP Month"]

    dca_pars_gas = pd.DataFrame(
        dm.session.query(
            Well_Oneline.ip_final_gas,
            Well_Oneline.di_gas,
            Well_Oneline.b_gas,
            Well_Oneline.dmin_gas,
            Well_Oneline.ip_gas_idx,
        )
        .filter(Well_Oneline.well_str == selected_well)
        .all()
    )
    dca_pars_gas.columns = ["IP", "De", "B", "Dmin", "Max IP Month"]

    dca_pars = pd.concat([dca_pars_oil, dca_pars_gas])
    copy_df_xl(
        df=dca_pars,
        sheet="Producing",
        name="fm_fn_producing_dca_pars",
        copy_columns=True,
        xl=xl,
    )


@xl_macro
def set_well_list(xl=None):
    dm = get_cached_object(get_value("data_obj_manager", xl=xl))
    selected_section = get_value("fm_fn_producing_section", xl=xl)

    data = (
        dm.session.query(
            Well_Oneline.well_str,
            Well_Oneline.api,
            Well_Oneline.operator_name,
            Well_Oneline.well_type,
            Well_Oneline.date_completion,
            Well_Oneline.oil_gross_volume,
            Well_Oneline.gas_gross_volume,
        )
        .join(Section_Well)
        .filter(Section_Well.trsm_heh == selected_section)
    )

    df = pd.DataFrame(data).assign(
        date_completion=lambda x: pd.to_datetime(x.date_completion)
    )
    df.columns = [
        "Well Name",
        "Api",
        "Operator",
        "Well Type",
        "Completion Date",
        "Cum Oil",
        "Cum Gas",
    ]

    # clear_list(containing_string="fm_fn_well_list", xl=xl)
    copy_df_xl(df, "Producing", "well_list", copy_columns=True, xl=xl)
