"""
IP generator that gives IP values for all current and future wells.
Have direct impact on the valuation of a section.

The logic is written in a for loop for easier understanding and compiled in numba for efficiency.
"""

import numpy as np
from numba import jit

# TODO: replace multiple index with single index. Eg a[i][j] to a[i, j]
def grid_set_values_max(int_array, float_array, nformations):
    """
    Sets the IP value in a grid defined by the cartesian coordinates of a section.

    Maximum of max30 and f1002a in a section is set as the final value.
    Based on int_array and float_array dtype the speed changes.
    Lower dtype faster execution.

    Written in a way to enable numba optimization.
    Perform all data validations before the function call.

    :param int_array: np.array of type int16 (3, nwells)
         0. Section cartesian_x
         1. Section cartesian_y
         2. formation_code encoded to Integers
         
    :param float_array: np.array of type float32 (4, nwells)
        0. f1002_oil
        1. max30_oil
        2. f1002a_gas
        3. max30_gas
        
    :param nformations: number of formations
    :return: 2D np.array with values set 
    """
    xmin = int_array[0].min()
    xmax = int_array[0].max()
    ymin = int_array[1].min()
    ymax = int_array[1].max()

    float_type = float_array.dtype
    int_type = int_array.dtype

    # Result array of shape (nformations, nstreams=2, xmax + 1, ymax + 1)
    result = np.zeros(shape=(np.int64(nformations), 2, xmax + 1, ymax + 1)).astype(
        float_type
    )

    # For every formation and every entry get the maximum of max30, f1002 and existing value
    # Set that as the final value.
    for j in range(nformations):
        j = int_type(j)
        ip_array_oil = np.zeros(shape=(xmax + 1, ymax + 1)).astype(float_type)
        ip_array_gas = np.zeros(shape=(xmax + 1, ymax + 1)).astype(float_type)

        form_mask = int_array[2] == j
        co_array = int_array[:2, form_mask]
        ip_array = float_array[:, form_mask]
        for i in range(co_array.shape[1]):
            # ip_array[0] - f1002_oil, ip_array[1] - max30_oil
            # ip_array_oil[co_array[0][i] - existing value (initialized with 0)
            oil_ip_values = np.array(
                [
                    ip_array_oil[co_array[0][i]][co_array[1][i]],
                    ip_array[0][i],
                    ip_array[1][i],
                ]
            )
            ip_array_oil[co_array[0][i]][co_array[1][i]] = np.max(oil_ip_values)

            # ip_array[0] - f1002_gas, ip_array[1] - max30_gas
            # ip_array_oil[co_array[0][i] - existing value (initialized with 0)
            gas_ip_values = np.array(
                [
                    ip_array_gas[co_array[0][i]][co_array[1][i]],
                    ip_array[2][i],
                    ip_array[3][i],
                ]
            )
            ip_array_gas[co_array[0][i]][co_array[1][i]] = np.max(gas_ip_values)

        result[j][0] = ip_array_oil
        result[j][1] = ip_array_gas

    return result


nb_grid_set_values_max = jit(
    grid_set_values_max, nopython=True, fastmath=True, error_model="numpy"
)


def plot_grid(result):
    nformations = result.shape[0]
    for i in range(nformations):
        plt.imshow(result[i][0].transpose())
        # plt.imshow(np.pad(result[1][0], pad_width=3, mode="constant").transpose())
        plt.show()


def spot_radius_average(ip_pad, radius):
    """
    IP average for a section based on neighboring spots defined by the radius.

    Written using loops to speed up with numba.
    :param ip_pad: np.array of shape (nformations, nstream, max_x, max_y)
        from grid_set_value with padding added at the borders
    :param radius: int
        radius that defines the spots to include while averaging
    :return:
    """
    idx_dtype = np.int16

    # Initialize the variables to proper format
    nforms = idx_dtype(ip_pad.shape[0])
    nstreams = idx_dtype(ip_pad.shape[1])
    xmax = idx_dtype(ip_pad.shape[2])
    ymax = idx_dtype(ip_pad.shape[3])
    r = idx_dtype(radius)

    ip_radius_avg = np.zeros_like(ip_pad)
    for f in range(nforms):
        for s in range(nstreams):
            # lower and upper control the spot sections oto be included based on radius
            lower = -r
            upper = r + idx_dtype(1)

            n = (idx_dtype(r) * idx_dtype(2) + idx_dtype(1)) ^ idx_dtype(2)
            for i in range(r, xmax - r):
                for j in range(r, ymax - r):
                    # For every unique coordinate average the spot ip's
                    sum_ip_spot = np.float32(0)

                    # For every section in the n spots of the current coordinate
                    for spot_x in range(lower, upper):
                        for spot_y in range(lower, upper):

                            sum_ip_spot += (
                                ip_pad[f][s][i + spot_x][j]
                                + ip_pad[f][s][i][j + spot_y]
                            )

                    ip_radius_avg[f][s][i][j] = sum_ip_spot / n

    return ip_radius_avg


nb_spot_radius_average = jit(
    spot_radius_average, nopython=True, fastmath=True, error_model="numpy"
)


def pad_result_array(result, npads):
    nforms = result.shape[0]
    nstreams = result.shape[1]
    maxx = result.shape[2]
    maxy = result.shape[3]

    result_pad = np.zeros(
        shape=(nforms, nstreams, maxx + npads, maxy + npads), dtype=result.dtype
    )
    for i in range(nforms):
        for j in range(nstreams):
            result_pad[i][j] = np.pad(
                result[i][j], pad_width=npads // 2, mode="constant"
            )
    return result_pad


def ip_generator(
    int_array: np.array, float_array: np.array, nformations: np.array, radius_spots: int
) -> np.array:
    """
    IP generator for all cartesian coordinate points based on the average of the spot radius
    :param int_array: np.array of type int16 (3, nwells)
         0. Section cartesian_x
         1. Section cartesian_y
         2. formation_code encoded to Integers

    :param float_array: np.array of type float32 (4, nwells)
        0. f1002_oil
        1. max30_oil
        2. f1002a_gas
        3. max30_gas

    :param nformations: int
        `number of formations
    :param radius_spots: int
        radius of the spots to look for averaging
    :return: 2D np.array with values set
    """
    result = nb_grid_set_values_max(int_array, float_array, nformations)

    radius = np.int(radius_spots)
    npads = radius * 2

    result_padded = pad_result_array(result, npads)
    final_result = nb_spot_radius_average(result_padded)

    return final_result
