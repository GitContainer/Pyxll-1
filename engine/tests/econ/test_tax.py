from econ.array_manipulations import append_zeroes_front
from tax import two_tax_regime, make_tax
import numpy as np


def test_two_tax_regime():
    period = 10
    switch_period = 5
    t1_tax = 0.05
    t2_tax = 0.036
    tax = make_tax(
        "two_tax_regime",
        periods=period,
        switch_period=switch_period,
        t1_tax=t1_tax,
        t2_tax=t2_tax,
    )
    assert tax.shape == (period,)
    assert np.all(tax[:switch_period] == t1_tax)
    assert np.all(tax[switch_period:] == t2_tax)


def test_append_zeroes_front():
    array = np.random.randint(0, 1000, (1000, 1000))
    nzeros = np.random.randint(0, 100, 1000)
    a = append_zeroes_front(array, nzeros, 600)
    assert True
