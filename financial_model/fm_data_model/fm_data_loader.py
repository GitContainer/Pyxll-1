import pandas as pd
import numpy as np
from sqlalchemy.sql.sqltypes import Float, Integer, Date

from generic_data_loader import DataLoader
from generic_fns import whoami, message_box, get_column_types
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

    @staticmethod
    def helper_add_missing_dates(df: pd.DataFrame) -> pd.DataFrame:
        """
        Adds missing dates to production stream.
        If a production for a month for a well is not reported this add the date and
        fills the value as zero.
        :param df: pd.DateFrame
            monthly df with missing productions
        :return: pd.DataFrame
            monthly df with production filled in as zero for missing dates
        """

        df_index = (
            df.groupby("api")
            .date.agg({"min", "max", "count"})
            .reset_index()
            .rename(columns={"min": "start", "max": "end", "count": "months"})
        )

        index_tuple = [None] * df_index.months.sum()

        index = 0
        for _, row in df_index.iterrows():
            date_range = pd.date_range(row["start"], row["end"], freq="MS")
            for month in range(row["months"]):
                index_tuple[index] = (row["api"], date_range[month])
                index += 1

        multi_idx = pd.MultiIndex.from_tuples(index_tuple, names=("api", "date"))
        df = df.set_index(["api", "date"]).reindex(multi_idx).fillna(0).reset_index()
        return df

    def monthlies(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            date_cols = get_column_types(table, Date)

            df = df.pipe(ccast, (date_cols, tf_date)).pipe(
                ccast, (["api"], tf_api)
            )  # type: pd.DataFrame
            df = df.sort_values(by=["api", "date"], ascending=True)

            df = self.helper_add_missing_dates(df)

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
            date_cols = get_column_types(table, Date)
            df = df.pipe(ccast, (date_cols, tf_date))
            return df

    def f1001s(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            df = self.resolve_duplicates_get_top(
                df, group_by="api", sort_by="spud_date", ascending=False
            )
            date_cols = get_column_types(table, Date)
            df = df.pipe(ccast, (date_cols, tf_date))
            return df

    def f1002s(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            df = self.resolve_duplicates_get_top(
                df, group_by="api", sort_by="well_completion_date", ascending=False
            )
            date_cols = get_column_types(table, Date)
            df = df.pipe(ccast, (date_cols, tf_date))
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
            float_cols = get_column_types(table, Float)
            df = df.pipe(ccast, (float_cols, tf_dca_pars))
            return df

    def section_assumptions(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            int_cols = get_column_types(table, Integer)
            df = df.pipe(ccast, (int_cols, tf_number_wells))
            return df

    def project_state_assets(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")

        if self.column_check(df.columns.tolist(), table):
            df = df.replace("-", 0)
            float_cols = get_column_types(table, Float)
            date_cols = get_column_types(table, Date)
            df = df.pipe(ccast, (float_cols, tf_net_acres)).pipe(
                ccast, (date_cols, tf_date)
            )
            pk = table.primary_key.columns.keys()
            duplicates = df.duplicated(pk)
            dup_idx = ", ".join(df[duplicates].index.astype("unicode").tolist())
            if np.all(duplicates):
                message_box(
                    f"Duplicate assets found at {dup_idx}. {', '.join(pk)} combination should be unique."
                )

            return df

    def project_parameters(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            return df

    def section_onelines(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        if self.column_check(df.columns.tolist(), table):
            int_cols = get_column_types(table, Integer)
            date_cols = get_column_types(table, Date)
            df = df.pipe(ccast, (int_cols, tf_number_wells)).pipe(
                ccast, (date_cols, tf_date)
            )
            return df

    def well_onelines(self, df: pd.DataFrame, table: SQLTable) -> pd.DataFrame:
        self._log.debug(f"Cleaning {whoami()}")
        # stream_cols = [
        #     par + "_" + stream
        #     for par in ["ip", "di", "dmin", "b"]
        #     for stream in ["oil", "gas"]
        # ]
        # exception_list = ["norm_formation"] + stream_cols
        # if self.column_check(df.columns.tolist(), table, exception_list):
        #     float_cols = get_column_types(table, Float)
        #     date_cols = get_column_types(table, Date)
        #     df = (
        #         df.pipe(ccast, (["api"], tf_api))
        #         .pipe(ccast, (["total_footage"], tf_u_int))
        #         .pipe(ccast, (float_cols, tf_float))
        #         .pipe(ccast, (date_cols, tf_date))
        #     )
        return df
