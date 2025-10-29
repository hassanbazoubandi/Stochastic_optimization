from pyomo.environ import *
from pyomo.opt import TerminationCondition

# ایجاد مدل
model = ConcreteModel()
# ===========================
# تعریف مجموعه‌ها
# ===========================
model.m = Set(initialize=['m1'], doc='Set of materials')
model.p = Set(initialize=['p1'], doc='Set of products')
model.tp = Set(initialize=['tp1'], doc='Set of time periods')
model.tr = Set(initialize=['tr1', 'tr2', 'tr3', 'tr4'], doc='Set of transportation tools')
model.sc = Set(initialize=[
    'SC1','SC2','SC3','SC4','SC5','SC6','SC7','SC8','SC9',
    'SC_oc1','SC_oc2','SC_of','SC_te','SC_r1','SC_r2','SC_r3',
    'SC_b1','SC_b2','SC_b3','SC_c1','SC_c2','SC_c3','SC_c4','SC_c5'
], doc='Set of scenarios')
model.b = Set(initialize=['b1'], doc='Set of distribution bases')
model.c = Set(initialize=['c1'], doc='Set of domestic customers')
model.oc = Set(initialize=['oc1'], doc='Set of overseas customers')
model.of = Set(initialize=['of1'], doc='Set of oil fields')
model.r = Set(initialize=['r1', 'r2', 'r3'], doc='Set of refineries')
model.te = Set(initialize=['te1'], doc='Set of terminals')
model.n = Set(initialize=['o_oc1', 'o_of', 'o_te', 'o_r1', 'o_b1', 'o_c1'], doc='Set of nodes in supply chain')
model.np = Set(initialize=['i_oc1', 'i_of', 'i_te', 'i_r1', 'i_b1', 'i_c1'], doc='Set of paired nodes in supply chain')

# ===========================
# تعریف اسکالرها
# ===========================
model.BigM = Param(initialize=1e11, doc='Large constant for constraints')
model.TAXC = Param(initialize=10, doc='Tax per ton of CO2 emitted')
# ===========================
# تعریف پارامترها
# ===========================
# Penalty for production backlog
model.BCK = Param(model.p, model.tp, initialize={('p1', 'tp1'): 50}, doc='Penalty for backlog')
# Lower and upper capacity limits for refineries
model.CAPL = Param(model.r, model.m, model.tp, initialize={('r1', 'm1', 'tp1'): 100}, doc='Lower capacity limit')
model.CAPU = Param(model.r, model.m, model.tp, initialize={('r1', 'm1', 'tp1'): 400}, doc='Upper capacity limit')
# Demand for domestic and overseas customers
model.DEM = Param(model.p, model.c, model.sc, model.tp, initialize={
    ('p1', 'c1', 'SC1', 'tp1'): 24,
    ('p1', 'c1', 'SC2', 'tp1'): 30,
    ('p1', 'c1', 'SC3', 'tp1'): 36,
    ('p1', 'c1', 'SC4', 'tp1'): 24,
    ('p1', 'c1', 'SC5', 'tp1'): 30,
    ('p1', 'c1', 'SC6', 'tp1'): 36,
    ('p1', 'c1', 'SC7', 'tp1'): 24,
    ('p1', 'c1', 'SC8', 'tp1'): 30,
    ('p1', 'c1', 'SC9', 'tp1'): 36,
}, doc='Demand for domestic customers') 
model.DEM_oc = Param(model.p, model.oc, model.sc, model.tp, initialize={
    ('p1', 'oc1', 'SC1', 'tp1'): 24,
    ('p1', 'oc1', 'SC2', 'tp1'): 30,
    ('p1', 'oc1', 'SC3', 'tp1'): 36,
    ('p1', 'oc1', 'SC4', 'tp1'): 24,
    ('p1', 'oc1', 'SC5', 'tp1'): 30,
    ('p1', 'oc1', 'SC6', 'tp1'): 36,
    ('p1', 'oc1', 'SC7', 'tp1'): 24,
    ('p1', 'oc1', 'SC8', 'tp1'): 30,
    ('p1', 'oc1', 'SC9', 'tp1'): 36,
}, doc='Demand for overseas customers')
# Distance between nodes

model.DIS = Param(model.n, model.np, initialize={
    ('o_oc1', 'i_oc1'): 0,
    ('o_oc1', 'i_of'): 0,
    ('o_oc1', 'i_te'): 0,
    ('o_oc1', 'i_r1'): 0,
    ('o_oc1', 'i_b1'): 0,
    ('o_oc1', 'i_c1'): 0,
    ('o_of', 'i_oc1'): 0,
    ('o_of', 'i_of'): 0,
    ('o_of', 'i_te'): 0,
    ('o_of', 'i_r1'): 10,
    ('o_of', 'i_b1'): 0,
    ('o_of', 'i_c1'): 0,
    ('o_te', 'i_oc1'): 10,
    ('o_te', 'i_of'): 0,
    ('o_te', 'i_te'): 0,
    ('o_te', 'i_r1'): 0,
    ('o_te', 'i_b1'): 10,
    ('o_te', 'i_c1'): 0,
    ('o_r1', 'i_oc1'): 0,
    ('o_r1', 'i_of'): 0,
    ('o_r1', 'i_te'): 10,
    ('o_r1', 'i_r1'): 0,
    ('o_r1', 'i_b1'): 10,
    ('o_r1', 'i_c1'): 0,
    ('o_b1', 'i_oc1'): 0,
    ('o_b1', 'i_of'): 0,
    ('o_b1', 'i_te'): 0,
    ('o_b1', 'i_r1'): 0,
    ('o_b1', 'i_b1'): 0,
    ('o_b1', 'i_c1'): 10,
    ('o_c1', 'i_oc1'): 0,
    ('o_c1', 'i_of'): 0,
    ('o_c1', 'i_te'): 0,
    ('o_c1', 'i_r1'): 0,
    ('o_c1', 'i_b1'): 0,
    ('o_c1', 'i_c1'): 0,
}, doc='Distance between nodes')

# Desulfurization ratio
model.DSR = Param(model.r, model.m, initialize={('r1', 'm1'): 0.5}, doc='Desulfurization ratio')

