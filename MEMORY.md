# MEMORY — PN5180 8-bay carrier

Context and decision log for whoever picks this up. Written on the evening of 2026-09-03
(local, −07:00; the generator stamps its files 2026-09-04 because that session's clock
ran on UTC) by the design session this log calls "rev 1.5" — the script itself only
stamps rev 1.3, as do the sheet title block and README; the owner has hand-edited since.
Updated 2026-09-04 for the KiCad 10 migration, with measured layout and check status
(history item 11, "Layout state", "Check status"). All clock times below are local.

## Owner and purpose

- Owner: **hyiger** (use that name on documents, never a real name or email; git commits
  as `hyiger` with the GitHub no-reply address). Public repo since 2026-09-04:
  https://github.com/hyiger/pn5180_carrier (branch `main`). Experienced FDM
  practitioner and developer; runs a Prusa Core One and a Bambu H2D; maintains Filament DB
  (TypeScript/Electron, NFC spool tags via OpenPrintTag/SLIX2, ACR1552U reader, PN5180
  multi-reader spec) and PrusaSlicer/OrcaSlicer profile tooling. Comfortable with SMD
  hand assembly, KiCad, crimping.
- Purpose: a "spool rack" that detects which NFC-tagged spool is in which of 8 bays.
  One PN5180 breakout per bay, ~30 cm cable to this carrier, ESP32-C6 reports to
  Filament DB over Wi-Fi. Powered from the Core One's 24 V PSU.

## How the design got here (chronological, with reasons)

1. **Architecture**: 8 PN5180 on one SPI bus. RST, SCK, MOSI, MISO shared; NSS and BUSY
   per board. BUSY is mandatory (the PN5180 SPI handshake needs it); IRQ is optional and
   was later dropped entirely. 74HC138 (3 addr + enable → NSS) and 74HC151 (BUSY mux)
   sharing the address lines reduce 8 readers to 5 GPIOs. Rule: change A0–A2 only while
   /EN is high. Firmware sweeps bays round-robin with one RF field on at a time.
2. **Schematic generator**: `gen_kicad.py` writes KiCad 7 format (version 20230121) with
   embedded symbols, global labels on short stubs, deterministic layout. Validated by
   `kicad-cli sch export netlist` plus an assertion script every revision. (KiCad 7 had
   no `sch erc` in the CLI; the owner's KiCad 10 has both `sch erc` and `pcb drc` — item 11.)
3. **Connectors** went KK-254 → Micro-Fit 3.0 SMT (all-SMD request) → C-Grid III box
   header (30 cm cable, "clips in") → **Molex CLIK-Mate 2.00 mm** after the owner showed
   the Prusa LoveBoard's white latching connectors (a Prusa forum thread confirms those are
   CLIK-Mate). Right-angle 502494 chosen because KiCad has verified footprints for
   1×2/1×10/1×12 (the vertical 502443 1×10 is missing from the library). Housings
   502439-xx00, terminals 502438-0100 (22–26 AWG), 3 A/contact.
