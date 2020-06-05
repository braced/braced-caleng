from caleng.parts import bolts, loads, reports, steel


# P001_EC3 SOLVER
def P003_EC3(conn):
    # Report and results manager
    rp = reports.Report(conn)
    # Setting up parts
    bolt = bolts.EuroBolt(conn.bolts['MAIN'], rp)
    bolt_group = bolts.ShearBoltArray(conn.bolt_arrays['MAIN'], bolt, rp)
    sls_forces = loads.ForcesSet(conn.forces['SLS'], rp)
    uls_forces = loads.ForcesSet(conn.forces['ULS'], rp)
    profile = steel.Profile(conn.profiles['MAIN'], rp)
    plate = steel.BoltedPlate(conn.plates['END_PLATE'], rp)
    # set the conected plate so the snug front plate solver can work
    bolt_group.connected_plate = plate

    # Solving bolts and plate
    if bolt_group.check(sls_forces, uls_forces, rp) and\
            plate.check(bolt_group, uls_forces, rp) and\
            plate.check_collisions(bolt_group, profile, rp):
        rp.set_safe()
    else:
        rp.set_unsafe()

    return rp
