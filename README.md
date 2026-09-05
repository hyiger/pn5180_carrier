# PN5180 8-Bay NFC Reader Carrier

Carrier board that lets 4 or 8 PN5180 breakout modules plug in over ~30 cm cables with
Molex CLIK-Mate 2.00 mm positive-lock connectors (the white latching style used on the
Prusa LoveBoard) and share one SPI bus with a Seeed Studio XIAO ESP32C6 socketed in the
middle of the board. It runs from the printer's 24 V supply through an MP1584EN buck
module soldered flat onto the carrier. Every part is SMD except the two 1×7 female
headers the XIAO sits in. A 74HC138 decodes 3 address lines into
the 8 chip selects; a 74HC151 muxes the 8 BUSY lines back to a single GPIO. A second
The PN5180's IRQ pin is not used — BUSY is the only handshake the SPI protocol needs.

**GPIO cost: 9 of the XIAO's 11 pins** — SCK, MOSI, MISO, A0, A1, A2, /EN, BUSY, /RST.
D6 and D7 are spare.

Author: hyiger · Rev 1.3 · KiCad 7 file format (opens in 7, 8 and 9)

## Files

| File | Purpose |
|---|---|
| `pn5180_carrier.kicad_pro` | Project file — open this in KiCad |
| `pn5180_carrier.kicad_sch` | Schematic (single A3 sheet, all symbols embedded) |
| `carrier.kicad_sym` + `sym-lib-table` | Project-local symbol library (same symbols, for editing) |
| `carrier.pretty/` + `fp-lib-table` | Project-local footprints: the XIAO 2×7 socket (geometry from Seeed's OPL library) and the MP1584EN module pads |
| `pn5180_carrier_schematic.pdf` / `.png` | Rendered schematic, no KiCad needed |
| `pn5180_carrier_bom.csv` | Full BOM: refs, qty, MPN, Mouser #, footprint, DNP flag |
| `pn5180_carrier_mouser_order.csv` | One-board order list for Mouser's BOM tool (populated parts + cable-side parts) |
| `gen_kicad.py` | Generator that produced everything above — edit and re-run to change the design |

There is no `.kicad_pcb` yet: open the PCB editor from the project and use
*Tools → Update PCB from Schematic* to pull in the footprints.

Footprints reference the stock KiCad libraries and every name was verified against
the 7.0 library set (`Connector_Molex`, `Package_SO`, `Resistor_SMD`, …). If a newer
library renames one, reassign it in the footprint tool — nothing in the netlist
depends on the footprint.

## Connector pinouts

### J1–J8: bay connectors (Molex 502494-1070, CLIK-Mate 2.00 mm 1×10 right-angle SMT)

Single row, so cavity *n* of the 502439-1000 housing is signal *n*. Signals 1–9 are in the
same order as the 9-pin header on the common red PN5180 module. Pin 10 is a second GND:
run it as a separate wire twisted with SCK and crimp both returns into the module's GND
at the far end, which tightens the SCK return loop over the 30 cm. Verify the module's
header order before building cables.

| Pin | Signal | Notes |
|---|---|---|
| 1 | 5V | From carrier 5V rail (module TVDD / RF power) |
| 2 | 3V3 | From carrier LDO via JP2 — see jumpers |
| 3 | /RST | Shared by all bays |
| 4 | NSS | Bay-specific, from 74HC138 output *n* |
| 5 | MOSI | Shared |
| 6 | MISO | Shared (module tri-states when NSS high) |
| 7 | SCK | Shared |
| 8 | BUSY | Bay-specific, to 74HC151 input *n*, 100k pull-down (RN1/RN2) |
| 9 | GND | |
| 10 | GND | Second return — twist with SCK in the harness |

Bay *n* ↔ J(n+1) ↔ 74HC138 Y*n* ↔ 74HC151 D*n*. Bay 0 is address 000, bay 7 is 111.

### U5: Seeed XIAO ESP32C6 socket (2 × 1×7 female headers, 15.24 mm row spacing)

Pin numbers follow Seeed's own symbol/footprint: 1–11 = D0–D10, 12 = 3V3 out, 13 = GND,
14 = 5V (USB VBUS). Pins 1 (D0) and 14 (5V) are at the USB end. The footprint carries the
21 × 17.8 mm outline, a USB marker and an antenna marker at the far end — place the XIAO
with the antenna end at the carrier's edge and keep copper off both layers under it.

| Signal | XIAO pin | Symbol pin | GPIO* | Note |
|---|---|---|---|---|
| SCK | D8 | 9 | 19 | hardware SPI SCK, via R6 33 Ω |
| MISO | D9 | 10 | 20 | hardware SPI MISO |
| MOSI | D10 | 11 | 18 | hardware SPI MOSI, via R7 33 Ω |
| /EN | D3 | 4 | 21 | → 74HC138 /E1 (acts as NSS) |
| A0 | D0 | 1 | 0 | |
| A1 | D1 | 2 | 1 | |
| A2 | D2 | 3 | 2 | |
| BUSY | D4 | 5 | 22 | 74HC151 output (I²C SDA pin, unused as such) |
| /RST | D5 | 6 | 23 | shared reset to all bays |
| spare | D6 | 7 | 16 | NC (UART0 TX) |
| spare | D7 | 8 | 17 | NC (UART0 RX) |
| 3V3 out | — | 12 | | NC — the carrier has its own 3V3 LDO |
| GND | — | 13 | | |
| 5V | — | 14 | | from carrier 5V via JP1 → D1 |

\* GPIO numbers per Seeed's pin diagram; write firmware with the `D0…D10` names from the
board's `pins_arduino.h` and they can't be wrong. `SPI.begin()` with no arguments uses
D8/D9/D10.

**Power path:** Seeed states the XIAO's 5V pin is the raw USB VBUS and that an external
supply must go through a diode. D1 (PMEG2010AEH, 0.3 V drop at our current) does that, so
USB can stay plugged in for flashing while the carrier is powered — neither source can
push into the other. The XIAO's own LDO makes its 3.3 V from ~4.7 V; that's fine. Open JP1
to run the XIAO from USB only.

### J10: 24 V input (Molex 502494-0270, CLIK-Mate 2.00 mm 1×2 right-angle SMT)

| Pin | Signal |
|---|---|
| 1 | +24 V from the printer PSU |
| 2 | GND (printer PSU return) |

**Tapping the Core One.** Take it from the PSU's 24 V output terminals — put a crimped
fork/spade terminal under the existing screw next to the xBuddy's lead, positive and
return together, 22 AWG is plenty. Check polarity with a meter before you plug the
carrier in; the connector is keyed but the PSU end isn't. Load is ~0.5 A at 24 V worst
case (5 V × 2 A through the buck), typically well under that, so the PSU's headroom is
not a concern. The xBuddy's MMU port also carries firmware-switched 24 V, but it's only
enabled when an MMU is configured, so the PSU terminals are the practical tap.

**Input stage (all on the carrier):** F1 1 A slow-blow → D2 SMAJ28A TVS (clamps motor
regen spikes; a reversed input forward-biases it and blows F1) → D3 PMEG6030EP reverse
Schottky (so a miswire doesn't even blow the fuse) → C8/C9 2 × 10 µF 50 V → U6.

**Buck (U6): MP1584EN mini module, mounted flat.** The footprint has four 3 mm
through-hole pads on the module's 18.54 × 8.13 mm pad rectangle; lay the module on the
carrier and solder down through its own plated holes, or stand it on four header-pin
stubs — both work on the same pads. IN pads at the "IN" silk end, OUT at "OUT", "+" marks
the top row. Module pad labels vary between makers, so check the module's own silkscreen
against the footprint before soldering.

Three things about this module on a 24 V rail:

- It's rated 28 V max. The TVS (28 V standoff, clamping from ~31 V) and C8/C9 are what
  keep spikes off it — don't leave them out to save parts.
- It's adjustable. **Set the pot to 5.00 V with a meter before mounting it**, then lock
  the pot with a dab of nail varnish. A bumped pot puts up to 20 V into the readers and
  the XIAO. If you can get a fixed-5 V variant, prefer it.
- The seller's own guidance is 1.5 A continuous without a heatsink. The carrier's real
  draw is well under 1 A (one RF field at a time), so that's fine; give it some copper
  under the pads anyway.

### Cables (~30 cm)

One connector family for everything. Bay cable: 502439-1000 housing at the carrier with
10 × 502438 terminals on 22–26 AWG stranded wire, 2.54 mm DuPont-style female on the module
end (or solder to the module header). Power: 502439-0200 with 22 AWG. There is no ESP32
cable any more — it's on the board.

The housing latches into the receptacle (the CLIK) and releases with a squeeze — no tools.
Molex's own hand crimper (63819-2800) is expensive; the 502438 is a standard open-barrel
terminal and a generic 2.0 mm-class ratchet crimper (PA-09 / SN-2549 type) does the job.
Molex also sells pre-crimped CLIK-Mate leads (79758-10xx series) if you'd rather skip
crimping entirely — check length and single/double-ended on Mouser.

Eight 30 cm unterminated stubs hanging off one SPI bus is a real transmission-line load,
so the design takes three precautions:

- **R6/R7 (33 Ω) in series with SCK and MOSI**, a few mm from the ESP32 socket pins and
  before the bus fans out — proper source termination for the star, taking the edge off
  the ESP32's ~2 ns rise times. Fit 0 Ω if you scope it and it's clean; 47–68 Ω if you
  see ringing.
- **SPI clock ≤ 1 MHz.** The PN5180 doesn't need more for inventory polling, and a 1 µs
  bit period gives the reflections on a 30 cm stub (a few ns round trip) time to settle.
- **Lowest ESP32 drive strength that works:** `gpio_set_drive_capability((gpio_num_t)D8,
  GPIO_DRIVE_CAP_0)` (and `D10` for MOSI) slows the edges further.

Route GND wires as close to SCK as the harness allows. MISO is driven by the PN5180 (slower
edges) and needs nothing extra. NSS/BUSY see one stub each and are fine.

## Jumpers

| Ref | Default | Function |
|---|---|---|
| JP1 | **bridged** | Carrier 5V → D1 → XIAO 5V pin. Leave bridged; D1 already prevents back-feeding USB. Open it only to run the XIAO from USB alone. |
| JP2 | **bridged** | Routes carrier 3V3 (from U4) to bay pin 2. Most common modules expect both 5V and 3.3V supplied. Open it if your modules regulate 3.3 V onboard and expose it as an *output* (paralleling two LDOs is sloppy, though rarely harmful). |

## How the selection logic works

- `A0..A2` → 74HC138 address inputs **and** both 74HC151 select inputs.
- `/EN` → 74HC138 `/E1` (G2A). Low = the addressed bay's NSS goes low; high = every NSS high.
  Wire the library's "NSS" pin to `/EN` and it just works — the library toggles NSS,
  the decoder routes it.
- `BUSY` (U5 pin 11, GPIO11) is the 74HC151 output = the BUSY of the addressed bay. Wire it
  to the library's "BUSY" pin.
- `/E2` is grounded, `E3` tied high; 74HC151 `/E` grounded (always enabled).
- R6/R7 sit between the ESP32 and the SCK/MOSI bus (nets `SCK_IN`/`MOSI_IN` on the ESP32 side).
- Pull-ups on `/EN` and `/RST` and pull-downs on `A0..A2` define everything while the
  ESP32 is booting or unplugged. The 4×100k arrays RN1/RN2 keep unfitted bays' BUSY
  inputs from floating. Array element *k* of RN1 is bay *k*, of RN2 is bay
  *k*+4 (pins 1–4 to the signals, 8–5 to GND, the standard 1–8/2–7/3–6/4–5 pairing).

**Rule:** change `A0..A2` only while `/EN` is high, or two NSS lines can glitch low
during the decoder transition.

## Firmware sketch (ATrappmann PN5180 library)

```cpp
// Seeed XIAO ESP32C6 in the carrier sockets (Arduino-ESP32 core 3.x, board "XIAO_ESP32C6")
#define PIN_A0   D0
#define PIN_A1   D1
#define PIN_A2   D2
#define PIN_EN   D3     // -> 74HC138 /E1, acts as "NSS" for the addressed bay
#define PIN_BUSY D4     // <- 74HC151 Y
#define PIN_RST  D5
#define BAYS      8     // 4 for a half-populated board
// SCK D8 / MISO D9 / MOSI D10 are the board's hardware SPI pins

PN5180ISO15693 nfc(PIN_EN, PIN_BUSY, PIN_RST);   // one instance for all bays

void selectBay(uint8_t n) {
  digitalWrite(PIN_EN, HIGH);            // deselect everything before changing address
  digitalWrite(PIN_A0, n & 1);
  digitalWrite(PIN_A1, (n >> 1) & 1);
  digitalWrite(PIN_A2, (n >> 2) & 1);
}

void setup() {
  pinMode(PIN_A0, OUTPUT); pinMode(PIN_A1, OUTPUT); pinMode(PIN_A2, OUTPUT);
  pinMode(PIN_EN, OUTPUT); digitalWrite(PIN_EN, HIGH);
  nfc.begin();                           // SPI on D8/D9/D10; keep the SPI clock <= 1 MHz
  gpio_set_drive_capability((gpio_num_t)D8,  GPIO_DRIVE_CAP_0);   // soften SCK/MOSI edges
  gpio_set_drive_capability((gpio_num_t)D10, GPIO_DRIVE_CAP_0);
  // shared /RST: pulse once, then finish the post-reset handshake per bay
  digitalWrite(PIN_RST, LOW);  delay(10);
  digitalWrite(PIN_RST, HIGH); delay(10);
  for (uint8_t b = 0; b < BAYS; b++) {
    selectBay(b);
    while (!(nfc.getIRQStatus() & IDLE_IRQ_STAT)) {}   // add a timeout in real code
    nfc.clearIRQStatus(0xFFFFFFFF);
  }
}

void loop() {
  for (uint8_t b = 0; b < BAYS; b++) {
    selectBay(b);
    nfc.setupRF();                       // RF on, this bay only
    uint8_t uid[8];
    bool present = (nfc.getInventory(uid) == ISO15693_EC_OK);
    nfc.setRF_off();                     // field off before moving to the next bay
    updateBay(b, present, uid);          // debounce: 2-3 misses before "removed"
  }
}
```

The stock library's `while (digitalRead(BUSY))` loops have no timeout; add one
(a few ms) so an empty bay or a wedged module can't hang the sweep.

## Layout notes

- Ground plane on one layer; SPI signals short, routed as a star or short daisy chain
  from U5 to the bay connectors. With 8 loads plus cable capacitance, ≤ 1 MHz SPI.
- U5 in the middle, USB end facing whichever edge is reachable, antenna end (opposite the
  USB) toward the far edge with no copper under it on either layer. The two sockets are
  plain 1×7 female headers on 15.24 mm centres; the footprint sets that spacing. The XIAO
  also has an external-antenna u.FL if the rack's metal gets in the way.
- Bay connectors along one board edge, in bay order, so cables don't cross. The 502494
  receptacles are SMT with two large solder-tab pads ("MP" in the footprint) — those tabs,
  not the signal pins, take the cable-pull load, so give them full paste and don't thin
  the copper under them. Right-angle parts: the cable leaves flat along the board plane.
- R6/R7 within a few mm of U5 pins 9/11 (D8 SCK / D10 MOSI), before the traces fan out.
- U1/U2 near U5 (short A0–A2, /EN, BUSY traces); the eight NSS/BUSY lines then run out
  to the connector edge.
- U6 module: C8/C9 right at its IN pads, a solid GND pour under it, and keep it away from
  the SPI lines and the XIAO's antenna (it switches at ~1.5 MHz with a small inductor).
- F1/D2/D3 near J10; C6/C7 and C4 near U4; C1/C2 within a few mm of their IC VCC pins.
- U4 (SOT-223) with a copper pour on the tab (tab = OUTPUT, part of the 3V3 net); at ~200 mA on 3V3 it dissipates ~0.35 W.
- Add M3 mounting holes (not in the schematic).
- For a 4-bay build simply leave J5–J8 (and RN2) unpopulated. Firmware `BAYS = 4`.

## BOM (all SMD)

Rev 1.3. Every symbol in the schematic carries `Manufacturer`, `MPN` and `Mouser` fields,
so KiCad's own BOM export reproduces this table. `pn5180_carrier_mouser_order.csv` can be
uploaded directly to Mouser's BOM tool.

| Ref | Qty | Part | Mouser # | Footprint |
|---|---|---|---|---|
| U1 | 1 | TI SN74HC138DR | 595-SN74HC138DR | Package_SO:SOIC-16_3.9x9.9mm_P1.27mm |
| U2 | 1 | TI SN74HC151DR | 595-SN74HC151DR | Package_SO:SOIC-16_3.9x9.9mm_P1.27mm |
| U4 | 1 | TI TLV1117LV33DCYR, 3.3 V 1 A ceramic-stable LDO | 595-TLV1117LV33DCYR | Package_TO_SOT_SMD:SOT-223-3_TabPin2 |
| J1–J8 | 8 | Molex 502494-1070, CLIK-Mate 2.00 mm RA SMT receptacle 1×10 | 538-502494-1070 | Connector_Molex:Molex_CLIK-Mate_502494-1070_1x10-1MP_P2.00mm_Horizontal |
| U5 | 1 | Seeed Studio XIAO ESP32C6 (SKU 113991182) — user-supplied | 713-113991182 (verify) | carrier:Seeed_XIAO_2x7_Socket |
| (U5 sockets) | 2 | Würth 61300711821, WR-PHD 1×7 female header 2.54 mm THT | 710-61300711821 | (part of the U5 footprint) |
| D1 | 1 | Nexperia PMEG2010AEH, Schottky 20 V 1 A, SOD-123 | 771-PMEG2010AEH | Diode_SMD:D_SOD-123 |
| J10 | 1 | Molex 502494-0270, CLIK-Mate 2.00 mm RA SMT receptacle 1×2 (24 V in) | 538-502494-0270 | Connector_Molex:Molex_CLIK-Mate_502494-0270_1x02-1MP_P2.00mm_Horizontal |
| U6 | 1 | MP1584EN mini buck module, 22 × 17 mm, set to 5.0 V — user-supplied (Amazon) | — | carrier:MP1584EN_Module_22x17 |
| F1 | 1 | Littelfuse 0453001.MR, 1 A slow-blow, NANO2 | 576-0453001.MR | Fuse:Fuse_Littelfuse-NANO2-451_453 |
| D2 | 1 | Littelfuse SMAJ28A TVS, 28 V standoff, SMA | 576-SMAJ28A | Diode_SMD:D_SMA |
| D3 | 1 | Nexperia PMEG6030EP Schottky 60 V 3 A (reverse polarity) | 771-PMEG6030EP | Diode_SMD:D_SOD-128 |
| C8, C9 | 2 | Murata GRM32ER71H106KA12L, 10 µF 50 V X7R 1210 | 81-GRM32ER71H106KA12L | Capacitor_SMD:C_1210_3225Metric_Pad1.33x2.70mm_HandSolder |
| JP1 | 1 | Solder jumper, open (PCB feature) | — | Jumper:SolderJumper-2_P1.3mm_Open_RoundedPad1.0x1.5mm |
| JP2 | 1 | Solder jumper, bridged (PCB feature) | — | Jumper:SolderJumper-2_P1.3mm_Bridged_RoundedPad1.0x1.5mm |
| R1–R5 | 5 | Yageo RC0603FR-0710KL, 10k 1% 0603 | 603-RC0603FR-0710KL | Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder |
| R6, R7 | 2 | Yageo RC0603FR-0733RL, 33 Ω 1% 0603 (SCK/MOSI series) | 603-RC0603FR-0733RL | Resistor_SMD:R_0603_1608Metric_Pad0.98x0.95mm_HandSolder |
| RN1, RN2 | 2 | Yageo YC164-FR-07100KL, 4×100k 1% isolated array | 603-YC164-FR-07100KL | Resistor_SMD:R_Array_Convex_4x0603 |
| C1, C2 | 2 | Murata GRM188R71H104KA93D, 100 nF 50 V X7R 0603 | 81-GRM188R71H104KA93D | Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder |
| C4 | 1 | Murata GRM188R61A106KE69D, 10 µF 10 V X5R 0603 | 81-GRM188R61A106KE69D | Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder |
| C5 | 1 | Murata GRM188R60J226MEA0D, 22 µF 6.3 V X5R 0603 | 81-GRM188R60J226MEA0D | Capacitor_SMD:C_0603_1608Metric_Pad1.08x0.95mm_HandSolder |
| C6 | 1 | Taiyo Yuden MSASJ32MAB5227MPNDT1, 220 µF 6.3 V X5R 1210 | 963-MSASJ32MAB5227MP | Capacitor_SMD:C_1210_3225Metric_Pad1.33x2.70mm_HandSolder |
| C7 | 1 | Same — **DNP**, parallel pads for extra bulk | 963-MSASJ32MAB5227MP | Capacitor_SMD:C_1210_3225Metric_Pad1.33x2.70mm_HandSolder |

Cable side:

| Part | Mouser # | Qty / board | Use |
|---|---|---|---|
| Molex 502439-1000 CLIK-Mate positive-lock housing 1×10 | 538-502439-1000 | 8 | Bay cables |
| Molex 502439-0200 CLIK-Mate positive-lock housing 1×2 | 538-502439-0200 | 1 | 24 V cable |
| Molex 502438-0100 CLIK-Mate crimp terminal, loose, 22–26 AWG | 538-502438-0100 | 82 (+spares) | All cables |

Vertical (top-entry) versions of the same receptacles are the 502443-xx70 series on
identical pads; KiCad's library has them in 2 and 12 circuits but not 10, so the design
uses right-angle throughout. Rated 3 A per contact, 30 mating cycles.

Mouser numbers follow Mouser's manufacturer-prefix + MPN scheme (595 = TI, 538 = Molex,
603 = Yageo, 81 = Murata, 710 = Würth, 771 = Nexperia, 713 = Seeed, 576 = Littelfuse). 963-MSASJ32MAB5227MP was read from the product page; the
others follow the scheme. Double-check stock and packaging (cut tape vs. reel) at checkout.

Capacitor notes:

- C6 is a 6.3 V X5R part on the 5 V rail. That's inside its rating, but class-2 ceramics
  lose capacitance under DC bias — expect roughly a quarter of its nominal 220 µF at
  5 V. Together with the MP1584EN module's own output capacitor that's plenty for the
  ~250 mA RF-on step; C7 gives you a second set of pads if the rail shows sag when a
  bay's field switches on.
- U4 is a TLV1117LV33, designed for ceramic output capacitors (TI specifies ≥ 10 µF,
  any ESR, stable at 0 mA load). C5's 22 µF 0603 is worth roughly 10–12 µF after
  DC-bias derating at 3.3 V, which meets that minimum; for more margin use a 22 µF in
  0805 or two 0603s in parallel. Don't substitute a classic AMS1117/TLV1117 here
  without changing C5 to a tantalum — those parts need output ESR to stay stable.
- TLV1117LV limits: Vin ≤ 5.5 V (6 V absolute). Fine on a regulated 5 V rail, but never
  feed J10 from an unregulated "5 V" adapter that idles at 6–7 V. Dropout is ~0.45 V at
  1 A, so 3V3 holds up even if the input droops to 4 V.

## Going to 16 bays

Swap U1 for a 74HC154 (4-to-16), add a second 74HC151 selected by A3 and two more
arrays: 6 GPIOs total. At that point split the SPI bus across HSPI and VSPI to keep loading sane.