4. **Passives**: 0603 everywhere possible; 4×100k arrays (Yageo YC164) for BUSY
   pull-downs; 220 µF 6.3 V X5R 1210 (Taiyo Yuden MSASJ32MAB5227MPNDT1, owner's pick)
   instead of an electrolytic, with parallel DNP pads C7. DC-bias derating discussed:
   expect ~¼ of nominal at 5 V.
5. **LDO**: AMS1117 → **TLV1117LV33DCYR** (ceramic-stable, same SOT-223 pinout, Vin
   ≤ 5.5 V/6 V abs). C5 22 µF 0603 is ~10–12 µF effective at 3.3 V, meets TI's ≥ 10 µF.
6. **MCU**: ESP32-DevKitC → ESP32-C6-DevKitC-1 → **Seeed XIAO ESP32C6** (14 pins).
   Socket footprint geometry taken from Seeed's official OPL KiCad library
   (`XIAO-ESP32-C6-DIP`): THT rows 15.24 mm apart, 7 × 2.54 mm, pins 1 (D0) and 14 (5V)
   at the USB end, board 21 × 17.8 mm. Seeed pin numbering: 1–11 = D0–D10, 12 = 3V3 out,
   13 = GND, 14 = 5V. Seeed states the 5V pin is USB VBUS with no diode → D1 Schottky
   added in series from the carrier's 5 V.
7. **Power input**: 5 V terminal → 24 V from the printer PSU. First a discrete
   LMR51420 buck (36 V part, reference design captured), then replaced by an
   **MP1584EN mini module** (owner's preference, fixed-5 V variant, no pot — though every
   design file still says adjustable, "set to 5.0 V"; unresolved, see open questions) on four
   3 mm THT pads at ±9.271 × ±4.064 mm (module drawing: 22.098 × 16.764 mm board,
   18.542 × 8.128 mm pad rectangle). Input protection kept: F1 1 A NANO2, D2 SMAJ28A
   TVS (module is 28 V max), D3 PMEG6030EP reverse Schottky, C8/C9 10 µF 50 V.
8. **IRQ removed** (rev 1.3): U3/C3/RN3/RN4 deleted, bay pin 10 became a second GND,
   XIAO D6 freed.
9. **JP1/JP2**: were solder jumpers (5 V → XIAO, 3V3 → bays). Judged vestigial once D1
   existed and the module type was fixed; **owner removed both in the repo schematic**.
   The generator still has them (rev 1.5) — that is the known divergence.
10. **PN5180 modules need both rails**: 3.3 V feeds VBAT/PVDD, 5 V feeds TVDD (RF).
    With only 3.3 V, SPI works but the field is dead. Carrier supplies both. NXP wants
    TVDD to rise with/after VBAT; the boot-time /RST pulse covers the mild violation.
11. **KiCad 10 migration** (owner, by 2026-09-04): the project was opened and saved in
    KiCad 10.0.6. Consequences: (a) `kicad_sch` is now format 20260306 and `kicad_pcb`
    20260206 — no longer readable by KiCad 9 or older; `gen_kicad.py` still emits the
    KiCad 7 format, so generator output and repo files can only be compared via netlists.
    (b) KiCad 10's local-history feature created `.history/` (its own git repo, ~590
    autosave/save snapshots; Preferences > Common > Project Backup toggles it); opening
    the project also rewrote `pn5180_carrier.kicad_prl`, the ordinary per-user GUI-state
    file every KiCad since 6 writes. (c) `kicad-cli` is at
    `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli` (not on PATH) and now provides
    ERC and DRC. (d) The 10.0 netlist export is pretty-printed one attribute per line
    (7 and 8 wrote one compact node per line); that silently broke `check_netlist.py`'s
    regex parser (0 nets) — made whitespace-tolerant
    2026-09-04, and its `24V_F` expectation renamed to KiCad's auto-name `Net-(D2-K)`
    because that node carries no label in the schematic (nor in the generator). (e) ERC
    reports 81 `lib_symbol_mismatch` warnings: every embedded `power:` symbol differs from
    KiCad 10's power library. Cosmetic. (f) Gerbers and drill files were exported to
    `gerbers/` at 21:46 and zipped at 21:48. They match the current PCB (the 22:06 save is
    byte-identical to the 21:46:42 local-history snapshot; the 21:42:36 one differs only
    in two plot-setting lines the export wrote) but five nets were still unrouted, there
    are no mounting holes, and they carry the skewed right edge (g) — a preview, not a
    fab package. (g) The owner moved the outline out at 18:28–18:29: left edge 109.5 →
    108.0, right edge 169 → 170.5 — 1.5 mm per side, three times the 0.5 mm discussed —
    but the bottom-right corner only reached 170.0, so the right edge ran (170.5, 52) →
    (170.0, 158.5); DRC does not flag such a thing. **Fixed at 23:25** on the owner's
    instruction by editing the two Edge.Cuts coordinates in the file (KiCad closed, backup
    taken): outline is a true 108–170.5 × 52–158.5 rectangle again; DRC unchanged (15
    violations, 10 unconnected, 0 parity). The stored zone fills still stop at the old
    slanted edge until the zones are refilled in the GUI, and `gerbers/` predates the fix.

## Verified facts (don't re-derive)

Rows without a date come from the 2026-09-03 design session.

