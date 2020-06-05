from caleng.parts import bolts, loads, reports, steel, stiffeners
from caleng.parts.unit_registry import *
from decimal import Decimal as D


# def test():
#     heigh_from_h = Q(D(self.db_profile.h -
#                        extra_data.side_gap), 'mm')

#     if heigh_from_h != heigh_from_e_p and\
#             extra_data.angles in ["LS", "RS"]:
#         raise CalengCrash("BoltedWeb inconsistency: \n"
#                           "heigh_from_h {} != heigh_from_e_p {}".format(
#                               heigh_from_h,
#                               heigh_from_e_p,
#                           ))
#     else:
#         self.heigh = heigh_from_h


def S006_EC3(parts):
    """ Main S006_EC3 Solver """

    # Report and results manager
    rp = reports.Report(parts['calc'])

    # LOS BOLTS DEL ALMA DEL LANDING PROFILE EN EL CASO DE CLIP SE SUPONEN =s
    # HAY QUE PENSAR QUE SE HACE. SE CALCULA TAMBIEN??? FUCK!

    # Setting up common parts
    bolt = bolts.EuroBolt(parts['main_bolt'], rp)
    bolt_array = bolts.ShearTensionBoltArray(
        parts['main_bolt_array'], bolt, rp)
    sls_forces = loads.ForcesSet(parts['sls_force'], rp)
    uls_forces = loads.ForcesSet(parts['uls_force'], rp)
    beam_profile = steel.Profile(parts['beam_profile'], rp)
    landing_profile = steel.Profile(parts['landing_profile'], rp)

    # -LA- OBJECTS:
    #    - Beam web * +rp
    #    - Lateral bolts  * +rp
    #    - Lateral forces *
    #    - Clip Angle * +rp
    #    - Frontal bolts * +rp
    #    - Frontal forces *
    #    - Landing web * +rp
    if parts['main_extra_data'].angles in ["LA"]:
        bolted_web = steel.BoltedWeb(
            beam_profile,
            bolt_array,
            parts['ang_bolts_plate'],
            rp)
        bolted_angle = steel.BoltedClipAngle(
            parts['clip_profile'],
            parts['ang_bolts_plate'],
            rp)
        # FORCES
        lat_uls_forces = uls_forces.rot90(2, 3, "SIDE_ULS", None)
        lat_sls_forces = sls_forces.rot90(2, 3, "SIDE_SLS", None)
        ec1 = bolted_angle.dist_bolts_to_plate(bolt_array)
        ec2 = Q(D(0), 'mm')
        # ec3 = - ec1 asumes a simmetrical boltedclipangle...
        # let's see what happens with time but this is a fucking problem
        ec3 = - ec1
        front_uls_forces = uls_forces.from_eccentricity(
            ec1, ec2, ec3, "FRONT_ULS", None)
        front_sls_forces = sls_forces.from_eccentricity(
            ec1, ec2, ec3, "FRONT_SLS", None)

        # BOLT ARRAYS (SAME BOLT ARRAY TO BE CHECKED WITH BOTH FORCES)
        # WHY? BECAUSE L ANGLE PROFILE IS SUPOSED SYMMETRICAL !!!!
        bolt_array.connected_plate = bolted_angle
        lat_bolt_array = bolt_array
        front_bolt_array = bolt_array
        front_bolted_web = steel.BoltedWeb(
            landing_profile,
            bolt_array,
            parts['ang_bolts_plate'],
            rp)

        if all([
                bolted_web.check(lat_uls_forces, rp),
                lat_bolt_array.check(lat_sls_forces, lat_uls_forces, rp),
                bolted_angle.check(bolt_array, front_uls_forces, rp),
                front_bolt_array.check(front_sls_forces, front_uls_forces, rp),
                front_bolted_web.check(front_uls_forces, rp),
        ]):
            rp.set_safe()
        else:
            rp.set_unsafe()

    # -RA- OBJECTS:
    #    - Beam web * +rp
    #    - Lateral bolts  * +rp
    #    - Lateral forces *
    #    - Clip Angle * +rp
    #    - Frontal bolts * +rp
    #    - Frontal forces *
    #    - Landing web * +rp
    if parts['main_extra_data'].angles in ["RA"]:
        bolted_web = steel.BoltedWeb(
            beam_profile,
            bolt_array,
            parts['ang_bolts_plate'],
            rp)
        bolted_angle = steel.BoltedClipAngle(
            parts['clip_profile'],
            parts['ang_bolts_plate'],
            rp)
        # FORCES
        lat_uls_forces = uls_forces.rot90(2, 1, "SIDE_ULS", None)
        lat_sls_forces = sls_forces.rot90(2, 1, "SIDE_SLS", None)
        ec1 = bolted_angle.dist_bolts_to_plate(bolt_array)
        ec2 = Q(D(0), 'mm')
        # ec3 = ec1 asumes a simmetrical boltedclipangle...
        # let's see what happens with time but this is a fucking problem
        ec3 = ec1
        front_uls_forces = uls_forces.from_eccentricity(
            ec1, ec2, ec3, "FRONT_ULS", None)
        front_sls_forces = sls_forces.from_eccentricity(
            ec1, ec2, ec3, "FRONT_SLS", None)

        # BOLT ARRAYS (SAME BOLT ARRAY TO BE CHECKED WITH BOTH FORCES)
        # WHY? BECAUSE L ANGLE PROFILE IS SUPOSED SYMMETRICAL !!!!
        bolt_array.connected_plate = bolted_angle
        lat_bolt_array = bolt_array
        front_bolt_array = bolt_array
        front_bolted_web = steel.BoltedWeb(
            landing_profile,
            bolt_array,
            parts['ang_bolts_plate'],
            rp)

        if all([
                bolted_web.check(lat_uls_forces, rp),
                lat_bolt_array.check(lat_sls_forces, lat_uls_forces, rp),
                bolted_angle.check(bolt_array, front_uls_forces, rp),
                front_bolt_array.check(front_sls_forces, front_uls_forces, rp),
                front_bolted_web.check(front_uls_forces, rp),
        ]):
            rp.set_safe()
        else:
            rp.set_unsafe()

    # -BA- OBJECTS:
    #    - Beam web +rp *
    #    - Lateral bolts +rp *
    #    - Lateral forces *
    #    - Clip Angle Pair +rp *
    #    - Frontal bolts +rp *
    #    - Frontal forces *
    #    - Landing web +rp *
    if parts['main_extra_data'].angles in ["BA"]:
        bolted_web = steel.BoltedWeb(
            beam_profile,
            bolt_array,
            parts['ang_bolts_plate'],
            rp)
        bolted_angle_pair = steel.BoltedClipAnglePair(
            parts['clip_profile'],
            parts['ang_bolts_plate'],
            rp)
        # FORCES
        lat_uls_forces = uls_forces.rot90(2, 3, "SIDE_ULS", None)\
            .from_factor(D(0.5), "SIDE_ULS", None)
        lat_uls_forces.P = Q(D(0), "kN")
        lat_sls_forces = sls_forces.rot90(2, 3, "SIDE_SLS", None)\
            .from_factor(D(0.5), "SIDE_ULS", None)
        lat_sls_forces.P = Q(D(0), "kN")
        ec1 = bolted_angle_pair.dist_bolts_to_plate(bolt_array)
        ec2 = Q(D(0), 'mm')
        # ec3 = - ec1 asumes a simmetrical boltedclipangle...
        # let's see what happens with time but this is a fucking problem
        ec3 = Q(D(0), 'mm')
        front_uls_forces = uls_forces.from_eccentricity(
            ec1, ec2, ec3, "FRONT_ULS", None)\
            .from_factor(D(0.5), "FRONT_ULS", None)
        front_sls_forces = sls_forces.from_eccentricity(
            ec1, ec2, ec3, "FRONT_SLS", None)\
            .from_factor(D(0.5), "FRONT_ULS", None)

        # Ojo aquí, habría que quitar el .form_factor(0.5) y crear una chapa
        # frontplate con el doble de ancho y tal. ancho de la L mas alma de
        # la beam. Sería lo apropiado. Y calcular así otros bolts también
        # creados así. Y la bolted web lo mismo. Más que nada por posibles
        # comprobaciones a las que les afecte esta interaccion entre tornillos
        # o simplemente simplificar?

        # DE MOMENTO SIMPLIFICAR !!! JAJAJA MUAJAJAJA !!
        bolt_array.connected_plate = bolted_angle_pair
        lat_bolt_array = bolt_array
        front_bolt_array = bolt_array
        front_bolted_web = steel.BoltedWeb(
            landing_profile,
            bolt_array,
            parts['ang_bolts_plate'],  # <- OJO ESTO PUEDE SER UN BUG !!!!!!!
            rp)

        if all([
                bolted_web.check(lat_uls_forces, rp),
                lat_bolt_array.check(lat_sls_forces, lat_uls_forces, rp),
                bolted_angle_pair.check(bolt_array, front_uls_forces, rp),
                front_bolt_array.check(front_sls_forces, front_uls_forces, rp),
                front_bolted_web.check(front_uls_forces, rp),
        ]):
            rp.set_safe()
        else:
            rp.set_unsafe()

    # -LS- OBJECTS:
    #    - Beam web +rp *
    #    - Lateral bolts +rp *
    #    - Lateral forces *
    #    - Bolted Stiffener +rp *
    if parts['main_extra_data'].angles in ["LS"]:
        print("a")
        bolted_web = steel.BoltedWeb(
            beam_profile,
            bolt_array,
            parts['stiff_plate'],
            rp)

        stiffener = stiffeners.BoltedStiffener(
            parts['stiff_plate'], landing_profile, bolt_array, rp)
        # FORCES
        lat_uls_forces = uls_forces.rot90(2, 3, "SIDE_ULS", None)
        lat_sls_forces = sls_forces.rot90(2, 3, "SIDE_SLS", None)
        # set the conected plate so the snug front plate solver can work
        bolt_array.connected_plate = stiffener
        lat_bolt_array = bolt_array

        if all([
                bolted_web.check(lat_uls_forces, rp),
                lat_bolt_array.check(lat_sls_forces, lat_uls_forces, rp),
                stiffener.check(bolt_array, lat_uls_forces, rp),
        ]):
            rp.set_safe()
        else:
            rp.set_unsafe()

    # -RS- OBJECTS:
    #    - Beam web +rp
    #    - Lateral bolts +rp
    #    - Lateral forces
    #    - Bolted Stiffener +rp
    if parts['main_extra_data'].angles in ["RS"]:
        bolted_web = steel.BoltedWeb(
            beam_profile,
            bolt_array,
            parts['stiff_plate'],
            rp)
        stiffener = stiffeners.BoltedStiffener(
            parts['stiff_plate'], landing_profile, bolt_array, rp)
        # FORCES
        lat_uls_forces = uls_forces.rot90(2, 1, "SIDE_ULS", None)
        lat_sls_forces = sls_forces.rot90(2, 1, "SIDE_SLS", None)
        # set the conected plate so the snug front plate solver can work
        bolt_array.connected_plate = stiffener
        lat_bolt_array = bolt_array

        if all([
                bolted_web.check(lat_uls_forces, rp),
                lat_bolt_array.check(lat_sls_forces, lat_uls_forces, rp),
                stiffener.check(bolt_array, lat_uls_forces, rp),
        ]):
            rp.set_safe()
        else:
            rp.set_unsafe()

    # Finally, we always return a report from a solver
    return rp
