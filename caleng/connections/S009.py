from caleng.parts import bolts, loads, reports, steel


# S009_EC3 MAIN SOLVER
def S009_EC3(conn):
    # Report and results manager
    rp = reports.Report(conn)

    # Setting up parts
    bolt = bolts.EuroBolt(conn.bolts['MAIN'], rp)
    bolt_group = bolts.ShearTensionBoltArray(
        conn.bolt_arrays['MAIN'], bolt, rp)
    sls_forces = loads.ForcesSet(conn.forces['SLS'], rp)
    uls_forces = loads.ForcesSet(conn.forces['ULS'], rp)

    beam_2 = steel.Profile(conn.profiles['ARRIVING'], rp)
    beam_1 = steel.Profile(conn.profiles['LANDING'], rp)
    end_plate = steel.BoltedPlate(conn.plates['END_PLATE'], rp)

    # set the conected plate so the snug front plate solver can work
    bolt_group.connected_plate = end_plate

    # Solving bolts

    if all([
        bolt_group.check(sls_forces, uls_forces, rp),
        beam_1.check(rp), beam_2.check(rp),
        end_plate.check(bolt_group, uls_forces, rp),
        end_plate.check_collisions(bolt_group, beam_2, rp),
        end_plate.check_collisions(bolt_group, beam_1, rp),
        end_plate.check_t_stubs(bolt_group, uls_forces, beam_2, rp),
        end_plate.check_t_stubs(bolt_group, uls_forces, beam_1, rp),
    ]):
        rp.set_safe()
    else:
        rp.set_unsafe()

    return rp
