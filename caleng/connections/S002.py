from caleng.parts import bolts, loads, reports, steel


# S002_EC3 SOLVER
def S002_EC3(conn):
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
    cover_plates = steel.BoltedPlate(conn.plates['COVER_PLATE'], rp)
    in_pipe_plate = steel.WeldedBoltedPlate(conn.plates['INPIPE_PLATE'], rp)
    in_pipe_plate.locked_edges = ['e1_main']
    pipe_stiffener = steel.WeldedPlate(conn.plates['PIPE_STIFFENER'], rp)

    # Solving bolts
    if all([bolt_group.check(rot_sls, rot_uls, rp),
            bracing_profile.check(rp), landing_profile.check(rp),
            cover_plates.check(bolt_group, rot_uls, rp),
            in_pipe_plate.check(bolt_group, rot_uls, rp),
            pipe_stiffener.check(rot_uls, rp)]):
        rp.set_safe()
    else:
        rp.set_unsafe()

    return rp
