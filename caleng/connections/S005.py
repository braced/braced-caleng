# OJO AQUI CON LAS DIRECCIONES 1 y 2 DE LA BOLTED WEB
from caleng.parts import bolts, loads, reports, steel


# S005_EC3 SOLVER
def S005_EC3(conn):
    # Report and results manager
    rp = reports.Report(conn)

    # Setting up parts
    bolt = bolts.EuroBolt(conn.bolts['MAIN'], rp)
    bolt_group = bolts.ShearTensionBoltArray(
        conn.bolt_arrays['MAIN'], bolt, rp)
    sls_forces = loads.ForcesSet(conn.forces['SLS'], rp)
    uls_forces = loads.ForcesSet(conn.forces['ULS'], rp)

    beam_profile = steel.Profile(conn.profiles['ARRIVING'], rp)
    landing_profile = steel.Profile(conn.profiles['LANDING'], rp)
    end_plate = steel.BoltedPlate(conn.plates['END_PLATE'], rp)

    # set the conected plate so the snug front plate solver can work
    bolt_group.connected_plate = end_plate
    # If frontplate connected to U Beam Web:
    if conn.profiles['LANDING']['section_orientation'] in ['ANY', 'WEB']\
            and conn.profiles['LANDING']['profile_type'] == "U"\
            and not landing_profile.mat_db_profile.is_any_reference:
        U_bolted_web = steel.BoltedWeb(
            landing_profile,
            bolt_group,
            conn.plates['END_PLATE'],
            rp)
        U_bolted_web_checked = U_bolted_web.check(uls_forces, rp)
    else:
        U_bolted_web_checked = True  # Not needed OBVIAMENTE

    if all([U_bolted_web_checked,
            bolt_group.check(sls_forces, uls_forces, rp),
            beam_profile.check(rp), landing_profile.check(rp),
            end_plate.check(bolt_group, uls_forces, rp),
            end_plate.check_collisions(bolt_group, beam_profile, rp),
            end_plate.check_t_stubs(
                bolt_group, uls_forces, beam_profile, rp)
            ]):
        rp.set_safe()
    else:
        rp.set_unsafe()

    return rp
