# This module was not designed to be used by the engine solvers. It is used by
# the steel.py module to help solving it's tstubs.


from decimal import Decimal as D
from caleng.parts.exceptions import CalengCrash
from caleng.parts.unit_registry import *
from caleng.parts.tstub_alfa_abacus import get_alfa
from shapely.geometry import Point
from shapely.geometry.polygon import Polygon
from shapely.geometry import LineString
from shapely import affinity
import numpy as np


class RawTStub():

    def get_Lb(self, rp):
        Lb = self.thickness * 2
        rp.addLine(100, 30, "", "Lb = " + str(Lb))
        return Lb

    def get_Lb_ast(self, rp):
        nb = D(1)  # NUMERO DE TORNILLOS POR FILA. ????
        Lb_ast = D(8.8) * self.m ** 3 *\
            self.bolt[7] * nb / self.leff / self.thickness ** 3
        rp.addLine(100, 30, "", "Lb* = " + str(Lb_ast))
        return Lb_ast

    def check(self, Ft_Ed, Ft_Rd, rp):

        # Mpl used for all modes of failure:
        Mpl_Rd = D(0.25) * self.leff * self.thickness ** 2 * self.fyd

        # PRYING FORCES MAY DEVELOP
        if self.get_Lb(rp) <= self.get_Lb_ast(rp):

            # MODE 1
            Ft_1_Rd = (D(4) * Mpl_Rd / self.m).to("kN")
            desc_string = "Prying forces may develop"
            rp.addLine(100, 30, desc_string, "Ft_1_Rd = " + str(Ft_1_Rd))
            # MODE 2
            Ft_2_Rd = (D(2) * Mpl_Rd + self.n * Ft_Rd) / (self.m + self.n)
            Ft_2_Rd = Ft_2_Rd.to("kN")
            rp.addLine(100, 30, "", "Ft_2_Rd = " + str(Ft_2_Rd))

            Ft_Rd = min(Ft_1_Rd, Ft_2_Rd)

        # NO PRYING FORCES
        else:
            Ft_1_2_Rd = (D(2) * Mpl_Rd / self.m).to("kN")
            desc_string = "No prying forces"
            rp.addLine(100, 30, desc_string, "Ft_1_2_Rd = " + str(Ft_1_2_Rd))
            Ft_Rd = Ft_1_2_Rd

        if Ft_Ed < Ft_Rd:
            ds_ok = "{} Check | {} | OK".format(self.type, self.bolt[0])
            calc_string = "Ft_Ed = {} < Ft_Rd = {}".format(Ft_Ed, Ft_Rd)
            rp.addLine(200, 30, ds_ok, calc_string)
            return True
        else:
            ds_fail = "{} Check | {} | FAIL".format(self.type, self.bolt[0])
            calc_string = "Ft_Ed = {} > Ft_Rd = {}".format(Ft_Ed, Ft_Rd)
            rp.addLine(500, 30, ds_fail, calc_string)
            return False


class SimpleTStub(RawTStub):
    """ One bolt tstub. Having only 1 side with
        a plate to resist forces """

    def __init__(self, t, fyd, bolt, e, e_other, m, bp, w, leff, rp):
        if t.magnitude == 0:
            raise CalengCrash("Plate thickness cant be 0")
        self.type = "Simple T-Stub"
        self.thickness = t
        self.fyd = fyd
        self.e = e
        self.m = m
        self.bolt = bolt
        self.n = min(e, D(1.25) * m)
        self.leff = min(
            D(4) * m + D(1.25) * e,
            e_other + D(2) * m + D(0.625) * e,
            D(0.5) * bp,
            D(0.5) * w + D(2) * m + D(0.625) * e,
        )

        desc_string = "Single T Stub | Bolt " + str(bolt[0])
        calc_string = "e={},m={},n={},leff={}"\
                      .format(self.e, self.m, self.n, self.leff)
        rp.addLine(100, 30, desc_string, calc_string)

    def __str__(self):
        return "SimpleTStub[e={},m={},n={},leff={}]"\
            .format(self.e, self.m, self.n, self.leff)


