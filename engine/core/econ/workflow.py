import numpy as np

from array_manipulations import (
    accumulate_axis,
    take_per_row_strided,
    append_zeroes_front,
)
from generic_fns import time_it
from mod_arps import np_mod_arps_fit
from pricing import flat_fill
from tax import two_tax_regime


def make_dca_pars(nwells, dtype):
    """
    :param nwells:
    :param dtype:
    :return:
    """
    ip = np.random.uniform(low=100, high=3000, size=nwells).astype(dtype)
    # Di cannot be lower than dmin else the logic will be incorrect.
    di = np.random.uniform(low=0.10, high=1, size=nwells).astype(dtype)
    dmin = np.random.uniform(low=0.06, high=0.08, size=nwells).astype(dtype)
    b = np.random.uniform(low=0, high=2, size=nwells).astype(dtype)

    dca_pars = np.array([ip, di, dmin, b])
    return dca_pars


def make_pricing(oil_flat_price, gas_flat_price, nmonths, start_date, dtype):

    oil_pricing = flat_fill(
        periods=nmonths, start_date=start_date, value=oil_flat_price, dtype=dtype
    )
    gas_pricing = flat_fill(
        periods=nmonths, start_date=start_date, value=gas_flat_price, dtype=dtype
    )
    dates = oil_pricing[0]
    pricing = np.array([oil_pricing[1], gas_pricing[1]], dtype=dtype)

    assert dates.shape[0] == pricing.shape[1]
    return dates, pricing


def make_tax(
    tax_t1,
    tax_t2,
    tax_change_month,
    nwells,
    nmonths,
    given_nmonths,
    non_par_start_month,
    pdp_shift,
    pud_shift,
    dtype=np.float32,
):
    oil_tax = np.tile(
        two_tax_regime(
            periods=nmonths,
            switch_period=tax_change_month,
            t1_tax=tax_t1,
            t2_tax=tax_t2,
            dtype=dtype,
        ),
        (nwells, 1),
    )
    gas_tax = np.tile(
        two_tax_regime(
            periods=nmonths,
            switch_period=tax_change_month,
            t1_tax=tax_t1,
            t2_tax=tax_t2,
            dtype=dtype,
        ),
        (nwells, 1),
    )

    assert nmonths >= given_nmonths
    oil_agg_tax = oil_tax.copy()
    gas_agg_tax = gas_tax.copy()
    oil_agg_tax[:, :non_par_start_month] = 0
    gas_agg_tax[:, :non_par_start_month] = 0

    oil_par_tax = take_per_row_strided(oil_tax, pdp_shift, given_nmonths)
    gas_par_tax = take_per_row_strided(gas_tax, pdp_shift, given_nmonths)

    oil_non_par_tax = take_per_row_strided(oil_agg_tax, pdp_shift, given_nmonths)
    gas_non_par_tax = take_per_row_strided(gas_agg_tax, pdp_shift, given_nmonths)

    oil_par_tax = append_zeroes_front(oil_par_tax, pud_shift, given_nmonths)
    gas_par_tax = append_zeroes_front(gas_par_tax, pud_shift, given_nmonths)

    oil_non_par_tax = append_zeroes_front(oil_non_par_tax, pud_shift, given_nmonths)
    gas_non_par_tax = append_zeroes_front(gas_non_par_tax, pud_shift, given_nmonths)

    tax = np.array(
        [[oil_par_tax, gas_par_tax], [oil_non_par_tax, gas_non_par_tax]], dtype=dtype
    )

    assert tax.shape == (2, 2, nwells, given_nmonths)
    return tax


