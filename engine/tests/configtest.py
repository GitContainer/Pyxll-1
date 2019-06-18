import pytest
import numpy as np


@pytest.fixture(scope="session")
def make_dca_pars(request):
    nwells = request.param[0]
    dtype = request.param[1]

    ip = np.random.uniform(low=100, high=3000, size=nwells).astype(dtype)
    # Di cannot be lower than dmin else the logic will be incorrect.
    di = np.random.uniform(low=0.10, high=1, size=nwells).astype(dtype)
    dmin = np.random.uniform(low=0.06, high=0.08, size=nwells).astype(dtype)
    b = np.random.uniform(low=0, high=2, size=nwells).astype(dtype)

    return np.array([ip, di, dmin, b])


@pytest.fixture(scope="session")
def date_strip(request):
    start_date = request.param[0].astype("datetime64[M]")
    periods = request.param[1]

    end_date = start_date + np.timedelta64(periods, "M")

    new_date_strip = np.arange(start_date, end_date).astype("datetime64[D]")
    return new_date_strip


@pytest.fixture(scope="session")
def price_strip(request):
    low = request.param[0]
    high = request.param[1]
    size = request.param[2]

    new_price_strip = np.random.randint(low, high, size)
    return new_price_strip