| Item | Value | Verified how |
|---|---|---|
| CLIK-Mate 2.00 RA 1×10 | Molex 502494-1070 | KiCad footprint exists; Molex listing |
| CLIK-Mate dual row | only in 1.50 mm: RA 503148-xx70, vertical 503154-xx90, housing 503149-xx00, terminal 502578; 2 A/contact; no KiCad footprint | Molex datasheet + series charts |
| XIAO ESP32C6 mechanicals | 2×7 THT, 15.24 mm rows, USB end = pins 1/14, 21 × 17.8 mm | Seeed OPL KiCad lib |
| XIAO 5V pin | direct USB VBUS, needs series diode for external feed | Seeed wiki |
| XIAO SPI | D8 SCK / D9 MISO / D10 MOSI; `SPI.begin()` default | Seeed wiki |
| TLV1117LV33DCYR | 1 A, Vin 2–5.5 V (6 V abs), ceramic-stable, ≥10 µF out | TI datasheet |
| MP1584EN module | 22.1 × 16.8 mm, pads 18.54 × 8.13 mm, 4.5–28 V in, 1.5 A cont. | module dimension drawing |
| LMR51420 (retired) | pinout 1 GND 2 SW 3 VIN 4 FB 5 EN 6 CB; 5 V ref: 10 µH, 2×22 µF, 100k/13.7k, 0.1 µF boot | TI datasheet |
| Taiyo Yuden 220 µF 1210 | MSASJ32MAB5227MPNDT1, 6.3 V X5R, Mouser 963-MSASJ32MAB5227MP, $1.72 | Mouser page |
| Mouser prefixes | 595 TI, 538 Molex, 603 Yageo, 81 Murata, 710 Würth, 771 Nexperia, 713 Seeed, 576 Littelfuse, 994 Coilcraft | live listings |
| Mouser numbers verified on a product page | 963-MSASJ32MAB5227MP, 538-90130-3310 (retired part) | — |
| Mouser numbers pattern-derived (spot-check at checkout) | all Murata 81-…, 713-113991182 (XIAO SKU), 710-61300711821 | — |
| Würth 1×7 socket | 61300711821 (WR-PHD series confirmed) | search |
| JLCPCB 2-layer limits | 0.127 trace/space, 0.3 drill, via 0.45–0.5 pad, 0.5 hole-hole, 0.2 edge, silk 0.15/1.0 | JLC capability pages |
| KiCad on the owner's Mac | 10.0.6; `kicad-cli` at `/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli`; stock libs under `…/Contents/SharedSupport/{symbols,footprints,3dmodels}`; bundled Python with `pcbnew` under `…/Contents/Frameworks/Python.framework/Versions/Current/bin/python3` | run 2026-09-04 |
| Stock footprints used by the PCB, all present in the 10.0 library | Capacitor_SMD C_0603/C_1210 HandSolder, Resistor_SMD R_0603 HandSolder + R_Array_Convex_4x0603, Diode_SMD D_SMA/D_SOD-123/D_SOD-128, Fuse_Littelfuse-NANO2-451_453, SOIC-16_3.9x9.9mm_P1.27mm, SOT-223-3_TabPin2, Molex_CLIK-Mate_502494-0270 and -1070 Horizontal | file check 2026-09-04 |
| Board outline | Rectangle, edge-line centres X 108.0–170.5, Y 52.0–158.5 → 62.5 × 106.5 mm, 0.05 mm stroke (bottom-right corner was at x 170.0 from 18:28 until fixed 23:25) | pcbnew 2026-09-04 23:25 |
| Connector tab pad to board edge | J5–J8: tab pads reach x 110.10–110.15, 2.10–2.15 mm to the edge. J1–J4: tab pads reach x 168.30–168.35, 2.15–2.20 mm. End connectors' tab pads are 1.25 mm from the top/bottom edges; J10's tab pads 0.65 mm from the bottom edge | pcbnew 2026-09-04 23:25 |
| Power netclass patterns | `+5V`, `+3V3`, `+24V`, `5V_*`, `24V_*`, `*D2-K*` (Default 0.25/0.25 via 0.6/0.3; Power 0.8/0.25 via 0.8/0.4) | .kicad_pro 2026-09-04 |
| Rasteriser | `cairosvg` absent everywhere; `qlmanage -t -s 2400 -o existing_dir file` → `file.png` works for PDF, footprint SVGs and the portrait board SVG (square render — crops the A3 schematic SVG, use the PDF); Pillow 12 in Homebrew python3 3.14 only | run 2026-09-04 |