class CornerTStub(RawTStub):
    """ This is a one bolt tstub. Having 2 sides with
        plate to resist forces """

    def __init__(self, t, fyd, bolt, e, m1, m2, rp):
        self.type = "Corner T-Stub"
        self.thickness = t
        self.fyd = fyd
        self.bolt = bolt
        self.e = e
        self.m1 = m1
        self.m2 = m2
        self.m = m1
        self.n = min(e, D(1.25) * self.m)
        self.n1 = min(e, D(1.25) * m1)
        lambda1 = self.m1 / (self.m1 + self.e)
        lambda2 = self.m2 / (self.m1 + self.e)  # This is ok! don't change
        try:
            self.alfa = Q(D(get_alfa(lambda1.magnitude, lambda2.magnitude)))
        except Exception as e:
            raise CalengCrash("Could not set tstub alfa: " + str(e))
        self.leff = self.alfa * self.m

    def __str__(self):
        return "SimpleTStub[e={},m1={},m2={},leff={}]"\
            .format(self.e, self.m1, self.m2, self.leff)


def solve_from_polygons(plate, profile, bolt_array, report):
    """ Returns a list of tstub objects from given elements """

    # usefull stuff
    t = plate.thickness
    fyd = plate.fy / plate.Ym0
    bolts = bolt_array.get_bolt_matrix()
    tstub_list = []

    # Get the profile positioned polygon
    rotated_pol = profile.get_polygon(report)
    # rotated_pol = affinity.rotate(
    #     unpos_profile_pol,
    #     float(position.rotation.magnitude),
    #     origin=Point(0, 0))
    profile_pol = affinity.translate(
        rotated_pol,
        xoff=-float(plate.g1.magnitude),
        yoff=-float(plate.g2.magnitude))
    # Get the plate polygon
    plate_pol = plate.get_polygon(report)

    # Get the profile square boundary
    pb = profile_pol.bounds

    # Return void list if profile is 0 sized
    if len(pb) < 3:
        report.addLine(100, 30, "Empty profile. No TSTUB solved",
                       "MANUAL REVIEW REQUIRED")
        return []
    else:
        profile_boundary = Polygon((
            (pb[2], pb[3]), (pb[2], pb[1]),
            (pb[0], pb[1]), (pb[0], pb[3]),
        ))

    if plate_pol.disjoint(profile_pol):
        raise CalengCrash("Profile boundary is outside plate!")

    # Outside plate and inside plate different tstub types
    out_plate = plate_pol.difference(profile_boundary)

    out_bolts = []
    in_bolts = []

    # Bolt data: (i, row, col, x1, x2, d, A, As)
    for bolt in bolts:
        point = Point(bolt[3].magnitude, bolt[4].magnitude)
        if point.within(out_plate):
            out_bolts.append(bolt)
        elif point.within(profile_boundary):
            in_bolts.append(bolt)
        else:
            print("Quizas este justo en el contorno. no?")
            raise CalengCrash("Problem at tstubs.solve_from_polygons()")

    # If profile is a pipe, we create SimpleTstub objects as if it were a tube
    # +---------+ +---------+
    # | +  |  + | | 1  |  2 |   <- We choose the worst m distance (biggest)
    # |---- ----| |---- ----|      it may be in the 1 or 2 direction.
    # |         | |         |
    # |---- ----| |---- ----|
    # | +  |  + | | 3  |  4 |
    # +---------+ +---------+
    # TUBE is the same shit
    if profile.profile_type == "PIP" or profile.profile_type == "TUB":
        for bolt in out_bolts:
            point = Point(bolt[3].magnitude, bolt[4].magnitude)
            # e = Q(D(point.distance(plate_pol.exterior)), "mm")
            e = plate.e2_main
            e_other = plate.e1_main
            bp = plate.width
            w = np.max(bolt_array.p1)
            m = Q(D(point.distance(profile_pol)), "mm")
            leff1 = plate.width / bolt_array.n1
            leff2 = plate.length / bolt_array.n2
            leff = min(leff1, leff2)
            args = (t, fyd, bolt, e, e_other, m, bp, w, leff, report)
            tstub = SimpleTStub(*args)
            tstub_list.append(tstub)

    # If profile is an H, we create SimpleTStub objects for the outter bolts
    # but we need to create CornerTStub objects for bolts between flanges
    # These bolts are into "in_bolts" list
    # +-----------+ +-----------+
    # |  +     +  | | 1   |   2 |   <- We choose the worst m distance (biggest)
    # |  _______  | |----- -----|      it may be in the 1 or 2 direction.
    # |  +  |  +  | | 3   |   4 |   <- 3 and 4 are CornerTstubs
    # |  _______  | |----- -----|
    # |  +     +  | | 5   |   6 |
    # +-----------+ +-----------+

    # If profile is U: Same as H but with only one side with CornerTStubs
    # +-----------+ +-----------+
    # |  +     +  | | 1   |   2 |   <- We choose the worst m distance (biggest)
    # |     ____  | |----- -----|      it may be in the 1 or 2 direction.
    # |  +  |  +  | | 3   |   4 |   <- only 4 is a CornerTstubs
    # |     ____  | |----- -----|
    # |  +     +  | | 5   |   6 |
    # +-----------+ +-----------+

    # If profile is L, same as U but may be a bug.

    else:  # ELSE: Profile is H, U or L
        for bolt in out_bolts:
            point = Point(bolt[3].magnitude, bolt[4].magnitude)
            # e = Q(D(point.distance(plate_pol.exterior)), "mm")
            e = plate.e2_main
            e_other = plate.e1_main
            bp = plate.width
            w = np.max(bolt_array.p1)
            m = Q(D(point.distance(profile_pol)), "mm")
            leff1 = plate.width / bolt_array.n1
            leff2 = plate.length / bolt_array.n2
            leff = min(leff1, leff2)
            args = (t, fyd, bolt, e, e_other, m, bp, w, leff, report)
            tstub = SimpleTStub(*args)
            tstub_list.append(tstub)

        if profile.profile_type == "H":
            for bolt in in_bolts:
                point = Point(bolt[3].magnitude, bolt[4].magnitude)

                # Horizontal and vertical line from the point
                lpoint = affinity.translate(point, xoff=-1000)
                rpoint = affinity.translate(point, xoff=1000)
                dpoint = affinity.translate(point, yoff=-1000)
                upoint = affinity.translate(point, yoff=1000)
                horizontal_line = LineString([lpoint, rpoint])
                vertical_line = LineString([dpoint, upoint])

                # Points where the lines clashes with boundaries
                clash_h_pro = horizontal_line.intersection(
                    profile_pol.exterior)
                clash_v_pro = vertical_line.intersection(
                    profile_pol.exterior)
                clash_h_plate = horizontal_line.intersection(
                    plate_pol.exterior)

                # Now, we need to find the closest point ¬¬'
                m1_adim = min(map(lambda x: point.distance(x), clash_h_pro))
                m2_adim = min(map(lambda x: point.distance(x), clash_v_pro))
                m1 = Q(D(m1_adim), "mm")
                m2 = Q(D(m2_adim), "mm")
                e_adim = min(map(lambda x: point.distance(x), clash_h_plate))
                e = Q(D(e_adim), "mm")
                tstub_list.append(CornerTStub(t, fyd, bolt, e, m1, m2, report))

        else:  # ELSE: Profile is U or L
            for bolt in in_bolts:
                point = Point(bolt[3].magnitude, bolt[4].magnitude)

    # Let's go up!
    return tstub_list


