import logging

from pyomo.environ import (
    Binary,
    ConcreteModel,
    Constraint,
    NonNegativeReals,
    Objective,
    Param,
    Set,
    SolverFactory,
    Suffix,
    Var,
    maximize,
    value,
)
from pyomo.opt import TerminationCondition

try:  # pragma: no cover - import depends on user Pyomo version
    from pyomo.util import infeasible as _infeasible_utils
except ImportError:  # pragma: no cover - gracefully degrade when unavailable
    _infeasible_utils = None

if _infeasible_utils is not None:
    log_infeasible_bounds = getattr(_infeasible_utils, "log_infeasible_bounds", None)
    log_infeasible_constraints = getattr(_infeasible_utils, "log_infeasible_constraints", None)
    log_infeasible_binary = getattr(
        _infeasible_utils,
        "log_infeasible_binary",
        getattr(_infeasible_utils, "log_infeasible_binary_vars", None),
    )
else:
    log_infeasible_bounds = None
    log_infeasible_constraints = None
    log_infeasible_binary = None


diagnostic_logger = logging.getLogger("infeasibility_report")
if not diagnostic_logger.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(levelname)s: %(message)s"))
    diagnostic_logger.addHandler(handler)
diagnostic_logger.setLevel(logging.INFO)
diagnostic_logger.propagate = False

model = ConcreteModel(name="Stochastic multi-echelon supply chain")

# -----------------------------------------------------------------------------
# Sets
# -----------------------------------------------------------------------------
model.m = Set(initialize=['m1'], ordered=True, doc='Materials')
model.p = Set(initialize=['p1'], ordered=True, doc='Products')
model.tp = Set(initialize=['tp1'], ordered=True, doc='Time periods')
model.tr = Set(initialize=['tr1', 'tr2', 'tr3', 'tr4'], ordered=True, doc='Transportation tools')
model.sc = Set(
    initialize=[
        'SC1', 'SC2', 'SC3', 'SC4', 'SC5', 'SC6', 'SC7', 'SC8', 'SC9',
        'SC_oc1', 'SC_oc2', 'SC_of', 'SC_te', 'SC_r1', 'SC_r2', 'SC_r3',
        'SC_b1', 'SC_b2', 'SC_b3', 'SC_c1', 'SC_c2', 'SC_c3', 'SC_c4', 'SC_c5',
    ],
    ordered=True,
    doc='Scenarios',
)
model.b = Set(initialize=['b1'], ordered=True, doc='Distribution bases')
model.c = Set(initialize=['c1'], ordered=True, doc='Domestic customers')
model.oc = Set(initialize=['oc1'], ordered=True, doc='Overseas customers')
model.of = Set(initialize=['of1'], ordered=True, doc='Oil fields')
model.r = Set(initialize=['r1', 'r2', 'r3'], ordered=True, doc='Refineries')
model.te = Set(initialize=['te1'], ordered=True, doc='Terminals')

node_pairs = {
    'of1': ('o_of', 'i_of'),
    'te1': ('o_te', 'i_te'),
    'r1': ('o_r1', 'i_r1'),
    'r2': ('o_r2', 'i_r2'),
    'r3': ('o_r3', 'i_r3'),
    'b1': ('o_b1', 'i_b1'),
    'c1': ('o_c1', 'i_c1'),
    'oc1': ('o_oc1', 'i_oc1'),
}

model.n = Set(initialize=sorted({v[0] for v in node_pairs.values()}), ordered=True)
model.np = Set(initialize=sorted({v[1] for v in node_pairs.values()}), ordered=True)

origin_node = {name: nodes[0] for name, nodes in node_pairs.items()}
destination_node = {name: nodes[1] for name, nodes in node_pairs.items()}

# -----------------------------------------------------------------------------
# Parameters (sourced from article tables)
# -----------------------------------------------------------------------------
model.BigM = Param(initialize=1e11, doc='Large constant')
model.TAXC = Param(initialize=10, doc='Carbon tax per ton of CO2')

model.BCK = Param(model.p, model.tp, initialize={('p1', 'tp1'): 50}, doc='Backlog penalty')
model.CAPL = Param(
    model.r,
    model.m,
    model.tp,
    initialize={
        ('r1', 'm1', 'tp1'): 100,
        ('r2', 'm1', 'tp1'): 0,
        ('r3', 'm1', 'tp1'): 0,
    },
    default=0,
    doc='Lower refinery capacity',
)
model.CAPU = Param(
    model.r,
    model.m,
    model.tp,
    initialize={
        ('r1', 'm1', 'tp1'): 400,
        ('r2', 'm1', 'tp1'): 0,
        ('r3', 'm1', 'tp1'): 0,
    },
    default=0,
    doc='Upper refinery capacity',
)

