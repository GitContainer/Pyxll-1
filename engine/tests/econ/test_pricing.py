import numpy as np
import pytest

from pricing import (
    flat_fill,
    forward_flat_fill,
    backward_flat_fill,
    forward_esc_fill,
    make_pricing,
)
from engine.tests.configtest import date_strip, price_strip


def test_flat_fill():
    periods = 660
    start_date = np.datetime64("2019-01-01")
    value = 50.01
    pricing = flat_fill(periods=periods, start_date=start_date, value=value)
    assert pricing.shape == (2, periods)
    assert np.isclose(pricing[1][1], value)


@pytest.mark.parametrize(
    "date_strip, price_strip",
    [((np.datetime64("2019-01-01"), 10), (50, 60, 10))],
    indirect=True,
)
def test_forward_flat_fill(date_strip, price_strip):
    extend_by = 10
    pricing = forward_flat_fill(extend_by, date_strip, price_strip)
    start_date = pricing[0][0]
    end_date = pricing[0][-1]
    pricing_end_date = (
        date_strip[-1].astype("datetime64[M]") + np.timedelta64(extend_by, "M")
    ).astype("datetime64[D]")

    assert pricing.shape == (2, extend_by + date_strip.shape[0])
    assert np.all(pricing[1][-extend_by:] == pricing[1][-(extend_by + 1)])
    assert start_date == date_strip[0]
    assert end_date == pricing_end_date


@pytest.mark.parametrize(
    "date_strip, price_strip",
    [((np.datetime64("2019-01-01"), 10), (50, 60, 10))],
    indirect=True,
)
def test_backward_flat_fill(date_strip, price_strip):
    extend_by = 10
    # pricing = backward_flat_fill(extend_by, date_strip, price_strip)
    pricing = make_pricing(
        "backward_flat_fill",
        periods=extend_by,
        date_strip=date_strip,
        price_strip=price_strip,
    )
    start_date = pricing[0][0]
    end_date = pricing[0][-1]
    pricing_start_date = (
        date_strip[0].astype("datetime64[M]") - np.timedelta64(extend_by, "M")
    ).astype("datetime64[D]")

    assert pricing.shape == (2, extend_by + date_strip.shape[0])
    assert np.all(pricing[1][:extend_by] == pricing[1][extend_by])
    assert end_date == date_strip[-1]
    assert start_date == pricing_start_date


@pytest.mark.parametrize(
    "date_strip, price_strip",
    [((np.datetime64("2019-01-01"), 10), (50, 60, 10))],
    indirect=True,
)
def test_forward_esc_fill(date_strip, price_strip):
    extend_by = 10
    escalation_factor = 0.03
    pricing = forward_esc_fill(extend_by, date_strip, price_strip, escalation_factor)
    start_date = pricing[0][0]
    end_date = pricing[0][-1]
    pricing_end_date = (
        date_strip[-1].astype("datetime64[M]") + np.timedelta64(extend_by, "M")
    ).astype("datetime64[D]")

    assert pricing.shape == (2, extend_by + date_strip.shape[0])
    assert (
        pricing[1][-1]
        == price_strip[-1] + price_strip[-1] * extend_by * escalation_factor
    )
    assert start_date == date_strip[0]
    assert end_date == pricing_end_date