## Pinouts and maps (as designed)

Bay connector J1–J8: 1 5V · 2 3V3 · 3 /RST · 4 NSS · 5 MOSI · 6 MISO · 7 SCK · 8 BUSY ·
9 GND · 10 GND. Bay *n* = J(n+1) = 74HC138 Y*n* = 74HC151 D*n* = RN(1+n÷4) element (n mod 4)+1.
Right-hand connectors are rotated 180° relative to the left column (absolute +90° vs −90°),
so pin 1 is at the bottom on J1–J4 and at the top on J5–J8.

XIAO: D0 A0, D1 A1, D2 A2, D3 /EN, D4 BUSY, D5 /RST, D6 spare, D7 spare, D8 SCK, D9 MISO,
D10 MOSI. GPIO numbers per Seeed: D0=0 D1=1 D2=2 D3=21 D4=22 D5=23 D6=16 D7=17 D8=19
D9=20 D10=18 (write code with the D names).

74HC138: 1 A0, 2 A1, 3 A2, 4 /E1=/EN, 5 /E2=GND, 6 E3=3V3, 7/9–15 Y7..Y0, 8 GND, 16 VCC.
74HC151: 4/3/2/1/15/14/13/12 = D0..D7, 11/10/9 = S0..S2, 7 /E=GND, 5 Y=BUSY, 6 /Y NC.

## Layout state (measured with pcbnew on 2026-09-04; earlier numbers came from screenshots)

- Portrait board **62.5 × 106.5 mm** (edge-line centres X 108.0–170.5, Y 52.0–158.5; the
  right edge was skewed to x 170.0 at the bottom from 18:28 until fixed at 23:25 —
  history item 11g).
  J5–J8 down the left edge (centre x 114.0 for J5/J7, 113.95 for J6/J8; rotated −90°),
  J1–J4 down the right (x 164.5, J3 at 164.45; +90°), at y = 65.5 / 92 / 118.5 / 145 —
  the 0.05 mm column misalignments look like hand nudges. Tab (MP) pads outboard, signal
  pads inboard. XIAO U5 at (140, 63) rot 90 at the top centre, USB toward the top edge,
  antenna inboard (F.Cu + B.Cu rule areas x 134.5–145.5, y 67–75.5: no fill/track/via/pad,
  honoured); U1 and U2 side by side below the XIAO; U4/C4/C5 below them; C6/C7; the
  MP1584 module centred; D2/D3/F1/C8/C9 below it; J10 at (139.88, 154) bottom centre, its
  tab pads 0.65 mm from the bottom edge. Top GND pour (priority 1), bottom GND plane,
  479 track segments (112 of them on B.Cu, across 26 nets), 142 vias, 4 zones.
- **Tab pad to board edge: J5–J8 2.10–2.15 mm; J1–J4 2.15–2.20 mm** (while the right
  edge was skewed, J1–J4 measured 1.66–2.14 mm). Before the owner's 18:28–18:29
  outline move (edges at 109.5/169 in the 18:00 snapshot) the gap was 0.60–0.70 mm, so the
  earlier screenshot estimate (~0.7 mm) was right. The 3V3 outer lane needs ≥ 1.35 mm
  (0.3 edge + 0.8 track + 0.25 Power clearance; the 1.2 mm quoted earlier was
  under-derived), so it now fits everywhere and no further move is needed. Tab-column
  gaps between connectors are ~2 mm — enough for the feeder vias.
- The XIAO body (F.Fab centreline) ends 0.45 mm inside the top edge and its courtyard sits
  on the edge line; only the USB-C shell outline (silk) crosses the edge, by ~1.05 mm —
  less than the 1–2 mm overhang the layout rule asks for.
- Power plan delivered as `power_routing_full.png` (not in the repo): 24 V in the bottom
  strip; 5 V trunk from OUT+ down the module centreline, right of C8/C9, via; 3V3 trunk
  from U4's tab down at ~1.3 mm off the module's right pads, via; both feeders on the
  bottom layer along the bottom edge and up under the tab columns to vias in the J7/J8
  and J3/J4 gaps; lanes up the columns; 5 V stubs to pin 1 direct, 3V3 stubs to pin 2
  with one short bottom jog each over the 5 V lane; 3V3 to U1/U2 VCC under the SOIC
  bodies; 5 V right lane continues to the top to feed D1. The "only two bottom-layer
  traces" rule is the plan; the saved board routes every signal group partly on B.Cu.
