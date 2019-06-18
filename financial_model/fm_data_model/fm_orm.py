import pickle
import zlib

import numpy as np
from sqlalchemy import Column, Integer, String, Float, Date, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.types import TypeDecorator, LargeBinary

base = declarative_base()


class NumpyType(TypeDecorator):
    """
    Numpy SQlAlchemy type to retrieve and store compressed numpy tensors
    """

    impl = LargeBinary

    def process_bind_param(self, value, dialect):
        return zlib.compress(value.dumps(), 9)

    def process_result_value(self, value, dialect):
        return pickle.loads(zlib.decompress(value))


class Project_State_Asset(base):
    __tablename__ = "project_state_assets"

    trsm_heh = Column(String, ForeignKey("sections.trsm_heh"), primary_key=True)
    net_acres = Column(Float, primary_key=True)
    royalty = Column(Float, primary_key=True)
    lease_bonus = Column(Float)
    lease_date = Column(Date)
    ask = Column(Float)
    fixed = Column(Float)
    var_oil = Column(Float)
    var_gas = Column(Float)

    section = relationship("Section", cascade="all, delete-orphan", single_parent=True)
    well = relationship(
        "Section_Well", cascade="all, delete-orphan", single_parent=True
    )
    assumption = relationship(
        "Section_Assumption", cascade="all, delete-orphan", single_parent=True
    )

    increased_density = relationship(
        "Increased_Density", cascade="all, delete-orphan", single_parent=True
    )

    spacing = relationship("Spacing", cascade="all, delete-orphan", single_parent=True)
    pooling = relationship("Pooling", cascade="all, delete-orphan", single_parent=True)
    markets = relationship("Market", cascade="all, delete-orphan", single_parent=True)

    def __str__(self):
        return f"{self.trsm_heh} - {self.net_acres} - {self.royalty}"


class Section(base):
    __tablename__ = "sections"

    trsm_heh = Column(String, primary_key=True)
    x = Column(Integer)
    y = Column(Integer)
    acres = Column(Float)

    def __str__(self):
        return f"{self.trsm_heh} - ({self.x}, {self.y})"


class Section_Well(base):
    __tablename__ = "section_wells"

    api = Column(Integer, primary_key=True)
    trsm_heh = Column(
        String, ForeignKey("project_state_assets.trsm_heh"), primary_key=True
    )
    allocation = Column(Float)
    proxy_allocation = Column(Float)
    footage = Column(Integer)
    total_footage = Column(Integer)

    monthly = relationship("Monthly", cascade="all, delete-orphan", single_parent=True)

    f1000 = relationship("f1000", cascade="all, delete-orphan", single_parent=True)
    f1001 = relationship("f1001", cascade="all, delete-orphan", single_parent=True)
    f1002 = relationship("f1002", cascade="all, delete-orphan", single_parent=True)

    def __str__(self):
        return f"{self.trsm_heh} - {self.proxy_allocation if not self.allocation else self.proxy_allocation} ({self.api})"


class Spacing(base):
    __tablename__ = "spacings"

    cause_number = Column(Integer, primary_key=True)
    order_number = Column(Integer)
    trsm_heh = Column(String, ForeignKey("project_state_assets.trsm_heh"))
    app_order = Column(String)
    order_type = Column(String)
    app_date = Column(Date)
    order_date = Column(Date)
    applicant = Column(String)
    is_multi_unit = Column(Boolean)
    included = Column(String)
    formation = Column(String)
    allocation = Column(Float)

    def __str__(self):
        mu = "MU" if self.is_multi_unit else None
        order_type = self.order_type if self.order_type else None
        return f"{self.cause_number} - {self.trsm_heh} - {self.app_order} - {order_type} - {mu}"


class Pooling(base):
    __tablename__ = "poolings"

    cause_number = Column(Integer, primary_key=True)
    order_number = Column(Integer)
    trsm_heh = Column(String, ForeignKey("project_state_assets.trsm_heh"))
    app_order = Column(String)
    order_type = Column(String)
    app_date = Column(Date)
    order_date = Column(Date)
    applicant = Column(String)
    formation = Column(String)
    allocation = Column(Float)

    def __str__(self):
        order_type = self.order_type if self.order_type else None
        return (
            f"{self.cause_number} - {self.trsm_heh} - {self.app_order} - {order_type}"
        )


class Increased_Density(base):
    __tablename__ = "increased_densities"

    cause_number = Column(Integer, primary_key=True)
    trsm_heh = Column(String, ForeignKey("project_state_assets.trsm_heh"))
    nwells = Column(Integer)
    app_order = Column(String)
    order_type = Column(String)
    app_date = Column(Date)
    order_date = Column(Date)

    def __str__(self):
        order_type = self.order_type if self.order_type else None
        return f"{self.cause_number} - {self.app_order} - {order_type} - {self.nwells}"


class f1000(base):
    __tablename__ = "f1000s"

    api = Column(Integer, ForeignKey("section_wells.api"), primary_key=True)
    well_name = Column(String)
    permit_date = Column(Date)
    operator_name = Column(String)

    def __str__(self):
        return f"{self.api if not self.well_name else self.well_name}"


class f1001(base):
    __tablename__ = "f1001s"

    api = Column(Integer, ForeignKey("section_wells.api"), primary_key=True)
    well_name = Column(String)
    spud_date = Column(Date)
    operator_name = Column(String)

    def __str__(self):
        return f"{self.api if not self.well_name else self.well_name}"


