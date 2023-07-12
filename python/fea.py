#!/usr/bin/env python3
# coding: utf-8
# Copyright 2023 David Kalliecharan <dave@dal.ca>
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
# DAMAGE

import numpy as np

# MFEM v4.5 uses deprecated numpy variable numpy.long
major, minor, micro = [int(v) for v in np.__version__.split('.')]
if major == 1 and micro > 23:
    np.long = np.longlong

from elasticity import (
        StrainCoefficient,
)

from argparse import ArgumentParser
import mfem.ser as mfem
from mfem.ser import ParaViewDataCollection, intArray
from pathlib import Path
from rich import print
from unicodedata import lookup


ROOT = Path(".").absolute().parent
MESH = Path(".").absolute()

X_HAT = 2
Y_HAT = 2
Z_HAT = 2

YOUNG_MOD = {}
YOUNG_MOD['CP-Ti-G2']    = 102.7E9  # GPa
YOUNG_MOD['Ti6Al4V-G5']  = 96.5E9   # GPa
YOUNG_MOD['Ti6Al4V-G23'] = 113.8E9  # GPa
YOUNG_MOD['Al 6061-T6']  = 68.9E9   # GPa

SHEAR_MOD = {}
SHEAR_MOD['CP-Ti-G2']    = 45E9
SHEAR_MOD['Ti6Al4V-G5']  = 43E9 # GPa
SHEAR_MOD['Ti6Al4V-G23'] = 44E9 # GPa
SHEAR_MOD['Al 6061-T6']  = 26E9 # GPa

def lambda_shear(E, G):
    return G * (E - 2 * G) / (3 * G - E)


def lambda_poisson(E, nu):
    return E * nu / ((1 + nu) * (1 - 2 * nu))


def get_components(coordinates:tuple[float, float, float],
                   mesh: mfem.Mesh, 
                   gf: mfem.GridFunction,
                   **kws: dict):
    """Returns magnitude, x, y, z components from a mesh and mfem.GridFunction"""
    if len(coordinates) != 3:
        raise ValueError("'coordinates' requires 3 float values (x, y, z)")
    _, elem_ids, ips = mesh.FindPoints([coordinates])
    # GridFunctio.GetValue dimensions needs to be from 1-3, hence i + 1
    components = [gf.GetValue(elem_ids[0], ips[0], i) for i in range(4)]
    components = {k: v for k, v in zip(["magnitude", "x", "y", "z"], components)}
    
    return components


def save_mfem_data(fname: str,
                   pwj_pos: float,
                   mesh: mfem.Mesh,
                   u: mfem.GridFunction,
                   strain: mfem.GridFunction):

    pos = f"{pwj_pos:+05.1f}mm"

    mesh.Print(f'{fname}_{pos}.mesh', 8)

    # Save inverted solution, backwards displacements to original grid
    u.Neg()
    u.Save(f'{fname}_{pos}.gf', 8)

    strain.Save(f'{fname}_stain_{pos}.gf', 8)


def save_paraview_frame(fname: str,
               pwj_pos: float,
               mesh: mfem.Mesh,
               u: mfem.GridFunction,
               strain: mfem.GridFunction,
               cycle: int=0,
               time: float=0.0,
               prefix="../paraview"):
    pos = f"{pwj_pos:+05.1f}mm"

    pdc = mfem.ParaViewDataCollection(f"{fname}", mesh)
    
    pdc.SetPrefixPath(prefix)
    pdc.SetLevelsOfDetail(1)
    pdc.SetCycle(cycle)
    pdc.SetDataFormat(mfem.VTKFormat_BINARY)
    pdc.SetHighOrderOutput(True)
    pdc.SetTime(time)
    #pdc.RegisterField(f"{pos}: displacement", u)
    #pdc.RegisterField(f"{pos}: strain(z,z)", strain)
    pdc.RegisterField(f"displacement", u)
    pdc.RegisterField(f"strain(z,z)", strain)
    pdc.Save()


