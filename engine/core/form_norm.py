"""
Formation Normalization normalizes a PDP well to one of the several known formation types.
This affects the way a well is categorized and that directly affects the timing logic and
the number of wells directly affecting the valuation of a section.

"""

import logging

import numpy as np


def form_norm(string_array, known_formations=None):
    """
    This function handles formation normalization through a sequence of logic provided by Robert.
    The logic accepts numpy array and returns a numpy array.
    
    # TODO: Strong test cases using test cases as well as hypothesis.
    :param string_array: np.array of shape (5, nwells)
        Array should be oneline. One row per well.

        0. well_name
        1. operator_name
        2. formation (concatenated with a delimiter)
        3. formation 1 (from section assumption)
        4. formation 2 (from section assumption)
    :param known_formations: np.array
    :return: np.array (1, nwells)
        Normalized formation. May contain empty string in case of no logic match.
    """
    if string_array.shape[1] == 0:
        return string_array

    assert string_array.shape[0] == 5, "Unexpected string_array shape"

    # string_array = string_array.upper().astype("unicode")
    wells = string_array[0]  # type: np.array
    operators = string_array[1]  # type: np.array
    formations = string_array[2]  # type: np.array
    formation_1 = string_array[3]  # type: np.array
    formation_2 = string_array[4]  # type: np.array

    if known_formations is None:
        known_formations = np.array(
            [
                "WOODFORD",
                "MERAMEC",
                "SPRINGER",
                "SYCAMORE",
                "OSAGE",
                "OSWEGO",
                "HOXBAR",
                "MAYES",
                "DES MOINES",
                "MARMATON",
                "CLEVELAND",
                "COTTAGE GROVE",
                "TONKAWA",
            ]
        ).astype(string_array.dtype.str)
    else:
        known_formations = known_formations.astype(string_array.dtype.str)

    columns, rows = string_array.shape
    use_dtype = string_array.dtype

    norm_form = np.chararray(rows, unicode=True).astype(use_dtype)

    assert (
        norm_form.dtype == known_formations.dtype == string_array.dtype
    ), "dtypes not matching"

    assert (
        np.sum(np.char.find(formations, "|") >= 0) > 0
    ), "formations (string_array[2]) should not contain pipe operator"

    # Think of the logic as a sequence of steps with priority.
    # If a case fulfills a condition then that should not be set by sub sequent steps.

    # If formation is from known_formation assign it
    norm_form = np.where(
        np.apply_along_axis(lambda x: np.isin(x, known_formations), 0, formations),
        formations,
        norm_form,
    )

    # If formation is not present and formation 1 exists then that is the formation
    norm_form = np.where(
        (norm_form == "") & (formation_1 != ""), formation_1, norm_form
    )

    # If Operator equals CASILLAS and Well Name contains "MXH" or "MH", then SYCAMORE.
    well_mxh_mh = (np.char.find(wells, "MXH") >= 0) | (np.char.find(wells, "MH") >= 0)
    norm_form = np.where(
        (norm_form == "") & (np.char.find(operators, "CASILLAS") >= 0) & well_mxh_mh,
        "SYCAMORE",
        norm_form,
    )

    # If Formation 1 or Formation 2 contain either SYCAMORE, SPRINGER, or OSAGE (all Mississippian aged rocks)
    # AND the second formation is NOT SYCAMORE, SPRINGER, OR OSAGE
    # AND, Well Name contains "MXH" or "MH"
    # THEN, normalized to the Miss Formation listed
    miss_rock = np.array(["SYCAMORE", "SPRINGER", "OSAGE"], dtype=use_dtype)
    form_1_miss = np.apply_along_axis(lambda x: np.isin(x, miss_rock), 0, formation_1)
    form_2_miss = np.apply_along_axis(lambda x: np.isin(x, miss_rock), 0, formation_2)

    both_form_miss = form_1_miss & form_2_miss
    norm_form = np.where(
        (form_1_miss & ~both_form_miss & well_mxh_mh), formation_1, norm_form
    )
    norm_form = np.where(
        (form_2_miss & ~both_form_miss & well_mxh_mh), formation_2, norm_form
    )

    # If formation contains 'WOODFORD' assign it WOODFORD
    norm_form = np.where(
        (norm_form == "") & (np.char.find(formations, "WOODFORD") >= 0),
        "WOODFORD",
        norm_form,
    )

    # If Operator contains 'OKLAHOMA ENERGY ACQUISITIONS' make formation 'OSAGE'
    norm_form = np.where(
        (norm_form == "")
        & (np.char.find(operators, "OKLAHOMA ENERGY ACQUISITIONS") >= 0),
        "OSAGE",
        norm_form,
    )

    # If formation 1 or 2 is 'MERAMEC' and formation contains "MISS" then "MERAMEC"
    norm_form = np.where(
        (norm_form == "")
        & (
            ((formation_1 == "MERAMEC") | (formation_2 == "MERAMEC"))
            & (np.char.find(formations, "MISS") >= 0)
        ),
        "MERAMEC",
        norm_form,
    )

    # If formation contains 'SPRINGER' or 'GODDARD' then 'SPRINGER'
    norm_form = np.where(
        (norm_form == "")
        & (
            (np.char.find(formations, "SPRINGER") >= 0)
            | (np.char.find(formations, "GODDARD") >= 0)
        ),
        "SPRINGER",
        norm_form,
    )

    # If formation 1 contains "OSWEGO" then formation 2
    norm_form = np.where(
        (norm_form == "") & (formation_1 == "OSWEGO"), formation_2, norm_form
    )

    # If formation 1 contains "WOODFORD" then formation 2
    norm_form = np.where(
        (norm_form == "") & (formation_1 == "WOODFORD"), formation_2, norm_form
    )

    logging.warning(
        f"{(norm_form == '').sum()}/{norm_form.shape[0]} wells have no normalized formations"
    )
    return norm_form
