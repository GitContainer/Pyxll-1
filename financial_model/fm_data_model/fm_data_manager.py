from datetime import datetime

import numpy as np
import pandas as pd

from fm_data_model import (
    fm_data_formatter as data_formatter,
    fm_data_loader as data_loader,
)

from generic_data_manager import DataManager
from generic_fns import get_curr_first_dom, array_to_sql_string, ParametersParser
from generic_objects import QueryManager, SourceConnector

from fm_orm import Project_Parameter
import fm_orm as orm


class FMDataManager(DataManager):
    """

    """

    def __init__(
        self,
        cfg: ParametersParser,
        qm: QueryManager,
        sc: SourceConnector,
        dl: data_loader,
        df: data_formatter,
        restore=None,
        echo=False,
    ):

        self._data_model = "fm"
        self._data_model_version = "0.2"

        super(FMDataManager, self).__init__(cfg, qm, sc, dl, df, orm, restore, echo)

        self.did_data_change = False
        self.is_session_saved = False

    def check_compatibility(self):
        self.check_data_model()
        self.check_data_version()

    def set_new_session(
        self,
        assets: pd.DataFrame,
        type_curves: pd.DataFrame,
        section_assumptions: pd.DataFrame,
    ):
        self["project_parameters"] = self.initiate_project_parameters()
        self["project_state_assets"] = assets
        self._log.info(self.tbl_names)
        self.set_sections(self.get_sections())

        self["type_curves"] = type_curves
        self["section_assumptions"] = section_assumptions
        self.load_data(self.query_manager["section_wells"])
        self.set_apis(self.get_apis())

        table_list = [
            "sections",
            "monthlies",
            "increased_densities",
            "f1000s",
            "f1001s",
            "f1002s",
            # "spacings",
            # "poolings",
            "oil_prices",
            "gas_prices",
            "well_onelines",
            "section_onelines"
            # "markets",
        ]
        self.load_data_list(table_list)

    def get_sections(self) -> np.ndarray:
        return self["project_state_assets"].trsm_heh.unique()

    def get_apis(self) -> np.ndarray:
        return self["section_wells"].api.unique()

    def set_apis(self, apis_list: np.ndarray):
        apis = array_to_sql_string(apis_list)
        self._log.info(f"Setting apis to {apis}")
        par_apis = Project_Parameter(name="apis", value=apis)
        self.session.add(par_apis)
        self.session.commit()

    def set_sections(self, section_list: np.ndarray):
        sections = array_to_sql_string(section_list)
        self._log.info(f"Setting sections to {sections}")
        par_sections = Project_Parameter(name="sections", value=sections)
        self.session.add(par_sections)
        self.session.commit()

    def initiate_project_parameters(self) -> pd.DataFrame:
        """

        Returns
        -------

        """
        first_dom = get_curr_first_dom()
        parameters = dict(
            name=[
                "data_model",
                "data_model_version",
                "project_state_fin_eff_date",
                "project_state_spacing_start_date",
                "project_state_pooling_start_date",
                "project_state_market_start_date",
            ],
            value=[
                self._data_model,
                self._data_model_version,
                str(first_dom),
                str(datetime(2000, 1, 1)),
                str(datetime(2000, 1, 1)),
                str(first_dom),
            ],
        )
        return pd.DataFrame(parameters)