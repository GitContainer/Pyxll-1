import logging

from fm_orm import Project_State_Asset, Well_Oneline, Section_Well, Section_Assumption
from financial_model.tests.configtest import *
import numpy as np
import pytest

from engine.tests.configtest import make_dca_pars
from form_norm import form_norm
from tests.configtest import *
from engine.core.dca.mod_arps import np_mod_arps_fit
from fm_ui import (
    reset_defaults,
    ui_reload,
    ui_initiation,
    ui_closure,
    read_project_settings,
)
from generic_fns import (
    halt_screen_update,
    add_xl_app,
    get_names_with_string,
    get_cached_object,
    get_address,
    xl_add_row,
    xl_add_column,
    copy_df_xl,
)


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
    "xl, fm_data_manager_xl, make_dca_pars, caplog",
    [(None, None, (100, np.float32), None)],
    indirect=True,
)
def test_kiran(xl, fm_data_manager_xl, make_dca_pars, caplog):
    caplog.set_level(logging.INFO)
    dm = fm_data_manager_xl

    assets = to_df(get_value("project_state_assets", xl=xl))
    type_curves = to_df(get_value("type_curves", xl=xl))
    section_assumptions = to_df(get_value("section_assumptions", xl=xl))

    dm.set_new_session(
        assets=assets, type_curves=type_curves, section_assumptions=section_assumptions
    )


@pytest.mark.parametrize(
    "xl, fm_data_manager_xl, caplog",
    [
        (
            None,
            # None,
            "C:/Users/adi/PycharmProjects/Pyxll/financial_model/backup/named/test.fm",
            None,
        )
    ],
    indirect=True,
)
def test_normalize_formation(xl, fm_data_manager_xl, caplog):
    caplog.set_level(logging.INFO)
    dm = fm_data_manager_xl  # type: FMDataManager

    data = (
        dm.session.query(
            Well_Oneline.api,
            Well_Oneline.well_name,
            Well_Oneline.operator_name,
            Well_Oneline.formation,
            Section_Assumption.formation_1,
            Section_Assumption.formation_2,
        )
        .join(Section_Well)
        .join(Project_State_Asset)
        .join(Section_Assumption)
        .all()
    )

    df = pd.DataFrame(data)

    # This line added in case a multi unit well lying in two different sections have two different
    # section assumptions

    df = df.drop_duplicates(["api"])
    string_array = df.iloc[:, 1:].values.transpose().astype("unicode")
    formation = form_norm(string_array)
    df["norm_formation"] = formation

    df.columns = [
        "api",
        "well_name",
        "operator_name",
        "formation",
        "formation_1",
        "formation_2",
        "norm_formation",
    ]

    assert formation.shape[0] == dm["well_onelines"].shape[0]

    with dm.session_scope() as session:
        for i, row in df.iterrows():
            selected_well = (
                session.query(Well_Oneline).filter(Well_Oneline.api == row["api"]).one()
            )  # type: Well_Oneline
            selected_well.norm_formation = row.norm_formation

    copy_df_xl(
        df=df,
        sheet="Formation",
        name="formation_state_normalizer",
        copy_columns=False,
        xl=xl,
    )

    dm.data_formatter.formation_state_normalizer()
    assert True
