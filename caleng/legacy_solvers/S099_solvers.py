from caleng.parts import bolts, loads, reports, steel


# S099_EC3 SOLVER
def S099_EC3(parts):
    # Report and results manager
    rp = reports.Report(parts['calc'])

    # Setting up parts
    bolt = bolts.EuroBolt(parts['main_bolt'], rp)
    bolt_group = bolts.ShearTensionBoltArray(
        parts['main_bolt_array'], bolt, rp)
    sls_forces = loads.ForcesSet(parts['sls_force'], rp)
    uls_forces = loads.ForcesSet(parts['uls_force'], rp)

    beam_profile = steel.Profile(parts['beam_profile'], rp)
    column_profile = steel.Profile(parts['column_profile'], rp)
    end_plate = steel.BoltedPlate(parts['end_plate'], rp)
    position = steel.SectionPosition(parts['main_position'], rp)
    position.profile = beam_profile
    position.bolt_array = bolt_group

    # set the conected plate so the snug front plate solver can work
    bolt_group.connected_plate = end_plate

    # Solving bolts

    if all([bolt_group.check(sls_forces, uls_forces, rp),
            beam_profile.check(rp), column_profile.check(rp),
            end_plate.check(bolt_group, uls_forces, rp),
            end_plate.check_collisions_legacy(bolt_group, beam_profile, position, rp),
            end_plate.check_t_stubs_legacy(
                bolt_group, uls_forces, beam_profile, position, rp)]):
        rp.set_safe()
    else:
        rp.set_unsafe()

    return rp
