#!/usr/bin/env python3
# Copyright 2023 David Kalliecharan <david@david.science>
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS”
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT
# OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH
# DAMAGE.

from argparse import ArgumentParser
import gmsh
from pathlib import Path
import re
from sys import exit


COMPONENT = {
    "x": 0,
    "y": 1,
    "z": 2,
    "radius": 3,
    "angle1": 4,
    "angle2": 5,
}

MESH_DIR = Path(".").absolute() / "../gmsh"

PWJ_GEO_FILES = {
    "center": "system.geo",
    "negative": {
        "intersect": "system.x.neg.intersect.geo",
        "overlap": "system.x.neg.overlap.geo",
    },
    "positive": {
        "intersect": "system.x.pos.intersect.geo",
        "overlap": "system.x.pos.overlap.geo",
    },
}


def guess_mesh_file(
        infile: str,
        x: float,
        y: float,
        radius: float,) -> str:
    with open(infile, "r") as f:
        geoscript = f.read()

    for l in geoscript.split('\n'):
        m = re.match(r"^Circle\(16\).*", l)
        if m is not None:
            _, _, _, sample_radius, _, _ = m.group().split("{")[-1].rstrip("};").split(",")

    sample_radius = float(sample_radius)
    if (abs(x) - abs(radius)) >= abs(sample_radius):
        raise ValueError("Applied boundary is outside of the Sample boundary!")

    if x < 0:
        sample_radius *= -1
        radius *= -1

    # Check how the radius interacts with the sample_radius
    mesh_select = abs(sample_radius - radius) - abs(x)
    if mesh_select > 0:
        return MESH_DIR / PWJ_GEO_FILES["center"]
    elif mesh_select < 0:
        boundary = "overlap"
    elif mesh_select == 0.0:
        boundary = "intersect"

    if x < 0:
        sign = "negative"
    else:
        sign = "positive"

    return MESH_DIR / PWJ_GEO_FILES[sign][boundary]

def update_pwj_parameters(
        infile: str,
        x: float,
        y: float,
        radius: float,
        **kws: dict) -> None:
    outfile = kws.setdefault("outfile", "output.geo")
    """Updates the pwj radius, and (x, y) position in the geo file"""
    debug = kws.setdefault("debug", False)

    with open(infile, "r") as f:
        geoscript = f.read()

    for l in geoscript.split('\n'):
        m = re.match(r"^Circle\(15\).*", l)
        if m is not None:
            pwj_str = m.group()
            continue
        m = re.match(r"^Circle\(16\).*", l)
        if m is not None:
            _, _, _, sample_radius, _, _ = m.group().split("{")[-1].rstrip("};").split(",")

    parameters = pwj_str.split("{")[-1].rstrip("};").split(",")
    x_old, y_old, z_old, radius_old, angle1_old, angle2_old, = parameters
    for i, j in zip(["x", "y", "pwj_r", "sample_r"],
                    (x_old, y_old, radius_old, sample_radius)):
        print(f"{i} : {j} mm")

    # Update PWJ area with new values
    pwj_comp = pwj_str.split(",")
    pwj_comp[COMPONENT["x"]] = pwj_comp[COMPONENT["x"]].replace(x_old, str(x))
    pwj_comp[COMPONENT["y"]] = pwj_comp[COMPONENT["y"]].replace(y_old, " " + str(y))
    pwj_comp[COMPONENT["radius"]] = pwj_comp[COMPONENT["radius"]].replace(radius_old, " " + str(radius))
    pwj_str_updated = ",".join(pwj_comp)

    print()
    if debug:
        print(geoscript.replace(pwj_str, pwj_str_updated))
        exit()
    else:
        print(pwj_str_updated)

    with open(outfile, "w") as f:
        f.write(geoscript.replace(pwj_str, pwj_str_updated))


def redefine_pwj_curves(geofile: str, curve_loop: str) -> None:
    """If intersections for pwj area cause extra curves, update them"""
    with open(geofile, "r") as f:
        geoscript = f.read()

    for l in geoscript.split('\n'):
        m = re.match(r"^Curve Loop\(14\).*", l)
        if m is not None:
            curve_loop_old = m.group()
            # NOTE: Skip first detection is before Boolean:Intersection
            if curve_loop_old == "Curve Loop(14) = {16};":
                continue
            break

    print(f"Using '{curve_loop}'")
    with open(geofile, "w") as f:
        f.write(geoscript.replace(curve_loop_old, curve_loop))


def generate_mesh(geofile: str, meshfile: str) -> None:
    gmsh.initialize()

    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.option.setNumber("Mesh.MeshSizeFactor", args.size)

    gmsh.clear()
    gmsh.open(geofile)

    gmsh.model.mesh.generate(3)
    gmsh.write(meshfile)

    gmsh.finalize()


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("file", help="Filename *.geo", type=str)
    parser.add_argument("-o", "--output", help="Output file name",
                        type=str, default="output")
    parser.add_argument("-s", "--size", help="Mesh Size Factor (dflt: 0.1)",
                        type=float, default=0.1)
    parser.add_argument("-n", "--steps",
                        help="Steps for pwj to go from edge to center",
                        type=int, default=1)
    parser.add_argument("-r", "--radius", help="Radius of PWJ",
                        type=float, default=2.5)
    parser.add_argument("-x", "--x-position", help="x position of the PWJ",
                        type=float, default=0)
    parser.add_argument("-y", "--y-position", help="y position of the PWJ",
                        type=float, default=0)
    parser.add_argument("-d", "--debug", help="Debug the *.geo file",
                        action="store_true")


    args = parser.parse_args()

    infile = guess_mesh_file(args.file, args.x_position, args.y_position, args.radius)
    update_pwj_parameters(
        str(infile),
        args.x_position,
        args.y_position,
        args.radius,
        outfile=f"{args.output}.geo",
        debug=args.debug,
    )
    generate_mesh(f"{args.output}.geo", f"{args.output}.msh")