- Top GND pour: 24 islands. Five hold exactly one GND pad and no via (R2.2, R3.2, R4.2,
  U1.5, J1.9 — U1.5 is /E2 of the 74HC138, so if it floats no chip select ever asserts);
  the largest island (~2000 mm², left/centre) has no GND via at all and reaches the plane
  only through THT pads U5.13, U6.2, U6.4; J1.10's island (37 mm²) hangs off a single
  thermal spoke of U5.13. 43 GND vias in total.
- Still missing: mounting holes (no NPTH footprint on the board); stitching vias in the
  top pour pockets; R1/R5 sit top-left with no clean 3V3 path (move beside U1 pins 4–5,
  or accept a jog under A0–A2).
- `gerbers/` (21:46) and `gerbers.zip` (21:48, 2026-09-04) are stale: made before routing,
  holes and the 23:25 outline fix — regenerate before ordering. The GND zone fills stored
  in the PCB also still stop at the old slanted edge; refill in the GUI.

## Check status (kicad-cli 10.0.6, 2026-09-04, files as saved 22:06)

- `check_netlist.py`: 38 nets, 189 nodes, 0 problems.
- ERC: **1 error** — `pin_to_pin`: PWR_FLAG #FLG01 is attached to U6 pin 3 (OUT+), which
  is already a Power-output pin; delete that flag. **81 warnings** — all
  `lib_symbol_mismatch` on `power:` symbols (+3V3, +5V, +24V, GND, PWR_FLAG — exactly the
  81 power-symbol instances): the copies embedded by gen_kicad.py differ from KiCad 10's
  power library. Cosmetic; "Update Symbols from Library" clears them.
- DRC with `--schematic-parity`: 0 parity issues. **3 errors** — `starved_thermal` on
  RN1 pin 5, U1 pin 5 and J1 pin 9 (one spoke into the top GND pour instead of two).
  **12 warnings** — U5's USB-C shell silk outline crossing the top edge ×2, D3 reference
  overlapping its outline, and 9 text height/thickness violations on 6 texts (U5 "ANTENNA"
  and U6 "OUT"/"IN" fail both height and thickness, the two U6 "+" fail height, the board
  text "NFC Carrier Card v1.0" fails thickness at 0.10 mm). **10 unconnected items** — the 5 orphaned
  GND pads listed under Layout state (each on its own pour island, no via) plus one open
  each on +3V3, ~{RST}, MOSI, MISO, SCK. DRC names different track segments for those
  opens on each run; compare by net, not by description.

## Things learned the hard way

- A wire ending on the middle of another wire needs a junction symbol at that point.
  The KiCad 7 session also split the through-wire; a test schematic under 10.0.6 shows
  the junction alone connects and the split changes nothing. If in doubt, run the
  netlist check.
- `kicad-cli` (7.0 and 10.0.6 alike) prints only "Failed to load schematic" on any parse
  error; bisect by section. Unescaped quotes inside strings were the first culprit.
- Power-symbol value text rotates with the symbol; side-mounted rotated power symbols
  need a separate upright text object.
- Mouser truncates long MPNs in its own part numbers (the Taiyo Yuden cap); don't
  assume prefix + full MPN for 18+ character MPNs.
- The vertical CLIK-Mate 2.00 1×10 (502443-1070) has no KiCad footprint even though
  1×9 and 1×12 do; the footprint is fully formulaic (L = n + 2 mm half-length) if one
  is ever needed.
- The 74HC138/151 approach scales to 16 bays with a 74HC154 and a second 74HC151 on A3.
- KiCad 10 pretty-prints the netlist and board files one attribute per line (7 and 8
  wrote compact one-node-per-line netlists). Regexes written against the compact form
  match nothing and report "0 nets" without error; `(gr_line …)` likewise spans several
  lines. Use `\s+` between tokens, or better, the bundled `pcbnew` Python for geometry.
  Also: `grep -c "(via"` over-counts by the two `(vias not_allowed)` rule-area lines.
