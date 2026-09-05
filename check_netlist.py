#!/usr/bin/env python3
"""Check a KiCad netlist export against the intended connectivity of the PN5180 carrier.

Usage:
    kicad-cli sch export netlist --format kicadsexpr -o net.txt pn5180_carrier.kicad_sch
    python3 check_netlist.py net.txt

EXPECTED below describes the design with JP1/JP2 removed (owner's current schematic):
  - D1 anode sits directly on +5V; D1 cathode -> 5V_XIAO -> XIAO pin 14
  - bay pin 2 sits directly on +3V3
If the owner's schematic names a net differently (e.g. kept a "3V3_BAY" label), the
script reports the difference — reconcile with the owner, then edit EXPECTED. Do not
"fix" the schematic to satisfy this file without asking.

Exit status 0 = all listed nets match exactly; 1 = differences found.
"""
import re, sys

J = lambda pin: {f"J{i}.{pin}" for i in range(1, 9)}

EXPECTED = {}
for i, n in enumerate((15, 14, 13, 12, 11, 10, 9, 7)):
    EXPECTED[f"NSS{i}"] = {f"J{i+1}.4", f"U1.{n}"}
for i, n in enumerate((4, 3, 2, 1, 15, 14, 13, 12)):
    EXPECTED[f"BUSY{i}"] = {f"J{i+1}.8", f"RN{1 + i // 4}.{i % 4 + 1}", f"U2.{n}"}
EXPECTED.update({
    "SCK":     J(7) | {"R6.2"},
    "SCK_IN":  {"R6.1", "U5.9"},
    "MOSI":    J(5) | {"R7.2"},
    "MOSI_IN": {"R7.1", "U5.11"},
    "MISO":    J(6) | {"U5.10"},
    "~{RST}":  J(3) | {"R5.2", "U5.6"},
    "A0":      {"R2.1", "U1.1", "U2.11", "U5.1"},
    "A1":      {"R3.1", "U1.2", "U2.10", "U5.2"},
    "A2":      {"R4.1", "U1.3", "U2.9",  "U5.3"},
    "~{EN}":   {"R1.2", "U1.4", "U5.4"},
    "BUSY":    {"U2.5", "U5.5"},
    "5V_XIAO": {"D1.1", "U5.14"},
    "24V_J":   {"J10.1", "F1.1"},
    # The fuse-to-TVS/Schottky node carries no label in the schematic (nor in gen_kicad.py);
    # KiCad auto-names it after D2's cathode. Add a "24V_F" global label if a fixed name is wanted.
    "Net-(D2-K)": {"F1.2", "D2.1", "D3.2"},
    "+24V":    {"D3.1", "C8.1", "C9.1", "U6.1"},
    "+5V":     J(1) | {"C4.1", "C6.1", "C7.1", "D1.2", "U4.3", "U6.3"},
    "+3V3":    J(2) | {"C1.1", "C2.1", "C5.1", "R1.1", "R5.1", "U1.16", "U1.6", "U2.16", "U4.2"},
    "GND":     J(9) | J(10) | {f"R{i}.2" for i in (2, 3, 4)}
               | {f"RN{n}.{p}" for n in (1, 2) for p in (5, 6, 7, 8)}
               | {"C1.2", "C2.2", "C4.2", "C5.2", "C6.2", "C7.2", "C8.2", "C9.2",
                  "D2.2", "J10.2", "U1.5", "U1.8", "U2.7", "U2.8", "U4.1", "U5.13",
                  "U6.2", "U6.4"},
})
# Pins that are intentionally unconnected (KiCad reports them as unconnected-(...) nets)
EXPECTED_NC = {"U2.6", "U5.7", "U5.8", "U5.12"}


def parse(path):
    txt = open(path).read()
    body = txt.split("(nets", 1)[1]
    nets = {}
    # Whitespace-tolerant: KiCad 7/8 wrote one node per line, KiCad 10 pretty-prints
    # one attribute per line.
    for block in re.split(r"\(net\b", body)[1:]:
        name = re.search(r'\(name\s+"([^"]*)"\)', block).group(1)
        nodes = re.findall(r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)', block)
        nets[name] = {f"{r}.{p}" for r, p in nodes}
    return nets


def main(path):
    nets = parse(path)
    bad = 0
    for name, want in EXPECTED.items():
        got = nets.get(name)
        if got is None:
            # maybe the same connectivity exists under another name
            alt = [n for n, v in nets.items() if v == want]
            print(f"MISSING net {name}" + (f" (same pins found as {alt[0]!r})" if alt else ""))
            bad += 1
            continue
        if got != want:
            print(f"MISMATCH {name}: extra={sorted(got - want)} missing={sorted(want - got)}")
            bad += 1
    nc = {p for n, v in nets.items() if n.startswith("unconnected-") for p in v}
    if nc != EXPECTED_NC:
        print(f"UNCONNECTED pins differ: extra={sorted(nc - EXPECTED_NC)} missing={sorted(EXPECTED_NC - nc)}")
        bad += 1
    known = set(EXPECTED) | {n for n in nets if n.startswith("unconnected-")}
    for n in sorted(set(nets) - known):
        print(f"UNEXPECTED net {n}: {sorted(nets[n])}")
        bad += 1
    print(f"{len(nets)} nets, {sum(len(v) for v in nets.values())} nodes, {bad} problem(s)")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "net.txt"))
