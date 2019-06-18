from fm_data_formatter import FMDataFormatter
from fm_data_loader import FMDataLoader
from generic_fns import to_df, get_value, load_config_path, add_xl_app, ParametersParser
from generic_type_hints import w32
from generic_ui import create_source_connector, create_query_manager
from fm_data_manager import FMDataManager


@add_xl_app
def debug_fm_data_manager(
    cfg: ParametersParser, xl: w32 = None, restore: str = None, echo: bool = False
) -> FMDataManager:
    """

    :rtype:
    """
    cfg = load_config_path(cfg)
    source_connector = create_source_connector(xl=xl)
    query_manager = create_query_manager(xl=xl)
    data_loader = FMDataLoader()
    data_formatter = FMDataFormatter()

    return FMDataManager(
        cfg=cfg,
        qm=query_manager,
        sc=source_connector,
        dl=data_loader,
        df=data_formatter,
        restore=restore,
        echo=echo,
    )


@add_xl_app
def debug_set_new_session(data_manager: FMDataManager, xl: w32 = None) -> FMDataManager:
    assets = to_df(get_value("project_state_assets", xl=xl))
    type_curves = to_df(get_value("type_curves", xl=xl))
    section_assumptions = to_df(get_value("section_assumptions", xl=xl))

    data_manager.set_new_session(
        assets=assets, type_curves=type_curves, section_assumptions=section_assumptions
    )
    return data_manager