def make_production(
    oil_dca_pars,
    gas_dca_pars,
    nmonths,
    given_nmonths,
    non_par_start_month,
    pdp_shift,
    pud_shift,
    dtype=np.float32,
):

    assert nmonths >= given_nmonths
    oil_prod = np_mod_arps_fit(mprod=nmonths, pars=oil_dca_pars)  # (nwells * nmonths)
    gas_prod = np_mod_arps_fit(mprod=nmonths, pars=gas_dca_pars)  # (nwells * nmonths)

    # Non WI do not get paid for the first n months
    oil_agg_prod = accumulate_axis(
        oil_prod, 0, non_par_start_month
    )  # (nwells * nmonths)
    gas_agg_prod = accumulate_axis(
        gas_prod, 0, non_par_start_month
    )  # (nwells * nmonths)

    # Shifting Production
    # Based on wells being PDP or PUD the production shifted.

    # PDP
    oil_par_prod = take_per_row_strided(oil_prod, pdp_shift, given_nmonths)
    gas_par_prod = take_per_row_strided(gas_prod, pdp_shift, given_nmonths)

    oil_non_par_prod = take_per_row_strided(oil_agg_prod, pdp_shift, given_nmonths)
    gas_non_par_prod = take_per_row_strided(gas_agg_prod, pdp_shift, given_nmonths)

    # PUD
    oil_par_prod = append_zeroes_front(oil_par_prod, pud_shift, given_nmonths)
    gas_par_prod = append_zeroes_front(gas_par_prod, pud_shift, given_nmonths)

    oil_non_par_prod = append_zeroes_front(oil_non_par_prod, pud_shift, given_nmonths)
    gas_non_par_prod = append_zeroes_front(gas_non_par_prod, pud_shift, given_nmonths)

    production = np.array(
        [[oil_par_prod, gas_par_prod], [oil_non_par_prod, gas_non_par_prod]],
        dtype=dtype,
    )
    assert production.shape == (2, 2, oil_prod.shape[0], given_nmonths)

    return production


def well_econ(pricing, tax_rate, production):
    assert pricing.shape[-1] == tax_rate.shape[-1] == production.shape[-1]

    nwells = production.shape[-2]
    nmonths = production.shape[-1]

    # Revenue
    pricing.resize((2, 1, nmonths))
    revenue = production * pricing

    # Tax
    tax = revenue * tax_rate

    # Profit
    profit_without_expense = revenue - tax

    pricing.resize((2, nmonths))
    assert tax.shape == revenue.shape == profit_without_expense
    return pricing, production, tax, revenue, profit_without_expense


def sample_workflow(nwells=1000, nmonths=600, dtype=np.float32):

    # Shift months indicate the month at which the production should be shifted to.
    # The value is relative to the current financial effective date.
    # Negative value indicate PDP wells the production should start from. Achieved by taking strides.
    # and to keep the code vectorized production is predicted for a total of nmonths + min(pdp_shift_months)
    # Positive value indicate PUD wells. Achieved by  appending zeroes in the front.
    shift_months = np.random.randint(low=-60, high=60, size=nwells)
    given_nmonths = nmonths
    nmonths = int(np.abs(np.min(shift_months)) + nmonths)

    start_date = np.datetime64("2019-06-01").astype("datetime64[D]")

    # Pricing
    oil_flat_price = 60.0
    gas_flat_price = 2.5

    dates, pricing = make_pricing(
        oil_flat_price, gas_flat_price, given_nmonths, start_date, dtype
    )

    non_par_start_month = 6
    pdp_shift = np.where(shift_months < 0, -shift_months, 0)
    pud_shift = np.where(shift_months > 0, shift_months, 0)

    # Tax
    tax_t1 = 0.05
    tax_t2 = 0.036
    tax_change_month = 18

    tax_rate = make_tax(
        tax_t1,
        tax_t2,
        tax_change_month,
        nwells,
        nmonths,
        given_nmonths,
        non_par_start_month,
        pdp_shift,
        pud_shift,
        dtype,
    )

    # Production
    oil_dca_pars = make_dca_pars(nwells, dtype)
    gas_dca_pars = make_dca_pars(nwells, dtype)

    production = make_production(
        oil_dca_pars,
        gas_dca_pars,
        nmonths,
        given_nmonths,
        non_par_start_month,
        pdp_shift,
        pud_shift,
        dtype,
    )

    assert dates.shape[0] == pricing.shape[1] == given_nmonths
    assert tax_rate.shape == production.shape == (2, 2, nwells, given_nmonths)

    pricing, tax, revenue, profit_without_expense = well_econ(
        pricing, tax_rate, production
    )

    print("me")


# sample_workflow(nwells=100, nmonths=600)
# time_it(workflow, repeat=1, number=10, nwells=1000)
