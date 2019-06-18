from generic_fns import (
    add_xl_app,
    get_address,
    make_columns_from_range,
    to_df,
    get_value,
)
from generic_type_hints import w32


class DataFormatter:
    @add_xl_app
    def map_columns_range(self, name: str, xl: w32 = None):
        address = get_address(name, xl=xl)
        excel_columns = make_columns_from_range(address)
        df_columns = to_df(get_value(name, xl=xl)).columns.values.tolist()

        return {key: value for key, value in zip(df_columns, excel_columns)}
