import numpy as np
import datetime

from numba import jit


def timing_core(well_numbers, well_dates, timing_dates, current_dates, ph_date):
    """
    The inputs should have the columns in the exact same order
    :param well_numbers: np.array (9, nsections)
        well_numbers = [
        "nwells_1", 0
        "tolerance_1", 1
        "nwells_2", 2
        "tolerance_2", 3
        "f1001_nwells", 4
        "f1000_nwells", 5
        "app_nwells", 6
        "order_nwells", 7
        "f1002a_nwells_f1", 8
        "f1002a_nwells_f2", 9]
    :param well_dates: np.array (7, nsections)
        well_dates = [
            "f1001_last_date", 0
            "f1001_first_date", 1
            "f1000_last_date", 2
            "f1000_first_date", 3
            "app_date", 4
            "order_date", 5
            "f1002a_last_date_f1", 6
            "f1002a_last_date_f2", 7
        ]
    :param timing_dates: np.array (7, 1)
        timing_dates = [
            tolerance, 0
            spud_to_rig_release, 1
            frac_to_sales, 2
            permit_to_spud, 3
            idorder_to_spud, 4
            idapp_to_spud, 5
            days_ntg_f1_pd, 6
            days_ntg_f2_pd, 7
        ]
    :param current_dates: np.array (nsections, 1)
        current date repeated along the number of sections
    :param ph_date: np.array (nsections, 1)
        placeholder date repeated along the number of sections
    :return:
        ["nwells_curr",
        "nwells_fut",
        "spud_date_curr",
        "sales_date_curr",
        "spud_date_fut",
        "sales_date_fut",
        "nwells_curr_2",
        "nwells_fut_2",
        "spud_date_curr_2",
        "sales_date_fut_2",
        "spud_date_fut_2",
        "sales_date_fut_2"]
    """
    nsections = well_numbers.shape[1]

    # Primary zone array initialization
    nwells_curr = np.zeros(shape=nsections, dtype=well_numbers.dtype)
    nwells_fut = np.zeros(shape=nsections, dtype=well_numbers.dtype)
    formation = np.uint8(1) + np.zeros(shape=nsections, dtype=well_numbers.dtype)

    spud_date_curr = ph_date.copy()
    sales_date_curr = ph_date.copy()

    spud_date_fut = ph_date.copy()
    sales_date_fut = ph_date.copy()

    # Secondary zone array initialization
    nwells_curr_2 = np.zeros(shape=nsections, dtype=well_numbers.dtype)
    nwells_fut_2 = np.zeros(shape=nsections, dtype=well_numbers.dtype)
    formation_2 = np.uint8(2) + np.zeros(shape=nsections, dtype=well_numbers.dtype)

    spud_date_curr_2 = ph_date.copy()
    sales_date_curr_2 = ph_date.copy()

    spud_date_fut_2 = spud_date_curr.copy()
    sales_date_fut_2 = spud_date_curr.copy()

    # Easier name assignments for easy logic understanding
    # well_numbers
    nwells_1 = well_numbers[0]
    tolerance_1 = well_numbers[1]
    nwells_2 = well_numbers[2]
    tolerance_2 = well_numbers[3]
    f1001_nwells = well_numbers[4]
    f1000_nwells = well_numbers[5]
    app_nwells = well_numbers[6]
    order_nwells = well_numbers[7]
    f1002a_nwells_f1 = well_numbers[8]
    f1002a_nwells_f2 = well_numbers[9]

    # well_dates
    f1001_last_date = well_dates[0]
    f1001_first_date = well_dates[1]
    f1000_last_date = well_dates[2]
    f1000_first_date = well_dates[3]
    app_date = well_dates[4]
    order_date = well_dates[5]
    f1002a_last_date_f1 = well_dates[6]
    f1002a_last_date_f2 = well_dates[7]

    # timing_dates
    tolerance = timing_dates[0]
    spud_to_rig_release = timing_dates[1]
    frac_to_sales = timing_dates[2]
    permit_to_spud = timing_dates[3]
    idorder_to_spud = timing_dates[4]
    idapp_to_spud = timing_dates[5]
    days_ntg_f1_pd = timing_dates[6]
    days_ntg_f2_pd = timing_dates[7]

    for i in range(nsections):

        # Primary Formation Calculation
        # Number of current wells is first calculated and then spud_date current based on that
        # f1001 > f1000> id order > id app

        # If f1001 last_date is greater than f1000 last date + tolerance then f1001 wells else f1000 nwells
        if f1001_nwells[i] > 0:
            if f1000_nwells[i] > 0:
                if f1001_last_date[i] > f1000_last_date[i] + tolerance:
                    nwells_curr[i] = f1001_nwells[i]
                else:
                    nwells_curr[i] = f1000_nwells[i]
            else:
                nwells_curr[i] = f1001_nwells[i]

        # If f1000 last_date is greater than ID order date + tolerance then f1000 wells else ID Order wells
        elif f1000_nwells[i] > 0:
            if order_nwells[i] > 0:
                if f1000_last_date[i] > order_date[i] + tolerance:
                    nwells_curr[i] = f1000_nwells[i]
                else:
                    nwells_curr[i] = order_nwells[i]
            else:
                nwells_curr[i] = f1000_nwells[i]

        # If ID order exits
        elif order_nwells[i] > 0:
            nwells_curr[i] = order_nwells[i]

        # If ID app exits
        elif app_nwells[i] > 0:
            nwells_curr[i] = app_nwells[i]

        # If f1001 well exist then spud date for current wells is f1001 first well date
        if f1001_nwells[i] > 0 and f1001_first_date[i] == f1001_first_date[i]:
            spud_date_curr[i] = f1001_first_date[i]

        # If f1000 well exist then spud date for current wells is f1000 first well date + permit to spud
        elif f1000_nwells[i] > 0 and f1000_first_date[i] == f1000_first_date[i]:
            spud_date_curr[i] = f1000_first_date[i] + permit_to_spud

        # If ID order exist then spud date for current wells is ID order date + idorder_to_spud
        elif order_nwells[i] > 0 and order_date[i] == order_date[i]:
            spud_date_curr[i] = order_date[i] + idorder_to_spud

        # If ID app exist then spud date for current wells is ID app date + idapp_to_spud
        elif app_nwells[i] > 0 and app_date[i] == app_date[i]:
            spud_date_curr[i] = app_date[i] + idapp_to_spud

        if nwells_curr[i] > 0:
            sales_date_curr[i] = (
                spud_date_curr[i]
                + (nwells_curr[i] * spud_to_rig_release)
                + frac_to_sales
            )

        # If current wells and PDP wells are less than tolerance 1 then assign the difference as future wells.
        if nwells_curr[i] + f1002a_nwells_f1[i] <= tolerance_1[i]:
            nwells_fut[i] = nwells_1[i] - nwells_curr[i]

        # If future wells exist then spud date for future wells is current date + days ntg f1 prod.
        if nwells_fut[i] > 0:
            spud_date_fut[i] = current_dates[0] + days_ntg_f1_pd
            sales_date_fut[i] = (
                spud_date_fut[i] + (nwells_fut[i] * spud_to_rig_release) + frac_to_sales
            )

        # Secondary Formation Calculation
        if f1002a_nwells_f2[i] >= tolerance_2[i]:
            nwells_fut_2[i] = np.uint8(0)
        else:
            nwells_fut_2[i] = nwells_2[i] - f1002a_nwells_f2[i]
            spud_date_fut_2[i] = current_dates[0] + days_ntg_f2_pd
            sales_date_fut_2[i] = (
                spud_date_fut_2[i]
                + (nwells_fut_2[i] * spud_to_rig_release)
                + frac_to_sales
            )

    return (
        nwells_curr,
        nwells_fut,
        spud_date_curr,
        sales_date_curr,
        spud_date_fut,
        sales_date_fut,
        nwells_curr_2,
        nwells_fut_2,
        spud_date_curr_2,
        sales_date_fut_2,
        spud_date_fut_2,
        sales_date_fut_2,
    )


