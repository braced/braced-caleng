from caleng.parts import bolts, loads, reports


# P001_EC3 SOLVER
def P001_EC3(parts):
    # Report and results manager
    rp = reports.Report(parts['calc'])
    # Setting up parts
    bolt = bolts.EuroBolt(parts['main_bolt'], rp)
    bolt_group = bolts.ShearBoltArray(parts['main_bolt_array'], bolt, rp)
    sls_forces = loads.ForcesSet(parts['sls_force'], rp)
    uls_forces = loads.ForcesSet(parts['uls_force'], rp)

    # Solving bolts
    if bolt_group.check(sls_forces, uls_forces, rp):
        rp.set_safe()
    else:
        rp.set_unsafe()

    return rp