# Purchase upper limit and unit price for extra products
model.EPPU = Param(model.p, model.tp, initialize={('p1', 'tp1'): 300}, doc='Upper limit of extra product purchase')
model.EPUP = Param(model.p, model.te, model.tp, initialize={('p1', 'te1', 'tp1'): 50}, doc='Extra product unit price')

# Inventory upper limits
model.IVU = Param(model.m, model.r, model.tp, initialize={('m1', 'r1', 'tp1'): 100}, doc='Inventory upper limit at refineries')
model.IVU_b = Param(model.p, model.b, model.tp, initialize={('p1', 'b1', 'tp1'): 100}, doc='Inventory upper limit at distribution bases')
model.IVU_te = Param(model.p, model.te, model.tp, initialize={('p1', 'te1', 'tp1'): 100}, doc='Inventory upper limit at terminals')

# Inventory unit prices
model.IVUP = Param(model.m, model.r, model.tp, initialize={('m1', 'r1', 'tp1'): 100}, doc='Inventory unit price at refineries')
model.IVUP_b = Param(model.p, model.b, model.tp, initialize={('p1', 'b1', 'tp1'): 100}, doc='Inventory unit price at distribution bases')
model.IVUP_te = Param(model.p, model.te, model.tp, initialize={('p1', 'te1', 'tp1'): 100}, doc='Inventory unit price at terminals')

# Unit price for materials at oil fields and terminals

# Upper purchase limit for materials
model.MPU = Param(model.m, model.tp, initialize={('m1', 'tp1'): 150}, doc='Purchase upper limit for materials')

# Unit price for materials at oil fields and terminals
model.MUP = Param(model.m, model.te, model.tp, initialize={('m1', 'te1', 'tp1'): 800}, doc='Material unit price at terminals')
model.MUP_of = Param(model.m, model.of, model.tp, initialize={('m1', 'of1', 'tp1'): 800}, doc='Material unit price at oil fields')

# Transportation unit prices for materials and products
model.MTUP = Param(model.m, model.n, model.np, model.tr, model.tp, initialize={
    ('m1', 'o_oc1', 'i_oc1', 'tr1', 'tp1'): 0,
    ('m1', 'o_oc1', 'i_of', 'tr1', 'tp1'): 0,
    ('m1', 'o_oc1', 'i_te', 'tr1', 'tp1'): 0,
    ('m1', 'o_oc1', 'i_r1', 'tr1', 'tp1'): 0,
    ('m1', 'o_oc1', 'i_b1', 'tr1', 'tp1'): 0,
    ('m1', 'o_oc1', 'i_c1', 'tr1', 'tp1'): 0,
    ('m1', 'o_of', 'i_oc1', 'tr1', 'tp1'): 0,
    ('m1', 'o_of', 'i_of', 'tr1', 'tp1'): 0,
    ('m1', 'o_of', 'i_te', 'tr1', 'tp1'): 0,
    ('m1', 'o_of', 'i_r1', 'tr1', 'tp1'): 85,
    ('m1', 'o_of', 'i_b1', 'tr1', 'tp1'): 0,
    ('m1', 'o_of', 'i_c1', 'tr1', 'tp1'): 0,
    ('m1', 'o_te', 'i_oc1', 'tr1', 'tp1'): 85,
    ('m1', 'o_te', 'i_of', 'tr1', 'tp1'): 0,
    ('m1', 'o_te', 'i_te', 'tr1', 'tp1'): 0,
    ('m1', 'o_te', 'i_r1', 'tr1', 'tp1'): 0,
    ('m1', 'o_te', 'i_b1', 'tr1', 'tp1'): 85,
    ('m1', 'o_te', 'i_c1', 'tr1', 'tp1'): 0,
    ('m1', 'o_r1', 'i_oc1', 'tr1', 'tp1'): 0,
    ('m1', 'o_r1', 'i_of', 'tr1', 'tp1'): 0,
    ('m1', 'o_r1', 'i_te', 'tr1', 'tp1'): 85,
    ('m1', 'o_r1', 'i_r1', 'tr1', 'tp1'): 0,
    ('m1', 'o_r1', 'i_b1', 'tr1', 'tp1'): 85,
    ('m1', 'o_r1', 'i_c1', 'tr1', 'tp1'): 0,
    ('m1', 'o_b1', 'i_oc1', 'tr1', 'tp1'): 0,
    ('m1', 'o_b1', 'i_of', 'tr1', 'tp1'): 0,
    ('m1', 'o_b1', 'i_te', 'tr1', 'tp1'): 0,
    ('m1', 'o_b1', 'i_r1', 'tr1', 'tp1'): 0,
    ('m1', 'o_b1', 'i_b1', 'tr1', 'tp1'): 0,
    ('m1', 'o_b1', 'i_c1', 'tr1', 'tp1'): 85,
    ('m1', 'o_c1', 'i_oc1', 'tr1', 'tp1'): 0,
    ('m1', 'o_c1', 'i_of', 'tr1', 'tp1'): 0,
    ('m1', 'o_c1', 'i_te', 'tr1', 'tp1'): 0,
    ('m1', 'o_c1', 'i_r1', 'tr1', 'tp1'): 0,
    ('m1', 'o_c1', 'i_b1', 'tr1', 'tp1'): 0,
    ('m1', 'o_c1', 'i_c1', 'tr1', 'tp1'): 0,
}, doc='Transportation unit price for materials between nodes')