def solve_from_polygons_legacy(plate, profile, position, bolt_array, report):
    """ Returns a list of tstub objects from given elements """

    # usefull stuff
    t = plate.thickness
    fyd = plate.fy / plate.Ym0
    bolts = bolt_array.get_bolt_matrix()
    tstub_list = []

    # Get the profile positioned polygon
    rotated_pol = profile.get_polygon(report)
    # rotated_pol = affinity.rotate(
    #     unpos_profile_pol,
    #     float(position.rotation.magnitude),
    #     origin=Point(0, 0))
    profile_pol = affinity.translate(
        rotated_pol,
        xoff=-float(position.g1.magnitude),
        yoff=-float(position.g2.magnitude))
    # Get the plate polygon
    plate_pol = plate.get_polygon(report)

    # Get the profile square boundary
    pb = profile_pol.bounds

    # Return void list if profile is 0 sized
    if len(pb) < 3:
        report.addLine(100, 30, "Empty profile. No TSTUB solved",
                       "MANUAL REVIEW REQUIRED")
        return []
    else:
        profile_boundary = Polygon((
            (pb[2], pb[3]), (pb[2], pb[1]),
            (pb[0], pb[1]), (pb[0], pb[3]),
        ))

    if plate_pol.disjoint(profile_pol):
        raise CalengCrash("Profile boundary is outside plate!")

    # Outside plate and inside plate different tstub types
    out_plate = plate_pol.difference(profile_boundary)

    out_bolts = []
    in_bolts = []

    # Bolt data: (i, row, col, x1, x2, d, A, As)
    for bolt in bolts:
        point = Point(bolt[3].magnitude, bolt[4].magnitude)
        if point.within(out_plate):
            out_bolts.append(bolt)
        elif point.within(profile_boundary):
            in_bolts.append(bolt)
        else:
            print("Quizas este justo en el contorno. no?")
            raise CalengCrash("Problem at tstubs.solve_from_polygons()")

    # If profile is a pipe, we create SimpleTstub objects as if it were a tube
    # +---------+ +---------+
    # | +  |  + | | 1  |  2 |   <- We choose the worst m distance (biggest)
    # |---- ----| |---- ----|      it may be in the 1 or 2 direction.
    # |         | |         |
    # |---- ----| |---- ----|
    # | +  |  + | | 3  |  4 |
    # +---------+ +---------+
    # TUBE is the same shit
    if profile.profile_type == "PIP" or profile.profile_type == "TUB":
        for bolt in out_bolts:
            point = Point(bolt[3].magnitude, bolt[4].magnitude)
            # e = Q(D(point.distance(plate_pol.exterior)), "mm")
            e = plate.e2_main
            e_other = plate.e1_main
            bp = plate.width
            w = np.max(bolt_array.p1)
            m = Q(D(point.distance(profile_pol)), "mm")
            leff1 = plate.width / bolt_array.n1
            leff2 = plate.length / bolt_array.n2
            leff = min(leff1, leff2)
            args = (t, fyd, bolt, e, e_other, m, bp, w, leff, report)
            tstub = SimpleTStub(*args)
            tstub_list.append(tstub)

    # If profile is an H, we create SimpleTStub objects for the outter bolts
    # but we need to create CornerTStub objects for bolts between flanges
    # These bolts are into "in_bolts" list
    # +-----------+ +-----------+
    # |  +     +  | | 1   |   2 |   <- We choose the worst m distance (biggest)
    # |  _______  | |----- -----|      it may be in the 1 or 2 direction.
    # |  +  |  +  | | 3   |   4 |   <- 3 and 4 are CornerTstubs
    # |  _______  | |----- -----|
    # |  +     +  | | 5   |   6 |
    # +-----------+ +-----------+

    # If profile is U: Same as H but with only one side with CornerTStubs
    # +-----------+ +-----------+
    # |  +     +  | | 1   |   2 |   <- We choose the worst m distance (biggest)
    # |     ____  | |----- -----|      it may be in the 1 or 2 direction.
    # |  +  |  +  | | 3   |   4 |   <- only 4 is a CornerTstubs
    # |     ____  | |----- -----|
    # |  +     +  | | 5   |   6 |
    # +-----------+ +-----------+

    # If profile is L, same as U but may be a bug.

    else:  # ELSE: Profile is H, U or L
        for bolt in out_bolts:
            point = Point(bolt[3].magnitude, bolt[4].magnitude)
            # e = Q(D(point.distance(plate_pol.exterior)), "mm")
            e = plate.e2_main
            e_other = plate.e1_main
            bp = plate.width
            w = np.max(bolt_array.p1)
            m = Q(D(point.distance(profile_pol)), "mm")
            leff1 = plate.width / bolt_array.n1
            leff2 = plate.length / bolt_array.n2
            leff = min(leff1, leff2)
            args = (t, fyd, bolt, e, e_other, m, bp, w, leff, report)
            tstub = SimpleTStub(*args)
            tstub_list.append(tstub)

        if profile.profile_type == "H":
            for bolt in in_bolts:
                point = Point(bolt[3].magnitude, bolt[4].magnitude)

                # Horizontal and vertical line from the point
                lpoint = affinity.translate(point, xoff=-1000)
                rpoint = affinity.translate(point, xoff=1000)
                dpoint = affinity.translate(point, yoff=-1000)
                upoint = affinity.translate(point, yoff=1000)
                horizontal_line = LineString([lpoint, rpoint])
                vertical_line = LineString([dpoint, upoint])

                # Points where the lines clashes with boundaries
                clash_h_pro = horizontal_line.intersection(
                    profile_pol.exterior)
                clash_v_pro = vertical_line.intersection(
                    profile_pol.exterior)
                clash_h_plate = horizontal_line.intersection(
                    plate_pol.exterior)

                # Now, we need to find the closest point ¬¬'
                m1_adim = min(map(lambda x: point.distance(x), clash_h_pro))
                m2_adim = min(map(lambda x: point.distance(x), clash_v_pro))
                m1 = Q(D(m1_adim), "mm")
                m2 = Q(D(m2_adim), "mm")
                e_adim = min(map(lambda x: point.distance(x), clash_h_plate))
                e = Q(D(e_adim), "mm")
                tstub_list.append(CornerTStub(t, fyd, bolt, e, m1, m2, report))

        else:  # ELSE: Profile is U or L
            for bolt in in_bolts:
                point = Point(bolt[3].magnitude, bolt[4].magnitude)

    # Let's go up!
    return tstub_list
