from caleng.parts import bolts, loads, reports, steel


# P002_EC3 MAIN SOLVER
def P002_EC3(parts):
    # Report and results manager
    rp = reports.Report(parts['calc'])
    # Setting up parts
    bolt = bolts.EuroBolt(parts['main_bolt'], rp)
    bolt_group = bolts.TensionBoltArray(parts['main_bolt_array'], bolt, rp)
    sls_forces = loads.ForcesSet(parts['sls_force'], rp)
    uls_forces = loads.ForcesSet(parts['uls_force'], rp)

    plate = steel.DummyBoltedPlate(parts['end_plate'], rp)
    # set the conected plate so the snug front plate solver can work
    bolt_group.connected_plate = plate

    # Solving bolts
    if bolt_group.check(sls_forces, uls_forces, rp):
        rp.set_safe()
    else:
        rp.set_unsafe()

    return rp
