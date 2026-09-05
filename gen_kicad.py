#!/usr/bin/env python3
"""Generate a KiCad 7-format project for the PN5180 8-bay carrier board.

All connectivity is done with short wire stubs + global labels / power symbols,
so every pin position is computed from the embedded symbol definitions.
"""
import uuid, json, os, datetime

G = 2.54
def g(n): return n * G
def U(): return str(uuid.uuid4())
def f(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("", "-0") else s

PROJECT   = "pn5180_carrier"
OUTDIR    = os.path.dirname(os.path.abspath(__file__))  
ROOT_UUID = U()
LIBNAME   = "carrier"
FONT      = "(effects (font (size 1.27 1.27)))"
FONT_H    = "(effects (font (size 1.27 1.27)) hide)"

# ---------------------------------------------------------------------------
# Symbol library (lib coords: +y is UP, as in .kicad_sym files)
# pin tuple: (number, name, etype, x, y, rot, length)
#   rot 0 = pin on LEFT side pointing right, 180 = RIGHT side, 270 = TOP, 90 = BOTTOM
# ---------------------------------------------------------------------------
SYMS = {}

def add_sym(name, ref, body, pins, graphics="", pin_names_offset=1.016,
            hide_names=False, hide_numbers=False, power=False, desc=""):
    SYMS[name] = dict(ref=ref, body=body, pins={p[0]: p for p in pins},
                      pinlist=pins, graphics=graphics, off=pin_names_offset,
                      hide_names=hide_names, hide_numbers=hide_numbers,
                      power=power, desc=desc)

def lr(n, name, et, y, side, L=5.08):
    x = -(10.16 + L) if side == "L" else (10.16 + L)
    return (n, name, et, x, y, 0 if side == "L" else 180, L)

# 74HC138 3-to-8 decoder --------------------------------------------------
add_sym("74HC138", "U", (-10.16, 12.7, 10.16, -12.7), [
    lr("1", "A0", "input", 10.16, "L"), lr("2", "A1", "input", 7.62, "L"),
    lr("3", "A2", "input", 5.08, "L"),
    lr("4", "~{E1}", "input", 0, "L"), lr("5", "~{E2}", "input", -2.54, "L"),
    lr("6", "E3", "input", -5.08, "L"),
    lr("15", "~{Y0}", "output", 10.16, "R"), lr("14", "~{Y1}", "output", 7.62, "R"),
    lr("13", "~{Y2}", "output", 5.08, "R"), lr("12", "~{Y3}", "output", 2.54, "R"),
    lr("11", "~{Y4}", "output", 0, "R"), lr("10", "~{Y5}", "output", -2.54, "R"),
    lr("9", "~{Y6}", "output", -5.08, "R"), lr("7", "~{Y7}", "output", -7.62, "R"),
    ("16", "VCC", "power_in", 0, 17.78, 270, 5.08),
    ("8", "GND", "power_in", 0, -17.78, 90, 5.08),
], desc="3-to-8 line decoder, active-low outputs")

# 74HC151 8:1 multiplexer --------------------------------------------------
add_sym("74HC151", "U", (-10.16, 15.24, 10.16, -20.32), [
    lr("4", "D0", "input", 12.7, "L"), lr("3", "D1", "input", 10.16, "L"),
    lr("2", "D2", "input", 7.62, "L"), lr("1", "D3", "input", 5.08, "L"),
    lr("15", "D4", "input", 2.54, "L"), lr("14", "D5", "input", 0, "L"),
    lr("13", "D6", "input", -2.54, "L"), lr("12", "D7", "input", -5.08, "L"),
    lr("11", "S0", "input", -10.16, "L"), lr("10", "S1", "input", -12.7, "L"),
    lr("9", "S2", "input", -15.24, "L"), lr("7", "~{E}", "input", -17.78, "L"),
    lr("5", "Y", "output", 5.08, "R"), lr("6", "~{Y}", "output", 2.54, "R"),
    ("16", "VCC", "power_in", 0, 20.32, 270, 5.08),
    ("8", "GND", "power_in", 0, -25.4, 90, 5.08),
], desc="8-input multiplexer")

# TLV1117LV33 LDO ----------------------------------------------------------
add_sym("TLV1117LV33", "U", (-5.08, 5.08, 5.08, -5.08), [
    ("3", "VI", "power_in", -10.16, 0, 0, 5.08),
    ("2", "VO", "power_out", 10.16, 0, 180, 5.08),
    ("1", "GND", "power_in", 0, -10.16, 90, 5.08),
], desc="TI TLV1117LV33DCYR: 1A LDO, 3.3V fixed, ceramic-stable, Vin 2-5.5V, SOT-223 (1=GND 2=OUT/tab 3=IN)")

# Connectors ---------------------------------------------------------------
def conn(name, names, ref="J"):
    n = len(names)
    pins = [(str(i + 1), nm, "passive", -5.08, 12.7 - i * 2.54, 0, 2.54)
            for i, nm in enumerate(names)]
    body = (-2.54, 15.24, 10.16, 12.7 - (n - 1) * 2.54 - 2.54)
    add_sym(name, ref, body, pins, desc=f"{n}-pin connector")

conn("Conn_Bay", ["5V", "3V3", "~{RST}", "NSS", "MOSI", "MISO", "SCK", "BUSY", "GND", "GND"])
add_sym("Conn_PWR", "J", (-7.62, 5.08, 2.54, -2.54), [
    ("1", "24V", "passive", 5.08, 2.54, 180, 2.54),
    ("2", "GND", "passive", 5.08, 0, 180, 2.54),
], desc="2-way connector, 24V input from the printer PSU")

# Seeed XIAO ESP32C6 (socketed) --------------------------------------------
# Official Seeed numbering: 1-11 = D0-D10, 12 = 3V3 out, 13 = GND, 14 = 5V (USB VBUS)
XIAO_LEFT  = [("1", "D0/A0"), ("2", "D1/A1"), ("3", "D2/A2"), ("4", "D3"), ("5", "D4/SDA"),
              ("6", "D5/SCL"), ("7", "D6/TX")]
XIAO_RIGHT = [("14", "5V"), ("13", "GND"), ("12", "3V3_OUT"), ("11", "D10/MOSI"),
              ("10", "D9/MISO"), ("9", "D8/SCK"), ("8", "D7/RX")]
def _xt(nm):
    if nm == "GND" or nm == "5V": return "power_in"
    if nm == "3V3_OUT": return "power_out"
    return "bidirectional"
XIAO_PINS = [(n, nm, _xt(nm), -17.78, 7.62 - i * 2.54, 0, 5.08) for i, (n, nm) in enumerate(XIAO_LEFT)] + \
            [(n, nm, _xt(nm), 17.78, 7.62 - i * 2.54, 180, 5.08) for i, (n, nm) in enumerate(XIAO_RIGHT)]
add_sym("XIAO-ESP32C6", "U", (-12.7, 10.16, 12.7, -10.16), XIAO_PINS,
        desc="Seeed Studio XIAO ESP32C6 on two 1x7 sockets; pin numbers per Seeed's library (USB end = pins 1 and 14)")

# Schottky diode, KiCad convention pin 1 = K, pin 2 = A; drawn with A on the left
add_sym("D_Schottky", "D", None, [
    ("2", "A", "passive", -3.81, 0, 0, 2.54),
    ("1", "K", "passive", 3.81, 0, 180, 2.54),
], graphics="""
      (polyline (pts (xy -1.27 1.27) (xy -1.27 -1.27) (xy 1.27 0) (xy -1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
      (polyline (pts (xy 1.27 1.27) (xy 1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
      (polyline (pts (xy 0.635 1.27) (xy 1.27 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
      (polyline (pts (xy 1.27 -1.27) (xy 1.905 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))""",
    hide_names=True, hide_numbers=True, pin_names_offset=0, desc="Schottky diode (SOD-123, pad 1 = cathode)")

# 24V -> 5V buck: MP1584EN mini module (22.1 x 16.8 mm, 4 pads) ---------------
add_sym("MP1584EN_Module", "U", (-10.16, 5.08, 10.16, -5.08), [
    ("1", "IN+", "power_in", -15.24, 2.54, 0, 5.08),
    ("2", "IN-", "power_in", -15.24, -2.54, 0, 5.08),
    ("3", "OUT+", "power_out", 15.24, 2.54, 180, 5.08),
    ("4", "OUT-", "power_in", 15.24, -2.54, 180, 5.08),
], desc="MP1584EN mini buck module (D-SUN style, 22.1 x 16.8 mm), 4.5-28V in, set to 5.0V, 3A peak / 1.5A cont.")

add_sym("L", "L", None, [
    ("1", "1", "passive", -5.08, 0, 0, 2.54),
    ("2", "2", "passive", 5.08, 0, 180, 2.54),
], graphics="""
      (arc (start -2.54 0) (mid -1.905 0.635) (end -1.27 0) (stroke (width 0.254) (type default)) (fill (type none)))
      (arc (start -1.27 0) (mid -0.635 0.635) (end 0 0) (stroke (width 0.254) (type default)) (fill (type none)))
      (arc (start 0 0) (mid 0.635 0.635) (end 1.27 0) (stroke (width 0.254) (type default)) (fill (type none)))
      (arc (start 1.27 0) (mid 1.905 0.635) (end 2.54 0) (stroke (width 0.254) (type default)) (fill (type none)))""",
    hide_names=True, hide_numbers=True, pin_names_offset=0, desc="Inductor")

add_sym("Fuse", "F", None, [
    ("1", "1", "passive", -3.81, 0, 0, 1.27),
    ("2", "2", "passive", 3.81, 0, 180, 1.27),
], graphics="""
      (rectangle (start -2.54 0.762) (end 2.54 -0.762) (stroke (width 0.254) (type default)) (fill (type none)))
      (polyline (pts (xy -2.54 0) (xy 2.54 0)) (stroke (width 0.254) (type default)) (fill (type none)))""",
    hide_names=True, hide_numbers=True, pin_names_offset=0, desc="Fuse")

add_sym("D_TVS", "D", None, [
    ("1", "K", "passive", 0, 5.08, 270, 2.54),
    ("2", "A", "passive", 0, -5.08, 90, 2.54),
], graphics="""
      (polyline (pts (xy -1.27 -1.27) (xy 1.27 -1.27) (xy 0 1.27) (xy -1.27 -1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
      (polyline (pts (xy -1.905 0.635) (xy -1.27 1.27) (xy 1.27 1.27) (xy 1.905 1.905)) (stroke (width 0.254) (type default)) (fill (type none)))""",
    hide_names=True, hide_numbers=True, pin_names_offset=0, desc="TVS diode (SMA, pad 1 = cathode)")

add_sym("+24V", "#PWR", None, [("1", "+24V", "power_in", 0, 0, 90, 0)], graphics="""
      (polyline (pts (xy 0 0) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none)))
      (polyline (pts (xy -0.762 1.27) (xy 0 2.54) (xy 0.762 1.27) (xy -0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))""",
    hide_names=True, hide_numbers=True, pin_names_offset=0, power=True,
    desc="Power symbol creates a global label with name \"+24V\"")

# Passives -----------------------------------------------------------------
add_sym("R", "R", (-1.016, 2.54, 1.016, -2.54), [
    ("1", "~", "passive", 0, 5.08, 270, 2.54),
    ("2", "~", "passive", 0, -5.08, 90, 2.54),
], hide_names=True, hide_numbers=True, pin_names_offset=0, desc="Resistor")

RPACK_GFX = "".join(
    f"\n      (rectangle (start {f(x - 1.016)} 2.54) (end {f(x + 1.016)} -2.54) (stroke (width 0.254) (type default)) (fill (type background)))"
    for x in (-7.62, -2.54, 2.54, 7.62))
add_sym("R_Pack04", "RN", None,
    [(str(i + 1), f"R{i + 1}.1", "passive", x, 5.08, 270, 2.54) for i, x in enumerate((-7.62, -2.54, 2.54, 7.62))] +
    [(str(8 - i), f"R{i + 1}.2", "passive", x, -5.08, 90, 2.54) for i, x in enumerate((-7.62, -2.54, 2.54, 7.62))],
    graphics=RPACK_GFX, hide_names=True, pin_names_offset=0,
    desc="4 isolated resistors in one package (R1=1-8, R2=2-7, R3=3-6, R4=4-5)")

CAP_GFX = """
      (polyline (pts (xy -2.032 0.762) (xy 2.032 0.762)) (stroke (width 0.508) (type default)) (fill (type none)))
      (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762)) (stroke (width 0.508) (type default)) (fill (type none)))"""
add_sym("C", "C", None, [
    ("1", "~", "passive", 0, 5.08, 270, 4.064),
    ("2", "~", "passive", 0, -5.08, 90, 4.064),
], graphics=CAP_GFX, hide_names=True, hide_numbers=True, pin_names_offset=0,
    desc="Capacitor")
add_sym("C_Polarized", "C", None, [
    ("1", "~", "passive", 0, 5.08, 270, 4.064),
    ("2", "~", "passive", 0, -5.08, 90, 4.064),
], graphics=CAP_GFX + """
      (polyline (pts (xy -3.302 2.286) (xy -3.302 1.27)) (stroke (width 0.254) (type default)) (fill (type none)))
      (polyline (pts (xy -3.81 1.778) (xy -2.794 1.778)) (stroke (width 0.254) (type default)) (fill (type none)))""",
    hide_names=True, hide_numbers=True, pin_names_offset=0, desc="Polarized capacitor")

JP_GFX = """
      (circle (center -0.762 0) (radius 0.635) (stroke (width 0.254) (type default)) (fill (type none)))
      (circle (center 0.762 0) (radius 0.635) (stroke (width 0.254) (type default)) (fill (type none)))
      (polyline (pts (xy -0.762 0.889) (xy 0.762 0.889)) (stroke (width 0.254) (type default)) (fill (type none)))
      (polyline (pts (xy -0.762 -0.889) (xy 0.762 -0.889)) (stroke (width 0.254) (type default)) (fill (type none)))"""
add_sym("SolderJumper", "JP", None, [
    ("1", "A", "passive", -3.81, 0, 0, 2.54),
    ("2", "B", "passive", 3.81, 0, 180, 2.54),
], graphics=JP_GFX, hide_names=True, hide_numbers=True, pin_names_offset=0,
    desc="Solder jumper, 2 pads")

# Power symbols ------------------------------------------------------------
add_sym("+5V", "#PWR", None, [("1", "+5V", "power_in", 0, 0, 90, 0)], graphics="""
      (polyline (pts (xy 0 0) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none)))
      (polyline (pts (xy -0.762 1.27) (xy 0 2.54) (xy 0.762 1.27) (xy -0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))""",
    hide_names=True, hide_numbers=True, pin_names_offset=0, power=True,
    desc="Power symbol creates a global label with name \"+5V\"")
add_sym("+3V3", "#PWR", None, [("1", "+3V3", "power_in", 0, 0, 90, 0)], graphics="""
      (polyline (pts (xy 0 0) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none)))
      (polyline (pts (xy -0.762 1.27) (xy 0 2.54) (xy 0.762 1.27) (xy -0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))""",
    hide_names=True, hide_numbers=True, pin_names_offset=0, power=True,
    desc="Power symbol creates a global label with name \"+3V3\"")
add_sym("GND", "#PWR", None, [("1", "GND", "power_in", 0, 0, 270, 0)], graphics="""
      (polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none)))""",
    hide_names=True, hide_numbers=True, pin_names_offset=0, power=True,
    desc="Power symbol creates a global label with name \"GND\", ground")
add_sym("PWR_FLAG", "#FLG", None, [("1", "pwr", "power_out", 0, 0, 90, 0)], graphics="""
      (polyline (pts (xy 0 0) (xy 0 1.27) (xy -1.016 1.905) (xy 0 2.54) (xy 1.016 1.905) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none)))""",
    hide_names=True, hide_numbers=True, pin_names_offset=0, power=True,
    desc="Special symbol for telling ERC where power comes from")

POWER_LIB = {"+5V", "+3V3", "+24V", "GND", "PWR_FLAG"}
def lib_id(name): return f"power:{name}" if name in POWER_LIB else f"{LIBNAME}:{name}"

# ---------------------------------------------------------------------------
# Emit a library symbol (used for both lib_symbols in the sheet and .kicad_sym)
# ---------------------------------------------------------------------------
def emit_symbol(name, prefix):
    s = SYMS[name]
    full = f"{prefix}{name}"
    hdr = f'(symbol "{full}"'
    if s["power"]: hdr += " (power)"
    if s["hide_numbers"]: hdr += " (pin_numbers hide)"
    hdr += f' (pin_names (offset {f(s["off"])})' + (" hide)" if s["hide_names"] else ")")
    hdr += " (in_bom yes) (on_board yes)"
    if s["power"]:
        ref_eff, val_at = FONT_H, "(at 0 3.556 0)" if name != "GND" else "(at 0 -3.81 0)"
    else:
        ref_eff, val_at = FONT, "(at 0 -2.54 0)"
    out = [hdr,
           f'    (property "Reference" "{s["ref"]}" (at 0 2.54 0) {ref_eff})',
           f'    (property "Value" "{name}" {val_at} {FONT})',
           f'    (property "Footprint" "" (at 0 0 0) {FONT_H})',
           f'    (property "Datasheet" "" (at 0 0 0) {FONT_H})',
           f'    (property "ki_description" "{s["desc"].replace(chr(34), chr(92)+chr(34))}" (at 0 0 0) {FONT_H})',
           f'    (symbol "{name}_0_1"']
    if s["body"]:
        x1, y1, x2, y2 = s["body"]
        out.append(f'      (rectangle (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) '
                   f'(stroke (width 0.254) (type default)) (fill (type background)))')
    if s["graphics"]:
        out.append(s["graphics"].rstrip())
    out.append("    )")
    out.append(f'    (symbol "{name}_1_1"')
    for (num, nm, et, x, y, rot, L) in s["pinlist"]:
        hide = " hide" if L == 0 else ""
        out.append(f'      (pin {et} line (at {f(x)} {f(y)} {rot}) (length {f(L)}){hide}')
        out.append(f'        (name "{nm}" {FONT})')
        out.append(f'        (number "{num}" {FONT})')
        out.append("      )")
    out.append("    )")
    out.append("  )")
    return "\n".join(out)

# ---------------------------------------------------------------------------
# Schematic content accumulators
# ---------------------------------------------------------------------------
wires, junctions, labels, ncs, texts, insts = [], [], [], [], [], []
pwr_n = [0]; flg_n = [0]
used_syms = set()

def wire(a, b):
    wires.append(f'  (wire (pts (xy {f(a[0])} {f(a[1])}) (xy {f(b[0])} {f(b[1])}))\n'
                 f'    (stroke (width 0) (type default))\n    (uuid {U()})\n  )')

def junction(p):
    junctions.append(f'  (junction (at {f(p[0])} {f(p[1])}) (diameter 0) (color 0 0 0 0)\n    (uuid {U()})\n  )')

def glabel(name, p, rot):
    just = "left" if rot in (0, 90) else "right"
    labels.append(f'  (global_label "{name}" (shape passive) (at {f(p[0])} {f(p[1])} {rot})\n'
                  f'    (effects (font (size 1.27 1.27)) (justify {just}))\n    (uuid {U()})\n  )')

def no_connect(p):
    ncs.append(f'  (no_connect (at {f(p[0])} {f(p[1])}) (uuid {U()}))')

def text(s, p, size=1.27, bold=False):
    b = " bold" if bold else ""
    s = s.replace('"', '\\"')
    texts.append(f'  (text "{s}" (at {f(p[0])} {f(p[1])} 0)\n'
                 f'    (effects (font (size {f(size)} {f(size)}){b}) (justify left bottom))\n    (uuid {U()})\n  )')

def text_h(s, p, just):
    texts.append(f'  (text "{s}" (at {f(p[0])} {f(p[1])} 0)\n'
                 f'    (effects (font (size 1.27 1.27)) (justify {just}))\n    (uuid {U()})\n  )')

class Inst:
    def __init__(self, ref, sym, X, Y, rot=0, value=None, footprint="",
                 dnp=False, ref_at=None, val_at=None, hide_ref=False, hide_val=False):
        self.ref, self.sym, self.X, self.Y, self.rot = ref, sym, X, Y, rot
        self.value = value if value is not None else sym
        self.footprint, self.dnp = footprint, dnp
        self.ref_at, self.val_at = ref_at, val_at
        self.hide_ref, self.hide_val = hide_ref, hide_val
        self.uuid = U()
        self.extra = {}
        used_syms.add(sym)
        insts.append(self)

    def pin(self, num):
        p = SYMS[self.sym]["pins"][num]
        x, y, rot = p[3], p[4], p[5]
        assert self.rot == 0 or (x == 0 and y == 0), "rotation only supported for power symbols"
        return (self.X + x, self.Y - y), rot

    def emit(self):
        s = SYMS[self.sym]
        ra = self.ref_at or (self.X, self.Y)
        va = self.val_at or (self.X, self.Y)
        rj = "(justify left)" if not self.hide_ref else "hide"
        vj = "(justify left)" if not self.hide_val else "hide"
        if s["power"]:
            rj, vj = "hide", ("hide" if self.hide_val else "")
        out = [f'  (symbol (lib_id "{lib_id(self.sym)}") (at {f(self.X)} {f(self.Y)} {self.rot}) (unit 1)',
               f'    (in_bom yes) (on_board yes) (dnp {"yes" if self.dnp else "no"})',
               f'    (uuid {self.uuid})',
               f'    (property "Reference" "{self.ref}" (at {f(ra[0])} {f(ra[1])} 0)',
               f'      (effects (font (size 1.27 1.27)) {rj})',
               f'    )',
               f'    (property "Value" "{self.value}" (at {f(va[0])} {f(va[1])} 0)',
               f'      (effects (font (size 1.27 1.27)) {vj})',
               f'    )',
               f'    (property "Footprint" "{self.footprint}" (at {f(self.X)} {f(self.Y)} 0)',
               f'      (effects (font (size 1.27 1.27)) hide)',
               f'    )',
               f'    (property "Datasheet" "" (at {f(self.X)} {f(self.Y)} 0)',
               f'      (effects (font (size 1.27 1.27)) hide)',
               f'    )']
        for k, v in self.extra.items():
            out += [f'    (property "{k}" "{v}" (at {f(self.X)} {f(self.Y)} 0)',
                    f'      (effects (font (size 1.27 1.27)) hide)',
                    f'    )']
        for num in s["pins"]:
            out.append(f'    (pin "{num}" (uuid {U()}))')
        out += [f'    (instances',
                f'      (project "{PROJECT}"',
                f'        (path "/{ROOT_UUID}"',
                f'          (reference "{self.ref}") (unit 1)',
                f'        )',
                f'      )',
                f'    )',
                f'  )']
        return "\n".join(out)

# -- stub helpers -----------------------------------------------------------
STUB = 5.08

def stub_label(inst, num, net, length=STUB):
    p, rot = inst.pin(num)
    if rot == 0:     e, lrot = (p[0] - length, p[1]), 180
    elif rot == 180: e, lrot = (p[0] + length, p[1]), 0
    elif rot == 270: e, lrot = (p[0], p[1] - length), 90
    else:            e, lrot = (p[0], p[1] + length), 270
    wire(p, e); glabel(net, e, lrot)
    return e

def power_symbol(net, p, srot):
    if net == "PWR_FLAG":
        flg_n[0] += 1; ref = f"#FLG0{flg_n[0]}"
    else:
        pwr_n[0] += 1; ref = f"#PWR0{pwr_n[0]:02d}"
    # value text placement: outward side of the graphic
    d = 3.81 if net != "GND" else 4.318
    if srot == 0:   va = (p[0], p[1] - d) if net != "GND" else (p[0], p[1] + d)
    elif srot == 180: va = (p[0], p[1] + d) if net != "GND" else (p[0], p[1] - d)
    elif srot == 90:  va = (p[0] - d - 1.5, p[1]) if net != "GND" else (p[0] + d + 1.5, p[1])
    else:             va = (p[0] + d + 1.5, p[1]) if net != "GND" else (p[0] - d - 1.5, p[1])
    if srot in (90, 270):
        Inst(ref, net, p[0], p[1], rot=srot, value=net, val_at=va, hide_val=True)
        left = (srot == 90) if net != "GND" else (srot == 270)
        tx = p[0] - 3.302 if left else p[0] + 3.302
        text_h(net, (tx, p[1]), "right" if left else "left")
    else:
        Inst(ref, net, p[0], p[1], rot=srot, value=net, val_at=va)

def stub_power(inst, num, net, length=2.54):
    """Stub from a pin to a power symbol. Side pins get a rotated symbol pointing outward."""
    p, rot = inst.pin(num)
    up = net != "GND"
    if rot == 270:   # top pin
        e = (p[0], p[1] - length); srot = 0 if up else 180
    elif rot == 90:  # bottom pin
        e = (p[0], p[1] + length); srot = 180 if up else 0
    elif rot == 0:   # left side pin -> symbol points left
        e = (p[0] - length, p[1]); srot = 90 if up else 270
    else:            # right side pin -> symbol points right
        e = (p[0] + length, p[1]); srot = 270 if up else 90
    wire(p, e); power_symbol(net, e, srot)
    return e

def stub_nc(inst, num):
    p, _ = inst.pin(num); no_connect(p)

# ---------------------------------------------------------------------------
# Footprints (stock KiCad 7/8/9 library names)
# ---------------------------------------------------------------------------
FP_SOIC16 = "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm"
FP_SOT223 = "Package_TO_SOT_SMD:SOT-223-3_TabPin2"
FP_R0603  = "Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder"
FP_RARRAY = "Resistor_SMD:R_Array_Convex_4x0603"
FP_C0603  = "Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder"
FP_C1210  = "Capacitor_SMD:C_1210_3225Metric_Pad1.33x2.70mm_HandSolder"
FP_CM10   = "Connector_Molex:Molex_CLIK-Mate_502494-1070_1x10-1MP_P2.00mm_Horizontal"
FP_XIAO   = f"{LIBNAME}:Seeed_XIAO_2x7_Socket"
FP_SOD123 = "Diode_SMD:D_SOD-123"
FP_SOD128 = "Diode_SMD:D_SOD-128"
FP_SMA    = "Diode_SMD:D_SMA"
FP_NANO2  = "Fuse:Fuse_Littelfuse-NANO2-451_453"
FP_MP1584 = f"{LIBNAME}:MP1584EN_Module_22x17"
FP_CM2    = "Connector_Molex:Molex_CLIK-Mate_502494-0270_1x02-1MP_P2.00mm_Horizontal"
FP_JP_OPEN = "Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm"
FP_JP_BRG  = "Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm"

# ---------------------------------------------------------------------------
# Place the design
# ---------------------------------------------------------------------------
def ic(ref, sym, X, Y, value, fp, dnp=False):
    top = SYMS[sym]["body"][1]; bot = SYMS[sym]["body"][3]
    return Inst(ref, sym, X, Y, value=value, footprint=fp, dnp=dnp,
                ref_at=(X - 10.16, Y - top - 2.54), val_at=(X - 17.78, Y - bot + 2.54))

def connector(ref, sym, X, Y, value, fp):
    top = SYMS[sym]["body"][1]; bot = SYMS[sym]["body"][3]
    return Inst(ref, sym, X, Y, value=value, footprint=fp,
                ref_at=(X - 2.54, Y - top - 1.905), val_at=(X - 2.54, Y - bot + 1.905))

def passive(ref, sym, X, Y, value, fp, dnp=False):
    return Inst(ref, sym, X, Y, value=value, footprint=fp, dnp=dnp,
                ref_at=(X + 2.54, Y - 1.27), val_at=(X + 2.54, Y + 1.27))

# --- Power input, LDO ------------------------------------------------------
J10 = connector("J10", "Conn_PWR", g(8), g(14), "24V IN (CLIK-Mate 1x2)", FP_CM2)
J10.ref_at = (g(8) - 7.62, g(14) - 7.62); J10.val_at = (g(8) - 7.62, g(14) + 5.08)
stub_label(J10, "1", "24V_J"); stub_power(J10, "2", "GND")

C6 = passive("C6", "C", g(16), g(15), "220uF", FP_C1210)
stub_power(C6, "1", "+5V"); stub_power(C6, "2", "GND")
C7 = passive("C7", "C", g(21), g(15), "220uF", FP_C1210, dnp=True)
stub_power(C7, "1", "+5V"); stub_power(C7, "2", "GND")

C4 = passive("C4", "C", g(26), g(15), "10uF", FP_C0603)
stub_power(C4, "1", "+5V"); stub_power(C4, "2", "GND")

U4 = ic("U4", "TLV1117LV33", g(37), g(14), "TLV1117LV33DCYR", FP_SOT223)
U4.ref_at = (g(37) - 5.08, g(14) - 7.62); U4.val_at = (g(37) - 19.05, g(14) + 8.89)
stub_power(U4, "3", "+5V"); stub_power(U4, "2", "+3V3"); stub_power(U4, "1", "GND")

C5 = passive("C5", "C", g(48), g(15), "22uF", FP_C0603)
stub_power(C5, "1", "+3V3"); stub_power(C5, "2", "GND")

# PWR_FLAGs (ERC): flag -- wire -- power symbol
for i, (net, X) in enumerate((("+5V", g(48)), ("GND", g(52)))):
    top = (X, g(27)); bot = (X, g(30))
    power_symbol("PWR_FLAG", top, 0)
    wire(top, bot)
    power_symbol(net, bot, 180 if net != "GND" else 0)

# Solder jumpers
JP1 = passive("JP1", "SolderJumper", g(37), g(23), "JP1 5V->ESP32 (bridged)", FP_JP_BRG)
JP1.ref_at = (g(37) - 1.27, g(23) - 3.175); JP1.val_at = (g(37) - 3.81, g(23) + 3.175)
stub_power(JP1, "1", "+5V"); stub_label(JP1, "2", "5V_ESP")

JP2 = passive("JP2", "SolderJumper", g(37), g(27), "JP2 3V3->bays (bridged)", FP_JP_BRG)
JP2.ref_at = (g(37) - 1.27, g(27) - 3.175); JP2.val_at = (g(37) - 3.81, g(27) + 3.175)
stub_power(JP2, "1", "+3V3"); stub_label(JP2, "2", "3V3_BAY")

# --- Seeed XIAO ESP32C6 in the middle of the board, on 1x7 sockets --------
U5 = ic("U5", "XIAO-ESP32C6", g(20), g(40), "XIAO ESP32C6", FP_XIAO)
U5.ref_at = (g(20) - 12.7, g(40) - 10.16 - 2.54); U5.val_at = (g(20) - 12.7, g(40) + 10.16 + 2.54)
XIAO_MAP = {  # pin number -> net (D-name in README)
    "1": "A0", "2": "A1", "3": "A2", "4": "~{EN}", "5": "BUSY", "6": "~{RST}",
    "9": "SCK_IN", "10": "MISO", "11": "MOSI_IN", "14": "5V_XIAO",
}
for num, net in XIAO_MAP.items():
    stub_label(U5, num, net)
stub_power(U5, "13", "GND")
for num in ("7", "8", "12"):
    stub_nc(U5, num)
# Series Schottky: the XIAO's 5V pin is USB VBUS with no diode, so the carrier supplies it through D1
D1 = passive("D1", "D_Schottky", g(46), g(34), "PMEG2010AEH", FP_SOD123)
D1.ref_at = (g(46) - 2.54, g(34) - 3.175); D1.val_at = (g(46) - 6.35, g(34) + 3.175)
stub_label(D1, "2", "5V_ESP"); stub_label(D1, "1", "5V_XIAO")
# PWR_FLAG on 5V_XIAO (ERC: U5 5V pin is power_in)
_fp = (g(38), g(31)); power_symbol("PWR_FLAG", _fp, 0); wire(_fp, (_fp[0], _fp[1] + 5.08)); glabel("5V_XIAO", (_fp[0], _fp[1] + 5.08), 270)

# Pull-ups / pull-downs on the ESP32 lines
R1 = passive("R1", "R", g(8), g(57), "10k", FP_R0603)
stub_power(R1, "1", "+3V3"); stub_label(R1, "2", "~{EN}")
R5 = passive("R5", "R", g(12), g(57), "10k", FP_R0603)
stub_power(R5, "1", "+3V3"); stub_label(R5, "2", "~{RST}")
for i, (ref, net) in enumerate((("R2", "A0"), ("R3", "A1"), ("R4", "A2"))):
    R = passive(ref, "R", g(16 + 4 * i), g(57), "10k", FP_R0603)
    stub_label(R, "1", net); stub_power(R, "2", "GND")
# series termination for the 8-way cable fan-out (source side of the star)
R6 = passive("R6", "R", g(28), g(57), "33R", FP_R0603)
stub_label(R6, "1", "SCK_IN"); stub_label(R6, "2", "SCK")
R7 = passive("R7", "R", g(32), g(57), "33R", FP_R0603)
stub_label(R7, "1", "MOSI_IN"); stub_label(R7, "2", "MOSI")

# --- Decoder / muxes -------------------------------------------------------
U1 = ic("U1", "74HC138", g(64), g(20), "74HC138", FP_SOIC16)
stub_label(U1, "1", "A0"); stub_label(U1, "2", "A1"); stub_label(U1, "3", "A2")
stub_label(U1, "4", "~{EN}")
stub_power(U1, "5", "GND"); stub_power(U1, "6", "+3V3")
for i, num in enumerate(("15", "14", "13", "12", "11", "10", "9", "7")):
    stub_label(U1, num, f"NSS{i}")
stub_power(U1, "16", "+3V3"); stub_power(U1, "8", "GND")
C1 = passive("C1", "C", g(84), g(20), "100nF", FP_C0603)
stub_power(C1, "1", "+3V3"); stub_power(C1, "2", "GND")

def mux(ref, Y, prefix, outnet, dnp, cref):
    Um = ic(ref, "74HC151", g(64), Y, "74HC151", FP_SOIC16, dnp=dnp)
    for i, num in enumerate(("4", "3", "2", "1", "15", "14", "13", "12")):
        stub_label(Um, num, f"{prefix}{i}")
    stub_label(Um, "11", "A0"); stub_label(Um, "10", "A1"); stub_label(Um, "9", "A2")
    stub_power(Um, "7", "GND")
    stub_label(Um, "5", outnet); stub_nc(Um, "6")
    stub_power(Um, "16", "+3V3"); stub_power(Um, "8", "GND")
    Cm = passive(cref, "C", g(84), Y, "100nF", FP_C0603, dnp=dnp)
    stub_power(Cm, "1", "+3V3"); stub_power(Cm, "2", "GND")
    return Um

U2 = mux("U2", g(48), "BUSY", "BUSY", False, "C2")

# BUSY / IRQ pull-downs as 4x100k arrays (undefined inputs on unpopulated bays)
def rpack(ref, X, Y, nets, dnp=False):
    RN = Inst(ref, "R_Pack04", X, Y, value="4x100k", footprint=FP_RARRAY, dnp=dnp,
              ref_at=(X + 10.16, Y - 1.27), val_at=(X + 10.16, Y + 1.27))
    for num, net in zip(("1", "2", "3", "4"), nets):
        stub_label(RN, num, net)
    xs = [X + dx for dx in (-7.62, -2.54, 2.54, 7.62)]
    rail = Y + 7.62
    for num, x in zip(("8", "7", "6", "5"), xs):
        p, _ = RN.pin(num); wire(p, (x, rail))
    for a, b in ((xs[0], xs[1]), (xs[1], X), (X, xs[2]), (xs[2], xs[3])):
        wire((a, rail), (b, rail))
    for x in (xs[1], X, xs[2]):
        junction((x, rail))
    power_symbol("GND", (X, rail), 0)
    return RN

rpack("RN1", g(10), g(90), [f"BUSY{i}" for i in range(4)])
rpack("RN2", g(22), g(90), [f"BUSY{i}" for i in range(4, 8)])

# --- 24V input protection + MP1584EN buck module (bottom-left) --------------------
F1 = passive("F1", "Fuse", g(34), g(88), "1A slow", FP_NANO2)
F1.ref_at = (g(34) - 1.27, g(88) - 2.54); F1.val_at = (g(34) - 3.81, g(88) + 2.794)
stub_label(F1, "1", "24V_J")
D3 = passive("D3", "D_Schottky", g(44), g(88), "PMEG6030EP", FP_SOD128)
D3.ref_at = (g(44) - 2.54, g(88) - 3.175); D3.val_at = (g(44) - 6.35, g(88) + 3.175)
D2 = passive("D2", "D_TVS", g(40), g(93), "SMAJ28A", FP_SMA)
_k = D2.pin("1")[0]; _t = (_k[0], F1.pin("2")[0][1])      # T-point on the fuse->Schottky line
wire(F1.pin("2")[0], _t); wire(_t, D3.pin("2")[0]); wire(_k, _t); junction(_t)
stub_power(D2, "2", "GND")
stub_power(D3, "1", "+24V")
for ref, X, val, fp in (("C8", g(30), "10uF/50V", FP_C1210), ("C9", g(34), "10uF/50V", FP_C1210)):
    Cx = passive(ref, "C", X, g(95), val, fp)
    stub_power(Cx, "1", "+24V"); stub_power(Cx, "2", "GND")
U6 = ic("U6", "MP1584EN_Module", g(52), g(97), "MP1584EN module (set 5.0V)", FP_MP1584)
U6.ref_at = (g(52) - 10.16, g(97) - 5.08 - 2.54); U6.val_at = (g(52) - 17.78, g(97) + 5.08 + 2.54)
stub_power(U6, "1", "+24V"); stub_power(U6, "2", "GND")
stub_power(U6, "3", "+5V");  stub_power(U6, "4", "GND")
_fp = (g(56), g(27)); power_symbol("PWR_FLAG", _fp, 0); wire(_fp, (_fp[0], _fp[1] + 7.62)); power_symbol("+24V", (_fp[0], _fp[1] + 7.62), 180)

# --- Bay connectors --------------------------------------------------------
for i in range(8):
    col = g(106) if i < 4 else g(140)
    row = g(16 + 16 * (i % 4))
    J = connector(f"J{i + 1}", "Conn_Bay", col, row, f"Bay {i} (CLIK-Mate 1x10)", FP_CM10)
    stub_power(J, "1", "+5V")
    stub_label(J, "2", "3V3_BAY")
    stub_label(J, "3", "~{RST}")
    stub_label(J, "4", f"NSS{i}")
    stub_label(J, "5", "MOSI")
    stub_label(J, "6", "MISO")
    stub_label(J, "7", "SCK")
    stub_label(J, "8", f"BUSY{i}")
    stub_power(J, "9", "GND")
    stub_power(J, "10", "GND")

# --- Notes -----------------------------------------------------------------
notes = [
    ("PN5180 8-BAY CARRIER - DESIGN NOTES", True),
    ("XIAO ESP32C6 pins: D8 SCK, D9 MISO, D10 MOSI, D3 ~{EN}, D0 A0, D1 A1, D2 A2, D4 BUSY, D5 ~{RST}; D6/D7 spare.", False),
    ("Bay select: A0..A2 -> 74HC138 address; ~{EN} (active low) = NSS of the addressed bay only.", False),
    ("BUSY = 74HC151 output for the addressed bay. Change A0..A2 only while ~{EN} is high.", False),
    ("Bays 4..7 (J5..J8) may be left unpopulated for a 4-bay build; RN1/RN2 keep unused BUSY inputs low.", False),
    ("JP1 (bridged) -> D1 Schottky -> XIAO 5V pin: the XIAO 5V pin is raw USB VBUS, D1 keeps the carrier from back-feeding USB.", False),
    ("JP2 (bridged): feeds carrier 3V3 to bay pin 2. Open it if your modules regulate 3V3 onboard.", False),
    ("Power: 24V from the printer PSU on J10 (~0.5 A). F1 1A -> D2 TVS -> D3 reverse Schottky -> C8/C9 -> U6 MP1584EN module -> 5V.", False),
    ("U6: MP1584EN mini module (28V max in) soldered flat on 4 pads. Set its pot to 5.00V BEFORE fitting; lock the pot with a dab of varnish.", False),
    ("Keep SPI <= 1 MHz with 8 bays on shared SCK/MOSI/MISO. Bay pinout matches the module header order.", False),
    ("All SMD except the XIAO sockets. Connectors: Molex CLIK-Mate 2.00mm RA receptacles (502494-xx70), housings 502439-xx00, terminals 502438.", False),
    ("Cables ~30 cm: R6/R7 (33R) source-terminate SCK/MOSI for the 8-way fan-out. SPI <= 1 MHz, ESP32 GPIO drive strength low.", False),
    ("U5 sits on two 1x7 female headers, 15.24 mm apart; antenna end (opposite USB) over the board edge, no copper under it.", False),
]
notes += [
    ("Bay connector (J1..J8): 1=5V 2=3V3 3=~{RST} 4=NSS 5=MOSI 6=MISO 7=SCK 8=BUSY 9=GND 10=GND (2nd return, twist with SCK).", False),
    ("U5 pins 1-7 = D0..D6 (USB end first), 8-11 = D7..D10, 12 = 3V3 out (NC), 13 = GND, 14 = 5V/VBUS (USB end)", False),
]
for k, (s, b) in enumerate(notes):
    text(s, (g(96), g(74) + k * 3.81), size=1.524 if b else 1.27, bold=b)

# ---------------------------------------------------------------------------
# Sourcing: manufacturer, MPN, Mouser part number, per reference
# ---------------------------------------------------------------------------
P = {  # key: (Manufacturer, MPN, Mouser #, description)
    "hc138": ("Texas Instruments", "SN74HC138DR", "595-SN74HC138DR", "3-to-8 decoder, SOIC-16"),
    "hc151": ("Texas Instruments", "SN74HC151DR", "595-SN74HC151DR", "8:1 mux, SOIC-16"),
    "ldo":   ("Texas Instruments", "TLV1117LV33DCYR", "595-TLV1117LV33DCYR", "3.3V 1A LDO, ceramic-stable, SOT-223"),
    "cm10":  ("Molex", "502494-1070", "538-502494-1070", "CLIK-Mate 2.00mm RA SMT receptacle 1x10, positive lock"),
    "xiao":  ("Seeed Studio", "XIAO ESP32C6 (SKU 113991182)", "713-113991182", "XIAO ESP32C6 module, 2x7 pins on 15.24mm (user-supplied; verify Mouser #)"),
    "d1":    ("Nexperia", "PMEG2010AEH", "771-PMEG2010AEH", "Schottky 20V 1A SOD-123"),
    "mp1584":("Generic (D-SUN style)", "MP1584EN mini buck module", "", "22x17mm adjustable module, user-supplied (Amazon); set to 5.0V"),
    "fuse":  ("Littelfuse", "0453001.MR", "576-0453001.MR", "1A slow-blow SMD fuse, NANO2"),
    "tvs":   ("Littelfuse", "SMAJ28A", "576-SMAJ28A", "TVS 28V standoff, 400W, SMA"),
    "d3":    ("Nexperia", "PMEG6030EP", "771-PMEG6030EP", "Schottky 60V 3A SOD-128 (reverse polarity)"),
    "c10u50":("Murata", "GRM32ER71H106KA12L", "81-GRM32ER71H106KA12L", "10uF 50V X7R 1210"),

    "cm2":   ("Molex", "502494-0270", "538-502494-0270", "CLIK-Mate 2.00mm RA SMT receptacle 1x2, positive lock"),
    "r33":   ("Yageo", "RC0603FR-0733RL", "603-RC0603FR-0733RL", "33R 1% 0603"),
    "r10k":  ("Yageo", "RC0603FR-0710KL", "603-RC0603FR-0710KL", "10k 1% 0603"),
    "rn100k":("Yageo", "YC164-FR-07100KL", "603-YC164-FR-07100KL", "4x100k 1% isolated array, 0603x4"),
    "c100n": ("Murata", "GRM188R71H104KA93D", "81-GRM188R71H104KA93D", "100nF 50V X7R 0603"),
    "c10u":  ("Murata", "GRM188R61A106KE69D", "81-GRM188R61A106KE69D", "10uF 10V X5R 0603"),
    "c22u":  ("Murata", "GRM188R60J226MEA0D", "81-GRM188R60J226MEA0D", "22uF 6.3V X5R 0603"),
    "c220u": ("Taiyo Yuden", "MSASJ32MAB5227MPNDT1", "963-MSASJ32MAB5227MP", "220uF 6.3V X5R 1210"),
    "jp":    ("", "", "", "PCB solder jumper, no part"),
}
REF2PART = {"U1": "hc138", "U2": "hc151", "U4": "ldo",
            "U5": "xiao", "D1": "d1", "J10": "cm2", "U6": "mp1584", "F1": "fuse", "D2": "tvs", "D3": "d3", "C8": "c10u50", "C9": "c10u50", "JP1": "jp", "JP2": "jp", "R6": "r33", "R7": "r33",
            "C1": "c100n", "C2": "c100n", "C3": "c100n", "C4": "c10u", "C5": "c22u",
            "C6": "c220u", "C7": "c220u"}
REF2PART.update({f"J{i}": "cm10" for i in range(1, 9)})
REF2PART.update({f"R{i}": "r10k" for i in range(1, 6)})
REF2PART.update({f"RN{i}": "rn100k" for i in range(1, 5)})

for inst in insts:
    if inst.ref in REF2PART:
        mfr, mpn, mou, desc = P[REF2PART[inst.ref]]
        inst.extra = {"Manufacturer": mfr, "MPN": mpn, "Mouser": mou, "Description": desc}

CABLE_PARTS = [  # (Manufacturer, MPN, Mouser #, qty, description)
    ("Molex", "502439-1000", "538-502439-1000", 8, "CLIK-Mate 2.00mm positive-lock housing 1x10 (bay cables)"),
    ("Wurth Elektronik", "61300711821", "710-61300711821", 2, "WR-PHD 1x7 female socket header 2.54mm, THT (XIAO sockets)"),
    ("Molex", "502439-0200", "538-502439-0200", 1, "CLIK-Mate 2.00mm positive-lock housing 1x2 (5V cable)"),
    ("Molex", "502438-0100", "538-502438-0100", 100, "CLIK-Mate 2.00mm crimp terminal, loose, tin, 22-26 AWG (82 needed + spares)"),
]

def write_boms(outdir):
    import csv
    groups = {}
    for inst in insts:
        if inst.ref not in REF2PART: continue
        key = (REF2PART[inst.ref], inst.dnp)
        groups.setdefault(key, []).append(inst)
    def refsort(r):
        import re
        m = re.match(r"([A-Z]+)(\d+)", r); return (m.group(1), int(m.group(2)))
    rows = []
    for (pk, dnp), lst in groups.items():
        mfr, mpn, mou, desc = P[pk]
        refs = sorted((i.ref for i in lst), key=refsort)
        val = lst[0].value if len({i.value for i in lst}) == 1 else desc
        rows.append([", ".join(refs), len(refs), val, SYMS[lst[0].sym]["ref"], mfr, mpn, mou,
                     lst[0].footprint, "DNP" if dnp else "", desc])
    rows.sort(key=lambda r: refsort(r[0].split(",")[0]))
    with open(f"{outdir}/{PROJECT}_bom.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["References", "Qty", "Value", "Type", "Manufacturer", "MPN", "Mouser Part Number",
                    "Footprint", "Populate", "Description"])
        w.writerows(rows)
    # Mouser BOM-tool import: populated board parts + cable-side parts, one board
    with open(f"{outdir}/{PROJECT}_mouser_order.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Mouser Part Number", "Quantity", "Manufacturer Part Number", "Description", "Customer Part Number"])
        for r in rows:
            if r[8] == "DNP" or not r[6]: continue
            w.writerow([r[6], r[1], r[5], r[9], r[0]])
        for mfr, mpn, mou, qty, desc in CABLE_PARTS:
            w.writerow([mou, qty, mpn, desc, "cable"])
    return rows

