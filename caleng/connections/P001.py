from caleng.parts import bolts, loads, reports


# P001_EC3 SOLVER
def P001_EC3(conn):
    # Report and results manager
    rp = reports.Report(conn)
    # Setting up parts
    bolt = bolts.EuroBolt(conn.bolts['MAIN'], rp)
    bolt_group = bolts.ShearBoltArray(conn.bolt_arrays['MAIN'], bolt, rp)
    sls_forces = loads.ForcesSet(conn.forces['SLS'], rp)
    uls_forces = loads.ForcesSet(conn.forces['ULS'], rp)

    # Solving bolts
    if bolt_group.check(sls_forces, uls_forces, rp):
        rp.set_safe()
    else:
        rp.set_unsafe()
    return rp
