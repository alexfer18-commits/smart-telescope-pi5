// NEMA 17 mounting bracket and 5 mm to 5 mm rigid shaft coupler.
// part = "bracket" | "coupler" | "motor" | "all"
include <params.scad>

part = "all";

plate_t   = 5;             // motor face plate thickness
foot_l    = 40;            // foot reach
gusset_w  = 4;             // rib thickness
set_screw = 2.6;           // M3 self-tap for the coupler set screw

module nema17() {
    // Reference body, for the assembly views. 17HS4401: 42.3 square, 40 long,
    // 5 mm shaft, 24 mm of it exposed, pilot boss 22 dia.
    color([0.15, 0.15, 0.17]) {
        translate([0, 0, -nema_body / 2 - plate_t])
            cube([nema_body, nema_body, nema_body], center = true);
        translate([0, 0, -plate_t - 0.5])
            cylinder(d = nema_boss_d, h = plate_t + 1);
        translate([0, 0, -plate_t - nema_shaft_len + plate_t + 1])
            cylinder(d = nema_shaft_d, h = nema_shaft_len);
    }
}

module nema_bracket() {
    // L-bracket: motor face plate + foot that bolts to the alt-az frame,
    // with two ribs so the 90-degree joint does not flex under motor torque.
    difference() {
        union() {
            translate([0, 0, plate_t / 2])
                cube([nema_body + 12, nema_body + 12, plate_t], center = true);
            translate([0, -(nema_body + 12) / 2 + plate_t / 2, -foot_l / 2])
                cube([nema_body + 12, plate_t, foot_l], center = true);
            // base reinforcement: two triangular ribs in the XZ plane
            for (x = [-1, 1])
                translate([x * (nema_body / 2 - 2), -(nema_body + 12) / 2 - 1, 0])
                    rotate([90, 0, 0])
                        linear_extrude(height = gusset_w, center = true)
                            polygon([[0, 0], [22, 0], [0, 22]]);
        }
        // pilot boss relief
        translate([0, 0, plate_t / 2])
            cylinder(d = nema_boss_d + clearance, h = plate_t + 2, center = true);
        // shaft pass-through
        translate([0, 0, plate_t / 2])
            cylinder(d = nema_shaft_d + 1, h = plate_t + 2, center = true);
        // 4 x M3 motor screws on the 31 x 31 grid
        for (x = [-1, 1], y = [-1, 1])
            translate([x * nema_hole_grid / 2, y * nema_hole_grid / 2, plate_t / 2])
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

module coupler(l = 25, d = 16) {
    // Rigid coupler, 5 mm bore through, one M3 set screw per end.
    // The shafts get a filed flat where the set screw lands; a round shaft
    // under a cone-point screw slips at roughly half the rated torque.
    difference() {
        cylinder(d = d, h = l, center = true);
        cylinder(d = nema_shaft_d + clearance, h = l + 2, center = true);
        // 2 set screws per end, 90 degrees apart, so the coupler cannot walk
        for (z = [-1, 1], a = [0, 90])
            rotate([0, 0, a])
                translate([d / 2 - 1, 0, z * (l / 2 - 4)])
                    rotate([90, 0, 0]) {
                        cylinder(d = set_screw, h = 12, center = true);
                        // heat-set insert pocket at the outer face
                        translate([0, 0, 4.2])
                            cylinder(d = 4.6, h = 4, center = true);
                    }
        // chamfer the bore so a burred shaft end does not jam
        for (z = [-1, 1])
            translate([0, 0, z * (l / 2 + 0.4)])
                cylinder(d1 = nema_shaft_d + clearance,
                         d2 = nema_shaft_d + 3, h = 1.2, center = true);
    }
}

if (part == "bracket" || part == "all") nema_bracket();
if (part == "coupler" || part == "all")
    translate([75, 0, 0]) rotate([0, 90, 0]) coupler();
if (part == "motor" || part == "all") translate([-85, 0, 0]) nema17();