# ---------------------------------------------------------------------------
# Write files
# ---------------------------------------------------------------------------
os.makedirs(OUTDIR, exist_ok=True)
today = datetime.date.today().isoformat()

lib_syms = "\n".join(emit_symbol(n, "power:" if n in POWER_LIB else f"{LIBNAME}:")
                     for n in sorted(used_syms))
sch = f"""(kicad_sch (version 20230121) (generator eeschema)

  (uuid {ROOT_UUID})

  (paper "A3")

  (title_block
    (title "PN5180 8-Bay NFC Reader Carrier")
    (date "{today}")
    (rev "1.3")
    (company "hyiger")
    (comment 1 "74HC138 chip-select decoder + 74HC151 BUSY/IRQ mux, 5 ESP32 GPIOs for 8 readers")
    (comment 2 "Generated with gen_kicad.py")
  )

  (lib_symbols
{lib_syms}
  )

{chr(10).join(junctions)}
{chr(10).join(ncs)}
{chr(10).join(wires)}
{chr(10).join(texts)}
{chr(10).join(labels)}
{chr(10).join(i.emit() for i in insts)}

  (sheet_instances
    (path "/" (page "1"))
  )
)
"""
with open(f"{OUTDIR}/{PROJECT}.kicad_sch", "w") as fh:
    fh.write(sch)