model.PTUP = Param(model.p, model.n, model.np, model.tr, model.tp, initialize={
    ('p1', 'o_oc1', 'i_oc1', 'tr1', 'tp1'): 0,
    ('p1', 'o_oc1', 'i_of', 'tr1', 'tp1'): 0,
    ('p1', 'o_oc1', 'i_te', 'tr1', 'tp1'): 0,
    ('p1', 'o_oc1', 'i_r1', 'tr1', 'tp1'): 0,
    ('p1', 'o_oc1', 'i_b1', 'tr1', 'tp1'): 0,
    ('p1', 'o_oc1', 'i_c1', 'tr1', 'tp1'): 0,
    ('p1', 'o_of', 'i_oc1', 'tr1', 'tp1'): 0,
    ('p1', 'o_of', 'i_of', 'tr1', 'tp1'): 0,
    ('p1', 'o_of', 'i_te', 'tr1', 'tp1'): 0,
    ('p1', 'o_of', 'i_r1', 'tr1', 'tp1'): 10,
    ('p1', 'o_of', 'i_b1', 'tr1', 'tp1'): 0,
    ('p1', 'o_of', 'i_c1', 'tr1', 'tp1'): 0,
    ('p1', 'o_te', 'i_oc1', 'tr1', 'tp1'): 10,
    ('p1', 'o_te', 'i_of', 'tr1', 'tp1'): 0,
    ('p1', 'o_te', 'i_te', 'tr1', 'tp1'): 0,
    ('p1', 'o_te', 'i_r1', 'tr1', 'tp1'): 0,
    ('p1', 'o_te', 'i_b1', 'tr1', 'tp1'): 10,
    ('p1', 'o_te', 'i_c1', 'tr1', 'tp1'): 0,
    ('p1', 'o_r1', 'i_oc1', 'tr1', 'tp1'): 0,
    ('p1', 'o_r1', 'i_of', 'tr1', 'tp1'): 0,
    ('p1', 'o_r1', 'i_te', 'tr1', 'tp1'): 10,
    ('p1', 'o_r1', 'i_r1', 'tr1', 'tp1'): 0,
    ('p1', 'o_r1', 'i_b1', 'tr1', 'tp1'): 10,
    ('p1', 'o_r1', 'i_c1', 'tr1', 'tp1'): 0,
    ('p1', 'o_b1', 'i_oc1', 'tr1', 'tp1'): 0,
    ('p1', 'o_b1', 'i_of', 'tr1', 'tp1'): 0,
    ('p1', 'o_b1', 'i_te', 'tr1', 'tp1'): 0,
    ('p1', 'o_b1', 'i_r1', 'tr1', 'tp1'): 0,
    ('p1', 'o_b1', 'i_b1', 'tr1', 'tp1'): 0,
    ('p1', 'o_b1', 'i_c1', 'tr1', 'tp1'): 10,
    ('p1', 'o_c1', 'i_oc1', 'tr1', 'tp1'): 0,
    ('p1', 'o_c1', 'i_of', 'tr1', 'tp1'): 0,
    ('p1', 'o_c1', 'i_te', 'tr1', 'tp1'): 0,
    ('p1', 'o_c1', 'i_r1', 'tr1', 'tp1'): 0,
    ('p1', 'o_c1', 'i_b1', 'tr1', 'tp1'): 0,
    ('p1', 'o_c1', 'i_c1', 'tr1', 'tp1'): 0,
}, doc='Transportation unit price for products between nodes')



# Unit price for products at terminals and distribution bases
model.PUP = Param(model.p, model.te, model.sc, model.tp, initialize={
    ('p1', 'te1', 'SC1', 'tp1'): 936,
    ('p1', 'te1', 'SC2', 'tp1'): 936,
    ('p1', 'te1', 'SC3', 'tp1'): 936,
    ('p1', 'te1', 'SC4', 'tp1'): 1170,
    ('p1', 'te1', 'SC5', 'tp1'): 1170,
    ('p1', 'te1', 'SC6', 'tp1'): 1170,
    ('p1', 'te1', 'SC7', 'tp1'): 1404,
    ('p1', 'te1', 'SC8', 'tp1'): 1404,
    ('p1', 'te1', 'SC9', 'tp1'): 1404,
}, doc='Product unit price at terminals')
model.PUP_b = Param(model.p, model.b, model.sc, model.tp, initialize={
    ('p1', 'b1', 'SC1', 'tp1'): 936,
    ('p1', 'b1', 'SC2', 'tp1'): 936,
    ('p1', 'b1', 'SC3', 'tp1'): 936,
    ('p1', 'b1', 'SC4', 'tp1'): 1170,
    ('p1', 'b1', 'SC5', 'tp1'): 1170,
    ('p1', 'b1', 'SC6', 'tp1'): 1170,
    ('p1', 'b1', 'SC7', 'tp1'): 1404,
    ('p1', 'b1', 'SC8', 'tp1'): 1404,
    ('p1', 'b1', 'SC9', 'tp1'): 1404,
}, doc='Product unit price at distribution bases')

# Upper limits for backlog and surplus products
model.QBU = Param(model.p, model.c, model.tp, initialize={('p1', 'c1', 'tp1'): 500}, doc='Backlog upper limit for domestic customers')
model.QBU_oc = Param(model.p, model.oc, model.tp, initialize={('p1', 'oc1', 'tp1'): 500}, doc='Backlog upper limit for overseas customers')
model.QSU = Param(model.p, model.c, model.tp, initialize={('p1', 'c1', 'tp1'): 500}, doc='Surplus upper limit for domestic customers')
model.QSU_oc = Param(model.p, model.oc, model.tp, initialize={('p1', 'oc1', 'tp1'): 500}, doc='Surplus upper limit for overseas customers')


# Refinery operation unit price
model.ROUP = Param(model.r, model.m, model.tp, initialize={('r1', 'm1', 'tp1'): 50}, doc='Refinery operation unit price')

# Sulfur content for materials and products
model.SC_m = Param(model.m, model.tp, initialize={('m1', 'tp1'): 50}, doc='Sulfur content of material')
model.SC_p = Param(model.p, model.tp, initialize={('p1', 'tp1'): 50}, doc='Sulfur content of product')

# Penalty for surplus production
model.SUR = Param(model.p, model.tp, initialize={('p1', 'tp1'): 30}, doc='Penalty for surplus production')

