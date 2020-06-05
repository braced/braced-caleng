from caleng.parts import bolts, loads, reports, steel


# S003_EC3 SOLVER
def S003_EC3(conn):
    # Report and results manager
    rp = reports.Report(conn)

    # Setting up parts
    bolt = bolts.EuroBolt(conn.bolts['MAIN'], rp)
    bolt_group = bolts.ShearBoltArray(conn.bolt_arrays['MAIN'], bolt, rp)
    sls_forces = loads.ForcesSet(conn.forces['SLS'], rp)
    uls_forces = loads.ForcesSet(conn.forces['ULS'], rp)

    # Rotated forces to check plates and bolts
    rot_sls = sls_forces.rot90(2, 1, "SIDE_SLS", rp)
    rot_uls = uls_forces.rot90(2, 1, "SIDE_ULS", rp)

    bracing_profile = steel.Profile(conn.profiles['ARRIVING'], rp)
    landing_profile = steel.Profile(conn.profiles['LANDING'], rp)
    gusset_plate = steel.BoltedPlate(conn.plates['GUSSET_PLATE'], rp)
    gusset_plate.locked_edges = ['e1_main']
    bracing_profile.bolt_the_web(bolt_group, gusset_plate, rp)

    if all([bolt_group.check(rot_sls, rot_uls, rp),
            bracing_profile.check(rp), landing_profile.check(rp),
            bracing_profile.bolted_web.check(rot_uls, rp),
            gusset_plate.check(bolt_group, rot_uls, rp)]):
        rp.set_safe()
    else:
        rp.set_unsafe()

    return rp