model.DEM = Param(
    model.p,
    model.c,
    model.sc,
    model.tp,
    initialize={
        ('p1', 'c1', 'SC1', 'tp1'): 24,
        ('p1', 'c1', 'SC2', 'tp1'): 30,
        ('p1', 'c1', 'SC3', 'tp1'): 36,
        ('p1', 'c1', 'SC4', 'tp1'): 24,
        ('p1', 'c1', 'SC5', 'tp1'): 30,
        ('p1', 'c1', 'SC6', 'tp1'): 36,
        ('p1', 'c1', 'SC7', 'tp1'): 24,
        ('p1', 'c1', 'SC8', 'tp1'): 30,
        ('p1', 'c1', 'SC9', 'tp1'): 36,
    },
    default=0,
    doc='Domestic demand',
)
model.DEM_oc = Param(
    model.p,
    model.oc,
    model.sc,
    model.tp,
    initialize={
        ('p1', 'oc1', 'SC1', 'tp1'): 24,
        ('p1', 'oc1', 'SC2', 'tp1'): 30,
        ('p1', 'oc1', 'SC3', 'tp1'): 36,
        ('p1', 'oc1', 'SC4', 'tp1'): 24,
        ('p1', 'oc1', 'SC5', 'tp1'): 30,
        ('p1', 'oc1', 'SC6', 'tp1'): 36,
        ('p1', 'oc1', 'SC7', 'tp1'): 24,
        ('p1', 'oc1', 'SC8', 'tp1'): 30,
        ('p1', 'oc1', 'SC9', 'tp1'): 36,
    },
    default=0,
    doc='Overseas demand',
)

model.DIS = Param(
    model.n,
    model.np,
    initialize={
        ('o_of', 'i_r1'): 10,
        ('o_te', 'i_oc1'): 10,
        ('o_te', 'i_b1'): 10,
        ('o_r1', 'i_te'): 10,
        ('o_r1', 'i_b1'): 10,
        ('o_b1', 'i_c1'): 10,
    },
    default=0,
    doc='Distances (km)',
)

model.DSR = Param(model.r, model.m, initialize={('r1', 'm1'): 0.5}, default=0, doc='Desulfurisation ratio')
model.EPPU = Param(model.p, model.tp, initialize={('p1', 'tp1'): 300}, doc='Extra product purchase limit')
model.EPUP = Param(model.p, model.te, model.tp, initialize={('p1', 'te1', 'tp1'): 50}, doc='Extra product price')

model.IVU = Param(model.m, model.r, model.tp, initialize={('m1', 'r1', 'tp1'): 100}, default=0, doc='Material inventory cap')
model.IVU_b = Param(model.p, model.b, model.tp, initialize={('p1', 'b1', 'tp1'): 100}, default=0, doc='Base inventory cap')
model.IVU_te = Param(model.p, model.te, model.tp, initialize={('p1', 'te1', 'tp1'): 100}, default=0, doc='Terminal inventory cap')

model.IVUP = Param(model.m, model.r, model.tp, initialize={('m1', 'r1', 'tp1'): 100}, default=0, doc='Material holding cost')
model.IVUP_b = Param(model.p, model.b, model.tp, initialize={('p1', 'b1', 'tp1'): 100}, default=0, doc='Base holding cost')
model.IVUP_te = Param(model.p, model.te, model.tp, initialize={('p1', 'te1', 'tp1'): 100}, default=0, doc='Terminal holding cost')

model.MPU = Param(model.m, model.tp, initialize={('m1', 'tp1'): 150}, doc='Material procurement limit')
model.MUP = Param(model.m, model.te, model.tp, initialize={('m1', 'te1', 'tp1'): 800}, doc='Material price at terminal')
model.MUP_of = Param(model.m, model.of, model.tp, initialize={('m1', 'of1', 'tp1'): 800}, doc='Material price at oil field')

model.MTUP = Param(
    model.m,
    model.n,
    model.np,
    model.tr,
    model.tp,
    initialize={
        ('m1', 'o_of', 'i_r1', 'tr1', 'tp1'): 85,
        ('m1', 'o_te', 'i_oc1', 'tr1', 'tp1'): 85,
        ('m1', 'o_te', 'i_b1', 'tr1', 'tp1'): 85,
        ('m1', 'o_r1', 'i_te', 'tr1', 'tp1'): 85,
        ('m1', 'o_r1', 'i_b1', 'tr1', 'tp1'): 85,
        ('m1', 'o_b1', 'i_c1', 'tr1', 'tp1'): 85,
    },
    default=0,
    doc='Material transport price (per km-ton)',
)

model.PTUP = Param(
    model.p,
    model.n,
    model.np,
    model.tr,
    model.tp,
    initialize={
        ('p1', 'o_of', 'i_r1', 'tr1', 'tp1'): 10,
        ('p1', 'o_te', 'i_oc1', 'tr1', 'tp1'): 10,
        ('p1', 'o_te', 'i_b1', 'tr1', 'tp1'): 10,
        ('p1', 'o_r1', 'i_te', 'tr1', 'tp1'): 10,
        ('p1', 'o_r1', 'i_b1', 'tr1', 'tp1'): 10,
        ('p1', 'o_b1', 'i_c1', 'tr1', 'tp1'): 10,
    },
    default=0,
    doc='Product transport price (per km-ton)',
)

