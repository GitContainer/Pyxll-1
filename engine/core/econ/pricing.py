import numpy as np
from numba import jit

_PRICERS = dict()


def register_pricer(func):
    _PRICERS[func.__name__] = func
    return func


def make_pricing(strategy, *args, **kwargs):
    if strategy in _PRICERS:
        return _PRICERS[strategy](*args, **kwargs)
    else:
        raise TypeError(f"{strategy} not found.")


@register_pricer
def flat_fill(periods: int, start_date: np.datetime64, value: float, dtype=np.float32):
    price_strip = np.repeat(value, periods).astype(dtype)

    start_date = start_date.astype("datetime64[M]")
    end_date = start_date + np.timedelta64(periods, "M")
    date_strip = np.arange(start_date, end_date).astype("datetime64[D]")

    pricing = np.array([date_strip, price_strip])
    return pricing


@register_pricer
def forward_flat_fill(
    periods: int, date_strip: np.ndarray, price_strip: np.ndarray, dtype=np.float32
):
    assert date_strip.shape == price_strip
    filler = np.repeat(price_strip[-1], periods)
    new_price_strip = np.concatenate((price_strip, filler), axis=None).astype(dtype)

    date_strip = date_strip.astype("datetime64[M]")
    delta = date_strip[-1] + np.timedelta64(periods + 1, "M")
    new_date_strip = np.arange(date_strip[0], delta).astype("datetime64[D]")

    pricing = np.array([new_date_strip, new_price_strip])
    return pricing


@register_pricer
def backward_flat_fill(
    periods: int, date_strip: np.ndarray, price_strip: np.ndarray, dtype=np.float32
):
    assert date_strip.shape == price_strip
    filler = np.repeat(price_strip[0], periods)
    new_price_strip = np.concatenate((filler, price_strip), axis=None).astype(dtype)

    date_strip = date_strip.astype("datetime64[M]")
    delta = date_strip[0] - np.timedelta64(periods, "M")
    new_date_strip = np.arange(delta, date_strip[-1] + np.timedelta64(1, "M")).astype(
        "datetime64[D]"
    )

    pricing = np.array([new_date_strip, new_price_strip])
    return pricing


@register_pricer
def forward_esc_fill(
    periods: int,
    date_strip: np.ndarray,
    price_strip: np.ndarray,
    escalation_factor: float,
    dtype=np.float32,
):
    assert date_strip.shape == price_strip
    escalation_strip = np.repeat(escalation_factor, periods).astype(dtype)
    escalation_strip = np.cumsum(escalation_strip)

    date_strip = date_strip.astype("datetime64[M]")
    filler = price_strip[-1] + np.repeat(price_strip[-1], periods) * escalation_strip
    new_price_strip = np.concatenate((price_strip, filler), axis=None).astype(dtype)

    delta = date_strip[-1] + np.timedelta64(periods + 1, "M")
    new_date_strip = np.arange(date_strip[0], delta).astype("datetime64[D]")

    pricing = np.array([new_date_strip, new_price_strip])
    return pricing
