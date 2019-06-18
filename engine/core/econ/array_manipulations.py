import numpy as np


def accumulate_axis(array: np.ndarray, start: int, end: int):
    """
    Accumulate values from start to end in the second dimension of a 2D array and sets it at end index.
    Also sets the value from start to end-1 as 0.

    :param array: np.ndarray
    :param start: int
    :param end: int
    :return:

    Examples
    --------
    >>> a = np.array([[1,2,3,4,5], [2,4,6,8,10], [3,6,9,12,15]])
    >>> agg_axis(a, 0, 3)
    array([[ 0,  0,  6,  4,  5],
           [ 0,  0, 12,  8, 10],
           [ 0,  0, 18, 12, 15]])
    """
    new_array = array.copy()
    new_array[:, end - 1] = np.sum(new_array[:, start:end], axis=1)
    new_array[:, start : (end - 1)] = 0
    return new_array


def take_per_row_strided(array: np.ndarray, start_indices: np.ndarray, nelements):
    """
    Slice the first dimension of a 2D array starting from different position
    given by index and ending at num_element.

    :param array: np.ndarray
        2D
    :param start_indices: np.ndarray
        1D
    :param num_elem: int
        Number of elements to select from each row starting from start_indices
    :return: np.ndarray

    Examples
    -------
    >>> array  = np.array([[1,2,3,4,5], [1,2,3,4,5], [1,2,3,4,5]])
    >>> start_indices = np.array([0,1,2])
    >>> take_per_row_strided(array, start_indices, 3)
    array([[1, 2, 3],
           [2, 3, 4],
           [3, 4, 5]])

    """

    row, cols = array.shape
    array.shape = -1
    s0 = array.strides[0]
    l_index = start_indices + cols * np.arange(len(start_indices))
    out = np.lib.stride_tricks.as_strided(
        array, (len(array) - nelements + 1, nelements), (s0, s0)
    )[l_index]
    array.shape = row, cols
    return out


def append_zeroes_front(array: np.ndarray, nzeros: np.ndarray, nelements):
    """
    Appends varying number of zeroes the first dimension of a 2D array/
    :param array: np.ndarray
    :param nzeros: np.ndarray
        Number fo zeroes to add at the start
    :param nelements: int
        Total number of elements to keep in array
    :return: np.ndarray
        Zero padded 2D array

    Examples
    --------
    >>> array = np.tile(np.arange(1, 4), 3).reshape(3, 3)
    >>> nzeros = np.array([0,1,3])
    >>> append_zeroes_front(array, nzeros, 3)
    array([[1, 2, 3],
           [0, 1, 2],
           [0, 0, 0]])
    """
    assert np.all(nzeros <= nelements), "nzeroes cannot be more than nelements"
    new_array = np.zeros_like(array)
    for i in range(array.shape[0]):
        new_array[i, nzeros[i] :] = array[i, : (array.shape[1] - nzeros[i])]

    return new_array
