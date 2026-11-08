// Azimuth axis: base plate, tower, NEMA 17, rigid coupler, thrust-bearing
// turntable. Direct drive, no belt — 1.8 deg/step and 16 microsteps give
// 0.1125 deg/step, and the vertical axis carries no gravitational load at all
// (see docs/mechanical_analysis.md, section 3).
//
// explode = 0 assembled, 1 shows the stack apart. Values between 0 and 1 are
// allowed and interpolate.
include <params.scad>
use <nema17_coupling.scad>

explode = 0;

base_t   = 6;      // base plate
tower_h  = 79;     // tower box height; the deck sits on it
deck_t   = 6;
post_h   = 22;
ring_t   = 6;      // lazy-susan / thrust bearing stack
plate_t  = 8;      // turntable platter
base_w   = 200;
post_r   = 60;
plate_d  = 150;
hub_d    = 70;
shaft_d  = 5.2;

function ex(z, k) = z + k * explode * 12;

// --- base -------------------------------------------------------------------
module base_plate() {
    difference() {
        translate([0, 0, base_t / 2]) cube([base_w, base_w, base_t], center = true);
        // 4 x M6 to the tripod head
        for (x = [-1, 1], y = [-1, 1])
            translate([x * 80, y * 80, 0]) cylinder(d = 6.6, h = base_t + 4, center = true);
        // centre relief so the tower sits flat on a printed surface
        translate([0, 0, base_t]) cylinder(d = 40, h = 4);
    }
}

module tower() {
    // Hollow box, 8 mm walls, open at the back for the motor lead.
    difference() {
        translate([0, 0, base_t + tower_h / 2]) cube([130, 130, tower_h], center = true);
        translate([0, 0, base_t + tower_h / 2 + 4])
            cube([114, 114, tower_h - 4], center = true);
        translate([0, 60, base_t + 30]) cube([40, 30, 20], center = true);   // lead exit
    }
}

module deck() {
    difference() {
        translate([0, 0, base_t + tower_h + deck_t / 2])
            cube([150, 150, deck_t], center = true);
        // motor shaft and pilot boss pass through
        translate([0, 0, base_t + tower_h + deck_t / 2])
            cylinder(d = 26, h = deck_t + 4, center = true);
        // 4 x M4 that hold the deck to the tower
        for (x = [-1, 1], y = [-1, 1])
            translate([x * 62, y * 62, base_t + tower_h + deck_t / 2])
                cylinder(d = 4.4, h = deck_t + 4, center = true);
    }
}

// --- turntable --------------------------------------------------------------
module platter() {
    z0 = ex(base_t + tower_h + deck_t + post_h + ring_t, 3);
    difference() {
        translate([0, 0, z0 + plate_t / 2]) cylinder(d = plate_d, h = plate_t, center = true);
        // 3 x M5 for the fork feet, on a 110 mm bolt circle
        for (a = [0, 120, 240])
            rotate([0, 0, a]) translate([55, 0, z0 + plate_t / 2])
                cylinder(d = 5.5, h = plate_t + 4, center = true);
        // lightening ring, keeps the print under 150 g
        for (a = [30, 90, 150, 210, 270, 330])
            rotate([0, 0, a]) translate([40, 0, z0 + plate_t / 2])
                cylinder(d = 14, h = plate_t + 4, center = true);
    }
    // fixed axis marker
    translate([0, plate_d / 2 - 6, z0 + plate_t]) cube([3, 8, 1.5], center = true);
}

module hub() {
    // Bolted to the platter's underside; the coupler's upper half grips its
    // 5 mm spigot.
    z0 = ex(base_t + tower_h + deck_t + post_h + ring_t - 6, 3);
    difference() {
        translate([0, 0, z0 + 3]) cylinder(d = hub_d, h = 6, center = true);
        for (a = [0, 120, 240])
            rotate([0, 0, a]) translate([28, 0, z0 + 3])
                cylinder(d = 4.4, h = 10, center = true);
    }
    // spigot down into the coupler
    translate([0, 0, z0 - 7]) cylinder(d = shaft_d, h = 8);
}

// --- assembly ---------------------------------------------------------------
module azimuth_axis() {
    base_plate();
    tower();
    deck();

    // motor: face plate up against the deck's underside
    translate([0, 0, base_t + tower_h])
        rotate([180, 0, 0]) nema17();

    // coupler, 22 mm, between the motor shaft and the hub spigot
    translate([0, 0, ex(base_t + tower_h + deck_t, 2) + 11])
        coupler(l = 22);

    // 3 posts + bearing ring
    for (a = [90, 210, 330])
        rotate([0, 0, a])
            translate([post_r, 0, ex(base_t + tower_h + deck_t + post_h / 2, 2)])
                difference() {
                    cylinder(d = 14, h = post_h, center = true);
                    translate([0, 0, 0]) cylinder(d = 4.4, h = post_h + 2, center = true);
                }
    translate([0, 0, ex(base_t + tower_h + deck_t + post_h + ring_t / 2, 2)])
        difference() {
            cylinder(d = plate_d, h = ring_t, center = true);
            cylinder(d = hub_d - 2, h = ring_t + 2, center = true);
        }

    hub();
    platter();
}

azimuth_axis();