# Transportation capacity upper limit
model.TCAU = Param(model.n, model.np, model.tr, model.tp, initialize={
    ('o_oc1', 'i_oc1', 'tr1', 'tp1'): 0,
    ('o_oc1', 'i_of', 'tr1', 'tp1'): 0,
    ('o_oc1', 'i_te', 'tr1', 'tp1'): 0,
    ('o_oc1', 'i_r1', 'tr1', 'tp1'): 0,
    ('o_oc1', 'i_b1', 'tr1', 'tp1'): 0,
    ('o_oc1', 'i_c1', 'tr1', 'tp1'): 0,
    ('o_of', 'i_oc1', 'tr1', 'tp1'): 0,
    ('o_of', 'i_of', 'tr1', 'tp1'): 0,
    ('o_of', 'i_te', 'tr1', 'tp1'): 0,
    ('o_of', 'i_r1', 'tr1', 'tp1'): 1000,
    ('o_of', 'i_b1', 'tr1', 'tp1'): 0,
    ('o_of', 'i_c1', 'tr1', 'tp1'): 0,
    ('o_te', 'i_oc1', 'tr1', 'tp1'): 1000,
    ('o_te', 'i_of', 'tr1', 'tp1'): 0,
    ('o_te', 'i_te', 'tr1', 'tp1'): 0,
    ('o_te', 'i_r1', 'tr1', 'tp1'): 0,
    ('o_te', 'i_b1', 'tr1', 'tp1'): 1000,
    ('o_te', 'i_c1', 'tr1', 'tp1'): 0,
    ('o_r1', 'i_oc1', 'tr1', 'tp1'): 0,
    ('o_r1', 'i_of', 'tr1', 'tp1'): 0,
    ('o_r1', 'i_te', 'tr1', 'tp1'): 1000,
    ('o_r1', 'i_r1', 'tr1', 'tp1'): 0,
    ('o_r1', 'i_b1', 'tr1', 'tp1'): 1000,
    ('o_r1', 'i_c1', 'tr1', 'tp1'): 0,
    ('o_b1', 'i_oc1', 'tr1', 'tp1'): 0,
    ('o_b1', 'i_of', 'tr1', 'tp1'): 0,
    ('o_b1', 'i_te', 'tr1', 'tp1'): 0,
    ('o_b1', 'i_r1', 'tr1', 'tp1'): 0,
    ('o_b1', 'i_b1', 'tr1', 'tp1'): 0,
    ('o_b1', 'i_c1', 'tr1', 'tp1'): 1000,
    ('o_c1', 'i_oc1', 'tr1', 'tp1'): 0,
    ('o_c1', 'i_of', 'tr1', 'tp1'): 0,
    ('o_c1', 'i_te', 'tr1', 'tp1'): 0,
    ('o_c1', 'i_r1', 'tr1', 'tp1'): 0,
    ('o_c1', 'i_b1', 'tr1', 'tp1'): 0,
    ('o_c1', 'i_c1', 'tr1', 'tp1'): 0,
}, doc='Transportation capacity limit between nodes')


# Yield ratio for materials to products
model.YDR = Param(model.r, model.m, model.p, initialize={
    ('r1', 'm1', 'p1'): 1
}, doc='Yield ratio of material to product')

# Yield ratio for materials to products
model.YDR_tp = Param(model.r, model.m, model.tp, initialize={
    ('r1', 'm1', 'tp1'): 1
}, doc='Yield ratio of material to product for time period')
# Carbon emission parameters
model.CCOEF = Param(model.tr, initialize={
    'tr1': -5304,
    'tr2': -5330,
    'tr3': -5928,
    'tr4': -5980
}, doc='Carbon emission coefficient for transportation tool tr')

model.EC = Param(model.r, initialize={
    'r1': 79,
    'r2': 492,
    'r3': 329
}, doc='Quantity of CO2 emitted per ton of material operated at refinery r')

# Scenario probabilities
model.PROB = Param(model.sc, initialize={
    'SC_oc1': 0,
    'SC_oc2': 0,
    'SC_of': 1,
    'SC_te': 0,
    'SC_r1': 0,
    'SC_r2': 1,
    'SC_r3': 1,
    'SC_b1': 0,
    'SC_b2': 0,
    'SC_b3': 1,
    'SC_c1': 1,
    'SC_c2': 1,
    'SC_c3': 1,
    'SC_c4': 1,
    'SC_c5': 0,
    # برای سناریوهای SC1 تا SC9 در شیت DEM و DEM_oc مقدار خاصی ارائه نشده؛ فرض می‌کنیم ۱ باشد.
    'SC1': 1,
    'SC2': 1,
    'SC3': 1,
    'SC4': 1,
    'SC5': 1,
    'SC6': 1,
    'SC7': 1,
    'SC8': 1,
    'SC9': 1,
}, doc='Probability of scenario sc')

# ===========================
# تعریف متغیرها
# ===========================
# Define positive variables
model.qps_oc = Var(model.p, model.oc, model.te, model.sc, model.tp, domain=NonNegativeReals,
                   doc="Quantity of product p sold at time period tp of scenario sc at terminal te to overseas customer oc")

model.qps = Var(model.p, model.c, model.b, model.sc, model.tp, domain=NonNegativeReals,
                doc="Quantity of product p sold at time period tp of scenario sc at distribution b to domestic customer c")

model.qmp = Var(model.m, model.te, model.r, model.tp, domain=NonNegativeReals,
                doc="Quantity of material m purchased by refinery r during time period tp at terminal te")

model.qmp_of = Var(model.m, model.of, model.r, model.tp, domain=NonNegativeReals,
                   doc="Quantity of material m purchased by refinery r during time period tp at oil field of")

model.qmtr = Var(model.m, model.n, model.np, model.tr, model.tp, domain=NonNegativeReals,
                 doc="Quantity of material m transported from node n to n' by transportation tool tr at time period tp")

model.qmo = Var(model.r, model.m, model.sc, model.tp, domain=NonNegativeReals,
                doc="Quantity of material m operated by refinery r at time period tp of scenario sc")

model.qmsto = Var(model.m, model.r, model.sc, model.tp, domain=NonNegativeReals,
                  doc="Quantity of material m stocked at refinery r")

model.qpsto = Var(model.p, model.te, model.sc, model.tp, domain=NonNegativeReals,
                  doc="Quantity of product p stocked at terminal te")

model.qpsto_b = Var(model.p, model.b, model.sc, model.tp, domain=NonNegativeReals,
                    doc="Quantity of product p stocked at distribution b")

model.qptr = Var(model.p, model.n, model.np, model.tr, model.sc, model.tp, domain=NonNegativeReals,
                 doc="Quantity of product p transported by transportation tool tr from node n to n' at tp of scenario sc")

model.qepp = Var(model.p, model.te, model.sc, model.tp, domain=NonNegativeReals,
                 doc="Quantity of extra product purchased at terminal te at time period tp of scenario sc")

