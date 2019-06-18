import numpy as np


def rmse(actual, predicted):
    return np.sqrt(np.sum(np.square(actual - predicted)))