model.PUP = Param(
    model.p,
    model.te,
    model.sc,
    model.tp,
    initialize={
        ('p1', 'te1', 'SC1', 'tp1'): 936,
        ('p1', 'te1', 'SC2', 'tp1'): 936,
        ('p1', 'te1', 'SC3', 'tp1'): 936,
        ('p1', 'te1', 'SC4', 'tp1'): 1170,
        ('p1', 'te1', 'SC5', 'tp1'): 1170,
        ('p1', 'te1', 'SC6', 'tp1'): 1170,
        ('p1', 'te1', 'SC7', 'tp1'): 1404,
        ('p1', 'te1', 'SC8', 'tp1'): 1404,
        ('p1', 'te1', 'SC9', 'tp1'): 1404,
    },
    default=0,
    doc='Selling price at terminal',
)
model.PUP_b = Param(
    model.p,
    model.b,
    model.sc,
    model.tp,
    initialize={
        ('p1', 'b1', 'SC1', 'tp1'): 936,
        ('p1', 'b1', 'SC2', 'tp1'): 936,
        ('p1', 'b1', 'SC3', 'tp1'): 936,
        ('p1', 'b1', 'SC4', 'tp1'): 1170,
        ('p1', 'b1', 'SC5', 'tp1'): 1170,
        ('p1', 'b1', 'SC6', 'tp1'): 1170,
        ('p1', 'b1', 'SC7', 'tp1'): 1404,
        ('p1', 'b1', 'SC8', 'tp1'): 1404,
        ('p1', 'b1', 'SC9', 'tp1'): 1404,
    },
    default=0,
    doc='Selling price at base',
)

model.QBU = Param(model.p, model.c, model.tp, initialize={('p1', 'c1', 'tp1'): 500}, doc='Domestic backlog limit')
model.QBU_oc = Param(model.p, model.oc, model.tp, initialize={('p1', 'oc1', 'tp1'): 500}, doc='Overseas backlog limit')
model.QSU = Param(model.p, model.c, model.tp, initialize={('p1', 'c1', 'tp1'): 500}, doc='Domestic surplus limit')
model.QSU_oc = Param(model.p, model.oc, model.tp, initialize={('p1', 'oc1', 'tp1'): 500}, doc='Overseas surplus limit')

model.ROUP = Param(
    model.r,
    model.m,
    model.tp,
    initialize={
        ('r1', 'm1', 'tp1'): 50,
        ('r2', 'm1', 'tp1'): 0,
        ('r3', 'm1', 'tp1'): 0,
    },
    default=0,
    doc='Refinery operation cost',
)
model.SC_m = Param(model.m, model.tp, initialize={('m1', 'tp1'): 50}, doc='Sulfur content material')
model.SC_p = Param(model.p, model.tp, initialize={('p1', 'tp1'): 50}, doc='Sulfur content product')
model.SUR = Param(model.p, model.tp, initialize={('p1', 'tp1'): 30}, doc='Surplus penalty')

model.TCAU = Param(
    model.n,
    model.np,
    model.tr,
    model.tp,
    initialize={
        ('o_of', 'i_r1', 'tr1', 'tp1'): 1000,
        ('o_te', 'i_oc1', 'tr1', 'tp1'): 1000,
        ('o_te', 'i_b1', 'tr1', 'tp1'): 1000,
        ('o_r1', 'i_te', 'tr1', 'tp1'): 1000,
        ('o_r1', 'i_b1', 'tr1', 'tp1'): 1000,
        ('o_b1', 'i_c1', 'tr1', 'tp1'): 1000,
    },
    default=0,
    doc='Transport capacity upper bound',
)

model.YDR = Param(model.r, model.m, model.p, initialize={('r1', 'm1', 'p1'): 1}, default=0, doc='Yield ratio')
model.YDR_tp = Param(model.r, model.m, model.tp, initialize={('r1', 'm1', 'tp1'): 1}, default=0, doc='Yield ratio (time specific)')

model.CCOEF = Param(
    model.tr,
    initialize={'tr1': 5304, 'tr2': 5330, 'tr3': 5928, 'tr4': 5980},
    doc='Transport emission factor',
)
model.EC = Param(model.r, initialize={'r1': 79, 'r2': 492, 'r3': 329}, doc='Refinery emission factor')

model.PROB = Param(
    model.sc,
    initialize={
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
        'SC1': 1,
        'SC2': 1,
        'SC3': 1,
        'SC4': 1,
        'SC5': 1,
        'SC6': 1,
        'SC7': 1,
        'SC8': 1,
        'SC9': 1,
    },
    default=0,
    doc='Scenario probability',
)

