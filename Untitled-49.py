from pyomo.environ import (Binary, ConcreteModel, Constraint, NonNegativeReals,
                           Objective, Param, Set, SolverFactory, Var, maximize)
from pyomo.opt import TerminationCondition

# -----------------------------------------------------------------------------
# Sets
# -----------------------------------------------------------------------------
model = ConcreteModel(name="Stochastic multi-echelon supply chain")

model.m = Set(initialize=['m1'], ordered=True, doc='Materials')
model.p = Set(initialize=['p1'], ordered=True, doc='Products')
model.tp = Set(initialize=['tp1'], ordered=True, doc='Time periods')
model.tr = Set(initialize=['tr1'], ordered=True, doc='Transportation tools')
model.sc = Set(initialize=['SC1'], ordered=True, doc='Scenarios')
model.b = Set(initialize=['b1'], ordered=True, doc='Distribution bases')
model.c = Set(initialize=['c1'], ordered=True, doc='Domestic customers')
model.oc = Set(initialize=['oc1'], ordered=True, doc='Overseas customers')
model.of = Set(initialize=['of1'], ordered=True, doc='Oil fields')
model.r = Set(initialize=['r1'], ordered=True, doc='Refineries')
model.te = Set(initialize=['te1'], ordered=True, doc='Terminals')

# Nodes that appear in transportation relations (o_: origin, i_: destination)
model.n = Set(initialize=['o_of', 'o_te', 'o_r1', 'o_b1', 'o_c1', 'o_oc1'], ordered=True)
model.np = Set(initialize=['i_of', 'i_te', 'i_r1', 'i_b1', 'i_c1', 'i_oc1'], ordered=True)

# Mapping utilities for translating facility identifiers to network nodes
origin_node = {
    'of1': 'o_of',
    'te1': 'o_te',
    'r1': 'o_r1',
    'b1': 'o_b1',
    'c1': 'o_c1',
    'oc1': 'o_oc1',
}
destination_node = {
    'of1': 'i_of',
    'te1': 'i_te',
    'r1': 'i_r1',
    'b1': 'i_b1',
    'c1': 'i_c1',
    'oc1': 'i_oc1',
}

# -----------------------------------------------------------------------------
# Parameters (data are taken from the shared Word/PDF resources)
# -----------------------------------------------------------------------------
model.BigM = Param(initialize=1e6, doc='Large constant')
model.TAXC = Param(initialize=10, doc='Carbon tax per ton of CO2')

model.BCK = Param(model.p, model.tp, initialize={('p1', 'tp1'): 50}, doc='Backlog penalty')
model.CAPL = Param(model.r, model.m, model.tp, initialize={('r1', 'm1', 'tp1'): 100}, doc='Lower refinery capacity')
model.CAPU = Param(model.r, model.m, model.tp, initialize={('r1', 'm1', 'tp1'): 400}, doc='Upper refinery capacity')

model.DEM = Param(model.p, model.c, model.sc, model.tp,
                  initialize={('p1', 'c1', 'SC1', 'tp1'): 24},
                  default=0, doc='Domestic customer demand')
model.DEM_oc = Param(model.p, model.oc, model.sc, model.tp,
                     initialize={('p1', 'oc1', 'SC1', 'tp1'): 24},
                     default=0, doc='Overseas customer demand')

model.DIS = Param(model.n, model.np, initialize={
    ('o_of', 'i_r1'): 10,
    ('o_te', 'i_r1'): 0,
    ('o_r1', 'i_te'): 10,
    ('o_r1', 'i_b1'): 10,
    ('o_te', 'i_oc1'): 10,
    ('o_b1', 'i_c1'): 10,
}, default=0, doc='Distances between nodes (km)')

model.DSR = Param(model.r, model.m, initialize={('r1', 'm1'): 0.5}, doc='Desulfurisation ratio')
model.EPPU = Param(model.p, model.tp, initialize={('p1', 'tp1'): 300}, doc='Extra product purchase limit')
model.EPUP = Param(model.p, model.te, model.tp,
                   initialize={('p1', 'te1', 'tp1'): 50}, doc='Extra product unit price')

model.IVU = Param(model.m, model.r, model.tp,
                  initialize={('m1', 'r1', 'tp1'): 100}, doc='Material inventory capacity at refinery')
