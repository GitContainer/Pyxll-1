import pandas as pd
from sqlalchemy.sql.sqltypes import Float, Integer, Date

from generic_data_loader import DataLoader
from generic_fns import whoami
from generic_tfs import (
    tf_api,
    tf_number_wells,
    tf_dca_pars,
    tf_date,
    tf_net_acres,
    tf_float,
    tf_u_int,
)
from generic_type_hints import SQLTable
from generic_utils import ccast


class FMDataLoader(DataLoader):
    def sections(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            return df

    def section_wells(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            # df = df.drop_duplicates(["api", "trsm_heh"]).reset_index(drop=True)
            return df

    def oil_prices(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            return df

    def gas_prices(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            return df

    def assets(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            return df

    def monthlies(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            return df

    def increased_densities(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            return df

    def f1000s(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            df = self.resolve_duplicates_get_top(
                df, group_by="api", sort_by="permit_date", ascending=False
            )
            return df

    def f1001s(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            df = self.resolve_duplicates_get_top(
                df, group_by="api", sort_by="spud_date", ascending=False
            )
            return df

    def f1002s(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            df = self.resolve_duplicates_get_top(
                df, group_by="api", sort_by="well_completion_date", ascending=False
            )
            return df

    def spacings(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            return df

    def poolings(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            return df

    def markets(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            return df

    def type_curves(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")

        if self.column_check(df.columns.tolist(), table):
            float_cols = self.get_column_types(table, Float)
            df = df.pipe(ccast, (float_cols, tf_dca_pars))
            return df

    def section_assumptions(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            int_cols = self.get_column_types(table, Integer)
            df = df.pipe(ccast, (int_cols, tf_number_wells))
            return df

    def project_state_assets(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")

        if self.column_check(df.columns.tolist(), table):
            df = df.replace("-", 0)
            float_cols = self.get_column_types(table, Float)
            date_cols = self.get_column_types(table, Date)
            df = df.pipe(ccast, (float_cols, tf_net_acres)).pipe(
                ccast, (date_cols, tf_date)
            )
            return df

    def project_parameters(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            return df

    def section_onelines(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            int_cols = self.get_column_types(table, Integer)
            date_cols = self.get_column_types(table, Date)
            df = df.pipe(ccast, (int_cols, tf_number_wells)).pipe(
                ccast, (date_cols, tf_date)
            )
            return df

    def well_onelines(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        exception_list = ["norm_formation"]
        if self.column_check(df.columns.tolist(), table, exception_list):
            float_cols = self.get_column_types(table, Float)
            date_cols = self.get_column_types(table, Date)
            df = (
                df.pipe(ccast, (["api"], tf_api))
                .pipe(ccast, (["total_footage"], tf_u_int))
                .pipe(ccast, (float_cols, tf_float))
                .pipe(ccast, (date_cols, tf_date))
            )
            return df
