from caleng.parts import bolts, loads, reports, steel


# S007_EC3 SOLVER
def S007_EC3(parts):
    # Report and results manager
    rp = reports.Report(parts['calc'])

    # Setting up parts
    bolt = bolts.EuroBolt(parts['main_bolt'], rp)
    bolt_array = bolts.ShearTensionBoltArray(
        parts['main_bolt_array'], bolt, rp)
    sls_forces = loads.ForcesSet(parts['sls_force'], rp)
    uls_forces = loads.ForcesSet(parts['uls_force'], rp)

    bottom_column = steel.Profile(parts['bottom_column_profile'], rp)
    top_column = steel.Profile(parts['top_column_profile'], rp)
    end_plate = steel.BoltedPlate(parts['end_plate'], rp)
    position = steel.SectionPosition(parts['main_position'], rp)
    position.profile = top_column
    position.bolt_array = bolt_array
    zero_position = steel.SectionPosition.centered()

    # set the conected plate so the snug front plate solver can work
    bolt_array.connected_plate = end_plate

    if all([
        bolt_array.check(sls_forces, uls_forces, rp),
        # bottom_column.check(rp), top_column.check(rp),  # NOT NEEDED
        end_plate.check(bolt_array, uls_forces, rp),
        end_plate.check_collisions_legacy(bolt_array,
                                   top_column, position, rp),
        end_plate.check_collisions_legacy(bolt_array,
                                   bottom_column, zero_position, rp),
        end_plate.check_t_stubs_legacy(bolt_array, uls_forces,
                                bottom_column, position, rp)
    ]):
        rp.set_safe()
    else:
        rp.set_unsafe()
    return rp
