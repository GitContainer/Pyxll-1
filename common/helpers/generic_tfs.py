"""
List of custom tranformation for the data.
Use this as a single place to control data types and data transformations.
x is a numpy array
"""

import pandas as pd
import numpy as np
from generic_exceptions import TransformationTypeError, ApiError

# TODO: Place checks and test it on pandas version


def tf_api(x):
    """
    api should be not null,
    else uint64 will fail
    :param x:
    :return:
    """
    if (~(x.astype(str).str.len() == 14)).sum() > 0:
        raise ApiError
    else:
        return x.astype("uint64")


def tf_date(x):
    return pd.to_datetime(x)


def tf_float(x):
    return x.astype("float32")


def tf_u_int(x):
    return x.astype("uint32")


def tf_int_with_nan(x, type):
    if isinstance(x, pd.Series):
        if x.dtype == "O":
            x = x.str.upper().replace("NONE", 0).values
        x = np.nan_to_num(x.astype("float32"), 0)
        return x.astype(type)
    else:
        raise TransformationTypeError(expected_type=pd.Series, received_type=type(x))


def tf_feet(x):
    return tf_int_with_nan(x, "uint16")


def tf_number_wells(x):
    return tf_int_with_nan(x, "uint8")


def tf_allocation(x):
    return x.astype("float32").fillna(0)


def tf_royalty(x):
    return tf_allocation(x)


def tf_formation(x):
    return x.fillna("").str.upper().replace("NONE", "")


def tf_stream_production(x):
    return x.astype("float32").fillna(0)


def tf_section_acres(x):

    return x.astype("float32")


def tf_net_acres(x):
    return x.astype("float32").fillna(0)


def tf_cartesian(x):
    return x.astype("uint16")


def tf_cause_number(x):
    return x.astype("uint32")


def tf_dca_pars(x):
    return x.astype("float32")