# -----------------------------------------------------------------------------
# Decision variables
# -----------------------------------------------------------------------------
model.qps_oc = Var(model.p, model.oc, model.te, model.sc, model.tp, domain=NonNegativeReals)
model.qps = Var(model.p, model.c, model.b, model.sc, model.tp, domain=NonNegativeReals)
model.qmp = Var(model.m, model.te, model.r, model.tp, domain=NonNegativeReals)
model.qmp_of = Var(model.m, model.of, model.r, model.tp, domain=NonNegativeReals)
model.qmtr = Var(model.m, model.n, model.np, model.tr, model.tp, domain=NonNegativeReals)
model.qmo = Var(model.r, model.m, model.sc, model.tp, domain=NonNegativeReals)
model.qmsto = Var(model.m, model.r, model.sc, model.tp, domain=NonNegativeReals)
model.qpsto = Var(model.p, model.te, model.sc, model.tp, domain=NonNegativeReals)
model.qpsto_b = Var(model.p, model.b, model.sc, model.tp, domain=NonNegativeReals)
model.qptr = Var(model.p, model.n, model.np, model.tr, model.sc, model.tp, domain=NonNegativeReals)
model.qepp = Var(model.p, model.te, model.sc, model.tp, domain=NonNegativeReals)
model.qsp = Var(model.p, model.c, model.sc, model.tp, domain=NonNegativeReals)
model.qsp_oc = Var(model.p, model.oc, model.sc, model.tp, domain=NonNegativeReals)
model.qbp = Var(model.p, model.c, model.sc, model.tp, domain=NonNegativeReals)
model.qbp_oc = Var(model.p, model.oc, model.sc, model.tp, domain=NonNegativeReals)
model.qpte = Var(model.p, model.r, model.te, model.sc, model.tp, domain=NonNegativeReals)
model.qpb = Var(model.p, model.r, model.b, model.sc, model.tp, domain=NonNegativeReals)
model.qepb = Var(model.p, model.b, model.te, model.sc, model.tp, domain=NonNegativeReals)

model.iqsp = Var(model.p, model.c, model.sc, model.tp, domain=Binary)
model.iqsp_oc = Var(model.p, model.oc, model.sc, model.tp, domain=Binary)
model.iqbp = Var(model.p, model.c, model.sc, model.tp, domain=Binary)
model.iqbp_oc = Var(model.p, model.oc, model.sc, model.tp, domain=Binary)

# -----------------------------------------------------------------------------
# Objective function: maximise expected profit
# -----------------------------------------------------------------------------

def objective_rule(model):
    revenue = sum(
        model.PROB[sc]
        * (
            sum(
                model.PUP[p, te, sc, tp] * model.qps_oc[p, oc, te, sc, tp]
                for p in model.p
                for oc in model.oc
                for te in model.te
                for tp in model.tp
            )
            + sum(
                model.PUP_b[p, b, sc, tp] * model.qps[p, c, b, sc, tp]
                for p in model.p
                for c in model.c
                for b in model.b
                for tp in model.tp
            )
        )
        for sc in model.sc
    )

    scenario_costs = sum(
        model.PROB[sc]
        * (
            sum(model.ROUP[r, m, tp] * model.qmo[r, m, sc, tp] for r in model.r for m in model.m for tp in model.tp)
            + sum(model.IVUP[m, r, tp] * model.qmsto[m, r, sc, tp] for m in model.m for r in model.r for tp in model.tp)
            + sum(model.IVUP_te[p, te, tp] * model.qpsto[p, te, sc, tp] for p in model.p for te in model.te for tp in model.tp)
            + sum(model.IVUP_b[p, b, tp] * model.qpsto_b[p, b, sc, tp] for p in model.p for b in model.b for tp in model.tp)
            + sum(
                model.PTUP[p, n, np, tr, tp] * model.DIS[n, np] * model.qptr[p, n, np, tr, sc, tp]
                for p in model.p
                for n in model.n
                for np in model.np
                for tr in model.tr
                for tp in model.tp
            )
            + sum(model.EPUP[p, te, tp] * model.qepp[p, te, sc, tp] for p in model.p for te in model.te for tp in model.tp)
            + sum(model.SUR[p, tp] * model.qsp[p, c, sc, tp] for p in model.p for c in model.c for tp in model.tp)
            + sum(model.SUR[p, tp] * model.qsp_oc[p, oc, sc, tp] for p in model.p for oc in model.oc for tp in model.tp)
            + sum(model.BCK[p, tp] * model.qbp[p, c, sc, tp] for p in model.p for c in model.c for tp in model.tp)
            + sum(model.BCK[p, tp] * model.qbp_oc[p, oc, sc, tp] for p in model.p for oc in model.oc for tp in model.tp)
        )
        for sc in model.sc
    )

    material_purchase = (
        sum(model.MUP[m, te, tp] * model.qmp[m, te, r, tp] for m in model.m for te in model.te for r in model.r for tp in model.tp)
        + sum(model.MUP_of[m, of_, tp] * model.qmp_of[m, of_, r, tp] for m in model.m for of_ in model.of for r in model.r for tp in model.tp)
    )

    material_transport = sum(
        model.MTUP[m, n, np, tr, tp] * model.DIS[n, np] * model.qmtr[m, n, np, tr, tp]
        for m in model.m
        for n in model.n
        for np in model.np
        for tr in model.tr
        for tp in model.tp
    )

    carbon_tax = (
        model.TAXC
        * sum(
            model.CCOEF[tr] * model.DIS[n, np] * model.qmtr[m, n, np, tr, tp]
            for m in model.m
            for n in model.n
            for np in model.np
            for tr in model.tr
            for tp in model.tp
        )
        + sum(
            model.PROB[sc]
            * (
                model.TAXC * sum(model.EC[r] * model.qmo[r, m, sc, tp] for r in model.r for m in model.m for tp in model.tp)
                + model.TAXC
                * sum(
                    model.CCOEF[tr] * model.DIS[n, np] * model.qptr[p, n, np, tr, sc, tp]
                    for p in model.p
                    for n in model.n
                    for np in model.np
                    for tr in model.tr
                    for tp in model.tp
                )
            )
            for sc in model.sc
        )
    )

    expected_profit = revenue - (material_purchase + material_transport + carbon_tax + scenario_costs)
    return expected_profit


