import numpy as np


def allocation_acre(acreage: np.ndarray, allocation: np.ndarray):
    """
    Given acreage and allocation return allocation per acre
    :param acreage:
    :param allocation:
    :return:
    """
    assert acreage.shape == allocation.shape
    return (1 / acreage) * allocation


def net_production(production: np.array, acreage, allocation):
    """

    :param production: np.ndarray (2, nwells, nmonths)
        3D array containing oil and gas production for nwells for nmonths
    :param acreage: np.ndarray (1, nwells)
    :param allocation:
    :return:
    """
    assert production.shape[1] == acreage