def run_analysis(fname: str, 
                 pwj_force: float, 
                 pwj_pos: float,
                 material_0: str="Al 6061-T6", 
                 material_1: str="Ti6Al4V-G23",
                 dataname="experiment",
                 cycle: int=0,
                 time: float=0.0):
    order = 1
    # MFEM cannot handle pathlib objects
    meshfile = fname 
    print(meshfile)

    mesh = mfem.Mesh(meshfile, 1, 1)
    dim = mesh.Dimension()
    print(f"Dimensions: {dim}")

    # Define a finite element space on the mesh.
    fec = mfem.H1_FECollection(order, dim)
    fespace = mfem.FiniteElementSpace(mesh, fec, dim)
    print("Number of finite element unknowns: " + str(fespace.GetTrueVSize()))

    # Deterimine list of true essential boundary degrees of freedom (dof).
    ess_tdof_list = intArray()
    ess_bdr = intArray([1]+[0]*(mesh.bdr_attributes.Max()-1))
    fespace.GetEssentialTrueDofs(ess_bdr, ess_tdof_list)
    print(f"Max Boundary Attributes (Domains): {mesh.bdr_attributes.Max()}")

    # Set up the linear form b(.) which corresponds to the RHS of the FEM linear system.
    # NOTE: The forcing function (pwj_force) needs to be in the same units
    # as the Lame parameters, i.e., If the Lame parameters are in Pa, so must the forcing function.
    f = mfem.VectorArrayCoefficient(dim)
    for i in range(dim-1):
        f.Set(i, mfem.ConstantCoefficient(0.0))

    pull_force = mfem.Vector([0] * mesh.bdr_attributes.Max())
    pull_force[1] = pwj_force
    f.Set(dim-1, mfem.PWConstCoefficient(pull_force))

    b = mfem.LinearForm(fespace)
    b.AddBoundaryIntegrator(mfem.VectorBoundaryLFIntegrator(f))
    print(f"RHS: b_i = "
          + f"{lookup('INTEGRAL')} "
          + "f"
          + f"{lookup('DOT OPERATOR')}"
          + f"{lookup('GREEK SMALL LETTER PHI')}_i")
    b.Assemble()

    # Define the solution vector x as a finite element grid function 
    # corresponding to fespace. Assuming zero satisfies the B.C.
    x = mfem.GridFunction(fespace)
    x.Assign(0.0)


    lamb_0 = lambda_shear(YOUNG_MOD[material_0], SHEAR_MOD[material_0])
    lamb_1 = lambda_shear(YOUNG_MOD[material_1], SHEAR_MOD[material_1])

    mu_0 = SHEAR_MOD[material_0]
    mu_1 = SHEAR_MOD[material_1]

    print(f"{material_0}  | {lookup('GREEK SMALL LETTER LAMDA')}_0 : {lamb_0:0.3g} | {lookup('GREEK SMALL LETTER MU')}_0 : {mu_0:0.3g}")
    print(f"{material_1}  | {lookup('GREEK SMALL LETTER LAMDA')}_1 : {lamb_1:0.3g} | {lookup('GREEK SMALL LETTER MU')}_1 : {mu_1:0.3g}")

    # Bilinear form of a(., .) on the finite element space corresponding to the 
    # linear elasticity integrator with piece-wise constants coefficient 
    # lambda (lamb) and mu.
    print(f"Max Attributes: {mesh.attributes.Max()}")
    lamb = mfem.Vector(mesh.attributes.Max())
    lamb.Assign(1.0)
    lamb[0] *= lamb_0
    lamb[1] *= lamb_1
    lamb_coef = mfem.PWConstCoefficient(lamb)

    mu = mfem.Vector(mesh.attributes.Max())
    mu.Assign(1.0)
    mu[0] *= mu_0
    mu[1] *= mu_1
    mu_coef = mfem.PWConstCoefficient(mu)

    a = mfem.BilinearForm(fespace)
    a.AddDomainIntegrator(mfem.ElasticityIntegrator(lamb_coef, mu_coef))

    # Assemble the bilinear form and corresponding linear system
    print(f"LHS: A_ij = "
          + f"{lookup('INTEGRAL')} "
          + f"{lookup('NABLA')}({lookup('GREEK SMALL LETTER PHI')}_i)"
          + f"{lookup('DOT OPERATOR')}"
          + f"{lookup('NABLA')}({lookup('GREEK SMALL LETTER PHI')}_j)")
    static_cond = False
    if (static_cond):
        a.EnableStaticCondensation()
    a.Assemble()

    A = mfem.OperatorPtr()
    B = mfem.Vector()
    X = mfem.Vector()
    a.FormLinearSystem(ess_tdof_list, x, b, A, X, B)
    print('Size of linear system: ' + str(A.Height()))

    # Solve
    AA = mfem.OperatorHandle2SparseMatrix(A)
    M = mfem.GSSmoother(AA)
    mfem.PCG(AA, M, B, X, 1, 500, 1e-8, 0.0)

    # Recover the solution as a finite element grid function
    A.RecoverFEMSolution(X, b, x)

    # For non-NURBS meshs, make the mesh curved based on the
    # finite element space. Meaning, we define the mesh elements
    # through a fespace based transormation of the reference element.
    # This allows us to save the displaced mesh as a curved mesh 
    # when using high-order finte element displacement field.
    if not mesh.NURBSext:
        print("Setting Nodal FE Space")
        mesh.SetNodalFESpace(fespace)

    # 14. Save the displacement mesh and the inverted solution (which
    #     gives the backwards displacements to the original grid). 
    #     this output can be view later using GLVis 
    scalar_space = mfem.FiniteElementSpace(mesh, fec)

    strain = mfem.GridFunction(scalar_space)
    strain_coef = StrainCoefficient()
    strain_coef.SetDisplacement(x)

    #stress = mfem.GridFunction(scalar_dg_space)
    #stress_coef = StressCoefficient(lamb_coef, mu_coef)
    #stress_coef.SetDisplacement(x)

    strain_coef.SetComponent(2, 2)
    strain.ProjectCoefficient(strain_coef)

    #stress_coef.SetComponent(z_hat, z_hat)
    #stress.ProjectCoefficient(stress_coef)

    print("Saving MFEM data")
    #save_mfem_data("test", pwj_pos, mesh, x, strain)
    save_paraview_frame(dataname, pwj_pos, mesh, x, strain, cycle, time) 


if __name__ == "__main__":
    parser = ArgumentParser()

    parser.add_argument("mesh", type=str, help="Input Mesh file")
    parser.add_argument("-m", "--sample-material", type=str, default="Ti6Al4V-G23",
                        help="Sample material defined in {YOUNG,SHEAR}_MOD")
    parser.add_argument("-p", "--pressure", type=float, default=-31.03E6,
                        help="Applied pressure in Pa")

    args = parser.parse_args()

    run_analysis(args.mesh,
                 args.pressure, 
                 0,
                 material_1=args.sample_material,
                 dataname="test")

    print("Finished.")
