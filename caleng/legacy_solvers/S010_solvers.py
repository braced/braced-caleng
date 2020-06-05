from caleng.parts import bolts, loads, reports, steel
from decimal import Decimal as D
from caleng.parts.unit_registry import *


# S010_EC3 SOLVER
def S010_EC3(parts):
    # Report and results manager
    rp = reports.Report(parts['calc'])

    # Setting up parts
    flange_bolt = bolts.EuroBolt(parts['flange_bolt'], rp)
    flange_bolt_array = bolts.ShearBoltArray(
        parts['flange_bolt_array'], flange_bolt, rp)

    web_bolt = bolts.EuroBolt(parts['web_bolt'], rp)
    web_bolt_array = bolts.ShearBoltArray(
        parts['web_bolt_array'], web_bolt, rp)

    flange_cover_plate = steel.BoltedPlate(parts['flange_cover_plate'], rp)
    web_cover_plate = steel.BoltedPlate(parts['web_cover_plate'], rp)

    bottom_column = steel.Profile(parts['bottom_column_profile'], rp)
    top_column = steel.Profile(parts['top_column_profile'], rp)
    if bottom_column.mat_db_profile.h > top_column.mat_db_profile.h:
        biggest_column = bottom_column
    else:
        biggest_column = top_column

    # SOME BACKEND COMPROBATIONS ABOUT PROFILES
    if bottom_column.profile_type != top_column.profile_type:
        raise Exception("Bottom column and top column must be same type"
                        ", prolly there is a frontend error")

    bottom_column.bolt_the_flange(flange_bolt_array, flange_cover_plate, rp)
    bottom_column.bolt_the_web(web_bolt_array, web_cover_plate, rp)
    top_column.bolt_the_flange(flange_bolt_array, flange_cover_plate, rp)
    top_column.bolt_the_web(web_bolt_array, web_cover_plate, rp)

    if bottom_column.profile_type == "U" and\
            bottom_column.name != top_column.name:
        width_diff = bottom_column.mat_db_profile.b -\
            top_column.mat_db_profile.b
        if width_diff > 0:
            bf = bottom_column.bolted_flange
            bf.e1_main = bf.e1_main - width_diff / 2  # web side
            bf.e1_other = bf.e1_other + width_diff / 2  # free side
        else:
            bf = top_column.bolted_flange
            bf.e1_main = bf.e1_main + width_diff / 2
            bf.e1_other = bf.e1_other - width_diff / 2
        if bf.e1_main != bf_e1_other:
            bf.is_e1_sym = False

    sls_forces = loads.ForcesSet(parts['sls_force'], rp)
    uls_forces = loads.ForcesSet(parts['uls_force'], rp)

    # Generating positioned forces. Needed 4 checkn' that cover plates.
    joint_gap = Q(parts['main_extra_data'].joint_gap, 'mm')
    zero = Q(D(0), 'mm')
    flange_ecc = flange_bolt_array.p2_sum() / 2 +\
        flange_cover_plate.e2_other + joint_gap
    web_ecc = web_bolt_array.p2_sum() / 2 +\
        web_cover_plate.e2_other + joint_gap
    flange_sls, web_sls = sls_forces.from_eccentricity(
        - flange_ecc, zero, zero, None, None
    ).get_flange_and_web_tuple(biggest_column, rp)
    flange_uls, web_uls = uls_forces.from_eccentricity(
        - web_ecc, zero, zero, None, None
    ).get_flange_and_web_tuple(biggest_column, rp)

    # # set the conected plate so the snug front plate solver can work
    flange_bolt_array.connected_plate = flange_cover_plate
    web_bolt_array.connected_plate = web_cover_plate

    # Solving
    flange_ok = flange_bolt_array.check(flange_sls, flange_uls, rp) &\
        flange_cover_plate.check(flange_bolt_array, flange_uls, rp)

    web_ok = web_bolt_array.check(web_sls, web_uls, rp) &\
        web_cover_plate.check(web_bolt_array, web_uls, rp)

    if bottom_column.name == top_column.name:
        # Then we dont need to check both columns
        columns_ok =\
            bottom_column.bolted_flange.check(flange_uls, rp) &\
            bottom_column.bolted_web.check(web_uls, rp)
    else:
        columns_ok =\
            bottom_column.bolted_flange.check(flange_uls, rp) &\
            bottom_column.bolted_web.check(web_uls, rp) &\
            top_column.bolted_flange.check(flange_uls, rp) &\
            top_column.bolted_web.check(web_uls, rp)

    # Return report
    print(flange_ok, web_ok, columns_ok)
    if all([flange_ok, web_ok, columns_ok]):
        rp.set_safe()
    else:
        rp.set_unsafe()
    return rp