- `kicad-cli` on macOS is not on PATH; the bundle path is in the Verified facts table.
  `pcbnew.LoadBoard` prints a wxApp "traits" assert to stderr that can be ignored, and
  `Board.Zones()` returns a tuple in 10 (no `.size()`).
- `cairosvg` is not installed here; `qlmanage -t` renders SVG or PDF to PNG well enough
  to inspect.
- `kicad-cli pcb export svg` in 10.0.6 defaults to the deprecated `--mode-single` (one
  file at `-o`) and warns about it; a directory at `-o` fails with "Failed to create
  file", exit 2. Pass `--mode-single` or `--mode-multi` explicitly. `fp export svg -o`
  creates the directory only when the path ends in `/`; otherwise, if the directory is
  missing, it prints "Error creating svg file" but still exits 0.
- `qlmanage -t` renders into a square, so it crops landscape SVGs (the A3 schematic loses
  J5–J8 and the title block); rasterise the PDF export instead. Its `-o` directory must
  exist, or it claims success and writes nothing.
- The ERC JSON reports positions in mm ÷ 100 although `coordinate_units` says "mm"
  (#FLG01 at 1.2192, 0.6858 = 121.92, 68.58 mm on the sheet). The netlist export omits
  #PWR/#FLG symbols entirely — a PWR_FLAG's net has to be found by wire tracing.
- DRC on a `.kicad_pcb` copied outside the project directory loses the project rules and
  the `carrier` library (default 0.5 mm edge clearance, `lib_footprint_issues`) and reports
  a different set of findings; and the track segments DRC names for an unconnected net
  differ between runs on the same file.
- KiCad 10's user-level `~/Library/Preferences/kicad/10.0/fp-lib-table` is a nested
  `(type "Table")` entry pointing at the bundle's template table under
  `Contents/SharedSupport/template/`; scripts that read the user table directly see no
  per-library rows.
- `git status`/`diff`/`add`/`gc` inside `.history/` rewrite its `.git/index`; only
  `git log`, `rev-list`, `show` are read-only there.

## Open questions for the owner

- ~~Move the board outline out 0.5 mm per side?~~ Done by the owner on 2026-09-04
  18:28–18:29, by 1.5 mm per side; tab-pad-to-edge is now 2.10–2.15 mm left, 2.15–2.20 mm
  right (pcbnew, after the 23:25 corner fix) and the 3V3 lane fits.
- ~~Straighten the right edge?~~ Owner chose x = 170.5; done 23:25. Refill zones and
  re-export gerbers in the GUI.
- Delete PWR_FLAG #FLG01 on U6 OUT+ (the one ERC error)? Update the embedded `power:`
  symbols from the KiCad 10 library to clear the 81 ERC warnings?
- Add a `24V_F` global label to the F1–D2–D3 node and drop the `*D2-K*` netclass pattern?
  Today the node is unlabeled; `check_netlist.py` expects the auto-name `Net-(D2-K)` and
  the Power netclass reaches it only via `*D2-K*` — editing D2 renames the net and
  silently drops it to the Default class.
- U6: fixed-5 V module (this log, CLAUDE.md) or adjustable "set the pot to 5.00 V"
  (schematic Value, BOM CSV, README, schematic DESIGN NOTES)? The files say adjustable.
- Is routing signals on B.Cu (112 segments today) accepted, or does the "two feeders
  only" bottom-layer rule still stand?
- U5 sits 0.45 mm inside the top edge instead of overhanging 1–2 mm: move it up, or
  relax the rule?
- README (line 15 "KiCad 7", line 30 "no .kicad_pcb yet", Jumpers section, JP1/JP2 BOM
  rows), `pn5180_carrier_bom.csv` (row "JP1, JP2") and the schematic's DESIGN NOTES /
  title comment ("BUSY/IRQ mux", JP1/JP2) all lag the design — update them?
- Delete the stray repo file `rites next to this script#`?
- Where do the M3 holes go? (Suggested: inboard of each connector column at the
  J5/J6 and J7/J8 gap levels, clear of tab pads.)
- Keep the 30 cm harness spec (22–26 AWG, second GND twisted with SCK)?
- Retire `gen_kicad.py`, or port the JP1/JP2 removal and any other hand edits into it?
- 4-bay build variant: J5–J8 and RN2 unpopulated, `BAYS = 4` in firmware — document?