model.qsp = Var(model.p, model.c, model.sc, model.tp, domain=NonNegativeReals,
                doc="Quantity of surplus product p to be purchased at time period tp of sc by domestic customer c")

model.qsp_oc = Var(model.p, model.oc, model.sc, model.tp, domain=NonNegativeReals,
                   doc="Quantity of surplus product p to be purchased at time period tp of sc by overseas customer oc")

model.qbp = Var(model.p, model.c, model.sc, model.tp, domain=NonNegativeReals,
                doc="Quantity of backlog product p needed at time period tp of scenario sc by domestic customer c")

model.qbp_oc = Var(model.p, model.oc, model.sc, model.tp, domain=NonNegativeReals,
                   doc="Quantity of backlog product p needed at time period tp of scenario sc by overseas customer oc")

model.qpte = Var(model.p, model.r, model.te, model.sc, model.tp, domain=NonNegativeReals,
                 doc="Quantity of product p produced by refinery r sold at tp of scenario sc at terminal te")

model.qpb = Var(model.p, model.r, model.b, model.sc, model.tp, domain=NonNegativeReals,
                doc="Quantity of product p produced by refinery r sold at tp of scenario sc at distribution b")

model.qepb = Var(model.p, model.b, model.te, model.sc, model.tp, domain=NonNegativeReals,
                 doc="Quantity of extra product p purchased at te to be sold at distribution b at time period tp of scenario sc")

# Binary variables
model.iqsp = Var(model.p, model.c, model.sc, model.tp, domain=Binary,
                 doc="Binary variable of surplus product by domestic customer c")

model.iqsp_oc = Var(model.p, model.oc, model.sc, model.tp, domain=Binary,
                    doc="Binary variable of surplus product by overseas customer oc")

model.iqbp = Var(model.p, model.c, model.sc, model.tp, domain=Binary,
                 doc="Binary variable of backlog product by domestic customer c")

model.iqbp_oc = Var(model.p, model.oc, model.sc, model.tp, domain=Binary,
                    doc="Binary variable of backlog product by overseas customer oc")

# تعریف متغیرها
model.pf = Var(model.p, model.n, model.np, model.tr, model.tp, domain=NonNegativeReals, 
               doc="Flow of product p from node n to node np by transportation tool tr at time period tp")

model.pf_r_b = Var(
    model.p, model.r, model.b, model.tr, model.sc, model.tp,
    within=NonNegativeReals,
    doc='Flow of product p from refinery r to distribution b by transportation tool tr at time period tp of scenario sc'
)

model.pf_r_te = Var(
    model.p, model.r, model.te, model.tr, model.sc, model.tp,
    within=NonNegativeReals,
    doc='Flow of product p from refinery r to terminal te by transportation tool tr at time period tp of scenario sc'
)

model.pf_b_c = Var(
    model.p, model.b, model.c, model.tr, model.sc, model.tp,
    within=NonNegativeReals,
    doc='Flow of product p from distribution b to domestic customer c by transportation tool tr at time period tp of scenario sc'
)

model.pf_te_oc = Var(
    model.p, model.te, model.oc, model.tr, model.sc, model.tp,
    within=NonNegativeReals,
    doc='Flow of product p from terminal te to overseas customer oc by transportation tool tr at time period tp of scenario sc'
)

model.pf_te_b = Var(
    model.p, model.te, model.b, model.tr, model.sc, model.tp,
    within=NonNegativeReals,
    doc='Flow of product p from terminal te to distribution b by transportation tool tr at time period tp of scenario sc'
)

model.pf_n_np = Var(
    model.p, model.n, model.np, model.tr, model.tp,
    within=NonNegativeReals,
    doc='Flow of product p from node n to node n\' by transportation tool tr at time period tp'
)
# تعریف متغیرها
model.mf = Var(
    model.m, model.n, model.np, model.tr, model.tp,
    within=NonNegativeReals,
    doc='Flow of material m from node n to node n\' by transportation tool tr at time period tp'
)

model.mf_te_r = Var(
    model.m, model.te, model.r, model.tr, model.tp,
    within=NonNegativeReals,
    doc='Flow of material m from terminal te to refinery r by transportation tool tr at time period tp'
)

model.mf_of_r = Var(
    model.m, model.of, model.r, model.tr, model.tp,
    within=NonNegativeReals,
    doc='Flow of material m from oil field of to refinery r by transportation tool tr at time period tp'
)

# ===========================
# تابع هدف
# ===========================

