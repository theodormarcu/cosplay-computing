// powerbank_cradle.scad
// Removable power-bank cradle for the magma-cube orb's detachable bottom.
//
// Holds a ~75 x 45 x 25 mm USB-C power bank in a snug pocket that pulls
// straight out (finger notch) for air travel. Includes a cable exit slot,
// zip-tie strain-relief holes, and optional detent bumps / Velcro strap slots.
//
// Print: PLA/PETG, 0.2 mm layers, 3 walls, 20% infill. No supports needed
// (pocket opens upward). Glue or screw the base into the printed bottom,
// or set base_dia > 0 to print a round tray that drops into the orb bottom.
//
// Open in OpenSCAD: F5 preview, F6 render, then Export as STL.

// ── Power bank dimensions (MEASURE yours; defaults from the listing) ──
pb_w = 75;          // width  (long edge that lies flat)
pb_l = 45;          // length (short edge)
pb_h = 25;          // height (thickness)

// ── Fit & structure ──────────────────────────────────────────────────
clr        = 0.5;   // clearance per side (FDM prints run small; 0.4-0.6 ok)
wall       = 2.4;   // pocket wall thickness (~3 perimeters @ 0.4 nozzle)
floor_t    = 2.0;   // pocket floor thickness
pocket_depth = pb_h;// how deep the pocket holds the bank (<= pb_h)
corner_r   = 3;     // outer corner rounding
chamfer    = 1.5;   // entry chamfer at the pocket lip

// ── Features (toggle on/off) ─────────────────────────────────────────
finger_notch = true;   // U-scallop to grab and pull the bank out
notch_w      = 22;     // width of finger notch
notch_depth  = 16;     // how far down from the lip the notch cuts

cable_slot   = true;   // slot for the USB-C cable to exit toward the board
cable_w      = 12;     // cable slot width
cable_h      = 7;      // cable slot height (above the floor)

ziptie       = true;   // strain-relief holes (anchor cable, protect board port)
ziptie_d     = 4;      // hole diameter for a small zip tie
ziptie_gap   = 8;      // spacing between the two zip-tie holes

detents      = true;   // small bumps that "click" the bank in but release easily
detent_r     = 1.2;    // bump radius
detent_frac  = 0.7;    // height up the pocket where bumps sit (0..1)

velcro       = false;  // slots for a strap over the top (belt-and-suspenders)
strap_w      = 25;     // strap width
strap_h      = 4;      // strap slot height

base_dia     = 0;      // >0 = add a round tray of this dia to drop into the orb
base_t       = 2.5;    // round tray thickness

$fn = 64;

// ── Derived ──────────────────────────────────────────────────────────
in_w = pb_w + 2*clr;             // pocket inner width
in_l = pb_l + 2*clr;             // pocket inner length
out_w = in_w + 2*wall;           // cradle outer width
out_l = in_l + 2*wall;           // cradle outer length
out_h = floor_t + pocket_depth;  // cradle outer height
top_z = out_h;                   // z of the pocket lip
eps = 0.1;

// ── Helpers ──────────────────────────────────────────────────────────
// Rounded box: footprint w x l, height h, vertical-edge radius r.
module rbox(w, l, h, r) {
    linear_extrude(height = h)
        offset(r = r) offset(r = -r)
            square([w, l], center = true);
}

// ── Build ────────────────────────────────────────────────────────────
module cradle() {
    union() {
        difference() {
            // Solid outer body
            rbox(out_w, out_l, out_h, corner_r);

            // Hollow pocket (open top)
            translate([0, 0, floor_t])
                rbox(in_w, in_l, pocket_depth + eps, max(0.1, corner_r - wall));

            // Entry chamfer around the lip
            if (chamfer > 0)
                translate([0, 0, top_z - chamfer + eps])
                    rotate_extrude()
                        translate([in_w/2, 0, 0])  // approx on the wider axis
                            polygon([[0,0],[ -chamfer - eps, 0],[0, chamfer + eps]]);

            // Finger notch on the +Y long wall
            if (finger_notch) {
                translate([0, out_l/2, top_z - notch_depth/2 + eps])
                    cube([notch_w, wall*4, notch_depth + eps], center = true);
                translate([0, out_l/2, top_z - notch_depth])
                    rotate([90, 0, 0])
                        cylinder(h = wall*4, r = notch_w/2, center = true);
            }

            // Cable exit slot on the +X short wall, just above the floor
            if (cable_slot)
                translate([out_w/2, 0, floor_t + cable_h/2])
                    cube([wall*4, cable_w, cable_h], center = true);

            // Zip-tie strain-relief holes through the floor near the cable
            if (ziptie)
                for (s = [-1, 1])
                    translate([out_w/2 - wall - 5, s*ziptie_gap/2, -eps])
                        cylinder(h = floor_t + 2*eps, d = ziptie_d);

            // Velcro strap slots through both long walls near the top
            if (velcro)
                for (s = [-1, 1])
                    translate([0, s*out_l/2, top_z - strap_h*1.5])
                        cube([strap_w, wall*4, strap_h], center = true);
        }

        // Detent bumps on the inner long walls (added back in)
        if (detents)
            for (s = [-1, 1])
                translate([0, s*(in_l/2), floor_t + pocket_depth*detent_frac])
                    sphere(r = detent_r);
    }
}

// Optional round tray to seat the cradle in the orb bottom
module base_tray() {
    if (base_dia > 0)
        translate([0, 0, -base_t])
            cylinder(h = base_t, d = base_dia);
}

base_tray();
cradle();
