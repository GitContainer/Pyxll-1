import numpy as np

_TAXERS = dict()


def register_taxer(func):
    _TAXERS[func.__name__] = func
    return func


def make_tax(strategy, *args, **kwargs):
    if strategy in _TAXERS:
        return _TAXERS[strategy](*args, **kwargs)
    else:
        raise TypeError(f"{strategy} not found.")


@register_taxer
def two_tax_regime(
    periods: int, switch_period: int, t1_tax: float, t2_tax: float, dtype=np.float32
):
    assert switch_period < periods
    t1_tax_strip = np.repeat(t1_tax, switch_period)
    t2_tax_strip = np.repeat(t2_tax, periods - switch_period)
    tax_strip = np.concatenate((t1_tax_strip, t2_tax_strip), axis=None).astype(
        dtype=dtype
    )
    return tax_strip
