import pytest

from fm_data_formatter import FMDataFormatter
from fm_data_loader import FMDataLoader
from fm_data_manager import FMDataManager
from fm_ui import read_project_settings
from generic_debugger import connect_to_excel
from generic_fns import get_value, load_config_path, to_df, ParametersParser
from generic_objects import SourceConnector, QueryManager
from generic_type_hints import w32
from generic_ui import create_source_connector, create_query_manager
import pandas as pd


@pytest.fixture(scope="session")
def ok_sections() -> pd.DataFrame:
    return pd.DataFrame(
        "C:/Users/adi/OneDrive/Work/Pyxll/financial_model/resources/data/ok_sections.csv"
    ).trsm_heh.values


@pytest.fixture(scope="session")
def xl() -> w32:
    xl = connect_to_excel()
    return xl


@pytest.fixture(scope="session")
def config_xl(xl) -> ParametersParser:
    cfg_path = get_value("data_cfg_path")
    return load_config_path(cfg_path)


@pytest.fixture(scope="session")
def source_connector_xl(xl) -> SourceConnector:
    return create_source_connector(xl=xl)


@pytest.fixture(scope="session")
def query_manager_xl(xl) -> QueryManager:
    return create_query_manager(xl=xl)


@pytest.fixture(scope="session")
def data_loader_xl() -> FMDataLoader:
    return FMDataLoader()


@pytest.fixture(scope="session")
def data_formatter_xl() -> FMDataFormatter:
    return FMDataFormatter()


@pytest.fixture(scope="session")
def assets_xl(xl) -> pd.DataFrame:
    return to_df(get_value("project_state_assets", xl=xl))


@pytest.fixture(scope="session")
def section_assumptions_xl(xl) -> pd.DataFrame:
    return to_df(get_value("section_assumptions", xl=xl))


@pytest.fixture(scope="session")
def type_curves_xl(xl) -> pd.DataFrame:
    return to_df(get_value("type_curves", xl=xl))


@pytest.fixture(scope="session")
def create_data_manager_xl(
    xl,
    config_xl,
    query_manager_xl,
    source_connector_xl,
    data_loader_xl,
    data_formatter_xl,
) -> FMDataManager:

    return FMDataManager(
        cfg=config_xl,
        qm=query_manager_xl,
        sc=source_connector_xl,
        dl=data_loader_xl,
        df=data_formatter_xl,
        restore=None,
    )


@pytest.fixture(scope="session")
def fm_data_manager_xl(
    xl,
    config_xl,
    query_manager_xl,
    source_connector_xl,
    data_loader_xl,
    data_formatter_xl,
    request,
) -> FMDataManager:

    dm = FMDataManager(
        cfg=config_xl,
        qm=query_manager_xl,
        sc=source_connector_xl,
        dl=data_loader_xl,
        df=data_formatter_xl,
        restore=request.param,
    )

    if request.param is None:
        assets = to_df(get_value("project_state_assets", xl=xl))
        type_curves = to_df(get_value("type_curves", xl=xl))
        section_assumptions = to_df(get_value("section_assumptions", xl=xl))
        external_settings = read_project_settings(string="sett_", xl=xl)

        dm.set_new_session(
            external_settings=external_settings,
            assets=assets,
            type_curves=type_curves,
            section_assumptions=section_assumptions,
        )

    return dm
