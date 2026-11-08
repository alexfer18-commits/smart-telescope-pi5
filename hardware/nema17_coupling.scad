// NEMA 17 mounting bracket and 5 mm to 5 mm rigid shaft coupler.
// part = "bracket" | "coupler" | "all"
include <params.scad>

part = "all";

module nema_bracket() {
    // L-bracket: motor face plate + foot that bolts to the alt-az frame
    plate_t = 5;
    foot_l = 40;
    difference() {
        union() {
            cube([nema_body + 12, nema_body + 12, plate_t], center = true);
            translate([0, -(nema_body + 12) / 2 + plate_t / 2, -foot_l / 2])
                cube([nema_body + 12, plate_t, foot_l], center = true);
        }
        // pilot boss relief
        translate([0, 0, 0])
            cylinder(d = nema_boss_d + clearance, h = plate_t + 2, center = true);
        // shaft pass-through
        cylinder(d = nema_shaft_d + 1, h = plate_t + 2, center = true);
        // M3 motor screws on the 31 x 31 grid
        for (x = [-1, 1], y = [-1, 1])
            translate([x * nema_hole_grid / 2, y * nema_hole_grid / 2, 0])
                cylinder(d = nema_hole_d, h = plate_t + 2, center = true);
        // two M4 slots in the foot for frame adjustment
        for (x = [-1, 1])
            translate([x * 14, -(nema_body + 12) / 2 + plate_t / 2, -foot_l / 2])
                hull() {
                    translate([0, 0, -10]) cylinder(d = 4.5, h = 20, center = true);
                    translate([0, 0, 10]) cylinder(d = 4.5, h = 20, center = true);
                }
    }
}

module coupler() {
    // Rigid coupler, 5 mm bore each side, two M4 set screws per side.
    l = 25;
    d = 16;
    difference() {
        cylinder(d = d, h = l, center = true);
        cylinder(d = nema_shaft_d + clearance, h = l + 2, center = true);
        // helical slit for compliance (single cut is enough at these torques)
        translate([0, 0, 0])
            cube([d + 2, 1.2, l * 0.55], center = true);
        for (z = [-1, 1], a = [90, 270])
            rotate([0, 0, a])
                translate([d / 2 - 4, 0, z * (l / 2 - 4)])
                    rotate([90, 0, 0])
                        cylinder(d = 3.4, h = 12, center = true);
    }
}

if (part == "bracket" || part == "all") nema_bracket();
if (part == "coupler" || part == "all") translate([70, 0, 0]) rotate([0, 90, 0]) coupler();
