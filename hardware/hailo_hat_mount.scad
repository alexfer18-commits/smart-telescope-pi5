// Standoff set that stacks the Hailo-8L AI HAT+ on the Pi 5 tray.
// The HAT+ uses the Pi's own 58 x 49 hole grid, so the tray needs no change:
// these standoffs simply raise it above the USB/Ethernet connectors.
// part = "standoff" | "spacer" | "all"
include <params.scad>

part = "all";

module standoff() {
    // M2.5 male/female standoff, 11 mm tall
    difference() {
        union() {
            cylinder(d = 5, h = hailo_standoff_h);
            translate([0, 0, hailo_standoff_h])
                cylinder(d = 5.5, h = 2.5);
        }
        translate([0, 0, 2])
            cylinder(d = 2.2, h = hailo_standoff_h + 2);
        // self-tapping thread relief on the female end
        translate([0, 0, hailo_standoff_h - 1])
            cylinder(d = 2.5, h = 2.5);
    }
}

module spacer() {
    // 2 mm shim for the camera side, keeps the ribbon clear of the HAT
    difference() {
        cylinder(d = 8, h = 2);
        cylinder(d = 2.7, h = 4, center = true);
    }
}

if (part == "standoff" || part == "all")
    for (x = [-1, 1], y = [-1, 1])
        translate([x * pi5_hole_grid[0] / 2, y * pi5_hole_grid[1] / 2, 0])
            standoff();
if (part == "spacer" || part == "all")
    translate([40, 0, 0]) spacer();
