
# coding: utf-8


import numpy as np
import pyodbc
import pandas as pd
import logging
import pytest
from financial_model.tests.configtest import *
from engine.tests.configtest import make_dca_pars
from generic_fns import (
    get_value,
    to_df)

# ## dynamically generates params value using database name|



def db_params(database_name, server_name=""):
    # code to connect to db
    server = (
        "syntax-dev-sql.database.windows.net"
    )  # 'syntax-dev-sql.database.windows.net'
    database = database_name
    username = "syntax-admin"
    password = "OneuptopAhk2018"  # 'cR5ULPxIVdxG'
    driver = "{ODBC Driver 17 for SQL Server}"

    params = (
        "DRIVER="
        + driver
        + ";SERVER="
        + server
        + ";PORT=1443;DATABASE="
        + database
        + ";UID="
        + username
        + ";PWD="
        + password
        + ";Persist Security Info=True"
    )
    return params


# ## formats a data frame values




def format_df(d_frame):
    d_frame = d_frame.apply(lambda x: x.astype(str).str.upper())
    d_frame = d_frame.replace("NAN", np.nan, regex=True)
    d_frame = d_frame.replace("NAT", np.nan, regex=True)
    d_frame = d_frame.replace("NULL", np.nan, regex=True)
    d_frame = d_frame.replace(r"^\s*$", np.nan, regex=True)
    d_frame = d_frame.replace("NONE", np.nan, regex=True)

    return d_frame



def transform_table(df_i_well, df_inp):
    try:
        df_result = pd.merge(
        df_inp,
        df_i_well[['api','trsm_heh']],
        how="inner",
        left_on=["api"],
        right_on=["api"]    )
    except :
        df_result  =  df_inp
        df_result['api'] =''
        length = df_result.shape[1]
        row_list = ['place_holder']*length
        df_result.loc[len(df_result)] = row_list
    return df_result



