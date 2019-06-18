from typing import NewType, List
import win32com.client

from typing import NewType, List, Callable, Dict, Iterable, NoReturn
from sqlalchemy import Table, Column
from sqlalchemy.orm.session import query
from sqlalchemy.orm import session

w32 = NewType("w32", win32com.client.Dispatch("Excel.Application"))
SQLTable = NewType("SQLTable", Table)
SQLColumn = NewType("SQLTable", Column)
SQLQuery = NewType("SQLQuery", query)
SQLSession = NewType("SQLSession", session)