class f1002(base):
    __tablename__ = "f1002s"

    api = Column(Integer, ForeignKey("section_wells.api"), primary_key=True)
    well_name = Column(String)
    operator_name = Column(String)
    total_depth = Column(String)
    well_completion_date = Column(Date)
    first_prod_date = Column(Date)
    formation = Column(String)

    def __str__(self):
        return f"{self.api if not self.well_name else self.well_name}"


class Monthly(base):
    __tablename__ = "monthlies"

    api = Column(Integer, ForeignKey("section_wells.api"), primary_key=True)
    date = Column(Date, primary_key=True)
    oil = Column(Float)
    gas = Column(Float)

    def __str__(self):
        return f"{self.api} - {self.date} - {self.oil} BBLPM - {self.gas} MCFPM"


class Oil_Price(base):
    __tablename__ = "oil_prices"

    date = Column(Date, primary_key=True)
    price = Column(Float)

    def __str__(self):
        return f"{self.date} - ${self.price}/BBL"


class Gas_Price(base):
    __tablename__ = "gas_prices"

    date = Column(Date, primary_key=True)
    price = Column(Float)

    def __str__(self):
        return f"{self.date} - ${self.price}/MCF"


class Market(base):
    __tablename__ = "markets"

    trsm_heh = Column(
        String, ForeignKey("project_state_assets.trsm_heh"), primary_key=True
    )
    market_price = Column(Float)


class Section_Assumption(base):
    __tablename__ = "section_assumptions"

    trsm_heh = Column(
        String, ForeignKey("project_state_assets.trsm_heh"), primary_key=True
    )
    portfolio_area = Column(String)
    formation_1 = Column(String)
    nwells_1 = Column(Integer)
    formation_1_tc = Column(String)
    tolerance_1 = Column(Integer)
    formation_2 = Column(String)
    nwells_2 = Column(Integer)
    formation_2_tc = Column(String)
    tolerance_2 = Column(Integer)
    section_acres = Column(Float)

    def __str__(self):
        return f"""{self.trsm_heh} {self.formation_1}({self.nwells_1, self.tolerance_1}),
                    {self.formation_2}({self.nwells_2, self.tolerance_2})"""


class Type_Curve(base):
    __tablename__ = "type_curves"

    portfolio_area = Column(String, primary_key=True)
    type_curve = Column(String, primary_key=True)
    di_oil = Column(Float)
    di_gas = Column(Float)
    b_oil = Column(Float)
    b_gas = Column(Float)
    dmin_oil = Column(Float)
    dmin_gas = Column(Float)
    diff_oil = Column(Float)
    diff_gas = Column(Float)
    afe = Column(Float)

    def __str__(self):
        return f"""{self.portfolio_area} - {self.type_curve} - oil({self.di_oil, self.b_oil, self.di_oil}),
                gas({self.di_gas, self.b_gas, self.di_gas})"""


class Project_Parameter(base):
    __tablename__ = "project_parameters"

    name = Column(String, primary_key=True)
    value = Column(String)

    def __init__(self, name, value):
        self.name = name
        self.value = value


class Well_Production(base):
    __tablename__ = "well_productions"

    api = Column(Integer, ForeignKey("well_onelines.api"), primary_key=True)

    ip_oil = Column(Float)
    di_oil = Column(Float)
    dmin_oil = Column(Float)
    b_oil = Column(Float)

    ip_gas = Column(Float)
    di_gas = Column(Float)
    dmin_gas = Column(Float)
    b_gas = Column(Float)

    pred_oil_prod = Column(NumpyType, default=np.array([]))
    gross_oil_prod = Column(Float)
    pred_gas_prod = Column(NumpyType, default=np.array([]))
    gross_gas_prod = Column(Float)


class Section_Oneline(base):
    __tablename__ = "section_onelines"

    trsm_heh = Column(String, primary_key=True)

    no_wells_permitted = Column(Integer)
    no_wells_spud = Column(Integer)
    no_wells_completed = Column(Integer)
    inc_den_order_nwells = Column(Integer)
    inc_den_app_nwells = Column(Integer)

    date_first_permit = Column(Date)
    date_last_permit = Column(Date)
    date_first_spud = Column(Date)
    date_last_spud = Column(Date)
    date_first_completion = Column(Date)
    date_last_completion = Column(Date)
    date_inc_den_app = Column(Date)
    date_inc_den_order = Column(Date)


class Well_Oneline(base):
    __tablename__ = "well_onelines"

    api = Column(Integer, primary_key=True)
    formation = Column(String)
    operator_name = Column(String)
    well_name = Column(String)

    total_footage = Column(Integer)

    norm_formation = Column(String)

    f1002a_oil = Column(Float)
    f1002a_gas = Column(Float)
    max30_oil = Column(Float)
    max30_gas = Column(Float)

    ip_oil = Column(Float)
    ip_gas = Column(Float)
    norm_ip_oil_7500 = Column(Float)
    norm_ip_gas_7500 = Column(Float)

    oil_gross_volume = Column(Float)
    gas_gross_volume = Column(Float)

    date_permit = Column(Date)
    date_spud = Column(Date)
    date_completion = Column(Date)
    date_first_prod = Column(Date)
    date_last_prod = Column(Date)
