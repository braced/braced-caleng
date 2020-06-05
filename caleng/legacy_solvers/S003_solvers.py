from caleng.parts import bolts, loads, reports, steel


# S003_EC3 SOLVER
def S003_EC3(parts):
    # Report and results manager
    rp = reports.Report(parts['calc'])

    # Setting up parts
    bolt = bolts.EuroBolt(parts['main_bolt'], rp)
    bolt_group = bolts.ShearBoltArray(parts['main_bolt_array'], bolt, rp)
    sls_forces = loads.ForcesSet(parts['sls_force'], rp)
    uls_forces = loads.ForcesSet(parts['uls_force'], rp)

    # Rotated forces to check plates and bolts
    rot_sls = sls_forces.rot90(2, 1, "SIDE_SLS", rp)
    rot_uls = uls_forces.rot90(2, 1, "SIDE_ULS", rp)

    bracing_profile = steel.Profile(parts['bracing_profile'], rp)
    landing_profile = steel.Profile(parts['landing_profile'], rp)
    gusset_plate = steel.BoltedPlate(parts['gusset_plate'], rp)

    bracing_profile.bolt_the_web(bolt_group, gusset_plate, rp)


    # e_dict needed to be passed to the web block tearing function.
    # e_dict = {
    #     "e1_main": gusset_plate.e1_main,
    #     "e2_main": gusset_plate.e2_main,
    #     "e1_other": gusset_plate.e1_other,
    #     "e2_other": gusset_plate.e1_other,
    # }

    # in_pipe_plate = steel.WeldedBoltedPlate(parts['in_pipe_plate'],
    #                                         rp, e_dict=e_dict)

    # Solving bolts

    if all([bolt_group.check(rot_sls, rot_uls, rp),
            # bracing_profile.check(rp), landing_profile.check(rp),
            bracing_profile.bolted_web.check(rot_uls, rp),
            gusset_plate.check(bolt_group, rot_uls, rp)]):
        rp.set_safe()
    else:
        rp.set_unsafe()

    return rp
