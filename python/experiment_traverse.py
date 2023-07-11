#!/usr/bin/env python3
# coding: utf-8

import numpy as np

# MFEM v4.5 uses deprecated numpy variable numpy.long
major, minor, micro = [int(v) for v in np.__version__.split('.')]
if major == 1 and micro > 23:
    np.long = np.longlong

from elasticity import (
        StrainCoefficient,
)

from argparse import ArgumentParser
from fea import run_analysis
from mesh import (
    guess_mesh_file,
    update_pwj_parameters,
    generate_mesh,
)
from numpy import arange
from sys import exit

X_HAT = 2
Y_HAT = 2
Z_HAT = 2

SAMPLE_BOUNDARY = 9.5 # mm

if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("geofile", type=str, help="Input geo file")
    parser.add_argument("-m", "--sample-material", type=str, default="Ti6Al4V-G23",
                        help="Sample material defined in {YOUNG,SHEAR}_MOD")
    parser.add_argument("-p", "--pressure", type=float, default=-31.03E6,
                        help="Applied pressure in Pa")
    parser.add_argument("-v", "--vtr", type=float, default=21.167,
                        help="VTR in mm/s")
    parser.add_argument("--mpa", action="store_true", default=False,
                        help="Rescale all units to MPa")
    parser.add_argument("--no-overlap", action="store_true", default=False,
                        help="Only allow PWJ to be fully on sample")
    parser.add_argument("-n", "--name", type=str, default="experiment",
                        help="Paraview output name")

    group = parser.add_argument_group("Mesh settings")
    group.add_argument("-o", "--output", help="Output file name",
                       type=str, default="output")
    group.add_argument("-R", "--radius", help="Radius of PWJ",
                       type=float, default=2.5)
    group.add_argument("-s", "--size", help="Mesh Size Factor (dflt: 0.1)",
                       type=float, default=0.1)
    group.add_argument("--step-size", type=float, default=1,
                       help="Step size [mm] for PWJ to traverse")
    group.add_argument("-d", "--debug", action="store_true", default=False,
                       help="Debug range")

    args = parser.parse_args()

    print(args)

    step_size = args.step_size
    radius = args.radius
    vtr = args.vtr
    no_overlap = args.no_overlap
    dataname = args.name

    limit = SAMPLE_BOUNDARY + radius
    if no_overlap == True:
        sweep = arange(-SAMPLE_BOUNDARY + radius,
                       SAMPLE_BOUNDARY - radius + step_size,
                       step_size)
    else:
        sweep = arange(-limit + step_size, limit, step_size)

    for i, x in enumerate(sweep):
        # Ensure precision is within 1 decimal point
        x = np.round(x, 1)
        print(f"Calculating with PWJ at {x} mm")

        elapsed_time = step_size * i / vtr
        elapsed_time = round(elapsed_time, 4)
        print(f"Time step at {elapsed_time} s")
        if args.debug == True:
            continue
        geofile_guess = guess_mesh_file(args.geofile, x, 0.0, radius)
        update_pwj_parameters(
            geofile_guess,
            x,
            0.0,
            radius,
            outfile=f"{args.output}.geo",
        )

        generate_mesh(f"{args.output}.geo", f"{args.output}.msh", args.size)

        run_analysis(
            f"{args.output}.msh",
            args.pressure,
            x,
            material_1=args.sample_material,
            cycle=i,
            time=elapsed_time,
            dataname=dataname,
        )

    print("Finished.")
