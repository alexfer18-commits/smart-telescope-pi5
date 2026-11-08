// Pi 5 tray + Camera Module 3 carrier for a 60 mm guidescope.
//
// Three printed parts, no belt, no machined adapter:
//   collar  — two-piece tube ring, 2 x M4 pinch bolts
//   tray    — vented Pi 5 plate, bolts to the collar with 2 x M4
//   arm     — camera mast reaching back to the eyepiece, 2 x M3 to the tray
//   plate   — Camera Module 3 carrier, slides 18 mm vertically on the arm
//
// 4 x M4 total: 2 pinch the collar closed, 2 fix the tray to the collar pads.
//
// part = "collar" | "tray" | "arm" | "plate" | "all"
include <params.scad>

part = "all";

collar_h  = tube_clamp_w;      // 18, along the tube axis
r_in      = tube_d / 2 + clearance / 2;
r_out     = r_in + wall;
slot_w    = 2.6;               // split width; the bolts close it
tab_t     = 8;
tab_len   = 14;
m4        = 4.4;
m4_head   = 8.2;

tray_t    = wall;
tray_z    = r_out + 12;        // underside of the tray: 45.2
tray_w    = pi5_pcb[0] + 8;    // 93
tray_d    = pi5_pcb[1] + 8;    // 64

// --- collar -----------------------------------------------------------------
// Built with its bore along Z, then rotated so the bore runs along Y (the tube
// axis) and the mounting pads end up on top.
module tube_clamp() {
    difference() {
        union() {
            cylinder(r = r_out, h = collar_h, center = true);
            // split tabs, opening downward in the final orientation
            for (x = [-1, 1])
                translate([x * (slot_w / 2 + tab_t / 2),
                           -(r_out + tab_len / 2 - 2), 0])
                    cube([tab_t, tab_len, collar_h], center = true);
            // two pads on the opposite side: the tray lands on these
            for (x = [-1, 1])
                translate([x * (r_out + 5), r_out + 5, 0])
                    cube([10, 14, collar_h], center = true);
        }
        cylinder(r = r_in, h = collar_h + 2, center = true);
        // the split
        translate([0, -r_out / 2 - 1, 0])
            cube([slot_w, r_out + 2, collar_h + 4], center = true);
        // 2 x M4 pinch bolts through both tabs
        for (z = [-1, 1])
            translate([0, -(r_out + tab_len / 2 - 2), z * 5])
                rotate([0, 90, 0]) {
                    cylinder(d = m4, h = 40, center = true);
                    translate([0, 0, 14]) cylinder(d = m4_head, h = 6, center = true);
                }
        // 2 x M4 tray bolts, drilled into the pads along the local Y axis
        for (x = [-1, 1])
            translate([x * (r_out + 5), r_out + 11, 0])
                rotate([-90, 0, 0]) {
                    cylinder(d = m4, h = 16);
                    translate([0, 0, 13]) cylinder(d = 6, h = 5);  // nut pocket
                }
    }
}

// --- tray -------------------------------------------------------------------
module pi5_tray() {
    difference() {
        union() {
            translate([0, 0, tray_t / 2])
                cube([tray_w, tray_d, tray_t], center = true);
            // rails that locate the PCB edges
            for (s = [-1, 1])
                translate([0, s * (pi5_pcb[1] / 2 + 1.5), tray_t + 2])
                    cube([pi5_pcb[0], 3, 4], center = true);
        }
        // M2.5 through the board's 58 x 49 grid
        for (x = [-1, 1], y = [-1, 1])
            translate([x * pi5_hole_grid[0] / 2, y * pi5_hole_grid[1] / 2, 0])
                cylinder(d = pi5_hole_d, h = tray_t + 4, center = true);
        // 2 x M4 to the collar pads
        for (x = [-1, 1])
            translate([x * (r_out + 5), 0, 0])
                cylinder(d = m4, h = tray_t + 4, center = true);
        // 2 x M3 to the camera arm (heat-set inserts, from below)
        for (x = [-1, 1])
            translate([x * 20, -pi5_pcb[1] / 2, 0])
                cylinder(d = 3.4, h = tray_t + 4, center = true);
        // ventilation: 15 slots, clear of the mounting holes
        for (x = [-22, -11, 0, 11, 22], y = [-18, 0, 18])
            translate([x, y, 0])
                cube([7, 12, tray_t + 4], center = true);
    }
    // M2.5 bosses
    for (x = [-1, 1], y = [-1, 1])
        translate([x * pi5_hole_grid[0] / 2, y * pi5_hole_grid[1] / 2, tray_t])
            difference() {
                cylinder(d = 6, h = 6);
                translate([0, 0, -1]) cylinder(d = 2.2, h = 8);
            }
}

// --- camera arm -------------------------------------------------------------
arm_z   = tray_z - 4;          // base plate sits under the tray
cam_z   = 34;                  // optical axis of the camera, tube height + 4

module camera_arm() {
    difference() {
        union() {
            // base plate, 2 x M3 up into the tray
            translate([0, -28, arm_z + 2])
                cube([44, 26, 4], center = true);
            // vertical web
            translate([0, -33, (arm_z + 26) / 2 - 1])
                cube([22, 6, arm_z - 26], center = true);
            // horizontal arm back to the eyepiece
            translate([0, -55, 28.5])
                cube([28, 46, 5], center = true);
            // end pad: the camera plate bolts to its rear face
            translate([0, -75, cam_z])
                cube([34, 6, 34], center = true);
        }
        // 2 x M3 into the tray
        for (x = [-1, 1])
            translate([x * 20, -28, arm_z + 2])
                cylinder(d = 3.4, h = 10, center = true);
        // light path through the end pad
        translate([0, -75, cam_z])
            rotate([90, 0, 0]) cylinder(d = cam_lens_d + 2, h = 10, center = true);
        // 2 x M3 heat-set inserts for the camera plate
        for (x = [-1, 1])
            translate([x * 12, -78.5, cam_z])
                rotate([90, 0, 0]) {
                    cylinder(d = 3.4, h = 8, center = true);
                    translate([0, 0, -2]) cylinder(d = 4.6, h = 5, center = true);
                }
    }
}

// --- camera plate -----------------------------------------------------------
// Slots, not holes: the camera slides 18 mm vertically so the same bracket
// works with eyepieces of different back focus.
module camera_plate() {
    difference() {
        cube([34, 3, 34], center = true);
        // 2 vertical slots on 24 mm centres
        for (x = [-1, 1])
            translate([x * 12, 0, 0])
                hull() {
                    translate([0, 0, -9]) cylinder(d = 3.4, h = 8, center = true);
                    translate([0, 0, 9]) cylinder(d = 3.4, h = 8, center = true);
                }
        // lens opening
        rotate([90, 0, 0]) cylinder(d = cam_lens_d, h = 8, center = true);
        // 4 x M2 on the 21 x 12.5 grid
        for (x = [-1, 1], z = [-1, 1])
            translate([x * cam_hole_grid[0] / 2, 0, z * cam_hole_grid[1] / 2])
                rotate([90, 0, 0])
                    cylinder(d = cam_hole_d, h = 8, center = true);
    }
}

if (part == "collar" || part == "all")
    rotate([90, 0, 0]) tube_clamp();
if (part == "tray" || part == "all")
    translate([0, 0, tray_z]) pi5_tray();
if (part == "arm" || part == "all")
    camera_arm();
if (part == "plate" || part == "all")
    translate([0, -80.5, cam_z]) camera_plate();
