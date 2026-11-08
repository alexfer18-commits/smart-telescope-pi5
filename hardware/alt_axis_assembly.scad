// Altitude axis: fork on the azimuth platter, NEMA 17 on the +X cheek,
// rigid coupler, 8 mm shaft in two bearings, tube saddle.
//
// The altitude axis is the only one that sees gravity: the tube's centre of
// mass must sit ON this axis or the motor has to hold a static torque
// (docs/mechanical_analysis.md, section 2). The saddle's slot lets the tube
// slide fore and aft until it balances.
//
// explode = 0 assembled, 1 shows the stack apart.
include <params.scad>
use <nema17_coupling.scad>

explode = 0;

fork_h    = 120;      // cheek height above the platter
cheek_t   = 12;
cheek_y   = 70;
spread    = 72;       // cheeks at x = +/- spread
alt_z     = 105;      // altitude axis height above the platter
shaft_d   = 8.2;      // 8 mm shaft, clearance bore
bearing_d = 22.2;     // 608ZZ housing bore
saddle_w  = 100;

function ex(z, k) = z + k * explode * 10;

// --- fork -------------------------------------------------------------------
module foot() {
    difference() {
        translate([0, 0, 4]) cube([60, 90, 8], center = true);
        // 2 x M5 into the azimuth platter
        for (x = [-1, 1])
            translate([x * 20, 0, 4]) cylinder(d = 5.5, h = 12, center = true);
        // lightening
        translate([0, 0, 4]) cube([30, 50, 12], center = true);
    }
}

module cheek(side) {
    // side = +1 right (carries the motor), -1 left
    difference() {
        translate([side * (spread + cheek_t / 2), 0, fork_h / 2])
            cube([cheek_t, cheek_y, fork_h], center = true);
        // bearing housing
        translate([side * (spread + cheek_t / 2), 0, alt_z])
            rotate([0, 90, 0]) {
                cylinder(d = bearing_d, h = cheek_t + 16, center = true);
                cylinder(d = shaft_d, h = cheek_t + 18, center = true);
            }
        // triangular lightening cut, keeps the cheek stiff in bending
        translate([side * (spread + cheek_t / 2), 0, 40])
            rotate([0, 0, 0])
                cube([cheek_t + 2, 34, 60], center = true);
        // 2 x M6 through-bolts to the foot
        for (y = [-1, 1])
            translate([side * (spread + cheek_t / 2), y * 25, 10])
                cylinder(d = 6.6, h = cheek_t + 4, center = true);
    }
    // brace from the cheek to the platter foot
    translate([side * (spread - 10), 0, 8])
        rotate([0, 0, 0])
            linear_extrude(height = cheek_t, center = true)
                polygon([[0, 0], [0, 55], [-22, 0]]);
}

// --- altitude shaft ---------------------------------------------------------
module alt_shaft() {
    rotate([0, 90, 0])
        translate([0, 0, 0])
            cylinder(d = 8, h = 2 * spread + 40, center = true);
}

module shaft_hub() {
    // Clamps onto the shaft with an M6 pinch bolt, carries the saddle.
    difference() {
        translate([0, 0, 0]) cube([70, saddle_w, 34], center = true);
        rotate([0, 90, 0]) cylinder(d = 8.6, h = 80, center = true);
        // saddle bolt pattern, 2 x M6
        for (y = [-1, 1])
            translate([0, y * 36, 0]) cylinder(d = 6.6, h = 40, center = true);
        // split for the pinch bolt
        translate([0, 0, 0]) cube([80, 2, 6], center = true);
        translate([0, 0, -12]) rotate([0, 90, 0]) cylinder(d = 6.4, h = 80, center = true);
    }
}

// --- saddle -----------------------------------------------------------------
module saddle() {
    // V-block under the tube: it locates the OTA and lets it slide fore/aft.
    difference() {
        translate([0, 0, 0]) cube([76, saddle_w, 26], center = true);
        // the tube sits in this half-round
        rotate([0, 90, 0]) translate([0, 0, 0])
            cylinder(d = tube_d + clearance, h = 90, center = true);
        for (y = [-1, 1])
            translate([0, y * 36, 0]) cylinder(d = 6.6, h = 40, center = true);
    }
    // dovetail-style rib on the underside
    translate([0, 0, -15]) cube([30, saddle_w, 8], center = true);
}

module strap() {
    // Top half of the tube ring, 3 mm, 2 x M5 draw bolts.
    z = tube_d / 2 + 2;
    difference() {
        cylinder(d = tube_d + 2 * wall + 4, h = 16, center = true);
        cylinder(d = tube_d + clearance, h = 18, center = true);
        translate([0, -200, 0]) cube([400, 400, 20], center = true);
        for (x = [-1, 1])
            translate([x * (tube_d / 2 + wall + 1), 0, 0])
                cylinder(d = 5.5, h = 20, center = true);
    }
}

// --- assembly ---------------------------------------------------------------
module altitude_axis() {
    translate([-spread, 0, 0]) foot();
    translate([spread, 0, 0]) foot();
    cheek(-1);
    cheek(1);

    translate([0, 0, alt_z]) alt_shaft();
    translate([0, 0, alt_z]) shaft_hub();

    // motor on the right cheek, shaft along -X into the coupler
    translate([spread + cheek_t + 24 + ex(0, 1), 0, alt_z])
        rotate([0, 90, 0]) nema17();
    translate([spread + cheek_t + 12, 0, alt_z])
        rotate([0, 90, 0]) coupler(l = 22);

    // tube and saddle
    translate([0, 0, alt_z + 8]) saddle();
    translate([0, 0, alt_z + 8]) strap();
    %translate([0, 0, alt_z + 8])
        rotate([90, 0, 0]) cylinder(d = tube_d, h = 400, center = true);
}

altitude_axis();