# Project-local symbol library with the same custom symbols
custom = [n for n in sorted(used_syms) if n not in POWER_LIB]
lib = "(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor)\n" + \
      "\n".join(emit_symbol(n, "") for n in custom) + "\n)\n"
with open(f"{OUTDIR}/{LIBNAME}.kicad_sym", "w") as fh:
    fh.write(lib)

def xiao_footprint():
    """Pads and outline taken from Seeed's OPL 'XIAO-ESP32-C6-DIP' footprint (CC-BY-SA-4.0):
    THT pins on y = +/-7.62 (15.24 mm rows), x = -7.62..7.62 at 2.54; USB end at +x.
    Pad size/drill changed to the 1.7/1.0 mm used for 2.54 mm female sockets."""
    L = ['(footprint "Seeed_XIAO_2x7_Socket" (version 20221018) (generator pcbnew)',
         '  (layer "F.Cu")',
         '  (descr "Seeed Studio XIAO (ESP32C6 etc.) on two 1x7 2.54mm female sockets, 15.24mm row spacing. '
         'Pin 1 (D0) and pin 14 (5V) at the USB end (+x). Geometry from Seeed OPL XIAO-ESP32-C6-DIP; '
         'board 21 x 17.8 mm. Antenna at the -x end: keep copper clear.")',
         '  (tags "XIAO Seeed socket module ESP32C6")',
         '  (attr through_hole)']
    def txt(kind, text, x, y, layer, size=1.0, th=0.15, rot=0):
        L.append(f'  (fp_text {kind} "{text}" (at {f(x)} {f(y)} {rot}) (layer "{layer}")\n'
                 f'    (effects (font (size {size} {size}) (thickness {th})))\n    (tstamp {U()})\n  )')
    def rect(x1, y1, x2, y2, layer, w):
        L.append(f'  (fp_rect (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (layer "{layer}") (width {w}) (fill none) (tstamp {U()}))')
    def line(x1, y1, x2, y2, layer, w):
        L.append(f'  (fp_line (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (layer "{layer}") (width {w}) (tstamp {U()}))')
    txt("reference", "REF**", 0, -11.5, "F.SilkS")
    txt("value", "XIAO ESP32C6", 0, 11.5, "F.Fab")
    txt("user", "${REFERENCE}", 0, 0, "F.Fab")
    txt("user", "ANTENNA", -7.5, 0, "F.SilkS", 0.7, 0.1, 90)
    txt("user", "USB", 9.4, 0, "F.Fab", 0.7, 0.1, 90)
    # board outline (Seeed: x -10.425..10.55, y +/-8.9), USB connector stub at +x
    rect(-10.425, -8.9, 10.55, 8.9, "F.Fab", 0.1)
    rect(-10.9, -9.4, 11.0, 9.4, "F.CrtYd", 0.05)
    line(-10.414, -6.985, -10.414, 6.985, "F.SilkS", 0.12)
    line(-8.509, -8.89, 8.636, -8.89, "F.SilkS", 0.12)
    line(-8.509, 8.89, 8.636, 8.89, "F.SilkS", 0.12)
    line(10.541, -6.985, 10.541, 6.985, "F.SilkS", 0.12)
    line(10.541, -4.5, 12.05, -4.5, "F.SilkS", 0.12)
    line(12.05, -4.5, 12.05, 4.5, "F.SilkS", 0.12)
    line(12.05, 4.5, 10.541, 4.5, "F.SilkS", 0.12)
    rect(-10.425, -4.0, -6.0, 4.0, "F.SilkS", 0.12)      # antenna keep-out marker
    for yc in (-7.62, 7.62):                             # 1x7 socket bodies
        rect(-8.89, yc - 1.27, 8.89, yc + 1.27, "F.Fab", 0.1)
    line(9.2, -9.6, 9.8, -9.0, "F.SilkS", 0.12)          # pin-1 chevron by pad 1
    line(9.2, -9.6, 8.6, -9.0, "F.SilkS", 0.12)
    for i in range(7):
        x = 7.62 - i * 2.54
        n1, n2 = i + 1, 14 - i                            # top row 1..7 (right->left), bottom row 14..8
        L.append(f'  (pad "{n1}" thru_hole {"rect" if n1 == 1 else "oval"} (at {f(x)} -7.62) (size 1.7 1.7) (drill 1) (layers *.Cu *.Mask) (tstamp {U()}))')
        L.append(f'  (pad "{n2}" thru_hole oval (at {f(x)} 7.62) (size 1.7 1.7) (drill 1) (layers *.Cu *.Mask) (tstamp {U()}))')
    L.append(')')
    return "\n".join(L) + "\n"

