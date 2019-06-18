"""
THis module is a helper for Jupyter notebook debug of pyxll modules.
For usage check out check_pyxll.ipynb in common/jupyter
"""
import sys
from configparser import ConfigParser
import psutil
from pyxll import xl_app
from generic_type_hints import w32
import logging


def kill_excel_bg():
    """
    Kills excel Background process inorder to fetch the active worksheet.
    This is dangerous and close all other excel sheets before using this function.
    """
    excel_process = [
        process for process in psutil.process_iter() if process.name() == "EXCEL.EXE"
    ]
    for process in excel_process:
        xl_files = [f.path for f in process.open_files() if ".xl" in f.path]
        print(xl_files)
        if len(xl_files) == 0:
            process.kill()


def connect_to_excel() -> w32:
    """
    Connects to the current active excel workbook and return win32com client object.
    Using this function has known issues.
    :return: w32
        Active open excel worksheet
    """
    xl = xl_app()
    if xl.ActiveWorkbook is None:
        kill_excel_bg()
        xl = xl_app()  # type: w32
        logging.info(f"Connected to excel sheet {xl.ActiveWorkbook.Name}")
    return (
        xl
        if check_jupyter_excel_connection(xl)
        else Exception("Not connected to excel")
    )


def load_modules_from_config(cfg: str):
    """
    Load modules from the pyxll config file.
    Useful in a jupyter notebook environment

    :param cfg: str
        Config file path
    """
    pyxll_cfg = ConfigParser()
    pyxll_cfg.read(cfg)

    for path in pyxll_cfg["PYTHON"]["pythonpath"].split("\n"):
        sys.path.append(path)


def check_jupyter_excel_connection(xl: w32) -> bool:
    """
    Checks it the excel handle supplied is valid

    :param xl: w32
        Excel active workbook
    :return: bool
    """
    return True if xl.ActiveWorkbook is not None else False