model.IVU_b = Param(model.p, model.b, model.tp,
                    initialize={('p1', 'b1', 'tp1'): 100}, doc='Product inventory capacity at base')
model.IVU_te = Param(model.p, model.te, model.tp,
                     initialize={('p1', 'te1', 'tp1'): 100}, doc='Product inventory capacity at terminal')

model.IVUP = Param(model.m, model.r, model.tp,
                   initialize={('m1', 'r1', 'tp1'): 100}, doc='Inventory holding cost at refinery')
model.IVUP_b = Param(model.p, model.b, model.tp,
                     initialize={('p1', 'b1', 'tp1'): 100}, doc='Inventory holding cost at base')
model.IVUP_te = Param(model.p, model.te, model.tp,
                      initialize={('p1', 'te1', 'tp1'): 100}, doc='Inventory holding cost at terminal')

model.MPU = Param(model.m, model.tp, initialize={('m1', 'tp1'): 150}, doc='Material procurement limit')
model.MUP = Param(model.m, model.te, model.tp,
                  initialize={('m1', 'te1', 'tp1'): 800}, doc='Material price at terminal')
model.MUP_of = Param(model.m, model.of, model.tp,
                     initialize={('m1', 'of1', 'tp1'): 800}, doc='Material price at oil field')

model.MTUP = Param(model.m, model.n, model.np, model.tr, model.tp, initialize={
    ('m1', 'o_of', 'i_r1', 'tr1', 'tp1'): 85,
    ('m1', 'o_te', 'i_r1', 'tr1', 'tp1'): 85,
}, default=0, doc='Transportation price for material (per km-ton)')

model.PTUP = Param(model.p, model.n, model.np, model.tr, model.tp, initialize={
    ('p1', 'o_r1', 'i_te', 'tr1', 'tp1'): 10,
    ('p1', 'o_r1', 'i_b1', 'tr1', 'tp1'): 10,
    ('p1', 'o_te', 'i_oc1', 'tr1', 'tp1'): 10,
    ('p1', 'o_b1', 'i_c1', 'tr1', 'tp1'): 10,
}, default=0, doc='Transportation price for product (per km-ton)')

model.PUP = Param(model.p, model.te, model.sc, model.tp,
                  initialize={('p1', 'te1', 'SC1', 'tp1'): 936},
                  default=0, doc='Selling price at terminal')
model.PUP_b = Param(model.p, model.b, model.sc, model.tp,
                    initialize={('p1', 'b1', 'SC1', 'tp1'): 936},
                    default=0, doc='Selling price at base')

model.QBU = Param(model.p, model.c, model.tp, initialize={('p1', 'c1', 'tp1'): 500}, doc='Backlog limit domestic')
model.QBU_oc = Param(model.p, model.oc, model.tp, initialize={('p1', 'oc1', 'tp1'): 500}, doc='Backlog limit overseas')
model.QSU = Param(model.p, model.c, model.tp, initialize={('p1', 'c1', 'tp1'): 500}, doc='Surplus limit domestic')
model.QSU_oc = Param(model.p, model.oc, model.tp, initialize={('p1', 'oc1', 'tp1'): 500}, doc='Surplus limit overseas')

model.ROUP = Param(model.r, model.m, model.tp,
                   initialize={('r1', 'm1', 'tp1'): 50}, doc='Refinery operation cost')
model.SC_m = Param(model.m, model.tp, initialize={('m1', 'tp1'): 50}, doc='Sulfur content material (ppm)')
model.SC_p = Param(model.p, model.tp, initialize={('p1', 'tp1'): 50}, doc='Sulfur content product (ppm)')
model.SUR = Param(model.p, model.tp, initialize={('p1', 'tp1'): 30}, doc='Surplus penalty')

model.TCAU = Param(model.n, model.np, model.tr, model.tp, initialize={
    ('o_of', 'i_r1', 'tr1', 'tp1'): 1000,
    ('o_te', 'i_r1', 'tr1', 'tp1'): 1000,
    ('o_r1', 'i_te', 'tr1', 'tp1'): 1000,
    ('o_r1', 'i_b1', 'tr1', 'tp1'): 1000,
    ('o_te', 'i_oc1', 'tr1', 'tp1'): 1000,
    ('o_b1', 'i_c1', 'tr1', 'tp1'): 1000,
}, default=0, doc='Transportation capacity upper bound')