# تعریف تابع هدف
def objective_rule(model):

    # هزینه مواد اولیه
    Cmp = (
        sum(model.MUP[m, te, tp] * model.qmp[m, te, r, tp]
            for m in model.m for te in model.te for r in model.r for tp in model.tp) +
        sum(model.MUP_of[m, of_, tp] * model.qmp_of[m, of_, r, tp]
            for m in model.m for of_ in model.of for r in model.r for tp in model.tp)
    )

    # هزینه حمل و نقل مواد اولیه
    Cmtr = sum(
        model.MTUP[m, n, np, tr, tp] * model.DIS[n, np] * model.qmtr[m, n, np, tr, tp]
        for m in model.m for n in model.n for np in model.np for tr in model.tr for tp in model.tp
    )

    # مالیات انتشار کربن
    Cctax = (
        model.TAXC * sum(
            model.CCOEF[tr] * model.DIS[n, np] * model.qmtr[m, n, np, tr, tp]
            for m in model.m for n in model.n for np in model.np for tr in model.tr for tp in model.tp
        ) +
        sum(
            model.PROB[sc] * (
                model.TAXC * sum(model.EC[r] * model.qmo[r, m, sc, tp]
                                 for r in model.r for m in model.m for tp in model.tp) +
                model.TAXC * sum(
                    model.CCOEF[tr] * model.DIS[n, np] * model.qptr[p, n, np, tr, sc, tp]
                    for p in model.p for n in model.n for np in model.np for tr in model.tr for tp in model.tp
                )
            )
            for sc in model.sc
        )
    )

    # هزینه‌های مربوط به هر سناریو
    scenario_costs = sum(
        model.PROB[sc] * (
            # فروش
            (
             +   sum(model.PUP[p, te, sc, tp] * model.qps_oc[p, oc, te, sc, tp]
                    for p in model.p for oc in model.oc for te in model.te for tp in model.tp) +
                sum(model.PUP_b[p, b, sc, tp] * model.qps[p, c, b, sc, tp]
                    for p in model.p for c in model.c for b in model.b for tp in model.tp)
            )
            # هزینه عملیات پالایشگاه
            - sum(model.ROUP[r, m, tp] * model.qmo[r, m, sc, tp]
                  for r in model.r for m in model.m for tp in model.tp)
            # هزینه‌های عملیاتی و ذخیره‌سازی
            - (
                sum(model.IVUP[m, r, tp] * model.qmsto[m, r, sc, tp]
                    for m in model.m for r in model.r for tp in model.tp) +
                sum(model.IVUP_te[p, te, tp] * model.qpsto[p, te, sc, tp]
                    for p in model.p for te in model.te for tp in model.tp) +
                sum(model.IVUP_b[p, b, tp] * model.qpsto_b[p, b, sc, tp]
                    for p in model.p for b in model.b for tp in model.tp)
            )
            # هزینه‌های حمل و نقل محصولات
            - (sum(
                model.PTUP[p, n, np, tr, tp] * model.DIS[n, np] * model.qptr[p, n, np, tr, sc, tp]
                for p in model.p for n in model.n for np in model.np for tr in model.tr for tp in model.tp
            )
              )
            # هزینه خرید محصولات اضافی
            - (sum(model.EPUP[p, te, tp] * model.qepp[p, te, sc, tp]
                  for p in model.p for te in model.te for tp in model.tp)
              )
            # هزینه مازاد
            - (
                sum(model.SUR[p, tp] * model.qsp[p, c, sc, tp]
                    for p in model.p for c in model.c for tp in model.tp) +
                sum(model.SUR[p, tp] * model.qsp_oc[p, oc, sc, tp]
                    for p in model.p for oc in model.oc for tp in model.tp)
            )
            # هزینه کمبود
            - (
                sum(model.BCK[p, tp] * model.qbp[p, c, sc, tp]
                    for p in model.p for c in model.c for tp in model.tp) +
                sum(model.BCK[p, tp] * model.qbp_oc[p, oc, sc, tp]
                    for p in model.p for oc in model.oc for tp in model.tp)
            )
        )
        for sc in model.sc
    )

    # بازگشت تابع هدف
    return -Cmp - Cmtr - Cctax + scenario_costs

# اضافه کردن تابع هدف به مدل
model.Obj = Objective(rule=objective_rule, sense=maximize)

# ===========================
# قیود
# ===========================
# قید تعادل مواد
def material_balance_rule(model, m, r, tp, sc):
    if tp == 'tp1':  # شرط برای دوره اول
        return (
            sum(model.qmp[m, te, r, tp] for te in model.te) +
            sum(model.qmp_of[m, of, r, tp] for of in model.of)
            ==
            model.qmo[r, m, sc, tp]+ model.qmsto[m, r, sc, tp]
        )
    else:  # برای دوره‌های دیگر
        return (
            sum(model.qmp[m, te, r, tp] for te in model.te) +
            sum(model.qmp_of[m, of, r, tp] for of in model.of) +
            model.qmsto[m, r, sc, tp - 1]
            ==
            model.qmo[r, m, sc, tp] + model.qmsto[m, r, sc, tp]
        )

model.MaterialBalance = Constraint(model.m, model.r, model.tp, model.sc, rule=material_balance_rule)

# قید محدودیت ظرفیت جریان مواد
def transport_capacity_rule(model, n, np, tr, tp):
    return (
        sum(model.mf[m, n, np, tr, tp] for m in model.m) +
        sum(model.pf[p, n, np, tr, tp] for p in model.p)
        <= model.TCAU[n, np, tr, tp]
    )

model.transport_capacity = Constraint(model.n, model.np, model.tr, model.tp, rule=transport_capacity_rule)

def flow_terminal_to_refinery_rule(model, m, te, r, tp):
    return model.qmp[m, te, r, tp] == sum(model.mf_te_r[m, te, r, tr, tp] for tr in model.tr)
model.flow_terminal_to_refinery_constraint = Constraint(
    model.m, model.te, model.r, model.tp, 
    rule=flow_terminal_to_refinery_rule, 
    doc="Flow of material from terminal to refinery"
)


def flow_oilfield_to_refinery_rule(model, m, of, r, tp):
    return model.qmp_of[m, of, r, tp] == sum(model.mf_of_r[m, of, r, tr, tp] for tr in model.tr)
model.flow_oilfield_to_refinery_constraint = Constraint(
    model.m, model.of, model.r, model.tp, 
    rule=flow_oilfield_to_refinery_rule, 
    doc="Flow of material from oilfield to refinery"
)

def flow_refinery_to_base_rule(model, p, r, b, sc, tp):
    return model.qpb[p, r, b, sc, tp] == sum(model.pf_r_b[p, r, b, tr, sc, tp] for tr in model.tr)
model.flow_refinery_to_base_constraint = Constraint(
    model.p, model.r, model.b, model.sc, model.tp, 
    rule=flow_refinery_to_base_rule, 
    doc="Flow of product from refinery to base"
)
def flow_refinery_to_terminal_rule(model, p, r, te, sc, tp):
    return model.qpte[p, r, te, sc, tp] == sum(model.pf_r_te[p, r, te, tr, sc, tp] for tr in model.tr)
model.flow_refinery_to_terminal_constraint = Constraint(
    model.p, model.r, model.te, model.sc, model.tp, 
    rule=flow_refinery_to_terminal_rule, 
    doc="Flow of product from refinery to terminal"
)

def flow_base_to_customer_rule(model, p, b, c, sc, tp):
    return model.qps[p, c, b, sc, tp] == sum(model.pf_b_c[p, b, c, tr, sc, tp] for tr in model.tr)
model.flow_base_to_customer_constraint = Constraint(
    model.p, model.b, model.c, model.sc, model.tp, 
    rule=flow_base_to_customer_rule, 
    doc="Flow of product from base to customer"
)
def flow_terminal_to_overseas_customer_rule(model, p, te, oc, sc, tp):
    return model.qps_oc[p, oc, te, sc, tp] == sum(model.pf_te_oc[p, te, oc, tr, sc, tp] for tr in model.tr)