def mp1584_footprint():
    """MP1584EN mini module, 22.098 x 16.764 mm, four plated pads on an 18.542 x 8.128 mm
    rectangle (module dimension drawing). Carrier pads are 3.0 mm THT rings with a 1.0 mm
    drill so the module can be soldered flat through its own holes, or on short pin stubs."""
    L = ['(footprint "MP1584EN_Module_22x17" (version 20221018) (generator pcbnew)',
         '  (layer "F.Cu")',
         '  (descr "MP1584EN mini buck module (D-SUN style) 22.1 x 16.8 mm mounted flat; pads at +/-9.271, +/-4.064 mm. '
         '1 = IN+, 2 = IN-, 3 = OUT+, 4 = OUT-. IN side at -x, OUT side at +x. Verify pad labels on the module before soldering.")',
         '  (tags "MP1584 buck module")',
         '  (attr through_hole)']
    def txt(kind, text, x, y, layer, size=1.0, th=0.15, rot=0):
        L.append(f'  (fp_text {kind} "{text}" (at {f(x)} {f(y)} {rot}) (layer "{layer}")\n'
                 f'    (effects (font (size {size} {size}) (thickness {th})))\n    (tstamp {U()})\n  )')
    def rect(x1, y1, x2, y2, layer, w):
        L.append(f'  (fp_rect (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (layer "{layer}") (width {w}) (fill none) (tstamp {U()}))')
    txt("reference", "REF**", 0, -10.0, "F.SilkS")
    txt("value", "MP1584EN module", 0, 10.0, "F.Fab")
    txt("user", "${REFERENCE}", 0, 0, "F.Fab")
    txt("user", "IN", -9.3, 0, "F.SilkS", 0.8, 0.12, 90)
    txt("user", "OUT", 9.3, 0, "F.SilkS", 0.8, 0.12, 90)
    txt("user", "+", -9.3, -6.6, "F.SilkS", 0.9, 0.15)
    txt("user", "+", 9.3, -6.6, "F.SilkS", 0.9, 0.15)
    rect(-11.05, -8.38, 11.05, 8.38, "F.Fab", 0.1)
    rect(-11.05, -8.38, 11.05, 8.38, "F.SilkS", 0.12)
    rect(-11.55, -8.88, 11.55, 8.88, "F.CrtYd", 0.05)
    for n, (x, y) in enumerate(((-9.271, -4.064), (-9.271, 4.064), (9.271, -4.064), (9.271, 4.064)), start=1):
        L.append(f'  (pad "{n}" thru_hole {"rect" if n == 1 else "circle"} (at {f(x)} {f(y)}) (size 3 3) (drill 1) '
                 f'(layers *.Cu *.Mask) (tstamp {U()}))')
    L.append(')')
    return "\n".join(L) + "\n"