model.Obj = Objective(rule=objective_rule, sense=maximize)

# -----------------------------------------------------------------------------
# Constraints
# -----------------------------------------------------------------------------

def material_balance_rule(model, m, r, tp, sc):
    inflow = sum(model.qmp[m, te, r, tp] for te in model.te) + sum(model.qmp_of[m, of_, r, tp] for of_ in model.of)
    if model.tp.ord(tp) > 1:
        inflow += model.qmsto[m, r, sc, model.tp.prev(tp)]
    return inflow == model.qmo[r, m, sc, tp] + model.qmsto[m, r, sc, tp]


model.MaterialBalance = Constraint(model.m, model.r, model.tp, model.sc, rule=material_balance_rule)


def transport_capacity_rule(model, n, np, tr, tp):
    return (
        sum(model.qmtr[m, n, np, tr, tp] for m in model.m)
        + sum(model.qptr[p, n, np, tr, sc, tp] for p in model.p for sc in model.sc)
        <= model.TCAU[n, np, tr, tp]
    )


model.TransportCapacity = Constraint(model.n, model.np, model.tr, model.tp, rule=transport_capacity_rule)


def terminal_procurement_flow_rule(model, m, te, r, tp):
    origin = origin_node[te]
    destination = destination_node[r]
    return model.qmp[m, te, r, tp] == sum(model.qmtr[m, origin, destination, tr, tp] for tr in model.tr)


model.TerminalToRefineryFlow = Constraint(model.m, model.te, model.r, model.tp, rule=terminal_procurement_flow_rule)


def oilfield_procurement_flow_rule(model, m, of_, r, tp):
    origin = origin_node[of_]
    destination = destination_node[r]
    return model.qmp_of[m, of_, r, tp] == sum(model.qmtr[m, origin, destination, tr, tp] for tr in model.tr)


model.OilfieldToRefineryFlow = Constraint(model.m, model.of, model.r, model.tp, rule=oilfield_procurement_flow_rule)


def refinery_to_base_flow_rule(model, p, r, b, sc, tp):
    origin = origin_node[r]
    destination = destination_node[b]
    return model.qpb[p, r, b, sc, tp] == sum(model.qptr[p, origin, destination, tr, sc, tp] for tr in model.tr)


model.RefineryToBaseFlow = Constraint(model.p, model.r, model.b, model.sc, model.tp, rule=refinery_to_base_flow_rule)


def refinery_to_terminal_flow_rule(model, p, r, te, sc, tp):
    origin = origin_node[r]
    destination = destination_node[te]
    return model.qpte[p, r, te, sc, tp] == sum(model.qptr[p, origin, destination, tr, sc, tp] for tr in model.tr)


model.RefineryToTerminalFlow = Constraint(model.p, model.r, model.te, model.sc, model.tp, rule=refinery_to_terminal_flow_rule)


def base_to_customer_flow_rule(model, p, b, c, sc, tp):
    origin = origin_node[b]
    destination = destination_node[c]
    return model.qps[p, c, b, sc, tp] == sum(model.qptr[p, origin, destination, tr, sc, tp] for tr in model.tr)


model.BaseToCustomerFlow = Constraint(model.p, model.b, model.c, model.sc, model.tp, rule=base_to_customer_flow_rule)