nb_timing_core = jit(timing_core, nopython=True, fastmath=True, error_model="numpy")


def timing(well_numbers, well_dates, timing_dates=None):
    """
    For every section
        For primary and secondary formation
            For current and future wells
                Number of Wells, Spud Date, Sales Date

     The inputs should have the columns in the exact same order
    :param well_numbers: np.array (9, nsections)
        well_numbers = [
        "nwells_1", 0
        "tolerance_1", 1
        "nwells_2", 2
        "tolerance_2", 3
        "f1001_nwells", 4
        "f1000_nwells", 5
        "app_nwells", 6
        "order_nwells", 7
        "f1002a_nwells_f1", 8
        "f1002a_nwells_f2", 9]
    :param well_dates: np.array (7, nsections)
        well_dates = [
            "f1001_last_date", 0
            "f1001_first_date", 1
            "f1000_last_date", 2
            "f1000_first_date", 3
            "app_date", 4
            "order_date", 5
            "f1002a_last_date_f1", 6
            "f1002a_last_date_f2", 7
        ]
    :param timing_dates: np.array (7, 1)
        timing_dates = [
            tolerance, 0
            spud_to_rig_release, 1
            frac_to_sales, 2
            permit_to_spud, 3
            idorder_to_spud, 4
            idapp_to_spud, 5
            days_ntg_f1_pd, 6
            days_ntg_f2_pd, 7
        ]
    :return:
        ["nwells_curr",
        "nwells_fut",
        "spud_date_curr",
        "sales_date_curr",
        "spud_date_fut",
        "sales_date_fut",
        "nwells_curr_2",
        "nwells_fut_2",
        "spud_date_curr_2",
        "sales_date_fut_2",
        "spud_date_fut_2",
        "sales_date_fut_2"]
    """
    # tolerance, spud_to_rig_release, frac_to_sales, permit_to_spud, idorder_to_spud,
    # idapp_to_spud, days_ntg_f1_pd, days_ntg_f2_pd

    if timing_dates is None:
        timing_dates = (45, 20, 45, 180, 365, 545, 365 * 3, 365 * 6)

    timing_dates = np.array([np.timedelta64(date, "D") for date in timing_dates])

    current_dates = np.repeat(
        np.datetime64((datetime.datetime.now()).strftime("%Y-%m-%d")).astype("<M8[D]"),
        well_numbers.shape[1],
    )
    ph_date = np.repeat(
        np.datetime64("1900-01-01", type=current_dates.dtype), well_numbers.shape[1]
    )

    timing_result = nb_timing_core(
        well_numbers, well_dates, timing_dates, current_dates, ph_date
    )
    return timing_result