def process_section_online(df_i_w_l,df_f1000, df_f1001,df_f1002,df_inc_den):
    



    df_index_well_land = df_i_w_l
    df_1000 = transform_table(df_i_w_l,df_f1000)
    df_1001 = transform_table(df_i_w_l,df_f1001)
    df_1002A = transform_table(df_i_w_l,df_f1002)
    df_i_density =transform_table(df_i_w_l, df_inc_den)

    print("processing data")
    apis_list = df_index_well_land["api"].tolist()
    trsm_heh_list = df_index_well_land["trsm_heh"].tolist()



    # ## calculating latest, oldest dates, wells count for form 1000

    


    print("processing required information from production data")
    df_1000_permit_dates = (
        df_1000[["trsm_heh", "permit_date"]]
        .dropna(subset=["permit_date"], how="all")
        .reset_index(drop=True)
    )
    df_1000_permit_dates = df_1000_permit_dates.drop_duplicates()


    


    df_1000_wells_count = df_1000_permit_dates[["trsm_heh"]]
    df_1000_wells_count = (
        df_1000_wells_count.groupby(["trsm_heh"])
        .size()
        .reset_index(name="no_wells_permitted")
    )


    


    print(df_1000_permit_dates.shape)
    df_1000_permit_dates["permit_date"] = pd.to_datetime(
        df_1000_permit_dates["permit_date"]
    )
    df_1000_permit_dates = (
        df_1000_permit_dates.sort_values("permit_date")
        .groupby("trsm_heh")["permit_date"]
        .agg(["first", "last"])
    )
    # df_1000_permit_dates.index.api = ['api']
    df_1000_permit_dates.rename(
        columns={"first": "date_first_permit", "last": "date_last_permit"}, inplace=True
    )
    df_1000_permit_dates = df_1000_permit_dates.rename_axis("trsm_heh").reset_index()
    df_1000_permit_dates.reset_index(drop=True, inplace=True)


    


    df_form_1000_fmt = pd.merge(
        df_1000_wells_count,
        df_1000_permit_dates,
        how="left",
        left_on=["trsm_heh"],
        right_on=["trsm_heh"],
    )


    # ## calculating latest, oldest dates, wells count for form 1001

    


    print("processing required information from form 1001")
    df_1001_spud_dates = (
        df_1001[["trsm_heh", "spud_date"]]
        .dropna(subset=["spud_date"], how="all")
        .reset_index(drop=True)
    )
    df_1001_spud_dates = df_1001_spud_dates.drop_duplicates()
    print(df_1001_spud_dates.shape)


    


    df_1001_wells_count = df_1001_spud_dates[["trsm_heh"]]
    df_1001_wells_count = (
        df_1001_wells_count.groupby(["trsm_heh"]).size().reset_index(name="no_wells_spud")
    )


    


    df_1001_spud_dates["spud_date"] = pd.to_datetime(df_1001_spud_dates["spud_date"])
    df_1001_spud_dates = (
        df_1001_spud_dates.sort_values("spud_date")
        .groupby("trsm_heh")["spud_date"]
        .agg(["first", "last"])
    )

    df_1001_spud_dates.rename(
        columns={"first": "date_first_spud", "last": "date_last_spud"}, inplace=True
    )
    df_1001_spud_dates = df_1001_spud_dates.rename_axis("trsm_heh").reset_index()
    df_1001_spud_dates.reset_index(drop=True, inplace=True)


    


    df_form_1001_fmt = pd.merge(
        df_1001_wells_count,
        df_1001_spud_dates,
        how="left",
        left_on=["trsm_heh"],
        right_on=["trsm_heh"],
    )


    # ## calculating latest, oldest dates, wells count for form 1002A

    


    print("processing required information from production data")
    df_1002A_completion_dates = (
        df_1002A[["api", "well_completion_date"]]
        .dropna(subset=["well_completion_date"], how="all")
        .reset_index(drop=True)
    )


    df_1002A_completion_dates = pd.merge(
        df_1002A_completion_dates,
        df_index_well_land[["api", "trsm_heh"]],
        how="left",
        left_on=["api"],
        right_on=["api"],
    )
    df_1002A_completion_dates = df_1002A_completion_dates.drop_duplicates()
    df_1002A_completion_dates = df_1002A_completion_dates.drop(["api"], axis=1)


    


    df_1002A_wells_count = df_1002A_completion_dates[["trsm_heh"]]
    df_1002A_wells_count = (
        df_1002A_wells_count.groupby(["trsm_heh"])
        .size()
        .reset_index(name="no_wells_completed")
    )


    


    print(df_1002A_completion_dates.shape)
    df_1002A_completion_dates["well_completion_date"] = pd.to_datetime(
        df_1002A_completion_dates["well_completion_date"]
    )
    df_1002A_completion_dates = (
        df_1002A_completion_dates.sort_values("well_completion_date")
        .groupby("trsm_heh")["well_completion_date"]
        .agg(["first", "last"])
    )
    # df_1002A_permit_dates.index.api = ['api']
    df_1002A_completion_dates.rename(
        columns={"first": "date_first_completion", "last": "date_last_completion"},
        inplace=True,
    )
    df_1002A_completion_dates = df_1002A_completion_dates.rename_axis(
        "trsm_heh"
    ).reset_index()
    df_1002A_completion_dates.reset_index(drop=True, inplace=True)


    


    df_form_1002A_fmt = pd.merge(
        df_1002A_wells_count,
        df_1002A_completion_dates,
        how="left",
        left_on=["trsm_heh"],
        right_on=["trsm_heh"],
    )


    # ## calculating latest app dates and counts for increased density

    try:
        df_latest_app = pd.DataFrame()
        df_latest_app_dates = pd.DataFrame()
        df_latest_inc_den_app_wells_count = pd.DataFrame()
        df_latest_app = df_i_density[["trsm_heh", "app_date"]]

        df_latest_app_dates = (
            df_latest_app.sort_values("app_date")
            .groupby("trsm_heh")["app_date"]
            .agg(["first", "last"])
        )

        df_latest_app_dates.rename(
            columns={"first": "date_oldest_inc_den_app", "last": "date_inc_den_app"},
            inplace=True,
        )
        df_latest_app_dates = df_latest_app_dates.rename_axis("trsm_heh").reset_index()
        df_latest_app_dates = df_latest_app_dates.drop(["date_oldest_inc_den_app"], axis=1)
        df_latest_app_dates.reset_index(drop=True, inplace=True)

        # finding the count number of latest inc_denmsity apps
        df_latest_inc_den_app_wells_count = df_i_density[["trsm_heh", "app_date"]]
        df_latest_apps = df_latest_app_dates.copy()
        df_latest_apps.rename(
            columns={"date_inc_den_app": "app_date"}, inplace=True
        )

        df_latest_inc_den_app_wells_count = pd.merge(
            df_latest_inc_den_app_wells_count,
            df_latest_apps,
            how="inner",
            left_on=["trsm_heh", "app_date"],
            right_on=["trsm_heh", "app_date"],
        )

        df_latest_inc_den_app_wells_count = (
            pd.crosstab(
                df_latest_inc_den_app_wells_count.trsm_heh,
                df_latest_inc_den_app_wells_count.app_date,
            )
                .replace(0, np.nan)
                .stack()
                .reset_index()
                .rename(columns={0: "inc_den_app_nwells"})
        )
        df_latest_inc_den_app_wells_count = df_latest_inc_den_app_wells_count.drop(
            ["app_date"], axis=1)

    except:
        df_latest_app_dates['trsm_heh']=''
        df_latest_app_dates['date_inc_den_app'] = ''
        df_latest_inc_den_app_wells_count['trsm_heh']=''
        df_latest_inc_den_app_wells_count['inc_den_app_nwells']=''
    # calculating increased densities for orders

    try:
            df_latest_order = pd.DataFrame()
            df_latest_order_dates = pd.DataFrame()
            df_latest_inc_den_order_wells_count = pd.DataFrame()
            df_latest_order = df_i_density[["trsm_heh", "order_date"]]

            df_latest_order_dates = (
                df_latest_order.sort_values("order_date")
                .groupby("trsm_heh")["order_date"]
                .agg(["first", "last"])
            )

            df_latest_order_dates.rename(
                columns={"first": "date_oldest_inc_den_order", "last": "date_inc_den_order"},
                inplace=True,
            )
            df_latest_order_dates = df_latest_order_dates.rename_axis("trsm_heh").reset_index()
            df_latest_order_dates = df_latest_order_dates.drop(
                ["date_oldest_inc_den_order"], axis=1
            )
            df_latest_order_dates.reset_index(drop=True, inplace=True)


            # finding the count of number of latest increasd density orders
            df_latest_inc_den_order_wells_count = df_i_density[["trsm_heh", "order_date"]]
            df_latest_orders = df_latest_order_dates.copy()
            df_latest_orders .rename(
                columns={"date_inc_den_order": "order_date"}, inplace=True
            )

            df_latest_inc_den_order_wells_count = pd.merge(
                df_latest_inc_den_order_wells_count,
                df_latest_orders ,
                how="inner",
                left_on=["trsm_heh", "order_date"],
                right_on=["trsm_heh", "order_date"],
            )


            df_latest_inc_den_order_wells_count = (
                pd.crosstab(
                    df_latest_inc_den_order_wells_count.trsm_heh,
                    df_latest_inc_den_order_wells_count.order_date,
                )
                    .replace(0, np.nan)
                    .stack()
                    .reset_index()
                    .rename(columns={0: "inc_den_order_nwells"})
            )
            df_latest_inc_den_order_wells_count = df_latest_inc_den_order_wells_count.drop(
                ["order_date"], axis=1
            )
    except:
        df_latest_order_dates['trsm_heh']=''
        df_latest_order_dates['date_inc_den_order'] = ''
        df_latest_inc_den_order_wells_count['trsm_heh']=''
        df_latest_inc_den_order_wells_count['inc_den_order_nwells']=''

    


    df_inc_dens_fmt = pd.merge(
        df_latest_app_dates,
        df_latest_order_dates,
        how="outer",
        left_on=["trsm_heh"],
        right_on=["trsm_heh"],
    )

    df_inc_dens_fmt = pd.merge(
        df_inc_dens_fmt,
        df_latest_inc_den_app_wells_count,
        how="outer",
        left_on=["trsm_heh"],
        right_on=["trsm_heh"],
    )

    df_inc_dens_fmt = pd.merge(
        df_inc_dens_fmt,
        df_latest_inc_den_order_wells_count,
        how="outer",
        left_on=["trsm_heh"],
        right_on=["trsm_heh"],
    )
    df_inc_dens_fmt.shape


    # ## Creating timing data

    


    df_timing_data = df_index_well_land[["trsm_heh"]].drop_duplicates()
    df_timing_data.shape


    # adding form_1000_data

    


    df_timing_data = pd.merge(
        df_timing_data,
        df_form_1000_fmt,
        how="left",
        left_on=["trsm_heh"],
        right_on=["trsm_heh"],
    )
    df_timing_data.shape


    # adding form_1001_data

    


    df_timing_data = pd.merge(
        df_timing_data,
        df_form_1001_fmt,
        how="left",
        left_on=["trsm_heh"],
        right_on=["trsm_heh"],
    )
    df_timing_data.shape


    # adding form_1002A_data

    


    df_timing_data = pd.merge(
        df_timing_data,
        df_form_1002A_fmt,
        how="left",
        left_on=["trsm_heh"],
        right_on=["trsm_heh"],
    )
    df_timing_data.shape


    # adding increasing density data

    


    df_timing_data = pd.merge(
        df_timing_data,
        df_inc_dens_fmt,
        how="left",
        left_on=["trsm_heh"],
        right_on=["trsm_heh"],
    )
    df_timing_data.shape


    


    cols = [
        "date_first_permit",
        "date_last_spud",
        "date_first_completion",
        "date_last_completion",
        "date_inc_den_app",
        "date_inc_den_order",
    ]
    for date_col in cols:
        df_timing_data[date_col] = pd.to_datetime(df_timing_data[date_col])



    print("processing timing data is successful")

    return df_timing_data


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
            assets=assets, type_curves=type_curves, section_assumptions=section_assumptions )
        index_well_land = dm['section_wells']
        f1000 = dm['f1000s']
        f1001 = dm['f1001s']
        f1002 = dm['f1002s']
        inc_den = dm['increased_densities']

        print(inc_den.shape,index_well_land.shape)
        result_df =  process_section_online(index_well_land,f1000,f1001,f1002,inc_den)
        print(result_df.shape)

        assert True