def terminal_to_overseas_flow_rule(model, p, te, oc, sc, tp):
    origin = origin_node[te]
    destination = destination_node[oc]
    return model.qps_oc[p, oc, te, sc, tp] == sum(model.qptr[p, origin, destination, tr, sc, tp] for tr in model.tr)


model.TerminalToOverseasFlow = Constraint(model.p, model.te, model.oc, model.sc, model.tp, rule=terminal_to_overseas_flow_rule)


def terminal_to_base_extra_flow_rule(model, p, te, b, sc, tp):
    origin = origin_node[te]
    destination = destination_node[b]
    return model.qepb[p, b, te, sc, tp] == sum(model.qptr[p, origin, destination, tr, sc, tp] for tr in model.tr)


model.TerminalToBaseExtraFlow = Constraint(model.p, model.te, model.b, model.sc, model.tp, rule=terminal_to_base_extra_flow_rule)


def product_balance_refinery_rule(model, m, p, r, tp, sc):
    production = model.qmo[r, m, sc, tp] * model.YDR[r, m, p]
    shipments = sum(model.qpte[p, r, te, sc, tp] for te in model.te) + sum(model.qpb[p, r, b, sc, tp] for b in model.b)
    return production == shipments


model.RefineryProductBalance = Constraint(model.m, model.p, model.r, model.tp, model.sc, rule=product_balance_refinery_rule)


def product_balance_terminal_rule(model, p, te, tp, sc):
    inflow = sum(model.qpte[p, r, te, sc, tp] for r in model.r) + model.qepp[p, te, sc, tp]
    if model.tp.ord(tp) > 1:
        inflow += model.qpsto[p, te, sc, model.tp.prev(tp)]
    outflow = (
        sum(model.qps_oc[p, oc, te, sc, tp] for oc in model.oc)
        + sum(model.qepb[p, b, te, sc, tp] for b in model.b)
        + model.qpsto[p, te, sc, tp]
    )
    return inflow == outflow


model.TerminalBalance = Constraint(model.p, model.te, model.tp, model.sc, rule=product_balance_terminal_rule)


def product_balance_base_rule(model, p, b, tp, sc):
    inflow = sum(model.qpb[p, r, b, sc, tp] for r in model.r) + sum(model.qepb[p, b, te, sc, tp] for te in model.te)
    if model.tp.ord(tp) > 1:
        inflow += model.qpsto_b[p, b, sc, model.tp.prev(tp)]
    outflow = sum(model.qps[p, c, b, sc, tp] for c in model.c) + model.qpsto_b[p, b, sc, tp]
    return inflow == outflow


model.BaseBalance = Constraint(model.p, model.b, model.tp, model.sc, rule=product_balance_base_rule)


def sulfur_content_rule(model, p, r, tp, sc):
    processed_sulfur = sum(
        model.qmo[r, m, sc, tp] * model.SC_m[m, tp] * (1 - model.DSR[r, m]) * model.YDR[r, m, p]
        for m in model.m
    )
    total_output = sum(model.qpte[p, r, te, sc, tp] for te in model.te) + sum(model.qpb[p, r, b, sc, tp] for b in model.b)
    return processed_sulfur <= model.SC_p[p, tp] * total_output


model.SulfurConstraint = Constraint(model.p, model.r, model.tp, model.sc, rule=sulfur_content_rule)


def procurement_capacity_material_rule(model, m, tp):
    return (
        sum(model.qmp[m, te, r, tp] for te in model.te for r in model.r)
        + sum(model.qmp_of[m, of_, r, tp] for of_ in model.of for r in model.r)
        <= model.MPU[m, tp]
    )


model.MaterialProcurementLimit = Constraint(model.m, model.tp, rule=procurement_capacity_material_rule)


def procurement_capacity_extra_rule(model, p, tp, sc):
    return sum(model.qepp[p, te, sc, tp] for te in model.te) <= model.EPPU[p, tp]


model.ExtraProcurementLimit = Constraint(model.p, model.tp, model.sc, rule=procurement_capacity_extra_rule)


def refinery_operation_bounds_lower_rule(model, r, m, tp, sc):
    return model.qmo[r, m, sc, tp] >= model.CAPL[r, m, tp]


def refinery_operation_bounds_upper_rule(model, r, m, tp, sc):
    return model.qmo[r, m, sc, tp] <= model.CAPU[r, m, tp]


model.RefineryLowerBound = Constraint(model.r, model.m, model.tp, model.sc, rule=refinery_operation_bounds_lower_rule)
model.RefineryUpperBound = Constraint(model.r, model.m, model.tp, model.sc, rule=refinery_operation_bounds_upper_rule)


def inventory_capacity_material_rule(model, m, r, sc, tp):
    return model.qmsto[m, r, sc, tp] <= model.IVU[m, r, tp]


def inventory_capacity_terminal_rule(model, p, te, sc, tp):
    return model.qpsto[p, te, sc, tp] <= model.IVU_te[p, te, tp]


