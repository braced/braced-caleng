from caleng.parts import bolts, loads, reports, steel


# S007_EC3 MAIN SOLVER
def S007_EC3(conn):
    # Report and results manager
    rp = reports.Report(conn)

    # Setting up parts
    bolt = bolts.EuroBolt(conn.bolts['MAIN'], rp)
    bolt_group = bolts.ShearTensionBoltArray(
        conn.bolt_arrays['MAIN'], bolt, rp)
    sls_forces = loads.ForcesSet(conn.forces['SLS'], rp)
    uls_forces = loads.ForcesSet(conn.forces['ULS'], rp)

    top_column = steel.Profile(conn.profiles['ARRIVING'], rp)
    bottom_column = steel.Profile(conn.profiles['LANDING'], rp)
    end_plate = steel.BoltedPlate(conn.plates['END_PLATE'], rp)

    # set the conected plate so the snug front plate solver can work
    bolt_group.connected_plate = end_plate

    # Solving bolts

    if all([
        bolt_group.check(sls_forces, uls_forces, rp),
        bottom_column.check(rp), top_column.check(rp),
        end_plate.check(bolt_group, uls_forces, rp),
        end_plate.check_collisions(bolt_group, top_column, rp),
        end_plate.check_collisions(bolt_group, bottom_column, rp),
        end_plate.check_t_stubs(bolt_group, uls_forces, top_column, rp),
        end_plate.check_t_stubs(bolt_group, uls_forces, bottom_column, rp),
    ]):
        rp.set_safe()
    else:
        rp.set_unsafe()

    return rp
