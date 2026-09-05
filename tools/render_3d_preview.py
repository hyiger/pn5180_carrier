#!/usr/bin/env python3
"""Render 3D previews of the carrier with KiCad's own renderer (kicad-cli pcb render).

Works on a temporary copy of the project, so the real PCB is never touched. Until the PCB
has been updated from the schematic (CLAUDE.md open item 12) the copy also swaps J1-J8 to
the 2x5 CLIK-Mate footprint and attaches the carrier.3dshapes models to U5, U6 and J10,
so the preview shows the intended finished board rather than the board as saved.

Run with KiCad's bundled Python (it has the pcbnew module):
  /Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3 \
      tools/render_3d_preview.py [output_dir]

Outputs top.png, iso.png and closeup_top.png in output_dir (default: renders/ under the
project). The footprint swap is skipped automatically once the PCB already carries the
503148-1090 footprints.
"""
import os, shutil, subprocess, sys, tempfile

import pcbnew

KICAD_CLI = "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli"
PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "pn5180_carrier"
MODELS = {
    "U5": "${KIPRJMOD}/carrier.3dshapes/Seeed_XIAO_ESP32C6_on_2x7_sockets.wrl",
    "U6": "${KIPRJMOD}/carrier.3dshapes/MP1584EN_Module_22x17.wrl",
    "J10": "${KIPRJMOD}/carrier.3dshapes/Molex_CLIK-Mate_502494-0270_1x02_RA.wrl",
}
BAY_FOOTPRINT = "Molex_CLIK-Mate_503148-1090_2x05-1MP_P1.50mm_Horizontal"
VIEWS = {
    "top.png": ["--side", "top", "--zoom", "1"],
    "iso.png": ["--rotate", "-40,0,30", "--perspective", "--zoom", "1.1", "--floor"],
    "closeup_top.png": ["--rotate", "-55,0,-35", "--perspective", "--zoom", "2.2", "--pan", "0,2.2,0"],
}


def set_model(fp, path):
    fp.Models().clear()
    m = pcbnew.FP_3DMODEL()
    m.m_Filename = path
    m.m_Show = True
    m.m_Scale = pcbnew.VECTOR3D(1, 1, 1)
    m.m_Offset = pcbnew.VECTOR3D(0, 0, 0)
    m.m_Rotation = pcbnew.VECTOR3D(0, 0, 0)
    fp.Models().push_back(m)


def main(outdir):
    tmp = tempfile.mkdtemp(prefix="pn5180_preview_")
    for f in (f"{NAME}.kicad_pro", f"{NAME}.kicad_pcb", "fp-lib-table"):
        shutil.copy(os.path.join(PROJECT, f), os.path.join(tmp, f))
    for d in ("carrier.pretty", "carrier.3dshapes"):
        shutil.copytree(os.path.join(PROJECT, d), os.path.join(tmp, d))
    board_path = os.path.join(tmp, f"{NAME}.kicad_pcb")
    b = pcbnew.LoadBoard(board_path)
    swapped = []
    for fp in list(b.GetFootprints()):
        ref = fp.GetReference()
        if ref in MODELS and not any(str(m.m_Filename).endswith(".wrl") for m in fp.Models()):
            set_model(fp, MODELS[ref])
        elif ref in ("J1", "J2", "J3", "J4", "J5", "J6", "J7", "J8") \
                and BAY_FOOTPRINT not in str(fp.GetFPID().GetLibItemName()):
            new = pcbnew.FootprintLoad(os.path.join(tmp, "carrier.pretty"), BAY_FOOTPRINT)
            new.SetReference(ref)
            new.SetValue(fp.GetValue())
            new.SetPosition(fp.GetPosition())
            new.SetOrientationDegrees(fp.GetOrientationDegrees())
            nets = {p.GetNumber(): p.GetNet() for p in fp.Pads()}
            for p in new.Pads():
                if p.GetNumber() in nets:
                    p.SetNet(nets[p.GetNumber()])
            b.Remove(fp)
            b.Add(new)
            swapped.append(ref)
    pcbnew.SaveBoard(board_path, b)
    if swapped:
        print("preview only: swapped to the 2x5 footprint:", ", ".join(sorted(swapped)))
    os.makedirs(outdir, exist_ok=True)
    for fname, args in VIEWS.items():
        out = os.path.join(outdir, fname)
        cmd = [KICAD_CLI, "pcb", "render", "--quality", "high", "--background", "opaque", *args, "-o", out, board_path]
        subprocess.run(cmd, check=True, cwd=tmp, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("wrote", out)
    shutil.rmtree(tmp)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(PROJECT, "renders"))
