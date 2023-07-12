#!/usr/bin/env python3
# coding: utf-8

import numpy as np
from rich import print

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
    parser.add_argument("-p", "--pressure", type=float, default=-30.0E6,
                        help="Applied pressure in Pa")
    parser.add_argument("--mpa", action="store_true", default=False,
                        help="Rescale all units to MPa")

    group = parser.add_argument_group("Mesh settings")
    group.add_argument("-o", "--output", help="Output file name",
                       type=str, default="calibration")
    group.add_argument("-s", "--size", help="Mesh Size Factor (dflt: 0.1)",
                       type=float, default=0.1)
    group.add_argument("-d", "--debug", action="store_true", default=False,
                       help="Debug range")

    args = parser.parse_args()

    geofile = args.geofile
    fname_out = args.output
    mesh_size = args.size
    pressure_applied = args.pressure
    sample_material = args.sample_material
    
    if args.debug == True:
        print(args)
        exit()

    generate_mesh(geofile, f"{fname_out}.msh", mesh_size)

    pwj_loc = 0
    run_analysis(
        f"{fname_out}.msh", 
        pressure_applied, 
        pwj_loc,
        material_1=sample_material,
        dataname="calibration",
    )

    print("Finished.")
