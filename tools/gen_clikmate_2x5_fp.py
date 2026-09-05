#!/usr/bin/env python3
"""Generate the KiCad footprint for Molex CLIK-Mate 1.50 mm dual-row RA SMT receptacle
503148-1090 (2x5, 10 circuits) from Molex's catalog drawing (recommended PCB pattern).

Coordinates (mm), KiCad footprint frame (Y positive = down on screen):
  origin        = body centre
  body          = 11.80 (X) x 8.75 (Y), rear edge at Y=-4.375, mating face at Y=+4.375
  signal pads   = 10 x (0.55 x 2.70) at 0.75 mm pitch, one line at the rear; rear pad
                  edge flush with the body rear; pad 1 at +X (Molex top view: circuit 1
                  right, circuit N left, mating face toward the viewer's bottom)
  nail pads     = 2 x (1.20 x 4.65), outer edge flush with the body ends (X = +/-5.30),
                  front-to-back position scaled from the drawing: top 3.95 mm below the
                  signal pad rear edge, bottom 0.15 mm inside the mating face
Written in the KiCad 7 footprint format (20221018) like the other carrier.pretty files.
"""
import uuid, sys

NAME = "Molex_CLIK-Mate_503148-1090_2x05-1MP_P1.50mm_Horizontal"
PITCH = 0.75
PAD_W, PAD_L = 0.55, 2.70
BODY_X, BODY_Y = 11.80, 8.75
NAIL_W, NAIL_L = 1.20, 4.65
NAIL_X = BODY_X / 2 - NAIL_W / 2            # 5.30
REAR = -BODY_Y / 2                          # -4.375
FRONT = BODY_Y / 2                          # +4.375
PAD_Y = REAR + PAD_L / 2                    # -3.025
NAIL_TOP = REAR + 4.10                      # -0.275: nail front edge on the mating-face datum
NAIL_Y = NAIL_TOP + NAIL_L / 2              # +2.05
# The pad line is NOT centred: odd-circuit tails exit straight under the 1.5 mm contact
# columns (0, +/-1.5, +/-3.0) and even-circuit tails jog 0.75 mm toward circuit N, so the
# ten pads run from +3.0 (pad 1) to -3.75 (pad 10) — 0.375 mm off the body centreline.
PAD1_X = 3.0
CY_X = BODY_X / 2 + 0.25
CY_REAR = REAR - 0.25                       # -4.625
CY_FRONT = 5.0                              # housing may protrude ~0.4 past the nails
SILK_OFF = 0.11

def ts():
    return str(uuid.uuid4())

