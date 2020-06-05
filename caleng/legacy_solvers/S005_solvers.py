from caleng.parts import bolts, loads, reports, steel


# S005_EC3 SOLVER
def S005_EC3(parts):
    # Report and results manager
    rp = reports.Report(parts['calc'])

    # Setting up parts
    bolt = bolts.EuroBolt(parts['main_bolt'], rp)
    bolt_array = bolts.ShearTensionBoltArray(
        parts['main_bolt_array'], bolt, rp)
    sls_forces = loads.ForcesSet(parts['sls_force'], rp)
    uls_forces = loads.ForcesSet(parts['uls_force'], rp)

    # Now, computing the resultant forces

    beam_profile = steel.Profile(parts['beam_profile'], rp)
    landing_profile = steel.Profile(parts['landing_profile'], rp)
    end_plate = steel.BoltedPlate(parts['end_plate'], rp)
    position = steel.SectionPosition(parts['main_position'], rp)
    position.profile = beam_profile
    position.bolt_array = bolt_array

    # set the conected plate so the snug front plate solver can work
    bolt_array.connected_plate = end_plate

    # If frontplate connected to U Beam Web:
    if parts['main_extra_data'].U_beam_position in ['ANY', 'WEB']\
            and parts['landing_profile'].profile_type == "U"\
            and not parts['main_extra_data'].dont_check_U_web:
        U_bolted_web = steel.BoltedWeb(
            landing_profile,
            bolt_array,
            parts['end_plate'],
            rp)
        U_bolted_web_checked = U_bolted_web.check(uls_forces, rp)
    else:
        U_bolted_web_checked = True  # Not needed OBVIAMENTE

    if all([U_bolted_web_checked,
            bolt_array.check(sls_forces, uls_forces, rp),
            beam_profile.check(rp), landing_profile.check(rp),
            end_plate.check(bolt_array, uls_forces, rp),
            end_plate.check_collisions_legacy(bolt_array, beam_profile, position, rp),
            end_plate.check_t_stubs_legacy(
                bolt_array, uls_forces, beam_profile, position, rp)
            ]):
        rp.set_safe()
    else:
        rp.set_unsafe()

    return rp