model.flow_terminal_to_overseas_customer_constraint = Constraint(
    model.p, model.te, model.oc, model.sc, model.tp, 
    rule=flow_terminal_to_overseas_customer_rule, 
    doc="Flow of product from terminal to overseas customer"
)
def flow_terminal_to_base_rule(model, p, te, b, sc, tp):
    return model.qepb[p, b, te, sc, tp] == sum(model.pf_te_b[p, te, b, tr, sc, tp] for tr in model.tr)
model.flow_terminal_to_base_constraint = Constraint(
    model.p, model.te, model.b, model.sc, model.tp, 
    rule=flow_terminal_to_base_rule, 
    doc="Flow of product from terminal to base"
)

# قید تعادل محصولات

def product_balance_rule1(model, m, p, r, tp, sc):
    return (
        model.qmo[r, m, sc, tp] * model.YDR[r, m, p] ==
        sum(model.qpte[p, r, te, sc, tp] for te in model.te) +
        sum(model.qpb[p, r, b, sc, tp] for b in model.b)
    )

model.product_balance1 = Constraint(model.m, model.p, model.r, model.tp, model.sc, rule=product_balance_rule1)

def product_balance_rule2(model, p, te, tp, sc):
    if tp == 'tp1':
        return (
            sum(model.qpte[p, r, te, sc, tp] for r in model.r) +
            model.qepp[p, te, sc, tp] -
            sum(model.qepb[p, b, te, sc, tp] for b in model.b) ==
            sum(model.qps_oc[p, oc, te, sc, tp] for oc in model.oc) +
            model.qpsto[p, te, sc, tp]
        )
    else:
        return (
            sum(model.qpte[p, r, te, sc, tp] for r in model.r) +
            model.qepp[p, te, sc, tp] -
            sum(model.qepb[p, b, te, sc, tp] for b in model.b) +
            model.qpsto[p, te, sc, tp - 1] ==
            sum(model.qps_oc[p, oc, te, sc, tp] for oc in model.oc) +
            model.qpsto[p, te, sc, tp]
        )

model.product_balance2 = Constraint(model.p, model.te, model.tp, model.sc, rule=product_balance_rule2)

def product_balance_rule3(model, p, b, tp, sc):
    if tp == 'tp1':
        return (
            sum(model.qpb[p, r, b, sc, tp] for r in model.r) +
            sum(model.qepb[p, b, te, sc, tp] for te in model.te) ==
            sum(model.qps[p, c, b, sc, tp] for c in model.c) +
            model.qpsto_b[p, b, sc, tp]
        )
    else:
        return (
            sum(model.qpb[p, r, b, sc, tp] for r in model.r) +
            sum(model.qepb[p, b, te, sc, tp] for te in model.te) +
            model.qpsto_b[p, b, sc, tp - 1] ==
            sum(model.qps[p, c, b, sc, tp] for c in model.c) +
            model.qpsto_b[p, b, sc, tp]
        )

model.product_balance3 = Constraint(model.p, model.b, model.tp, model.sc, rule=product_balance_rule3)

# قید محدودیت موجودی در پایانه
def terminal_inventory_rule(model, p, te, tp, sc):
    tp_index = list(model.tp).index(tp)
    if tp_index > 0:
        prev_tp = list(model.tp)[tp_index - 1]
        return (
            sum(model.qpte[p, r, te, sc, tp] for r in model.r) +
            model.qepp[p, te, sc, tp] +
            model.qpsto[p, te, sc, prev_tp]
            ==
            sum(model.qps_oc[p, oc, te, sc, tp] for oc in model.oc) +
            model.qpsto[p, te, sc, tp]
        )
    else:
        return (
            sum(model.qpte[p, r, te, sc, tp] for r in model.r) +
            model.qepp[p, te, sc, tp]
            ==
            sum(model.qps_oc[p, oc, te, sc, tp] for oc in model.oc) +
            model.qpsto[p, te, sc, tp]
        )

model.TerminalInventory = Constraint(model.p, model.te, model.tp, model.sc, rule=terminal_inventory_rule)

# قید محدودیت موجودی در مرکز توزیع
def distribution_inventory_rule(model, p, b, tp, sc):
    tp_index = list(model.tp).index(tp)
    if tp_index > 0:
        prev_tp = list(model.tp)[tp_index - 1]
        return (
            sum(model.qpb[p, r, b, sc, tp] for r in model.r) +
            sum(model.qepb[p, b, te, sc, tp] for te in model.te) +
            model.qpsto_b[p, b, sc, prev_tp]
            ==
            sum(model.qps[p, c, b, sc, tp] for c in model.c) +
            model.qpsto_b[p, b, sc, tp]
        )
    else:
        return (
            sum(model.qpb[p, r, b, sc, tp] for r in model.r) +
            sum(model.qepb[p, b, te, sc, tp] for te in model.te)
            ==
            sum(model.qps[p, c, b, sc, tp] for c in model.c) +
            model.qpsto_b[p, b, sc, tp]
        )

model.DistributionInventory = Constraint(model.p, model.b, model.tp, model.sc, rule=distribution_inventory_rule)

# قید محدودیت کیفیت
def sulfur_content_rule(model, p, r, tp, sc):
    return (
        sum(model.qmo[r, m, sc, tp] * model.SC_m[m, tp] * model.YDR[r, m, p] * (1 - model.DSR[r, m])
            for m in model.m)
        <=
    (sum(model.qmo[r, m, sc, tp] * model.YDR_tp[r, m, tp] for m in model.m)) * model.SC_p[p, tp]
    )

model.SulfurContent = Constraint(model.p, model.r, model.tp, model.sc, rule=sulfur_content_rule)

# قید محدودیت ظرفیت خرید مواد اولیه
def procurement_capacity_material_rule(model, m, te, of, tp):
    return (
        sum(model.qmp[m, te, r, tp] for te in model.te for r in model.r) +
        sum(model.qmp_of[m, of, r, tp] for r in model.r)
        <= model.MPU[m, tp]
    )

model.ProcurementCapacityMaterial = Constraint(model.m, model.te, model.of, model.tp, rule=procurement_capacity_material_rule)

# قید محدودیت خرید محصولات اضافی
def procurement_capacity_extra_rule(model, p, tp, sc):
    return (
        sum(model.qepp[p, te, sc, tp] for te in model.te)
        <= model.EPPU[p, tp]
    )

