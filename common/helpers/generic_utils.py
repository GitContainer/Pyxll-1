"""
Helper file for enabling easier usage of pandas.
"""

from functools import reduce

# TODO: Place checks and test it on pandas version


class AttrDict(dict):
    """Set and Get elements of a dictionary using the dot operator"""

    __getattr__ = dict.__getitem__
    __setattr__ = dict.__setitem__


# Custom pipe Functions
def csnap(orig_df, fn=lambda x: x.shape, msg=None):
    """ Custom Help function to print things in method chaining.
        Returns back the df to further use in chaining.
    """
    if msg:
        print(msg)
    print(fn(orig_df))
    return orig_df


def cfilter(orig_df, fn, axis="rows"):
    """ Custom Filters based on a condition and returns the df.
        function - a lambda function that returns a binary vector
        thats similar in shape to the dataframe
        axis = rows or columns to be filtered.
        A single level indexing
    """
    if axis == "rows":
        return orig_df[fn(orig_df)]
    elif axis == "columns":
        return orig_df.iloc[:, fn(orig_df)]


def csetcols(orig_df, fn=lambda x: x.columns.map("_".join), cols=None):
    """Sets the column of the data frame to the passed column list.
    """
    df = orig_df.copy()
    if cols:
        df.columns = cols
    else:
        df.columns = fn(df)
    return df


def ccast(orig_df, tf_tuple):
    """
    df - Data frame
    tf_tuple - ([column names], transformation) - A tuple containing pair of column name list and assaociated transformation to be applied to it
    """
    df = orig_df.copy()
    columns, tf = tf_tuple
    for col in columns:
        df[col] = tf(df[col])
    return df


def ccol(orig_df, string, sep=";"):
    """ Custom column filtering that works in multi level indexing.
    """
    return orig_df.iloc[
        :,
        reduce(
            lambda x, y: x & y,
            [
                (
                    orig_df.columns.get_level_values(i)
                    .to_series()
                    .str.contains(string, case=False)
                    .fillna(True)
                    .values
                )
                for i, string in enumerate(string.split(sep))
            ],
        ),
    ]
