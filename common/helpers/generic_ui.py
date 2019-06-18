from pyxll import xl_func, xl_app, set_ribbon_xml, get_ribbon_xml, xl_menu
import pydevd
from generic_objects import SourceConnector, SourceConnection, Query, QueryManager
from generic_fns import (
    to_df,
    get_value,
    add_element,
    get_cached_object,
    load_config_path,
    ParametersParser,
    add_xl_app,
)

import xml.etree.ElementTree as ET
import os
import logging


@xl_func(":bool")
def load_pyxll_ribbon():
    try:
        xl = xl_app()
        is_pyxll = get_value("data_pyxll_flag", xl=xl)
        if is_pyxll:
            logging.info("Setting pyxll ribbon")
            cfg = ParametersParser()
            cfg.read(get_value("data_cfg_path", xl=xl))
            ET.register_namespace("", cfg["PROJECT"]["xml_ns"])
            ribbon_start = ET.fromstring(get_ribbon_xml())
            pyxll = ET.parse(cfg["XML"]["pyxll"]).getroot()
            ribbon_end = add_element(ribbon_start, pyxll)
            ribbon_end_string = ET.tostring(
                ribbon_end, encoding="unicode", method="xml"
            )
            set_ribbon_xml(ribbon_end_string, reload=True)
            return True

    except Exception:
        return False


@xl_menu("Connect to PyCharm")
def connect_to_pycharm():
    pydevd.settrace(
        "localhost", port=5000, suspend=False, stdoutToServer=True, stderrToServer=True
    )


@xl_menu("Re-connect to PyCharm")
def reconnect_to_pycharm():
    pydevd.connected = False
    pydevd.settrace(
        "localhost", port=5000, suspend=False, stdoutToServer=True, stderrToServer=True
    )


@xl_func()
def set_logging_level(selection):
    logging.basicConfig()
    if selection == "INFO":
        logging.getLogger().setLevel(logging.INFO)
    elif selection == "WARNING":
        logging.getLogger().setLevel(logging.INFO)
    elif selection == "ERROR":
        logging.getLogger().setLevel(logging.INFO)


@add_xl_app
@xl_func
def create_source_connector(xl=None):
    """
    @type xl: win32com.client.Dispatch("Excel.Application")
    :param xl:
    :return:
    """
    connection_settings = to_df(get_value("data_servers", xl=xl))
    sql_cnxns = list()
    for cnxn in connection_settings.itertuples():
        new_connection = SourceConnection(
            cnxn.db,
            cnxn.server,
            cnxn.driver,
            int(cnxn.port),
            os.environ[cnxn.user],
            os.environ[cnxn.pwd],
            cnxn.auth,
        )
        sql_cnxns.append(new_connection)
    sql_manager = SourceConnector(sql_cnxns)
    return sql_manager


@add_xl_app
@xl_func
def create_query_manager(xl=None):
    """
    @type xl: win32com.client.Dispatch("Excel.Application")
    :param xl:
    :return:
    """
    sql_queries = to_df(get_value("data_queries", xl=xl))
    queries = list()
    for query in sql_queries.itertuples():
        new_connection = Query(
            query.name, query.db, query.query, query.filter, query.function_call
        )
        queries.append(new_connection)
    query_manager = QueryManager(queries)
    return query_manager


#
# @add_xl_app
# @xl_func
# def create_data_manager(xl=None):
#     source_connector = create_source_connector(xl=xl)
#     query_manager = create_query_manager(xl=xl)
#     return DataManager(query_manager, source_connector, dl, orm)


@xl_func("string handler")
def check_cache(handler):
    logging.info(get_cached_object(handler))


@xl_func(volatile=False)
def load_config_xl():
    logging.info("Loading Configurations")
    xl = xl_app()
    cfg_path = xl.Evaluate("data_cfg_path").Value
    config = load_config_path(cfg_path)
    return config


@add_xl_app
@xl_func("""object xl: """)
def load_mode(xl, cfg):
    logging.info("Loading Model Mode")
    mode = xl.Evaluate("data_model_mode").Value
    if mode.strip().upper() == "DEV":
        ET.register_namespace("", cfg["PROJECT"]["xml_ns"])
        ribbon_start = ET.fromstring(get_ribbon_xml())
        dev = ET.parse(cfg["XML"]["dev"]).getroot()
        ribbon_end = add_element(ribbon_start, dev)
        ribbon_end_string = ET.tostring(ribbon_end, encoding="unicode", method="xml")
        set_ribbon_xml(ribbon_end_string, reload=True)


@add_xl_app
@xl_func("""object xl: """)
def load_project_xml(xl=None):
    project_specific = get_value("data_load_tabs", xl=xl)
    logging.info(f"Loading {project_specific} ribbon")
    cfg = get_cached_object(get_value("data_obj_cfg"))

    ET.register_namespace("", cfg["PROJECT"]["xml_ns"])
    ribbon_start = ET.fromstring(get_ribbon_xml())
    project_xml = ET.parse(cfg["XML"][project_specific]).getroot()
    ribbon_end = add_element(ribbon_start, project_xml)
    ribbon_end_string = ET.tostring(ribbon_end, encoding="unicode", method="xml")
    set_ribbon_xml(ribbon_end_string, reload=True)


@add_xl_app
@xl_func("""string sheet, object xl: """)
def load_module_xml(module, xl=None):
    cfg = get_cached_object(get_value("data_obj_cfg"))

    ET.register_namespace("", cfg["PROJECT"]["xml_ns"])
    ribbon_start = ET.fromstring(get_ribbon_xml())
    project_xml = ET.parse(cfg["XML"][module]).getroot()
    ribbon_end = add_element(ribbon_start, project_xml)
    ribbon_end_string = ET.tostring(ribbon_end, encoding="unicode", method="xml")
    set_ribbon_xml(ribbon_end_string, reload=True)


# Context Managers
def add_meridian(control):
    xl = xl_app()
    for cell in xl.Selection:
        value = cell.Value
        if not isinstance(value, str):
            continue
        cell.Value = value + " IM"
