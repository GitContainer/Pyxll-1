import inspect
import itertools
import logging
import re
import statistics
import time
import timeit
from configparser import ConfigParser
from configparser import ExtendedInterpolation
from datetime import datetime
from functools import wraps, partial
from types import FunctionType
from datetime import datetime

import easygui
import math
import numpy as np
import pandas as pd
import win32api
import win32com
import win32com.client
from pyxll import xl_app, get_type_converter, ObjectCacheKeyError, xl_func

from generic_exceptions import (
    NamespaceMismatch,
    NameMissingInExcel,
    InvalidExcelAddressException,
    SheetNameNotFoundException,
    MismatchingColumnCountException,
)
from generic_type_hints import w32, List, Callable, Dict
from generic_utils import *

alphabets_value = dict(
    A=1,
    B=2,
    C=3,
    D=4,
    E=5,
    F=6,
    G=7,
    H=8,
    I=9,
    J=10,
    K=11,
    L=12,
    M=13,
    N=14,
    O=15,
    P=16,
    Q=17,
    R=18,
    S=19,
    T=20,
    U=21,
    V=22,
    W=23,
    X=24,
    Y=25,
    Z=26,
)

value_alphabets = {value: key for key, value in alphabets_value.items()}


def time_it(func, *args, **kwargs):
    units = ["s", "ms", "µs", "ns"]
    scaling = [1, 1e3, 1e6, 1e9]

    repeat = kwargs.pop("repeat", 1)
    number = kwargs.pop("number", 1000)

    timing = timeit.Timer(partial(func, *args, **kwargs)).repeat(
        repeat=repeat, number=number
    )
    time_taken = statistics.mean(timing) / number

    order = min(-int(math.floor(math.log10(time_taken)) // 3), 3)
    time_taken_str = f"{time_taken * scaling[order]:.04f} {units[order]}"
    logging.info(f"{func.__name__} took {time_taken_str}")
    print(f"{func.__name__} took {time_taken_str}")


def halt_screen_update(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            kwargs["xl"].ScreenUpdating = False
            result = func(*args, **kwargs)
        finally:
            kwargs["xl"].ScreenUpdating = True
        return result

    return wrapper


@xl_func(volatile=False)
class ParametersParser(ConfigParser):
    def __init__(self, xl_name="data_obj_cfg"):
        """
        Initialize ParametersParser

        Looks for Excel named range xl_name that contains ParametersParser object
        Parameters
        ----------
        xl_name
        """

        self.xl: w32 = xl_app()
        self.xl_name = xl_name

        self._log = logging.getLogger(__name__)

        ConfigParser.__init__(self, interpolation=ExtendedInterpolation())
        self._log.info(f"{__class__.__name__}({len(self)} groups)")

    def __str__(self):
        return f"{__class__.__name__}({len(self)} groups)"

    def __del__(self):
        obj_cleanup(self)


def get_fname_suffix() -> str:
    """
    Filename suffix to be used along with the db file.
    Should be incremental and able to name two different files created seconds apart.
    """
    return time.strftime("%Y%m%d-%H%M%S")


def get_curr_first_dom() -> datetime:
    """
    First date of the month from the current timestamp.
    """
    return datetime.today().replace(day=1)


def month_delta(date: datetime, nmonths: int) -> datetime:
    """
    Adds/Subtracts a month from python datetime

    Parameters
    ----------
    date: datetime
    nmonths: int
        Number of months to add(+)/subtract(-) from the python datetime

    Returns
    -------
    New datetime with nmonths added.
    """
    # TODO: Rewrite this to subtract months
    m = date.month + nmonths
    return date.replace(month=m)


def add_xl_app(func: Callable) -> Callable:
    """
    Wrapper for functions that depend on xl_app.

    Creates a new xl_app if a function is not given a named xl argument else use the one given.
    Should be used instead of validating and creating a new xl_app.
    Functions that use this wrapper should have a xl default named argument with value as None, xl_app

    Parameters
    ----------
    func: Function which may/may not have named xl argument defined.

    Returns
    -------
    Function with xl argument defined.

    Examples
    -------
    @add_xl_app
    def foo(xl=None):
        # The wrapper adds xl_app to xl here.
        pass

    """

    def xl_app_checker(*args, **kwargs):

        if "xl" not in kwargs.keys():
            kwargs["xl"] = xl_app()
            # logging.info(f"xl_app created for {func.__name__}")

        elif kwargs["xl"] is None:
            kwargs["xl"] = xl_app()
            # logging.info(f"xl_app created for {func.__name__}")

        return func(*args, **kwargs)

    return xl_app_checker


@add_xl_app
def excel_formatter(address: str, format_option: str, xl: w32 = None):
    """
    Formats a Excel Range

    Parameters
    ----------
    address: str
        Excel Address
    format_option: str
        Excel Formatting option.
        For further information,
        https://support.microsoft.com/en-us/help/264372/how-to-control-and-understand-settings-in-the-format-cells-dialog-box
    xl:  {None, xl_app}
    """
    xl.Range(address).NumberFormat = format_option


@add_xl_app
def excel_styler(address: str, style_format: str, xl: w32 = None):
    """
    Styles a Excel Range

    Parameters
    ----------
    address: str
        Excel Address
    style_format: str
        Excel Styling option
    xl:  {None, xl_app}
    """
    xl.Range(address).Style = style_format


@add_xl_app
def default_formatter(address, xl: w32 = None):
    """
    Default formatting an Excel Range.

    Parameters
    ----------
    address: str
    xl:  {None, xl_app}
    """
    return excel_formatter(address, format_option="@", xl=xl)


@add_xl_app
def date_formatter(address, xl: w32 = None):
    """
    Project wise date formatter

    Parameters
    ----------
    address: str
    xl:  {None, xl_app}
    """
    return excel_formatter(address, format_option="mm/dd/yyyy", xl=xl)


@add_xl_app
def acreage_formatter(address, xl: w32 = None):
    """
    Project wide acreage formatter

    Parameters
    ----------
    address:str
    xl:  {None, xl_app}
    """
    return excel_formatter(address, format_option="0.0000", xl=xl)


@add_xl_app
def royalty_formatter(address, xl: w32 = None):
    """
    Project wide royalty formatter

    Parameters
    ----------
    address:str
    xl:  {None, xl_app}
    """
    return excel_formatter(address, format_option="0.0000", xl=xl)


@add_xl_app
def currency_styler(address, xl: w32 = None):
    """
    Project wide currency styler

    Parameters
    ----------
    address:str
    xl:  {None, xl_app}
    """
    return excel_styler(address, style_format="Currency", xl=xl)


@add_xl_app
def money_formatter(address, xl: w32 = None):
    """
    Project wide money formatter

    Parameters
    ----------
    address:str
    xl:  {None, xl_app}
    """
    currency_styler(address, xl=xl)
    return excel_formatter(address, format_option="$##,###,##0;;-", xl=xl)


@add_xl_app
def var_loe_formatter(address, xl: w32 = None):
    """
    Project wide Variable LOE formatter

    Parameters
    ----------
    address:str
    xl:  {None, xl_app}
    """
    return excel_formatter(address, format_option="0.00", xl=xl)


@add_xl_app
def align_center(address, how="center", xl=None):
    """

    :param address: str
        Excel Range
    :param how: {"center", "left", "right"}
    :return:
    """
    xlLeft, xlRight, xlCenter = -4131, -4152, -4108
    if how == "center":
        xl.Range(address).HorizontalAlignment = xlCenter


@xl_func("string address: string[]", auto_resize=True)
def make_columns_from_range(address: str) -> List:
    """
    Given a Excel address returns a List of column strings in that range.
    See example for details.

    Parameters
    ----------
    address: str
        Excel Address

    Returns
    -------
    List of Excel columns in str

    Raises
    ------
    InvalidExcelAddressException when the address is not a valid table address.
    It should be of the format [A-Z]\d+:[A-Z]\d+

    Examples
    --------
    >>> make_columns_from_range("A3:C5")
    ['A3:A5', 'B3:B5', 'C3:C5']
    """

    columns = re.findall(r"[A-Z]", address)
    rows = re.findall(r"\d+", address)

    columns_list = list()

    if len(columns) == 2 and len(rows) == 2:

        for i in range(alphabets_value[columns[0]], alphabets_value[columns[1]] + 1):

            columns_list.append(
                str(value_alphabets[i])
                + str(rows[0])
                + ":"
                + str(value_alphabets[i])
                + str(rows[1])
            )
        return columns_list

    else:
        raise InvalidExcelAddressException(address)


@add_xl_app
def load_user_tables(xl: w32 = None, state_str="state"):
    """
    Load Tables from DataManager.
    The tables should have `state` string int their name to indicate that they are stateful.

    Parameters
    ----------
    xl : {None, xl_app}
    state_str: str
        String that is in Excel Named range that indicates that it is a state variable
    Raises
    ------
    MismatchingColumnCountException if the Excel named variable range and the Table shape doesn't Match.
    """
    # TODO : reduce COC
    dm = get_cached_object(get_value("data_obj_manager", xl=xl))
    tables = dm.tbl_names
    for table in tables:
        if state_str in table:
            excel_ncols = count_ncols(excel_address=get_address(table))
            table_ncols = dm.get_data_column_count(table)
            table_sheet = get_sheet_of_name(table, xl=xl)
            if excel_ncols == table_ncols:
                df = dm[table]
                copy_df_xl(df, table_sheet, table, copy_columns=False, xl=xl)
                formatter = getattr(dm.data_formatter, table)
                formatter()
            else:
                raise MismatchingColumnCountException(
                    expected_count=excel_ncols, recieved_count=table_ncols
                )


@add_xl_app
def load_user_zones(xl: w32 = None):
    """
    Loads user tables and project parameters

    Parameters
    ----------
    xl: {None, xl_app}
    """
    load_user_tables(xl=xl)
    load_project_parameters(xl=xl)


@add_xl_app
def load_project_parameters(
    xl: w32 = None, xl_data_mgr_str: str = "data_obj_manager", state_str: str = "state"
):
    """
    Loads project parameters from project_parameters table in DataManager
    The parameters should have string `state` indicating that the are stateful.

    Parameters
    ----------
    xl:  {None, xl_app}
    xl_data_mgr_str: str
        Excel named range that refers to the DataManager
    state_str: str
        String that is in Excel Named range that indicates that it is a state variable
    """
    dm = get_cached_object(get_value(xl_data_mgr_str, xl=xl))
    project_parameters = dm["project_parameters"]

    state_pars = project_parameters.name.str.contains(state_str)
    project_state_parameters = project_parameters.loc[state_pars, :]

    for index, row in project_state_parameters.iterrows():

        if check_name_present(row["name"]):
            sheet = get_sheet_of_name(row["name"], xl=xl)

            xl.ActiveWorkbook.Sheets(sheet).Activate()
            set_address(row["name"], row["value"])

    dm.data_formatter.project_parameters()


@add_xl_app
def clear_list(containing_string: str, xl: w32 = None):
    """
    Clears Named ranges in the excel that contains a specific string.
    See example for usage.

    Parameters
    ----------
    containing_string: str
        This string that is used to group named variables that needs to be cleared
    xl:  {None, xl_app}

    Examples
    -------
    # To clear all the named ranges that have string `obj` which indicated that they are
    # Object and needs to be cleared when a session starts and ends
    clear_list("obj", xl=None)
    """
    logging.info(f"Clearing list containing {containing_string}")
    remove_list = get_names_with_string(containing_string, xl=xl)
    for entity in remove_list:
        set_formula(entity, fn=None, xl=xl, replace=True)


def is_scalar(excel_address: str) -> bool:
    """
    Checks if a excel address is scalar or vector.
    If it contains ':' then it is vector else scalar.

    Parameters
    ----------
    excel_address: str
        Excel Address

    Returns
    -------
    bool

    Examples
    --------
    >>> is_scalar("A3")
    True
    >>> is_scalar("A3:B20")
    False
    """
    return False if ":" in excel_address else True


@add_xl_app
def clear_user_zones(
    containing_string: str = "state", including_columns: bool = False, xl: w32 = None
):
    """
    Clears user zones from the sheet.
    Very similar to clear_list

    Parameters
    ----------
    containing_string: str
        String that group user zones in the project.
    including_columns: bool
        Flag to clear columns.
    xl:  {None, xl_app}

    See Also
    --------
    clear_list
    """
    # TODO: reduce COC
    xl.ScreenUpdating = False
    logging.info("Clearing user input zones")
    remove_list = get_names_with_string(containing_string, xl=xl)
    try:
        for entity in remove_list:
            if including_columns or is_scalar(get_address(entity)):
                set_formula(entity, fn=None, xl=xl, replace=True)
            elif count_nrows(get_address(entity)) > 1:
                current_range = get_address(entity)
                entity_sheet = get_sheet_of_name(entity)
                modified_range = xl_add_row(current_range)

                xl.ActiveWorkbook.Sheets(entity_sheet).Activate()
                xl.ActiveSheet.Range(modified_range).Formula = ""
    finally:
        xl.ScreenUpdating = True


def array_to_sql_string(array: np.ndarray) -> str:
    """
    Converts a numpy array to comma separated string within a tuple.
    Intended for use in SQL Queries generated.

    Parameters
    ----------
    array: np.ndarray
        a numoy string array

    Returns
    -------
    A single comma separated string

    Examples
    --------
    Multiple elements
    >>> array_to_sql_string(np.array(["13N-10W,12 IM", "13N-10W,25 IM"]))
    "('13N-10W,12 IM', '13N-10W,25 IM')"

    Single element
    >>> array_to_sql_string(np.array(["01N-01W,01 IM"]))
    "('01N-01W,01 IM')"
    """
    return "(" + ", ".join("'{0}'".format(i) for i in array) + ")"


def file_picker(message: str, path: str):
    """
    Invokes a easy-gui file picker and lets user pick a file
    from a given path and returns the file name

    Parameters
    ----------
    message: str
        Message in the file picker windows
    path: str
        path to open the file browser

    Returns
    -------
    File name as str
    """
    return easygui.fileopenbox(message, default=path, multiple=False)


def file_saver(message: str, path: str):
    """
    Invokes a easy-gui file saver and lets user create a new file
    in a given path and returns the file name.

    Parameters
    ----------
    message: str
        Message in the file picker windows
    path: str
        path to open the file browser

    Returns
    -------
    File name as str
    """
    return easygui.filesavebox(message, default=path)


def namespace(element):
    """
    returns the namespace of an XML element

    Parameters
    ----------
    element: XML element

    Returns
    -------
    Namespace in str
    """
    match = re.match(r"\{.*\}", element.tag)
    return match.group(0) if match else ""


def get_cached_object(name: str):
    """
    Given a named excel variable returns the Cache object from Pyxll model
    This named excel variable should refer to a pyxll object populated by a function
    with a wrapper xl_func and a signature `object` for its return argument.
    Only objects returned in this way are cached by pyxll mode.
    https://www.pyxll.com/docs/examples/objectcache.html

    Parameters
    ----------
    name: str
        Excel Name variable

    Returns
    -------
    Cached object from Pyxll Model.

    """
    converter = get_type_converter("str", "object")
    return converter(name)


def whoami() -> str:
    """
    Get the function name inside the scope of the same function.

    Returns
    -------
    function name as str
    """
    return inspect.stack()[1][3]


def lol_list(lol) -> List:
    """
    Converts list of list into a flat list

    Parameters
    ----------
    lol: list of list

    Returns
    -------
    A 1D List

    See Also
    --------
    lol_array

    Examples
    --------
    >>> lol_list([[1,2], [3]])
    [1, 2, 3]
    >>> lol_list([[1]])
    [1]
    >>> lol_list([[1, 2, 3]])
    [1, 2, 3]
    """
    return list(itertools.chain(*lol))


def lol_array(lol) -> np.ndarray:
    """
    Converts a list of list into a numpy array

    Parameters
    ----------
    lol: list of list

    Returns
    -------
    A 1D numpy array

    See Also
    --------
    lol_list
    """
    return np.array(lol_list(lol))


def to_df(range, contains_cnames: bool = True) -> pd.DataFrame:
    """
    Converts a tuple of tuple into a Data frame
    Accessing the value of a Named range in excel returns a tuple of tuple.

    Parameters
    ----------
    range: Tuple of tuple
    contains_cnames: bool
        Flag controlling inclusion of column names

    Returns
    -------
    Pandas Dataframe made from range
    """
    df = pd.DataFrame(list(range))
    if contains_cnames:
        df = df.pipe(csetcols, lambda x: x.iloc[0]).iloc[1:]
    return df


@xl_func
@add_xl_app
def get_address(name: str, xl: w32 = None) -> str:
    """
    Address from a named range
    Parameters
    ----------
    name: str
        Excel Address
    xl:  {None, xl_app}

    Returns
    -------
    range address as str
    """
    return xl.Evaluate(name).GetAddress()


@add_xl_app
def set_value(name, value, xl: w32 = None):
    """
    Sets value in a given range

    Parameters
    ----------
    name: str
        Excel named range
    value: value
        Value to be placed in the range
    xl:  {None, xl_app}
    """
    logging.info(f"Setting {name} value")
    xl.Range(name).Value = value


def xl_add_row(address: str, nrows: int = 1) -> str:
    """
    Adds row to a excel address
    See example

    Parameters
    ----------
    address: str
        Excel Address
    nrows: int
        number of rows to add to the address given
    replace_n: int
        number of instances to be replaced.
        If the range is 2D then this should be 2 els if it is scalar then 1.

    Returns
    -------
    Excel address with nrows added as str

    Examples
    --------
    >>> xl_add_row("A3", 5)
    'A8'
    >>> xl_add_row("F3", 2)
    'F5'

    """
    new_row = str(int(re.findall(r"\d+", address)[0]) + nrows)
    # Replace only the first digit encountered
    return re.sub(r"\d+", new_row, address, 1)


def xl_add_column(
    address: str,
    ncols: int = 1,
    value_alphabets: Dict = value_alphabets,
    alphabets_value: Dict = alphabets_value,
) -> str:
    """
    Adds row to a excel address's first part.
    See Example

    Parameters
    ----------
    address: str
        Excel Address
    ncols: int
        number of columns to add to the address given
    value_alphabets: dict
        mapping integers to alphabets
    alphabets_value: dict
        mapping alphabets to integers

    Returns
    -------
    Excel address with ncols added as str

    Examples
    --------
    >>> xl_add_column("A3", 5)
    'F3'
    >>> xl_add_column("G10", 3)
    'J10'

    """
    if is_scalar(address):
        given_col = re.findall(r"[A-Z]+", address)[0]
        col_no = alphabets_value[given_col]
        new_col = value_alphabets[col_no + ncols]
        # Replace only the first digit encountered
        return re.sub(given_col, new_col, address, 1)

    else:
        raise InvalidExcelAddressException(address)


@add_xl_app
def check_object_alive(name: str, xl: w32 = None) -> bool:
    """
    Checks if the object in the excel named range is alive

    Parameters
    ----------
    name: str
        Excel named range
    xl:  {None or xl_app}

    Returns
    -------
    bool indicating the alive status
    """
    if check_name_present(name, xl=xl):
        if not get_value(name, xl=xl):
            return False
        else:
            try:
                get_cached_object(name)
                return True
            except ObjectCacheKeyError:
                return False
    else:
        return False


@add_xl_app
def check_name_present(name: str, xl: w32 = None) -> bool:
    """
    Checks if the named range is present in the excel.

    Parameters
    ----------
    name: str
        Excel named range
    xl:  {None or xl_app}

    Returns
    -------
    bool indicating the presence of the named range
    """
    return False if isinstance(xl.Evaluate(name), int) else True


@add_xl_app
def get_names_with_string(pattern: str, xl: w32 = None) -> List:
    """
    Get all named range that has the pattern sub string
    Parameters
    ----------
    pattern: str
        Substring to look for
    xl:  {None or xl_app}
    Returns
    -------
    List containing named ranges containing patter sub string
    """
    return [x.Name for x in xl.ActiveWorkbook.Names if pattern in x.Name]


@add_xl_app
def get_sheet_of_name(name: str, xl: w32 = None) -> str:
    """
    Get Sheet name from a named range

    Parameters
    ----------
    name: str
        Excel named range
    xl:  {None or xl_app}

    Returns
    -------
    Sheet name as str
    """
    sheet_name = [x for x in xl.ActiveWorkbook.Names if name in x.Name][0]
    sheet = re.findall(r"=([A-Z]+[a-z]+)!", str(sheet_name))
    if sheet is not None:
        return sheet[0]
    else:
        raise SheetNameNotFoundException(name)


def count_nrows(excel_address: str) -> int:
    """
    Returns the number of rows in the excel vector address
    For scalar address it still returns 1

    Parameters
    ----------
    excel_address: str
        Excel address

    Returns
    -------
    Number of rows as int

    Raises
    ------
    InvalidExcelAddressException

    Examples
    --------
    >>> count_nrows("A3:A10")
    8
    >>> count_nrows("A1:D10")
    10
    >>> count_nrows("A3:A3")
    1
    """
    if not is_scalar(excel_address):
        rows = re.findall(r"\d+", excel_address)
        if len(rows) == 2:
            nrows = int(rows[1]) - int(rows[0]) + 1
            if nrows < 0:
                InvalidExcelAddressException(excel_address)
            else:
                return nrows
    else:
        return 1


def count_ncols(excel_address: str, alphabets_value: Dict = alphabets_value) -> int:
    """
        Returns the number of columns in the excel vector address

        Parameters
        ----------
        excel_address: str
            Excel address

        Returns
        -------
        Number of columns as int

        Raises
        ------
        InvalidExcelAddressException

        Examples
        --------
        >>> count_ncols("A3:A10")
        1
        >>> count_ncols("A1:D10")
        4
        """

    columns = re.findall(r"[A-Z]+", excel_address)
    if len(columns) == 2:
        return alphabets_value[columns[1]] - alphabets_value[columns[0]] + 1
    elif len(columns) == 1:
        return 0
    else:
        raise InvalidExcelAddressException(excel_address)


def normalize_column_names(columns: pd.Index):
    """
    Should be used to normalize the column to be used in pandas data frame

    Parameters
    ----------
    columns: pd.Index
        Dataframe columns

    Returns
    -------
    column names normalized in a list

    Examples
    --------
    >>> normalize_column_names(pd.DataFrame({"Test 1": [0,1], " Test 2 ":[1,2]}).columns)
    ['test_1', 'test_2']
    """
    return columns.str.lower().str.strip().str.replace(" ", "_").values.tolist()


@add_xl_app
@xl_func("string name")
def set_formula(
    name: str,
    fn: Callable = None,
    args: str = None,
    xl: w32 = None,
    replace: bool = False,
):
    """
    Set a formula ina  given cell. Used to instantiate objects like data_obj_cfg and data_obj_manager

    Parameters
    ----------
    name: str
        Excel named range
    fn: Callable
        A function to be executed
    args: str
        Arguments to the function
    xl: {None, xl_app}
    replace: bool
        Replace if exists flag
    """
    args = "" if not args else args
    if isinstance(fn, FunctionType):
        formula = f"={fn.__name__}({args})"
    else:
        formula = ""
    if not check_object_alive(name) or replace:
        logging.info(f"Setting {name} as {formula}")
        xl.Range(name).Formula = formula


@add_xl_app
def get_value(name: str, xl: w32 = None):
    """
    Returns the value of a excel named range

    Parameters
    ----------
    name: str
        Excel named range
    xl: {None, xl_app}

    Raises
    ------
    NameMissingInExcel

    Returns
    -------
    value of the range in a tuple

    """
    try:
        return xl.Evaluate(name).Value
    except AttributeError:
        raise NameMissingInExcel(name)


@add_xl_app
def set_address(address: str, value, xl: w32 = None):
    """
    Sets value to an address in excel.

    Parameters
    ----------
    address: str
        Excel address
    value:
        Value to be set at this address
    xl: {None, xl_app}
    """
    xl.ActiveSheet.Range(address).Value = value


@add_xl_app
def copy_df_xl(
    df: pd.DataFrame, sheet: str, name: str, copy_columns: bool = False, xl: w32 = None
):
    """
    Paste a Pandas df to an excel range.

    Parameters
    ----------
    df: pd.DataFrame
        Dataframe to be copied to the excel;
    sheet: str
        sheet where the copy needs to take place
    name: str
        Excel named range where the copy will occur
    copy_columns: bool
        Flag to control inclusion of column names in copying.
    xl: {None, xl_app}

    Warning
    -------
    Time taken is proportional to the data frame dimension.
    For a (1000, 9) df it takes ~ 90 sec.
    TODO: Try out PyExcelerate or xlsxwriter
    https://pypi.org/project/PyExcelerate/
    https://xlsxwriter.readthedocs.io/working_with_memory.html
    """
    xl.ScreenUpdating = False
    try:
        start_cell = get_address(name).split(":")[0]
        if not copy_columns:
            start_cell = xl_add_row(start_cell)

        xl.ActiveWorkbook.Sheets(sheet).Activate()

        for index, row in df.iterrows():
            for value in row:
                xl.ActiveSheet.Range(start_cell).Value = value
                start_cell = xl_add_column(start_cell)
            start_cell = xl_add_column(start_cell, ncols=-df.shape[1])
            start_cell = xl_add_row(start_cell)
    finally:
        xl.ScreenUpdating = True


@xl_func
def test():
    xl = xl_app()
    print("me")
    xl.ActiveSheet.Range("A1:B10000").Value = ("a", "b") * 10000


def add_element(xml, element, replace_if_exists=True):
    """
    Adds an Element to an xml object.

    Parameters
    ----------
    xml: XML
        An XML object like the ribbon
    element: Element
        An XML Element that needs to be added to the xml object
    replace_if_exists: bool
        Flag to control replace behaviour

    Raises
    ------
    NamespaceMismatch in case xml and element are from different namespaces.

    Returns
    -------
    xml with element appended as XML
    """
    if namespace(xml) == namespace(element):
        ns = ".//" + namespace(xml)
        tab = xml.find(ns + "tab")
        tab_group = element.find(ns + "group")
        tab_group_id = tab_group.attrib["id"]
        search_string = f"{ns}group[@id='{tab_group_id}']"
        existing_tab_group = xml.find(search_string)

        if existing_tab_group:
            if replace_if_exists:
                logging.info(f"Removing {existing_tab_group.attrib['id']} from Ribbon")
                tab.remove(existing_tab_group)
            else:
                return xml
        logging.info(f"Adding {tab_group.attrib['id']} to Ribbon")
        tab.append(tab_group)
        return xml
    else:
        raise NamespaceMismatch("main", element.attrib["label"])


def obj_cleanup(obj: object):
    """
    Called when an object is destroyed by the pyxll environment.
    Used to track unnecessary creation/deletion of objects in the model.

    Parameters
    ----------
    obj: object
        Pyxll cached object
    """
    logging.warning(f"Destroying {obj.__class__.__name__}object")


def load_config_path(cfg_path: str) -> ParametersParser:
    """
    Created a config object from the config file

    Parameters
    ----------
    cfg_path: str
        Path to the config file. Usually comes from the excel sheet.

    Returns
    -------
    ParametersParser
    """
    config = ParametersParser()
    config.read(cfg_path)
    return config


def message_box(message: str):
    """
    Displays the message in a small windows with an OK button to close it.
    Use this to inform warnings.

    Parameters
    ----------
    message: str
    """
    win32api.MessageBox(0, message)


def clear_win32com_cache():
    """
    Sometimes the win32com is cached in a User directory that causes unexpected error in pyxll.
    This function throws an warning prompting user to clear files in the appropriate directory.
    """
    cache_path = win32com.__gen_path__
    message_box(
        f"Pyxll encountering unexpected errors. Try clearing cache in {cache_path}"
    )
