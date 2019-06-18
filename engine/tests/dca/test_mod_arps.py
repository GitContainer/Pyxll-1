import numpy as np
from engine.core.dca.mod_arps import np_mod_arps_fit
from engine.tests.configtest import make_dca_pars
import pytest


@pytest.mark.parametrize("make_dca_pars", [(10000, np.float32)], indirect=True)
def test_np_mod_arps_fit(make_dca_pars):
    mprod = 600
    np_prod = np_mod_arps_fit(mprod, make_dca_pars)

    assert np.allclose(np_prod[:, 0], make_dca_pars[0]), "IP not matching"
    assert np.all(np_prod >= 0), "Prod not negative"