def inventory_capacity_base_rule(model, p, b, sc, tp):
    return model.qpsto_b[p, b, sc, tp] <= model.IVU_b[p, b, tp]


model.MaterialInventoryCapacity = Constraint(model.m, model.r, model.sc, model.tp, rule=inventory_capacity_material_rule)
model.TerminalInventoryCapacity = Constraint(model.p, model.te, model.sc, model.tp, rule=inventory_capacity_terminal_rule)
model.BaseInventoryCapacity = Constraint(model.p, model.b, model.sc, model.tp, rule=inventory_capacity_base_rule)


def demand_external_rule(model, p, oc, te, sc, tp):
    return model.qps_oc[p, oc, te, sc, tp] == model.DEM_oc[p, oc, sc, tp] + model.qsp_oc[p, oc, sc, tp] - model.qbp_oc[p, oc, sc, tp]


model.ExternalDemand = Constraint(model.p, model.oc, model.te, model.sc, model.tp, rule=demand_external_rule)


def demand_internal_rule(model, p, c, b, sc, tp):
    return model.qps[p, c, b, sc, tp] == model.DEM[p, c, sc, tp] + model.qsp[p, c, sc, tp] - model.qbp[p, c, sc, tp]


model.InternalDemand = Constraint(model.p, model.c, model.b, model.sc, model.tp, rule=demand_internal_rule)


def backlog_limit_external_rule(model, p, oc, sc, tp):
    return model.qbp_oc[p, oc, sc, tp] <= model.iqbp_oc[p, oc, sc, tp] * model.QBU_oc[p, oc, tp]


def backlog_limit_internal_rule(model, p, c, sc, tp):
    return model.qbp[p, c, sc, tp] <= model.iqbp[p, c, sc, tp] * model.QBU[p, c, tp]


def surplus_limit_external_rule(model, p, oc, sc, tp):
    return model.qsp_oc[p, oc, sc, tp] <= model.iqsp_oc[p, oc, sc, tp] * model.QSU_oc[p, oc, tp]


def surplus_limit_internal_rule(model, p, c, sc, tp):
    return model.qsp[p, c, sc, tp] <= model.iqsp[p, c, sc, tp] * model.QSU[p, c, tp]


def logical_relation_external_rule(model, p, oc, sc, tp):
    return model.iqsp_oc[p, oc, sc, tp] + model.iqbp_oc[p, oc, sc, tp] <= 1


def logical_relation_internal_rule(model, p, c, sc, tp):
    return model.iqsp[p, c, sc, tp] + model.iqbp[p, c, sc, tp] <= 1


model.BacklogLimitOverseas = Constraint(model.p, model.oc, model.sc, model.tp, rule=backlog_limit_external_rule)
model.BacklogLimitDomestic = Constraint(model.p, model.c, model.sc, model.tp, rule=backlog_limit_internal_rule)
model.SurplusLimitOverseas = Constraint(model.p, model.oc, model.sc, model.tp, rule=surplus_limit_external_rule)
model.SurplusLimitDomestic = Constraint(model.p, model.c, model.sc, model.tp, rule=surplus_limit_internal_rule)
model.LogicalRelationOverseas = Constraint(model.p, model.oc, model.sc, model.tp, rule=logical_relation_external_rule)
model.LogicalRelationDomestic = Constraint(model.p, model.c, model.sc, model.tp, rule=logical_relation_internal_rule)

# -----------------------------------------------------------------------------
# Solve the model
# -----------------------------------------------------------------------------
model.dual = Suffix(direction=Suffix.IMPORT, optional=True)
model.slack = Suffix(direction=Suffix.IMPORT, optional=True)
model.rc = Suffix(direction=Suffix.IMPORT, optional=True)
model.iis = Suffix(direction=Suffix.IMPORT, optional=True)