model.YDR = Param(model.r, model.m, model.p, initialize={('r1', 'm1', 'p1'): 1}, doc='Yield ratio')
model.YDR_tp = Param(model.r, model.m, model.tp, initialize={('r1', 'm1', 'tp1'): 1}, doc='Yield ratio by time')

model.CCOEF = Param(model.tr, initialize={'tr1': 5304}, doc='Transport emission factor')
model.EC = Param(model.r, initialize={'r1': 79}, doc='Refinery emission factor')

model.PROB = Param(model.sc, initialize={'SC1': 1.0}, doc='Scenario probability')

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
    # Revenue per scenario
    revenue = sum(
        model.PROB[sc] * (
            sum(model.PUP[p, te, sc, tp] * model.qps_oc[p, oc, te, sc, tp]
                for p in model.p for oc in model.oc for te in model.te for tp in model.tp) +
            sum(model.PUP_b[p, b, sc, tp] * model.qps[p, c, b, sc, tp]
                for p in model.p for c in model.c for b in model.b for tp in model.tp)
        )
        for sc in model.sc
    )

    # Scenario dependent operating costs
    scenario_costs = sum(
        model.PROB[sc] * (
            # Refinery operating cost
            sum(model.ROUP[r, m, tp] * model.qmo[r, m, sc, tp]
                for r in model.r for m in model.m for tp in model.tp) +
            # Inventory costs
            sum(model.IVUP[m, r, tp] * model.qmsto[m, r, sc, tp]
                for m in model.m for r in model.r for tp in model.tp) +
            sum(model.IVUP_te[p, te, tp] * model.qpsto[p, te, sc, tp]
                for p in model.p for te in model.te for tp in model.tp) +
            sum(model.IVUP_b[p, b, tp] * model.qpsto_b[p, b, sc, tp]
                for p in model.p for b in model.b for tp in model.tp) +
            # Product transportation costs
            sum(model.PTUP[p, n, np, tr, tp] * model.DIS[n, np] * model.qptr[p, n, np, tr, sc, tp]
                for p in model.p for n in model.n for np in model.np for tr in model.tr for tp in model.tp) +
            # Extra product purchase cost
            sum(model.EPUP[p, te, tp] * model.qepp[p, te, sc, tp]
                for p in model.p for te in model.te for tp in model.tp) +
            # Surplus and backlog penalties
            sum(model.SUR[p, tp] * model.qsp[p, c, sc, tp]
                for p in model.p for c in model.c for tp in model.tp) +
            sum(model.SUR[p, tp] * model.qsp_oc[p, oc, sc, tp]
                for p in model.p for oc in model.oc for tp in model.tp) +
            sum(model.BCK[p, tp] * model.qbp[p, c, sc, tp]
                for p in model.p for c in model.c for tp in model.tp) +
            sum(model.BCK[p, tp] * model.qbp_oc[p, oc, sc, tp]
                for p in model.p for oc in model.oc for tp in model.tp)
        )
        for sc in model.sc
    )

    # Material purchase costs (scenario independent)
    material_purchase = (
        sum(model.MUP[m, te, tp] * model.qmp[m, te, r, tp]
            for m in model.m for te in model.te for r in model.r for tp in model.tp) +
        sum(model.MUP_of[m, of_, tp] * model.qmp_of[m, of_, r, tp]
            for m in model.m for of_ in model.of for r in model.r for tp in model.tp)
    )

    # Material transportation costs
    material_transport = sum(
        model.MTUP[m, n, np, tr, tp] * model.DIS[n, np] * model.qmtr[m, n, np, tr, tp]
        for m in model.m for n in model.n for np in model.np for tr in model.tr for tp in model.tp
    )

    # Carbon taxation (material transport, product transport, and refinery processing)
    carbon_tax = (
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

    expected_profit = revenue - (material_purchase + material_transport + carbon_tax + scenario_costs)
    return expected_profit


model.Obj = Objective(rule=objective_rule, sense=maximize)

# -----------------------------------------------------------------------------
# Constraints
# -----------------------------------------------------------------------------

def material_balance_rule(model, m, r, tp, sc):
    prev_tp = model.tp.prev(tp)
    inventory_prev = model.qmsto[m, r, sc, prev_tp] if prev_tp is not None else 0
    inflow = sum(model.qmp[m, te, r, tp] for te in model.te) + \
        sum(model.qmp_of[m, of_, r, tp] for of_ in model.of) + inventory_prev
    return inflow == model.qmo[r, m, sc, tp] + model.qmsto[m, r, sc, tp]


model.MaterialBalance = Constraint(model.m, model.r, model.tp, model.sc, rule=material_balance_rule)


def transport_capacity_rule(model, n, np, tr, tp):
    return (
        sum(model.qmtr[m, n, np, tr, tp] for m in model.m) +
        sum(model.qptr[p, n, np, tr, sc, tp] for p in model.p for sc in model.sc)
        <= model.TCAU[n, np, tr, tp]
    )


model.TransportCapacity = Constraint(model.n, model.np, model.tr, model.tp, rule=transport_capacity_rule)


def terminal_procurement_flow_rule(model, m, te, r, tp):
    origin = origin_node[te]
    destination = destination_node[r]
    return model.qmp[m, te, r, tp] == sum(model.qmtr[m, origin, destination, tr, tp] for tr in model.tr)


model.TerminalToRefineryFlow = Constraint(model.m, model.te, model.r, model.tp,
                                          rule=terminal_procurement_flow_rule)


def oilfield_procurement_flow_rule(model, m, of_, r, tp):
    origin = origin_node[of_]
    destination = destination_node[r]
    return model.qmp_of[m, of_, r, tp] == sum(model.qmtr[m, origin, destination, tr, tp] for tr in model.tr)


model.OilfieldToRefineryFlow = Constraint(model.m, model.of, model.r, model.tp,
                                          rule=oilfield_procurement_flow_rule)


def refinery_to_base_flow_rule(model, p, r, b, sc, tp):
    origin = origin_node[r]
    destination = destination_node[b]
    return model.qpb[p, r, b, sc, tp] == sum(model.qptr[p, origin, destination, tr, sc, tp] for tr in model.tr)


model.RefineryToBaseFlow = Constraint(model.p, model.r, model.b, model.sc, model.tp,
                                      rule=refinery_to_base_flow_rule)


def refinery_to_terminal_flow_rule(model, p, r, te, sc, tp):
    origin = origin_node[r]
    destination = destination_node[te]
    return model.qpte[p, r, te, sc, tp] == sum(model.qptr[p, origin, destination, tr, sc, tp] for tr in model.tr)


model.RefineryToTerminalFlow = Constraint(model.p, model.r, model.te, model.sc, model.tp,
                                          rule=refinery_to_terminal_flow_rule)


def base_to_customer_flow_rule(model, p, b, c, sc, tp):
    origin = origin_node[b]
    destination = destination_node[c]
    return model.qps[p, c, b, sc, tp] == sum(model.qptr[p, origin, destination, tr, sc, tp] for tr in model.tr)


model.BaseToCustomerFlow = Constraint(model.p, model.b, model.c, model.sc, model.tp,
                                      rule=base_to_customer_flow_rule)


def terminal_to_overseas_flow_rule(model, p, te, oc, sc, tp):
    origin = origin_node[te]
    destination = destination_node[oc]
    return model.qps_oc[p, oc, te, sc, tp] == sum(model.qptr[p, origin, destination, tr, sc, tp] for tr in model.tr)


model.TerminalToOverseasFlow = Constraint(model.p, model.te, model.oc, model.sc, model.tp,
                                          rule=terminal_to_overseas_flow_rule)


def terminal_to_base_extra_flow_rule(model, p, te, b, sc, tp):
    origin = origin_node[te]
    destination = destination_node[b]
    return model.qepb[p, b, te, sc, tp] == sum(model.qptr[p, origin, destination, tr, sc, tp] for tr in model.tr)


model.TerminalToBaseExtraFlow = Constraint(model.p, model.te, model.b, model.sc, model.tp,
                                           rule=terminal_to_base_extra_flow_rule)


def product_balance_refinery_rule(model, m, p, r, tp, sc):
    production = model.qmo[r, m, sc, tp] * model.YDR[r, m, p]
    shipments = sum(model.qpte[p, r, te, sc, tp] for te in model.te) + \
        sum(model.qpb[p, r, b, sc, tp] for b in model.b)
    return production == shipments


model.RefineryProductBalance = Constraint(model.m, model.p, model.r, model.tp, model.sc,
                                          rule=product_balance_refinery_rule)


def product_balance_terminal_rule(model, p, te, tp, sc):
    prev_tp = model.tp.prev(tp)
    inventory_prev = model.qpsto[p, te, sc, prev_tp] if prev_tp is not None else 0
    inflow = sum(model.qpte[p, r, te, sc, tp] for r in model.r) + model.qepp[p, te, sc, tp] + inventory_prev
    outflow = sum(model.qps_oc[p, oc, te, sc, tp] for oc in model.oc) + \
        sum(model.qepb[p, b, te, sc, tp] for b in model.b) + model.qpsto[p, te, sc, tp]
    return inflow == outflow


model.TerminalBalance = Constraint(model.p, model.te, model.tp, model.sc, rule=product_balance_terminal_rule)


def product_balance_base_rule(model, p, b, tp, sc):
    prev_tp = model.tp.prev(tp)
    inventory_prev = model.qpsto_b[p, b, sc, prev_tp] if prev_tp is not None else 0
    inflow = sum(model.qpb[p, r, b, sc, tp] for r in model.r) + \
        sum(model.qepb[p, b, te, sc, tp] for te in model.te) + inventory_prev
    outflow = sum(model.qps[p, c, b, sc, tp] for c in model.c) + model.qpsto_b[p, b, sc, tp]
    return inflow == outflow


model.BaseBalance = Constraint(model.p, model.b, model.tp, model.sc, rule=product_balance_base_rule)


def sulfur_content_rule(model, p, r, tp, sc):
    processed_sulfur = sum(
        model.qmo[r, m, sc, tp] * model.SC_m[m, tp] * (1 - model.DSR[r, m]) * model.YDR[r, m, p]
        for m in model.m
    )
    total_output = sum(model.qpte[p, r, te, sc, tp] for te in model.te) + \
        sum(model.qpb[p, r, b, sc, tp] for b in model.b)
    if total_output == 0:
        return processed_sulfur <= 0
    return processed_sulfur <= model.SC_p[p, tp] * total_output


model.SulfurConstraint = Constraint(model.p, model.r, model.tp, model.sc, rule=sulfur_content_rule)


def procurement_capacity_material_rule(model, m, tp):
    return sum(model.qmp[m, te, r, tp] for te in model.te for r in model.r) + \
        sum(model.qmp_of[m, of_, r, tp] for of_ in model.of for r in model.r) <= model.MPU[m, tp]


model.MaterialProcurementLimit = Constraint(model.m, model.tp, rule=procurement_capacity_material_rule)


def procurement_capacity_extra_rule(model, p, tp, sc):
    return sum(model.qepp[p, te, sc, tp] for te in model.te) <= model.EPPU[p, tp]


model.ExtraProcurementLimit = Constraint(model.p, model.tp, model.sc, rule=procurement_capacity_extra_rule)


def refinery_operation_bounds_lower_rule(model, r, m, tp, sc):
    return model.qmo[r, m, sc, tp] >= model.CAPL[r, m, tp]


def refinery_operation_bounds_upper_rule(model, r, m, tp, sc):
    return model.qmo[r, m, sc, tp] <= model.CAPU[r, m, tp]


model.RefineryLowerBound = Constraint(model.r, model.m, model.tp, model.sc,
                                      rule=refinery_operation_bounds_lower_rule)
model.RefineryUpperBound = Constraint(model.r, model.m, model.tp, model.sc,
                                      rule=refinery_operation_bounds_upper_rule)


def inventory_capacity_material_rule(model, m, r, sc, tp):
    return model.qmsto[m, r, sc, tp] <= model.IVU[m, r, tp]


model.MaterialInventoryCapacity = Constraint(model.m, model.r, model.sc, model.tp,
                                             rule=inventory_capacity_material_rule)


def inventory_capacity_terminal_rule(model, p, te, sc, tp):
    return model.qpsto[p, te, sc, tp] <= model.IVU_te[p, te, tp]


model.TerminalInventoryCapacity = Constraint(model.p, model.te, model.sc, model.tp,
                                             rule=inventory_capacity_terminal_rule)


def inventory_capacity_base_rule(model, p, b, sc, tp):
    return model.qpsto_b[p, b, sc, tp] <= model.IVU_b[p, b, tp]


model.BaseInventoryCapacity = Constraint(model.p, model.b, model.sc, model.tp,
                                         rule=inventory_capacity_base_rule)


def demand_external_rule(model, p, oc, te, sc, tp):
    return model.qps_oc[p, oc, te, sc, tp] == model.DEM_oc[p, oc, sc, tp] + \
        model.qsp_oc[p, oc, sc, tp] - model.qbp_oc[p, oc, sc, tp]


model.ExternalDemand = Constraint(model.p, model.oc, model.te, model.sc, model.tp,
                                  rule=demand_external_rule)


def demand_internal_rule(model, p, c, b, sc, tp):
    return model.qps[p, c, b, sc, tp] == model.DEM[p, c, sc, tp] + \
        model.qsp[p, c, sc, tp] - model.qbp[p, c, sc, tp]


model.InternalDemand = Constraint(model.p, model.c, model.b, model.sc, model.tp,
                                  rule=demand_internal_rule)


def backlog_limit_external_rule(model, p, oc, sc, tp):
    return model.qbp_oc[p, oc, sc, tp] <= model.iqbp_oc[p, oc, sc, tp] * model.QBU_oc[p, oc, tp]


model.BacklogLimitOverseas = Constraint(model.p, model.oc, model.sc, model.tp,
                                        rule=backlog_limit_external_rule)


def backlog_limit_internal_rule(model, p, c, sc, tp):
    return model.qbp[p, c, sc, tp] <= model.iqbp[p, c, sc, tp] * model.QBU[p, c, tp]


model.BacklogLimitDomestic = Constraint(model.p, model.c, model.sc, model.tp,
                                        rule=backlog_limit_internal_rule)


def surplus_limit_external_rule(model, p, oc, sc, tp):
    return model.qsp_oc[p, oc, sc, tp] <= model.iqsp_oc[p, oc, sc, tp] * model.QSU_oc[p, oc, tp]


model.SurplusLimitOverseas = Constraint(model.p, model.oc, model.sc, model.tp,
                                        rule=surplus_limit_external_rule)


def surplus_limit_internal_rule(model, p, c, sc, tp):
    return model.qsp[p, c, sc, tp] <= model.iqsp[p, c, sc, tp] * model.QSU[p, c, tp]


model.SurplusLimitDomestic = Constraint(model.p, model.c, model.sc, model.tp,
                                        rule=surplus_limit_internal_rule)


def logical_relation_external_rule(model, p, oc, sc, tp):
    return model.iqsp_oc[p, oc, sc, tp] + model.iqbp_oc[p, oc, sc, tp] <= 1


model.LogicalRelationOverseas = Constraint(model.p, model.oc, model.sc, model.tp,
                                           rule=logical_relation_external_rule)


def logical_relation_internal_rule(model, p, c, sc, tp):
    return model.iqsp[p, c, sc, tp] + model.iqbp[p, c, sc, tp] <= 1


model.LogicalRelationDomestic = Constraint(model.p, model.c, model.sc, model.tp,
                                           rule=logical_relation_internal_rule)

# -----------------------------------------------------------------------------
# Solve the model
# -----------------------------------------------------------------------------
solver = SolverFactory('glpk')
result = solver.solve(model, tee=True)

if result.solver.termination_condition == TerminationCondition.optimal:
    print('Model solved optimally.')
elif result.solver.termination_condition == TerminationCondition.infeasible:
    print('Model is infeasible.')
else:
    print(f'Model status: {result.solver.termination_condition}')

# Display non-zero variable values for inspection
for var in model.component_objects(Var, active=True):
    has_value = False
    for index in var:
        value = var[index].value
        if value is not None and abs(value) > 1e-6:
            if not has_value:
                print(f"\nVariable {var.name}:")
                has_value = True
            print(f"  {index}: {value:.4f}")
