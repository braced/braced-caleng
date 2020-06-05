from caleng.parts import bolts, loads, reports, steel


# S004_EC3 MAIN SOLVER
def S004_EC3(conn):
    # Report and results manager
    rp = reports.Report(conn)

    # Setting up parts
    bolt = bolts.EuroBolt(conn.bolts['MAIN'], rp)
    bolt_group = bolts.ShearTensionBoltArray(
        conn.bolt_arrays['MAIN'], bolt, rp)
    sls_forces = loads.ForcesSet(conn.forces['SLS'], rp)
    uls_forces = loads.ForcesSet(conn.forces['ULS'], rp)
    bracs_forces = loads.ExtraBracingForces(
        conn.extra_data['arriving_bracings'], rp)

    # Now, computing the resultant forces
    sls_forces = bracs_forces.sum_to_this_sls(sls_forces, rp)
    uls_forces = bracs_forces.sum_to_this_uls(uls_forces, rp)

    beam_profile = steel.Profile(conn.profiles['ARRIVING'], rp)
    column_profile = steel.Profile(conn.profiles['LANDING'], rp)
    end_plate = steel.BoltedPlate(conn.plates['END_PLATE'], rp)

    # set the conected plate so the snug front plate solver can work
    bolt_group.connected_plate = end_plate

    # Solving bolts

    if all([bolt_group.check(sls_forces, uls_forces, rp),
            beam_profile.check(rp), column_profile.check(rp),
            end_plate.check(bolt_group, uls_forces, rp),
            end_plate.check_collisions(bolt_group, beam_profile, rp),
            end_plate.check_t_stubs(
                bolt_group, uls_forces, beam_profile, rp)]):
        rp.set_safe()
    else:
        rp.set_unsafe()

    return rp
