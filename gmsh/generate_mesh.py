#!/usr/bin/env python3
from argparse import ArgumentParser
import gmsh

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("file", help="Filename *.geo", type=str)
    parser.add_argument("-o", "--output", help="Output file name", 
                        type=str, default="output")
    parser.add_argument("-s", "--size", help="Mesh Size Factor (dflt: 0.1)",
                        type=float, default=0.1)

    args = parser.parse_args()

    gmsh.initialize()
    
    gmsh.option.setNumber("Mesh.MeshSizeFactor", args.size)

    gmsh.open(args.file)
    
    gmsh.model.mesh.generate(3)
    
    gmsh.write(f"{args.output}.msh")

    gmsh.finalize()