def f(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return s if s not in ("-0", "") else "0"

def line(x1, y1, x2, y2, layer, width):
    return (f'  (fp_line (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) '
            f'(layer "{layer}") (width {width}) (tstamp {ts()}))')

def text(kind, s, y, layer, hide=False):
    h = " hide" if hide else ""
    return (f'  (fp_text {kind} "{s}" (at 0 {f(y)} 0) (layer "{layer}"){h}\n'
            f'    (effects (font (size 1.0 1.0) (thickness 0.15)))\n'
            f'    (tstamp {ts()})\n  )')

out = []
out.append(f'(footprint "{NAME}" (version 20221018) (generator pcbnew)')
out.append('  (layer "F.Cu")')
out.append('  (descr "Molex CLIK-Mate 1.50mm dual-row right-angle SMT receptacle 503148-1090 (2x5, 10 circuits), '
           'mates with housing 503149-1000 / terminals 502579. Geometry from Molex\'s catalog drawing for '
           'series 503148 (recommended PCB pattern, re-measured at 600 dpi): 10 pads 0.55x2.70 at 0.75mm in '
           'one line at the rear, rear pad edge flush with the body rear; the line is offset 0.375mm toward '
           'circuit N (odd-circuit tails sit under the 1.5mm contact columns, even-circuit tails jog 0.75mm '
           'toward N): pad 1 at X=+3.0, pad 10 at X=-3.75. Two nail pads 1.20x4.65 at X=+/-5.30, front edge on '
           'the mating-face datum 8.75 behind the pad rear edge; body 11.8x8.75, height 9.15. Datum: body '
           'centre, mating face at +Y. Confirm the nail-to-pad-1 dimension and the 1..10 lead order against '
           'Molex SD-503148-1090 before fab. Molex top view: circuit 1 on the right, circuit N on the left.")')
out.append('  (tags "connector Molex CLIK-Mate dual row horizontal 503148")')
out.append('  (attr smd)')
out.append(text("reference", "REF**", -6.2, "F.SilkS"))
out.append(text("value", NAME, 5.7, "F.Fab"))
out.append(text("user", "${REFERENCE}", 0.6, "F.Fab"))

# F.Fab body outline with pin-1 chamfer at the +X rear corner
hx, ch = BODY_X / 2, 0.8
out.append(line(-hx, REAR, hx - ch, REAR, "F.Fab", 0.1))
out.append(line(hx - ch, REAR, hx, REAR + ch, "F.Fab", 0.1))
out.append(line(hx, REAR + ch, hx, FRONT, "F.Fab", 0.1))
out.append(line(hx, FRONT, -hx, FRONT, "F.Fab", 0.1))
out.append(line(-hx, FRONT, -hx, REAR, "F.Fab", 0.1))
# mating-face marker on F.Fab: short arrow-ish line pair at the front centre
out.append(line(-0.6, FRONT - 0.9, 0, FRONT - 0.2, "F.Fab", 0.1))
out.append(line(0.6, FRONT - 0.9, 0, FRONT - 0.2, "F.Fab", 0.1))

# F.SilkS: front edge between the nail pads, rear corners clear of the pad row, sides above the nail pads
sx = hx + SILK_OFF          # 6.01
sf = FRONT + SILK_OFF       # 4.485
sr = REAR - SILK_OFF        # -4.485
nail_inner = NAIL_X - NAIL_W / 2          # 4.70
out.append(line(-(nail_inner - 0.15), sf, nail_inner - 0.15, sf, "F.SilkS", 0.12))
for sgn in (-1, 1):
    out.append(line(sgn * sx, sr, sgn * sx, NAIL_TOP - 0.25, "F.SilkS", 0.12))
    # rear stubs stop clear of the end pads (pad 1 edge +3.275, pad 10 edge -4.025)
    out.append(line(sgn * sx, sr, 4.0 if sgn > 0 else -4.4, sr, "F.SilkS", 0.12))
# pin-1 triangle pointing at pad 1
x1 = PAD1_X
out.append(f'  (fp_poly (pts (xy {f(x1)} -4.85) (xy {f(x1-0.3)} -5.35) (xy {f(x1+0.3)} -5.35)) '
           f'(layer "F.SilkS") (width 0.1) (fill solid) (tstamp {ts()}))')

# F.CrtYd
out.append(line(-CY_X, CY_REAR, CY_X, CY_REAR, "F.CrtYd", 0.05))
out.append(line(CY_X, CY_REAR, CY_X, CY_FRONT, "F.CrtYd", 0.05))
out.append(line(CY_X, CY_FRONT, -CY_X, CY_FRONT, "F.CrtYd", 0.05))
out.append(line(-CY_X, CY_FRONT, -CY_X, CY_REAR, "F.CrtYd", 0.05))

# pads
for k in range(1, 11):
    x = x1 - PITCH * (k - 1)
    # 0.20 mm gap between adjacent pads: KiCad's DRC does not apply the netclass clearance
    # between pads of one footprint (verified on a scratch board with the project rules),
    # and 0.20 mm meets the board minimum and JLCPCB's 0.127 mm spacing.
    out.append(f'  (pad "{k}" smd roundrect (at {f(x)} {f(PAD_Y)}) (size {f(PAD_W)} {f(PAD_L)}) '
               f'(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.25) (tstamp {ts()}))')
for sgn in (-1, 1):
    out.append(f'  (pad "MP" smd roundrect (at {f(sgn*NAIL_X)} {f(NAIL_Y)}) (size {f(NAIL_W)} {f(NAIL_L)}) '
               f'(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio 0.2) (tstamp {ts()}))')
# simplified VRML model (carrier.3dshapes, generated by gen_3d_models.py); replace with Molex's
# STEP for 503148-1090 when available
out.append('  (model "${KIPRJMOD}/carrier.3dshapes/Molex_CLIK-Mate_503148-1090_2x05_RA.wrl"\n'
           '    (offset (xyz 0 0 0))\n    (scale (xyz 1 1 1))\n    (rotate (xyz 0 0 0))\n  )')
out.append(')')

body = "\n".join(out) + "\n"
for path in sys.argv[1:]:
    open(path, "w").write(body)
    print("wrote", path, len(body), "bytes")
