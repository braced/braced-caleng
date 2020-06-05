from caleng.parts import bolts, loads, reports, steel
from caleng.parts.unit_registry import *
from decimal import Decimal as D


# S009_EC3 SOLVER
def S009_EC3(parts):
    # Report and results manager
    rp = reports.Report(parts['calc'])

    # Setting up parts
    bolt = bolts.EuroBolt(parts['main_bolt'], rp)
    bolt_array = bolts.ShearTensionBoltArray(
        parts['main_bolt_array'], bolt, rp)
    sls_forces = loads.ForcesSet(parts['sls_force'], rp)
    uls_forces = loads.ForcesSet(parts['uls_force'], rp)

    beam_1 = steel.Profile(parts['beam_1_profile'], rp)
    beam_2 = steel.Profile(parts['beam_2_profile'], rp)
    end_plate = steel.BoltedPlate(parts['end_plate'], rp)

    side_gap = parts['main_extra_data'].side_gap
    # g1 = plate.h / 2 - beam.h / 2 - side_gap
    beam1_g1 = end_plate.length.magnitude / 2 - \
        beam_1.mat_db_profile.h / 2 - side_gap
    position1 = steel.SectionPosition.from_g1(beam1_g1, rp)
    position1.profile = beam_1
    position1.bolt_array = bolt_array
    beam2_g1 = end_plate.length.magnitude / 2 - \
        beam_2.mat_db_profile.h / 2 - side_gap
    position2 = steel.SectionPosition.from_g1(beam2_g1, rp)
    position2.profile = beam_2
    position2.bolt_array = bolt_array

    # set the conected plate so the snug front plate solver can work
    bolt_array.connected_plate = end_plate

    if all([bolt_array.check(sls_forces, uls_forces, rp),
            end_plate.check(bolt_array, uls_forces, rp),
            end_plate.check_collisions_legacy(bolt_array,
                                       beam_1, position1, rp),
            end_plate.check_collisions_legacy(bolt_array,
                                       beam_2, position2, rp),
            end_plate.check_t_stubs_legacy(bolt_array, uls_forces,
                                    beam_1, position1, rp),
            end_plate.check_t_stubs_legacy(bolt_array, uls_forces,
                                    beam_2, position2, rp)]):
        rp.set_safe()
    else:
        rp.set_unsafe()
    return rp
