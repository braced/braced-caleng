from caleng.parts import bolts, loads, reports, steel
from decimal import Decimal as D
from caleng.parts.unit_registry import *


class S008_EC3_Conn:
    def __init__(self, conn):
        # Report and results manager
        self.rp = reports.Report(conn)
        self.conn = conn
        self.flange_cp = "flanges" in conn.extra_data['cover_plates']
        self.web_lcp = "web_left" in conn.extra_data['cover_plates']
        self.web_rcp = "web_right" in conn.extra_data['cover_plates']
        self.joint_gap = Q(D(conn.extra_data['joint_gap']), 'mm')

    def setup(self):
        if True:  # XD
            self.columns_setup()
        if self.flange_cp:
            self.flange_setup()
        if self.web_lcp or self.web_rcp:
            self.web_setup()

        self.sls_forces = loads.ForcesSet(self.conn.forces['SLS'], self.rp)
        self.uls_forces = loads.ForcesSet(self.conn.forces['ULS'], self.rp)

        if self.flange_cp and self.web_lcp and self.web_rcp:
            # Reparto de fuerzas y división de web
            self.split_forces()
            self.divide_web_forces()
        elif self.flange_cp and self.web_lcp:
            # Reparto de fuerzas
            self.split_forces()
        elif self.flange_cp and self.web_rcp:
            # Reparto de fuerzas
            self.split_forces()
        elif self.web_lcp and self.web_rcp:
            # Fuerzas a web sin repartir. Solo orientar
            self.forces_to_web()
        elif self.flange_cp:
            # Fuerzas a flange sin repartir. Solo orientar
            self.forces_to_flange()
        elif self.web_lcp:
            # Fuerzas a web sin repartir. Solo orientar. Dividir.
            self.forces_to_web()
            self.divide_web_forces()
        elif self.web_rcp:
            # Fuerzas a web sin repartir. Solo orientar. Dividir.
            self.forces_to_web()
            self.divide_web_forces()
        else:
            self.rp.set_unsafe()
            return self.rp

    def columns_setup(self):
        # Columns
        top_column = steel.Profile(self.conn.profiles['ARRIVING'], self.rp)
        bottom_column = steel.Profile(self.conn.profiles['LANDING'], self.rp)
        if bottom_column.mat_db_profile.h > top_column.mat_db_profile.h:
            biggest_column = bottom_column
        else:
            biggest_column = top_column

        # SOME BACKEND COMPROBATIONS ABOUT PROFILES
        if bottom_column.profile_type != top_column.profile_type:
            raise Exception("Bottom column and top column must be same type"
                            ", prolly there is a frontend error")

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

        self.top_column = top_column
        self.bottom_column = bottom_column
        self.biggest_column = biggest_column

    def flange_setup(self):
        self.flange_bolt = bolts.EuroBolt(self.conn.bolts['FLANGE'], self.rp)
        self.flange_bolt_group = bolts.ShearTensionBoltArray(
            self.conn.bolt_arrays['FLANGE'], self.flange_bolt, self.rp)
        self.flange_cover_plate = steel.BoltedPlate(
            self.conn.plates['FLANGE_COVER_PLATE'], self.rp)
        self.bottom_column.bolt_the_flange(self.flange_bolt_group,
                                           self.flange_cover_plate, self.rp)
        self.top_column.bolt_the_flange(self.flange_bolt_group,
                                        self.flange_cover_plate, self.rp)
        self.flange_ecc = self.flange_bolt_group.p2_sum() / 2 +\
            self.flange_cover_plate.e2_other + self.joint_gap

    def web_setup(self):
        self.web_bolt = bolts.EuroBolt(self.conn.bolts['WEB'], self.rp)
        self.web_bolt_group = bolts.ShearTensionBoltArray(
            self.conn.bolt_arrays['WEB'], self.web_bolt, self.rp)
        self.web_cover_plate = steel.BoltedPlate(
            self.conn.plates['WEB_COVER_PLATE'], self.rp)
        self.bottom_column.bolt_the_web(
            self.web_bolt_group, self.web_cover_plate, self.rp)
        self.top_column.bolt_the_web(
            self.web_bolt_group, self.web_cover_plate, self.rp)
        self.web_ecc = self.web_bolt_group.p2_sum() / 2 +\
            self.web_cover_plate.e2_other + self.joint_gap

    def split_forces(self):
        zero = Q(D(0), 'mm')
        self.flange_sls, self.web_sls = self.sls_forces.from_eccentricity(
            - self.flange_ecc, zero, zero, None, None
        ).get_flange_and_web_tuple(self.biggest_column, self.rp)
        self.flange_uls, self.web_uls = self.uls_forces.from_eccentricity(
            - self.web_ecc, zero, zero, None, None
        ).get_flange_and_web_tuple(self.biggest_column, self.rp)

    def forces_to_web(self):
        zero = Q(D(0), 'mm')
        self.web_sls = self.sls_forces.from_eccentricity(
            - self.web_ecc, zero, zero, None, None
        )
        self.web_uls = self.uls_forces.from_eccentricity(
            - self.web_ecc, zero, zero, None, None
        )

    def forces_to_flange(self):
        zero = Q(D(0), 'mm')
        self.flange_sls = self.sls_forces.from_eccentricity(
            - self.flange_ecc, zero, zero, None, None
        )
        self.flange_uls = self.uls_forces.from_eccentricity(
            - self.flange_ecc, zero, zero, None, None
        )

    def divide_web_forces(self):
        self.web_sls = self.web_sls.from_factor(
            D(0.5), "WEB SLS FOR SINGLE COVER PLATE", self.rp)
        self.web_uls = self.web_uls.from_factor(
            D(0.5), "WEB ULS FOR SINGLE COVER PLATE", self.rp)

    def check_flange(self):
        if not self.flange_cp:
            return True
        self.flange_bolt_group.connected_plate = self.flange_cover_plate
        return self.flange_bolt_group.check(
            self.flange_sls, self.flange_uls, self.rp) &\
            self.flange_cover_plate.check(
                self.flange_bolt_group, self.flange_uls, self.rp)

    def check_web(self):
        if not self.web_lcp and not self.web_rcp:
            return True
        self.web_bolt_group.connected_plate = self.web_cover_plate
        return self.web_bolt_group.check(
            self.web_sls, self.web_uls, self.rp) &\
            self.web_cover_plate.check(
                self.web_bolt_group, self.web_uls, self.rp)

    def check_columns(self):
        if self.bottom_column.name == self.top_column.name:
            # Then we dont need to check both columns
            columns_ok =\
                self.bottom_column.bolted_flange.check(
                    self.flange_uls, self.rp) &\
                self.bottom_column.bolted_web.check(
                    self.web_uls, self.rp)
        else:
            columns_ok =\
                self.bottom_column.bolted_flange.check(
                    self.flange_uls, self.rp) &\
                self.bottom_column.bolted_web.check(
                    self.web_uls, self.rp) &\
                self.top_column.bolted_flange.check(
                    self.flange_uls, self.rp) &\
                self.top_column.bolted_web.check(
                    self.web_uls, self.rp)
        return columns_ok

    def check_and_report(self):
        # Return report
        if all([self.check_flange(), self.check_web(), self.check_columns()]):
            self.rp.set_safe()
        else:
            self.rp.set_unsafe()
        return self.rp
