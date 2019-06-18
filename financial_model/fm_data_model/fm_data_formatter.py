from generic_fns import (
    acreage_formatter,
    royalty_formatter,
    money_formatter,
    date_formatter,
    var_loe_formatter,
    align_center,
)
from generic_fns import add_xl_app, get_address, whoami
from generic_type_hints import w32
from generic_data_formatter import DataFormatter


class FMDataFormatter(DataFormatter):
    @add_xl_app
    def project_parameters(self, xl: w32 = None):
        date_formatter(get_address("project_state_fin_eff_date", xl=xl))

    @add_xl_app
    def project_state_assets(self, xl: w32 = None):
        column_range = self.map_columns_range(whoami(), xl=xl)

        acreage_formatter(column_range["net_acres"], xl=xl)
        royalty_formatter(column_range["royalty"], xl=xl)

        money_formatter(column_range["lease_bonus"], xl=xl)
        money_formatter(column_range["ask"], xl=xl)
        money_formatter(column_range["fixed"], xl=xl)

        date_formatter(column_range["lease_date"], xl=xl)
        var_loe_formatter(column_range["var_oil"], xl=xl)
        var_loe_formatter(column_range["var_gas"], xl=xl)
        align_center(get_address(whoami()))
