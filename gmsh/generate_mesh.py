#!/usr/bin/env python3
from argparse import ArgumentParser
import gmsh
import re
from sys import exit

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

    gmsh.initialize()

    gmsh.option.setNumber("Mesh.MshFileVersion", 2.2)
    gmsh.option.setNumber("Mesh.MeshSizeFactor", args.size)

    with open(args.file, "r") as f:
        geoscript = f.read()

    for l in geoscript.split('\n'):
        m = re.match(r"^Circle\(6\).*", l)
        if m is not None:
            pwj_str = m.group()
            continue
        m = re.match(r"^Circle\(7\).*", l)
        if m is not None:
            _, _, _, sample_radius, _, _ = m.group().split("{")[-1].rstrip("};").split(",")

    x, y, z, pwj_radius, angle1, angle2 = pwj_str.split("{")[-1].rstrip("};").split(",")
    for i, j in zip(["x", "pwj_r", "sample_r"], (x, pwj_radius, sample_radius)):
        print(f"{i} : {j} mm")

    pwj_radius_new = args.radius
    #x_new = float(sample_radius) - pwj_radius_new
    x_new = args.x_position
    y_new = args.y_position

    pwj_str_updated = (pwj_str
        .replace(x, str(x_new), 1)
        .replace(y, " " + str(y_new), 1)
        .replace(pwj_radius, str(pwj_radius_new), 1)
    )

    print()
    if args.debug:
        print(geoscript.replace(pwj_str, pwj_str_updated))
        exit()
    else:
        print(pwj_str_updated)

    with open("latest.geo", "w") as f:
        f.write(geoscript.replace(pwj_str, pwj_str_updated))

    gmsh.clear()
    gmsh.open("latest.geo")
    gmsh.model.mesh.generate(3)
    gmsh.write(f"{args.output}.msh")

    gmsh.finalize()