os.makedirs(f"{OUTDIR}/{LIBNAME}.pretty", exist_ok=True)
with open(f"{OUTDIR}/{LIBNAME}.pretty/MP1584EN_Module_22x17.kicad_mod", "w") as fh:
    fh.write(mp1584_footprint())
with open(f"{OUTDIR}/{LIBNAME}.pretty/Seeed_XIAO_2x7_Socket.kicad_mod", "w") as fh:
    fh.write(xiao_footprint())
with open(f"{OUTDIR}/fp-lib-table", "w") as fh:
    fh.write('(fp_lib_table\n  (version 7)\n'
             f'  (lib (name "{LIBNAME}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIBNAME}.pretty")(options "")(descr "PN5180 carrier custom footprints"))\n)\n')

with open(f"{OUTDIR}/sym-lib-table", "w") as fh:
    fh.write('(sym_lib_table\n  (version 7)\n'
             f'  (lib (name "{LIBNAME}")(type "KiCad")(uri "${{KIPRJMOD}}/{LIBNAME}.kicad_sym")(options "")(descr "PN5180 carrier custom symbols"))\n)\n')

pro = {
    "board": {"design_settings": {"defaults": {}, "rules": {}}},
    "boards": [],
    "cvpcb": {"equivalence_files": []},
    "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},
    "meta": {"filename": f"{PROJECT}.kicad_pro", "version": 1},
    "net_settings": {"classes": [{"name": "Default", "clearance": 0.2, "track_width": 0.25,
                                  "via_diameter": 0.8, "via_drill": 0.4,
                                  "diff_pair_gap": 0.25, "diff_pair_width": 0.2, "diff_pair_via_gap": 0.25,
                                  "microvia_diameter": 0.3, "microvia_drill": 0.1, "wire_width": 6, "bus_width": 12,
                                  "line_style": 0, "schematic_color": "rgba(0, 0, 0, 0.000)", "pcb_color": "rgba(0, 0, 0, 0.000)"}],
                     "meta": {"version": 3}, "net_colors": None, "netclass_assignments": None,
                     "netclass_patterns": []},
    "pcbnew": {"page_layout_descr_file": ""},
    "schematic": {"legacy_lib_dir": "", "legacy_lib_list": []},
    "sheets": [[ROOT_UUID, "Root"]],
    "text_variables": {},
}
with open(f"{OUTDIR}/{PROJECT}.kicad_pro", "w") as fh:
    json.dump(pro, fh, indent=2)

bom_rows = write_boms(OUTDIR)
print(f"wrote {OUTDIR}: {len(insts)} symbols, {len(wires)} wires, {len(labels)} labels, {len(ncs)} no-connects")
