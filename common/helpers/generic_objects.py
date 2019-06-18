import logging
from collections import namedtuple

import pyodbc

SourceConnection = namedtuple("SourceConnection", "db server driver port user pwd auth")
Query = namedtuple("Query", "name db query filter function_call")


class QueryManager:
    def __init__(self, sql_queries):
        self.xl_name = "data_query_manager"
        self._log = logging.getLogger(__name__)

        self.queries = dict()
        for query in sql_queries:
            self.queries[query.name] = query

        self._log.info(f"{self.__class__.__name__}({len(self.queries)} queries)")

    def __getitem__(self, name: str):
        return self.queries[name]

    def no_of_filter(self, name: str) -> int:
        if self.queries[name].query is None:
            return 0
        else:
            return self.queries[name].query.upper().count("AND")

    @staticmethod
    def create_new_query(query: Query, new_query: str) -> Query:
        return Query(query.name, query.db, new_query, query.filter, query.function_call)

    # def remove_query_filters(self, name: str):
    #     # If there are only one filter then there will be 1 WHERE clause and no AND clause.
    #     if self.no_of_filter(name) == 1:
    #         new_query = re.sub(pattern=r"where.*;", repl=";", string=self.queries[name], flags=re.IGNORECASE)
    #         self.queries[name] = self.create_new_query(self.queries[name], new_query)
    #     # If there are multiple filters there will be 1 WHERE clause and n AND clause
    #     elif self.no_of_filter(name) > 1:
    #

    def __repr__(self):
        return f"{self.__class__.__name__}({len(self.queries)} queries)"

    def __str__(self):
        return f"{self.__class__.__name__}({len(self.queries)} queries)"


class SourceConnector:
    def __init__(self, sql_cnxns):
        self.xl_name = "data_source_connector"
        self._log = logging.getLogger(__name__)

        self.cnxns = dict()
        for cnxn in sql_cnxns:
            try:
                self.connect(cnxn)
            except pyodbc.Error as error:
                self._log.error(error)

        self._log.info(f"{self.__class__.__name__}({len(self.cnxns)} connections)")

    def __getitem__(self, name: str):
        return self.get_cnxn(name)

    def connect(self, cnxn):
        self._log.info(f"connecting to {cnxn.db}")
        cnxn_string = f"""DRIVER={cnxn.driver};PORT={cnxn.port};SERVER={cnxn.server};PORT={cnxn.port};
                    DATABASE={cnxn.db};UID={cnxn.user};PWD={cnxn.pwd};Authentication={cnxn.auth}"""
        try:
            self.cnxns[cnxn.db] = pyodbc.connect(cnxn_string)
        except pyodbc.Error as error:
            self._log.error(error)

    def get_cnxn(self, db):
        if self.cnxns[db].timeout:
            self._log.error(f"{db} connection timeout.")
        return self.cnxns[db]

    def __repr__(self):
        return f"{self.__class__.__name__}({len(self.cnxns)} connections)"

    def __str__(self):
        return f"{self.__class__.__name__}({len(self.cnxns)} connections)"
