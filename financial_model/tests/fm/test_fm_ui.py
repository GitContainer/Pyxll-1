from fm_orm import Project_State_Asset, Well_Production
from financial_model.tests.configtest import *
import numpy as np
import pytest

from engine.tests.configtest import make_dca_pars
from engine.core.dca.mod_arps import np_mod_arps_fit
from fm_ui import reset_defaults


@pytest.mark.parametrize(
    "fm_data_manager_xl",
    [
        "C:/Users/adi/OneDrive/Work/Pyxll/financial_model/backup/named/test_random_988.fm"
    ],
    indirect=True,
)
def test_cascade_delete(fm_data_manager_xl: FMDataManager):
    dm = fm_data_manager_xl
    assert dm["section_wells"].shape[0] > 0, "Missing wells"
    remove_section = dm["section_wells"].trsm_heh.unique()[0]

    before_delete = dm.get_data_row_count("section_wells")
    delete_section = (
        dm.session.query(Project_State_Asset)
        .filter(Project_State_Asset.trsm_heh == remove_section)
        .first()
    )

    dm.delete_query(delete_section)
    after_delete = dm.get_data_row_count("section_wells")

    assert after_delete < before_delete


@pytest.mark.parametrize(
    "fm_data_manager_xl, make_dca_pars", [(None, (100, np.float32))], indirect=True
)
def test_numpy(fm_data_manager_xl: FMDataManager, make_dca_pars):
    # Depends on well_production that has ip, di, dmin , b and predicted prod(numpy).
    dm = fm_data_manager_xl
    nwells = 100
    mprod = 600
    prod = np_mod_arps_fit(mprod, make_dca_pars)

    with dm.session_scope() as session:
        wells_list = [None] * nwells
        for i in range(nwells):
            wells_list[i] = Well_Production(
                api=i,
                ip_oil=make_dca_pars[0][i],
                di_oil=make_dca_pars[1][i],
                dmin_oil=make_dca_pars[2][i],
                b_oil=make_dca_pars[3][i],
                pred_oil_prod=prod[i, :],
            )

        session.add_all(wells_list)

    with dm.session_scope() as session:
        well = session.query(Well_Production).filter(Well_Production.api == 0).one()
        new_array = np.zeros(mprod)
        new_di_oil = 0.001
        well.di_oil = new_di_oil
        well.pred_oil_prod = new_array

    assert dm["well_productions"].di_oil[0] == new_di_oil, "overwrite not working"
    assert np.all(
        dm["well_productions"].pred_oil_prod[0] == new_array
    ), "overwrite not working"


@pytest.mark.parametrize(
    "fm_data_manager_xl, make_dca_pars", [(None, (100, np.float32))], indirect=True
)
def test_np_array(fm_data_manager_xl: FMDataManager, make_dca_pars):
    # Depends on well_production that has ip, di, dmin , b and predicted prod(numpy).
    dm = fm_data_manager_xl
    nwells = 100
    mprod = 600
    prod = np_mod_arps_fit(mprod, make_dca_pars).astype(np.float32)

    with dm.session_scope() as session:
        wells_list = [None] * nwells
        for i in range(nwells):
            wells_list[i] = Well_Production(
                api=i,
                ip_oil=make_dca_pars[0][i],
                di_oil=make_dca_pars[1][i],
                dmin_oil=make_dca_pars[2][i],
                b_oil=make_dca_pars[3][i],
                pred_oil_prod=prod[i, :],
            )

        session.add_all(wells_list)
    get_oil_prod = dm.session.query(Well_Production.pred_oil_prod)
    temp = dm.get_np_array(get_oil_prod, shape=(nwells, mprod))
    assert temp.shape == (nwells, mprod)


@pytest.mark.parametrize(
    "xl, fm_data_manager_xl, make_dca_pars",
    [(None, None, (100, np.float32))],
    indirect=True,
)
def test_kiran(xl, fm_data_manager_xl, make_dca_pars):
    dm = fm_data_manager_xl

    assets = to_df(get_value("project_state_assets", xl=xl))
    type_curves = to_df(get_value("type_curves", xl=xl))
    section_assumptions = to_df(get_value("section_assumptions", xl=xl))

    dm.set_new_session(
        assets=assets, type_curves=type_curves, section_assumptions=section_assumptions
    )


def test_setf(xl):
    reset_defaults()
