// Pi 5 + Camera Module 3 carrier that clamps onto the guidescope tube.
// Print: pi5_tray() in PETG, 4 perimeters, 40% infill.
// part = "tray" | "clamp" | "camera" | "all"
include <params.scad>

part = "all";

module tube_clamp() {
    difference() {
        cylinder(d = tube_d + 2 * wall + 2, h = tube_clamp_w, center = true);
        cylinder(d = tube_d + clearance, h = tube_clamp_w + 2, center = true);
        // slit so the clamp can be pinched shut with an M4 bolt
        translate([0, 0, 0])
            cube([wall + 2, 3, tube_clamp_w + 2], center = true);
        translate([tube_d / 2 + wall, 0, 0])
            rotate([90, 0, 0])
                cylinder(d = 4.4, h = tube_clamp_w + 2, center = true);
    }
}

module pi5_tray() {
    plate = [pi5_pcb[0] + 8, pi5_pcb[1] + 8, wall];
    difference() {
        union() {
            cube([plate[0], plate[1], plate[2]], center = true);
            // two rails that locate the PCB edges
            for (s = [-1, 1])
                translate([0, s * (pi5_pcb[1] / 2 + 1.5), wall])
                    cube([pi5_pcb[0], 3, 4], center = true);
        }
        // PCB standoff holes on the official 58 x 49 grid
        for (x = [-1, 1], y = [-1, 1])
            translate([x * pi5_hole_grid[0] / 2, y * pi5_hole_grid[1] / 2, 0])
                cylinder(d = pi5_hole_d, h = plate[2] + 2, center = true);
        // ventilation slot under the SoC
        translate([-10, 0, 0])
            cube([30, 30, plate[2] + 2], center = true);
    }
    // M2.5 bosses
    for (x = [-1, 1], y = [-1, 1])
        translate([x * pi5_hole_grid[0] / 2, y * pi5_hole_grid[1] / 2, wall / 2])
            difference() {
                cylinder(d = 6, h = 6);
                translate([0, 0, 1])
                    cylinder(d = 2.2, h = 6);
            }
}

module camera_bracket() {
    // L-bracket: bolts to the tray, holds the Camera Module 3 facing the sky
    difference() {
        union() {
            cube([cam_pcb[0] + 6, wall, cam_pcb[1] + 6], center = true);
            translate([0, 0, -(cam_pcb[1] + 6) / 2 + wall / 2])
                cube([cam_pcb[0] + 6, 12, wall], center = true);
        }
        translate([0, 0, 0])
            rotate([90, 0, 0])
                cylinder(d = cam_lens_d, h = wall + 2, center = true);
        for (x = [-1, 1], z = [-1, 1])
            translate([x * cam_hole_grid[0] / 2, 0, z * cam_hole_grid[1] / 2])
                rotate([90, 0, 0])
                    cylinder(d = cam_hole_d, h = wall + 2, center = true);
    }
}

if (part == "clamp" || part == "all") tube_clamp();
if (part == "tray" || part == "all")
    translate([0, 0, tube_d / 2 + wall + 8]) pi5_tray();
if (part == "camera" || part == "all")
    translate([0, -(pi5_pcb[1] / 2 + 20), tube_d / 2 + wall + 20]) camera_bracket();