model.ProcurementCapacityExtra = Constraint(model.p, model.tp, model.sc, rule=procurement_capacity_extra_rule)

# قید محدودیت عملیات پالایشگاه
def refinery_operation_rule_lower(model, r, m, tp, sc):
    return model.qmo[r, m, sc, tp] >= model.CAPL[r, m, tp]

def refinery_operation_rule_upper(model, r, m, tp, sc):
    return model.qmo[r, m, sc, tp] <= model.CAPU[r, m, tp]

model.RefineryOperationLower = Constraint(model.r, model.m, model.tp, model.sc, rule=refinery_operation_rule_lower)

model.RefineryOperationUpper = Constraint(model.r, model.m, model.tp, model.sc, rule=refinery_operation_rule_upper)

# قید ظرفیت موجودی مواد
def inventory_capacity_material_rule(model, m, r, sc, tp):
    return model.qmsto[m, r, sc, tp] <= model.IVU[m, r, tp]

model.InventoryCapacityMaterial = Constraint(model.m, model.r, model.sc, model.tp, rule=inventory_capacity_material_rule)

# قید ظرفیت موجودی محصولات در پایانه
def inventory_capacity_product_terminal_rule(model, p, te, sc, tp):
    return model.qpsto[p, te, sc, tp] <= model.IVU_te[p, te, tp]

model.InventoryCapacityProductTerminal = Constraint(model.p, model.te, model.sc, model.tp, rule=inventory_capacity_product_terminal_rule)

# قید ظرفیت موجودی محصولات در مرکز توزیع
def inventory_capacity_product_distribution_rule(model, p, b, sc, tp):
    return model.qpsto_b[p, b, sc, tp] <= model.IVU_b[p, b, tp]

model.InventoryCapacityProductDistribution = Constraint(model.p, model.b, model.sc, model.tp, rule=inventory_capacity_product_distribution_rule)

# قید تقاضای مشتریان خارجی
def demand_external_rule(model, p, oc, te, sc, tp):
    return model.qps_oc[p, oc, te, sc, tp] == model.DEM_oc[p, oc, sc, tp] + model.qsp_oc[p, oc, sc, tp] - model.qbp_oc[p, oc, sc, tp]

model.DemandExternal = Constraint(model.p, model.oc, model.te, model.sc,model.tp, rule=demand_external_rule)

# قید تقاضای مشتریان داخلی
def demand_internal_rule(model, p, c, b, sc, tp):
    return model.qps[p, c, b, sc, tp] == model.DEM[p, c, sc, tp] + model.qsp[p, c, sc, tp] - model.qbp[p, c, sc, tp]

model.DemandInternal = Constraint(model.p, model.c, model.b, model.sc, model.tp, rule=demand_internal_rule)


#  حداکثر کمبود برای مشتریان خارجی
def backlog_limit_external_rule(model, p, oc, sc, tp):
    return model.qbp_oc[p, oc, sc, tp] <= model.iqbp_oc[p, oc, sc, tp] * model.QBU_oc[p, oc, tp]

model.BacklogLimitExternal = Constraint(model.p, model.oc, model.sc, model.tp, rule=backlog_limit_external_rule)

# قید حداکثر مازاد برای مشتریان داخلی
def surplus_limit_internal_rule(model, p, c, sc, tp):
    return model.qsp[p, c, sc, tp] <= model.iqsp[p, c, sc, tp] * model.QSU[p, c, tp]

model.SurplusLimitInternal = Constraint(model.p, model.c, model.sc, model.tp, rule=surplus_limit_internal_rule)

# قید حداکثر مازاد برای مشتریان خارجی
def surplus_limit_external_rule (model, p, oc, tp, sc):
    return model.qsp_oc[p, oc, sc, tp] <= model.iqsp_oc[p, oc, sc, tp] * model.QSU_oc[p, oc, tp]

model.surplusLimitExternal = Constraint(model.p, model.oc, model.tp, model.sc, rule=surplus_limit_external_rule)

# قید حداکثر کمبود برای مشتریان داخلی
def backlog_limit_internal_rule(model, p, c, sc, tp):
    return model.qbp[p, c, sc, tp] <= model.iqbp[p, c, sc, tp] * model.QBU[p, c, tp]

model.BacklogLimitInternal = Constraint(model.p, model.c, model.sc, model.tp, rule=backlog_limit_internal_rule)

# قید منطقی مازاد و کمبود برای مشتریان خارجی
def logical_constraint_external_rule(model, p, oc, sc, tp):
    return model.iqsp_oc[p, oc, sc, tp] + model.iqbp_oc[p, oc, sc, tp] <= 1

model.LogicalConstraintExternal = Constraint(model.p, model.oc, model.sc, model.tp, rule=logical_constraint_external_rule)

# قید منطقی مازاد و کمبود برای مشتریان داخلی
def logical_constraint_internal_rule(model, p, c, sc, tp):
    return model.iqsp[p, c, sc, tp] + model.iqbp[p, c, sc, tp] <= 1

model.LogicalConstraintInternal = Constraint(model.p, model.c, model.sc, model.tp, rule=logical_constraint_internal_rule)


# بررسی وضعیت مدل
solver = SolverFactory('glpk')
result = solver.solve(model, tee=True)

# بررسی وضعیت حل مدل
if result.solver.termination_condition == TerminationCondition.optimal:
    print("Model solved optimally.")
elif result.solver.termination_condition == TerminationCondition.infeasible:
    print("Model is infeasible. Extracting IIS...")
    model.write('infeasible_model.lp', format='lp')  # ذخیره مدل در فرمت LP
    print("Infeasible model saved as 'infeasible_model.lp'. Analyze it using glpsol:")
    print("  glpsol --cpxlp infeasible_model.lp --write iis.txt --output solution.txt")
elif result.solver.termination_condition == TerminationCondition.unbounded:
    print("Model is unbounded. Check the objective function or bounds.")
else:
    print(f"Model status: {result.solver.termination_condition}")
    



# نمایش متغیرها
print("Variable values:")
for var in model.component_objects(Var, active=True):
    print(f"Variable {var.name}:")
    for index in var:
        print(f"{index}: {var[index].value}")
        
