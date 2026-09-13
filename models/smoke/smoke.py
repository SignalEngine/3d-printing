from build123d import *
# XY = bed, Z = up. Plate lies flat (largest face down).
L, W, T = 60, 40, 4
with BuildPart() as part:
    with BuildSketch(Plane.XY):
        RectangleRounded(L, W, radius=3)
    extrude(amount=T)
    with Locations(part.faces().sort_by(Axis.Z)[-1]):
        with GridLocations(40, 20, 2, 2):
            CounterBoreHole(radius=1.7, counter_bore_radius=3.25, counter_bore_depth=2)
    chamfer(part.faces().sort_by(Axis.Z)[0].edges(), 0.4)
export_step(part.part, "smoke.step")
m = Mesher(); m.add_shape(part.part); m.write("smoke.3mf")
