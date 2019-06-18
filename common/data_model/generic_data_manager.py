import logging
from contextlib import contextmanager
from shutil import copyfile

import pandas as pd
from pyxll import xl_func
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from generic_exceptions import (
    IncompatibleDataModelException,
    IncompatibleDataModelVersionException,
    AssignmentErrorException,
    ErrorFindingProjectParameter,
    MissingDataLoaderFunction,
    MissingDataFormatterFunction,
)
from generic_exceptions import NullAttributeValue
from generic_fns import (
    obj_cleanup,
    get_fname_suffix,
    message_box,
    normalize_column_names,
    time_it,
)
from generic_objects import QueryManager, SourceConnector, Query
from generic_type_hints import SQLTable, List, Dict, SQLQuery, SQLSession
from generic_data_formatter import DataFormatter
from generic_data_loader import DataLoader
import numpy as np


class DataManager:
    def __init__(
        self,
        cfg,
        qm: QueryManager,
        sc: SourceConnector,
        dl: DataLoader,
        df: DataFormatter,
        orm,
        restore,
        echo=False,
    ):

        self.xl_name = "data_obj_manager"
        self._log = logging.getLogger(__name__)
        self._log.debug(f"Creating {self.__class__.__name__}")

        self.cfg = cfg
        self.query_manager = qm
        self.source_connector = sc
        self.data_loader = dl
        self.data_formatter = df
        self.orm = orm

        self._data_model = "gm"
        self._data_model_version = "0.1"

        file_name = self._data_model + "." + get_fname_suffix() + "." + self._data_model
        file = self.cfg["PROJECT"]["backup"] + file_name

        self.db_file = file

        if restore:
            # Even in restore copy the stored session into a new file.
            copyfile(restore, self.db_file)

        self._log.info(f"SQLite DB created at {self.db_file}")

        self.db_engine = create_engine(f"sqlite:///{self.db_file}", echo=echo)
        self.db_base = self.orm.base

        if not restore:
            # If not restore have to create all tables in the table from scratch.
            self.db_base.metadata.create_all(self.db_engine)

        self.session_handler = sessionmaker(bind=self.db_engine, autoflush=True)
        self.session = self.session_handler()

        # self.check_data_model_integrity()

    def __len__(self):
        return len(self.tbl_names)

    def __str__(self):
        return f"{__class__.__name__}({len(self)} groups)"

    def __repr__(self):
        return f"{__class__.__name__}({len(self)} groups)"

    def __getitem__(self, name: str) -> pd.DataFrame:
        """
        Overload the index operator to return a data frame.
        self["project_parameters"] to return the table as data frame

        Parameters
        ----------
        name

        Returns
        -------

        """
        return self.get_df(name)

    def __getattr__(self, item) -> SQLTable:
        """
        Overload the dot operator to return the SQLTable
        self.project_parameters to return table handle

        Parameters
        ----------
        item

        Returns
        -------

        """
        return self.get_table_handle(item)

    def __setitem__(self, name: str, value):
        if isinstance(value, pd.DataFrame):
            df = value
            df.columns = normalize_column_names(df.columns)
            table = self.get_table_handle(name)
            tbl_name = table.name

            tf = getattr(self.data_loader, tbl_name)
            df = tf(df, table)

        else:
            raise AssignmentErrorException(value)

        df.to_sql(tbl_name, self.db_engine, if_exists="append", index=False)
        self._log.info(f"{tbl_name}{df.shape}")

    @property
    def tbl_names(self) -> List:
        return self.get_table_names()

    @property
    def tbles(self) -> List:
        return self.db_base.metadata.tables

    @property
    def queries(self) -> Dict:
        return self.query_manager.queries

    @property
    def connections(self) -> Dict:
        return self.source_connector.cnxns

    @contextmanager
    def session_scope(self) -> SQLSession:
        """Provide a transactional scope around a series of operations."""
        try:
            yield self.session
            self.session.commit()
        except Exception:
            self.session.rollback()
            raise Exception
        finally:
            self.session.close()

    @xl_func(" :string []", auto_resize=True)
    def get_all_shapes(self) -> List:
        shapes = list()
        for table in self.tbl_names:
            shapes.append([table, self.get_data_shape(table)])

        return shapes

    def check_data_model(self):
        given_model = self.get_par("data_model")

        if given_model != self._data_model:
            message_box(f"Expected {self._data_model} but got {given_model}")
            raise IncompatibleDataModelException(self._data_model, given_model)

    def check_data_version(self):
        given_model_version = self.get_par("data_model_version")
        if given_model_version != self._data_model_version:
            message_box(
                f"Expected {self._data_model_version} but got {given_model_version}"
            )
            raise IncompatibleDataModelVersionException(
                self._data_model_version, given_model_version
            )

    def check_data_model_integrity(self, state_str="state"):
        for table in self.tbl_names:
            if self.data_loader.loader(table_name=table, df=None, table=None) is None:
                raise MissingDataLoaderFunction(table)

        # Data Formatter is expected only for User facing tables
        state_tables = [table for table in self.tbl_names if state_str in table]
        for table in state_tables:
            if getattr(self.data_formatter, table) is None:
                raise MissingDataFormatterFunction(table)

    def get_table_handle(self, name) -> SQLTable:
        return self.tbles[name]

    def save_as_db(self, dest):
        copyfile(self.db_file, dest)

    @xl_func("object dm, string name: string")
    def load_data_name(self, name: str) -> str:
        self.load_data(self.queries[name])
        return self.get_data_shape(name)

    def load_data_df(self, name: str, df: pd.DataFrame):
        df.columns = normalize_column_names(df.columns)
        table = self.get_table_handle(name)
        tbl_name = table.name

        tf = getattr(self.data_loader, tbl_name)
        df = tf(df, table)

        df.to_sql(tbl_name, self.db_engine)
        self._log.info(f"{tbl_name}{df.shape}")

    @xl_func("object dm, string name: string")
    def load_data_fn(self, fn):
        for query in self.queries:
            if query.function_call == fn:
                self.load_data(query)

    @xl_func
    def load_data_all(self):
        for query in self.queries:
            self.load_data(query)

    def load_data_list(self, tables: List):
        for table in tables:
            self.load_data(self.query_manager[table])

    @xl_func(
        """object dm, string name : dataframe<index=False, columns=True>""",
        auto_resize=True,
    )
    def get_df(self, name: str, statement=None) -> pd.DataFrame:
        table = self.get_table_handle(name)
        if not statement:
            statement = self.session.query(table).statement
        return pd.read_sql(statement, self.session.bind)

    @staticmethod
    def get_np_array(
        query: SQLQuery, shape: tuple = None, dtype: str = "float32"
    ) -> np.ndarray:
        """
        Retrieve a column from the SQlite table that is a numpy array
        :param query:
        :param shape:
        :param dtype:
        :return:
        """
        array = query.all()
        if shape is not None:
            array = np.reshape(array, shape)

        array = array.astype(dtype)

        return array

    def load_project_parameters(self, df: pd.DataFrame):
        df.to_sql(
            "project_parameters", self.db_engine, if_exists="replace", index=False
        )

    def get_par(self, filter: str, par_table="project_parameters") -> str:
        df = self[par_table].query("name == @filter")

        if df.shape[0] != 1:
            raise ErrorFindingProjectParameter(filter)

        return df.value.values[0]

    def is_par_empty(self, par: str) -> bool:
        return True if par == "()" else False

    def query_sub_pars(self, query: Query):
        # TODO: reduce COC
        sql_query = None
        if query.filter:
            if "|" in query.filter:
                for fil in query.filter.split("|"):
                    attr_value = self.get_par(fil)
                    if self.is_par_empty(attr_value):
                        sql_query = query.query.replace(fil, attr_value)
                    else:
                        raise NullAttributeValue(fil)
            else:
                attr_value = self.get_par(query.filter)
                if self.is_par_empty(attr_value):
                    self._log.info(f"{query.name}(0)")
                    return
                else:
                    sql_query = query.query.replace(query.filter, attr_value)

        else:
            sql_query = query.query

        return sql_query

    def clean_data(self, df: pd.DataFrame, table: SQLTable, table_name: str):
        tf = getattr(self.data_loader, table_name)
        df = tf(df, table)
        return df

    def load_data(self, query: Query, if_exists="append"):
        self._log.info(f"Fetching {query.name}")
        table = self.get_table_handle(query.name)
        tbl_name = table.name

        sql_query = self.query_sub_pars(query)

        if sql_query is not None:
            df = pd.read_sql(sql_query, self.source_connector[query.db])
            clean_df = self.clean_data(df, table, tbl_name)
            clean_df.to_sql(tbl_name, self.db_engine, if_exists=if_exists, index=False)

            self._log.info(f"{tbl_name}{clean_df.shape}")

        else:
            self._log.info(f"{tbl_name}(0)")

    def get_primary_keys(self, table_name) -> List:
        return self.get_table_handle(table_name).primary_key.columns.keys()

    def get_columns(self, table_name) -> List:
        return self.get_table_handle(table_name).columns.keys()

    @xl_func("object dm, string table_name: int")
    def get_data_row_count(self, table_name: str) -> int:
        table = self.get_table_handle(table_name)
        nrows = self.session.query(table).count()
        return nrows

    @xl_func("object dm, string name: int")
    def get_data_column_count(self, table_name: str) -> int:
        return len(self.get_columns(table_name))

    @xl_func("object dm, string name: string")
    def get_data_shape(self, name: str) -> str:
        return f"{self.get_data_row_count(name), self.get_data_column_count(name)}"

    @xl_func("object dm: string[]", auto_resize=True)
    def get_table_names(self) -> List:
        return list(self.db_base.metadata.tables.keys())

    def delete_query(self, query):
        self.session.delete(query)
        self.session.commit()

    def __del__(self):
        obj_cleanup(self)

    # TODO: table_name get for non empty tables.