def report_infeasibilities(model, logger, tol=1e-6):
    logger.info("=== Infeasibility diagnostics ===")

    if log_infeasible_bounds is not None:
        try:
            log_infeasible_bounds(model, tol=tol, log=logger)
        except Exception as exc:  # pragma: no cover - diagnostic safeguard
            logger.warning("Unable to evaluate bound feasibility: %s", exc)
    else:
        logger.info(
            "Pyomo infeasibility utility 'log_infeasible_bounds' is unavailable; "
            "skipping automatic bound diagnostics."
        )

    if log_infeasible_constraints is not None:
        try:
            log_infeasible_constraints(model, tol=tol, log=logger)
        except Exception as exc:  # pragma: no cover - diagnostic safeguard
            logger.warning("Unable to evaluate constraint feasibility: %s", exc)
    else:
        logger.info(
            "Pyomo infeasibility utility 'log_infeasible_constraints' is unavailable; "
            "skipping automatic constraint diagnostics."
        )

    if log_infeasible_binary is not None:
        try:
            log_infeasible_binary(model, log=logger)
        except Exception as exc:  # pragma: no cover - diagnostic safeguard
            logger.warning("Unable to evaluate binary feasibility: %s", exc)
    else:
        logger.info(
            "Pyomo infeasibility utility for binary variables is unavailable; "
            "performing manual check."
        )
        violations_found = False
        observed_binaries = False
        for var_data in model.component_data_objects(Var, active=True):
            is_binary = getattr(var_data, "is_binary", lambda: False)()
            if not is_binary:
                continue
            observed_binaries = True
            var_val = var_data.value
            if var_val is None:
                continue
            if var_val < -tol or var_val > 1 + tol:
                violations_found = True
                logger.error(
                    "Binary variable %s has infeasible value %.6f (outside [0, 1])",
                    var_data.name,
                    var_val,
                )
        if not observed_binaries:
            logger.info("No active binary variables found to inspect.")
        elif not violations_found:
            logger.info("No binary infeasibilities detected via manual check.")

    for var_data in model.component_data_objects(Var, active=True):
        lb = var_data.lb
        ub = var_data.ub
        if lb is not None and ub is not None and lb > ub + tol:
            logger.error(
                "Variable %s has inconsistent bounds: lower %.6f > upper %.6f",
                var_data.name,
                lb,
                ub,
            )

    try:
        iis_items = list(model.iis.items())
    except Exception:  # pragma: no cover - diagnostic safeguard
        iis_items = []

    if iis_items:
        logger.info("IIS entries identified by the solver:")
        for component, flag in iis_items:
            if not flag:
                continue
            parent = component.parent_component()
            ctype = parent.ctype
            name = component.name
            if ctype is Constraint:
                try:
                    lower = value(component.lower) if component.lower is not None else None
                except Exception:
                    lower = component.lower
                try:
                    upper = value(component.upper) if component.upper is not None else None
                except Exception:
                    upper = component.upper
                logger.info(
                    "  Constraint %s flagged (indicator=%s, lower=%s, upper=%s)",
                    name,
                    flag,
                    lower,
                    upper,
                )
            elif ctype is Var:
                logger.info(
                    "  Variable %s flagged (indicator=%s, bounds=(%s, %s))",
                    name,
                    flag,
                    component.lb,
                    component.ub,
                )
            else:
                logger.info("  Component %s flagged (indicator=%s)", name, flag)
    else:
        logger.info("Solver did not return IIS information.")


preferred_solvers = ['cplex', 'cplex_direct', 'glpk']
solver = None
solver_name = None
for name in preferred_solvers:
    try:
        candidate = SolverFactory(name)
    except Exception:  # pragma: no cover - solver availability guard
        continue
    if candidate is not None and candidate.available(False):
        solver = candidate
        solver_name = name
        break

if solver is None:
    raise RuntimeError('No suitable solver (CPLEX or GLPK) is available in the environment.')

print(f'Using solver: {solver_name}')

solve_kwargs = dict(tee=True)
if solver_name == 'cplex':
    solve_kwargs['suffixes'] = ['dual', 'slack', 'rc', 'iis']
    solve_kwargs['logfile'] = 'cplex.log'
elif solver_name == 'cplex_direct':
    solve_kwargs['suffixes'] = ['dual', 'slack', 'rc', 'iis']

retry_kwargs = dict(tee=True)
if solver_name == 'cplex':
    retry_kwargs['logfile'] = 'cplex.log'

try:
    result = solver.solve(model, **solve_kwargs)
except TypeError:
    solve_kwargs.pop('suffixes', None)
    solve_kwargs.pop('logfile', None)
    solve_kwargs = retry_kwargs
    result = solver.solve(model, **solve_kwargs)
except RuntimeError as exc:
    if 'suffix=iis' in str(exc):
        print('Solver was unable to provide IIS suffix information; retrying without IIS request.')
        solve_kwargs = retry_kwargs
        result = solver.solve(model, **solve_kwargs)
    else:
        raise

termination = result.solver.termination_condition

if termination == TerminationCondition.optimal:
    print('Model solved optimally.')
elif termination == TerminationCondition.infeasible:
    print('Model is infeasible.')
    report_infeasibilities(model, diagnostic_logger)
else:
    print(f'Model status: {termination}')
    if termination in {TerminationCondition.feasible, TerminationCondition.locallyOptimal}:
        print('A feasible solution was returned by the solver.')

has_solution = termination in {
    TerminationCondition.optimal,
    TerminationCondition.feasible,
    TerminationCondition.locallyOptimal,
}

if has_solution:
    for var in model.component_objects(Var, active=True):
        has_value = False
        for index in var:
            var_value = var[index].value
            if var_value is not None and abs(var_value) > 1e-6:
                if not has_value:
                    print(f"\nVariable {var.name}:")
                    has_value = True
                print(f"  {index}: {var_value:.4f}")
else:
    print('Variable values are unavailable because the solver did not return a feasible solution.')
