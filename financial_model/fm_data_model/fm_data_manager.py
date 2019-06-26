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
        external_settings: pd.DataFrame,
        assets: pd.DataFrame,
        type_curves: pd.DataFrame,
        section_assumptions: pd.DataFrame,
    ):
        df = self.initiate_project_parameters(external_settings)
        self["project_parameters"] = self.initiate_project_parameters(external_settings)
        self["project_state_assets"] = assets

        sections_str = array_to_sql_string(self.get_sections())
        self.set_par(name="sections", value=sections_str)

        self["type_curves"] = type_curves
        self["section_assumptions"] = section_assumptions

        self.load_data(self.query_manager["section_wells"])

        apis_str = array_to_sql_string(self.get_apis())
        self.set_par(name="apis", value=apis_str)

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
            # "section_onelines"
            # "markets",
        ]
        self.load_data_list(table_list)

    def get_sections(self) -> np.ndarray:
        return self["project_state_assets"].trsm_heh.unique()

    def get_apis(self) -> np.ndarray:
        return self["section_wells"].api.unique()

    def set_par(self, name: str, value: str):
        self._log.info(f"Setting {name} to {value}")
        with self.session_scope() as session:
            par_apis = Project_Parameter(name=name, value=value)
            session.add(par_apis)

    def initiate_project_parameters(self, external_settings) -> pd.DataFrame:
        """

        Returns
        -------

        """
        internal_settings = dict(
            name=["data_model", "data_model_version"],
            value=[self._data_model, self._data_model_version],
        )
        internal_settings = pd.DataFrame(internal_settings)

        settings = pd.concat([internal_settings, external_settings])
        return settings
