import logging
import numpy as np
from numba import jit
from scipy.optimize import minimize


def np_mod_arps_fit(mprod, pars):
    """
        Given days and Modified ARPS parameters 2D array returns the predicted production

        Modified ARPS is a Decline Curve Analysis methodology that models the production profile of a well.
        It splits the production profile into two periods.
            1.The initial transient period where the flow boundary moves outwards is
                modelled by a hyperbolic decline.
            2. The final boundary dominated period where the flow boundary is met is
                modelled by an exponential decline

        :param mprod: int
            Number of months to predict the production.
        :param pars: np.array
            Follow the same order.
            ip, d_hyp_eff, d_exp_eff, b

            ip -Initial Production (Max of the prod data)
            d_hyp_eff - Inital Decline; Hyperbolic Effective decline Rate
            d_exp_eff - Final Decline; Exponential Effective decline Rate
            b = 0 when exponential, 1 when harmonic and < 1 when hyperbolic
        Code written to avoid for loop to get better performance.

        For more information,
        http://www.fekete.com/SAN/WebHelp/FeketeHarmony/Harmony_WebHelp/Content/HTML_Files/Reference_Material/Analysis_Method_Theory/Traditional_Decline_Theory.htm
        """
    pars_dtype = pars.dtype
    batch_size = pars.shape[1]
    # days in year
    diy = pars_dtype.type(365)

    # months in year
    miy = pars_dtype.type(12)
    one = pars_dtype.type(1)
    zero = pars_dtype.type(0)

    ip = pars[0].reshape((-1, 1))
    d_hyp_eff = pars[1].reshape((-1, 1))
    d_exp_eff = pars[2].reshape((-1, 1))
    b = pars[3].reshape((-1, 1))

    # Effective to Nominal conversion
    d_hyp_nom = ((np.power((one - d_hyp_eff), -b) - one) / b) / diy
    d_exp_nom = -np.log(one - d_exp_eff) / diy

    # Find the Hyperbolic to Exponential switch point
    switch_day = ((d_hyp_nom / d_exp_nom) - one) / (d_hyp_nom * b)
    # switch_month = np.round(switch_day * (miy / diy)) - one

    switch_month = switch_day * (miy / diy) - one
    # Hyperbolic and exponential months
    month = np.arange(0, mprod, 1).astype(pars_dtype)
    # months = month.reshape((1, -1))
    months = np.reshape(np.tile(month, [batch_size]), [batch_size, mprod])

    # exp_months = np.round(np.maximum(months - switch_month, zero))
    exp_months = np.maximum(months - switch_month, zero)
    switch_flag = np.minimum(exp_months, one)

    # IP at switch point
    switch_ip = ip / np.power(
        (one + ((b * switch_month * (diy / miy)) * d_hyp_nom)), (one / b)
    )

    # Hyperbolic and Exponential prod
    hyp_prod = ip / np.power(
        (one + ((b * months * (diy / miy)) * d_hyp_nom)), (one / b)
    )
    exp_prod = switch_ip * np.exp(-d_exp_nom * exp_months * (diy / miy))

    # combining Hyperbolic and exponential together
    prod = (one - switch_flag) * hyp_prod + switch_flag * exp_prod
    return prod


nb_mod_arps = jit(np_mod_arps_fit, nopython=True, fastmath=True, error_model="numpy")


def modarps_rmse(pars, actual):
    pars = pars.reshape(-1, 1)
    mprod = actual.shape[0]
    predicted = np_mod_arps_fit(mprod, pars)
    return np.sqrt(np.sum(np.square(actual - predicted)))
