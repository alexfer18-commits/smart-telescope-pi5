// Shared dimensions for the smart-telescope mechanical design.
// All values in millimetres, taken from the official drawings:
//   Raspberry Pi 5 PCB 85 x 56, mounting holes M2.5 on a 58 x 49 grid.
//   Camera Module 3 PCB 25 x 24, mounting holes M2 on a 21 x 12.5 grid.
//   Hailo-8L AI HAT+ 65 x 56.5, holes on the Pi's 58 x 49 grid.
//   NEMA 17 (17HS4401) 42.3 x 42.3 body, M3 on a 31 x 31 grid,
//   pilot boss 22 dia, shaft 5 dia, 24 long.

pi5_pcb = [85, 56, 1.6];
pi5_hole_grid = [58, 49];
pi5_hole_d = 2.7;          // M2.5 clearance

cam_pcb = [25, 24, 1.6];
cam_hole_grid = [21, 12.5];
cam_hole_d = 2.2;          // M2 clearance
cam_lens_d = 14;           // lens barrel opening

hailo_pcb = [65, 56.5, 1.6];
hailo_standoff_h = 11;     // clears the Pi's USB/Ethernet connectors

nema_body = 42.3;
nema_hole_grid = 31;
nema_hole_d = 3.4;         // M3 clearance
nema_boss_d = 22;
nema_shaft_d = 5.05;
nema_shaft_len = 24;

tube_d = 60;               // guidescope OTA outside diameter
tube_clamp_w = 18;
wall = 3;
clearance = 0.4;           // FDM fit allowance
$fn = 64;
