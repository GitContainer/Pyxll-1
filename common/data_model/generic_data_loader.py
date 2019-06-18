import logging

from generic_exceptions import ColumnMismatch
from generic_type_hints import List, SQLTable
import pandas as pd


class DataLoader:
    def __init__(self):
        self._log = logging.getLogger(__name__)

    @staticmethod
    def resolve_duplicates_get_top(
        df: pd.DataFrame, group_by: str, sort_by: str, ascending=False
    ) -> pd.DataFrame:
        """
        Used to resolve duplicates in a table by grouping on a column and
        sorting on another column to get the top record.

        For example, if we have an api that have multiple f1000s then we can get
        the latest form based on permit date

        :param df:  pd.DataFrame
        :param group_by: str
            Pandas column name
        :param sort_by: str
            Pandas column name
        :param ascending:
        :return:  pd.DataFrame
        """
        df_new = df.copy()
        return (
            df_new.sort_values(sort_by, ascending=ascending)
            .groupby(group_by)
            .head(1)
            .reset_index(drop=True)
        )

    @staticmethod
    def column_check(
        df_columns: List, table: SQLTable, exception_list: List = None
    ) -> bool:
        """
        Compare the column count between the dataframe and teh SQL Table.

        Parameters
        ----------
        df_columns: List
            column names
        table: SQLTable
            SQLAlchemy Table
        exception_list: List
            column names populated at run time

        Raises
        ------
        ColumnMismatch in case of length mismatch

        Returns
        -------
        flag showing the result of comparision as bool
        """
        table_columns = table.columns.keys()
        if exception_list is not None:
            table_columns = [col for col in table_columns if col not in exception_list]

        if (
            len(df_columns)
            == len(table_columns)
            == len(set(df_columns) & set(table_columns))
        ):
            return True
        else:
            raise ColumnMismatch(
                expected_columns=table_columns, received_columns=df_columns
            )

    @staticmethod
    def get_column_types(table: SQLTable, col_type):
        """
        Used to get columns of certain type from the SQLTable

        Parameters
        ----------
        table: SQLTable
        col_type:
            SQLAlchemy Column Type to filter for

        Returns
        -------
        List of SQLAlchemy Columns
        """
        table_columns = table.columns
        cols = list()
        for column in table_columns:
            if isinstance(column.type, col_type):
                cols.append(column.name)
        return cols
