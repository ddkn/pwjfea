#!/usr/bin/env python
# coding: utf-8

import numpy as np

# MFEM v4.5 uses deprecated numpy variable numpy.long
major, minor, micro = [int(v) for v in np.__version__.split('.')]
if major == 1 and micro > 23:
    np.long = np.longlong

from elasticity import (
        StrainCoefficient,
        StrainVectorCoefficient,
        StressCoefficient,
        StressVectorCoefficient,
)
import ipywidgets as wgt
from itertools import product
from glvis import glvis, to_stream
import mfem.ser as mfem
from mfem.ser import intArray
from pathlib import Path
from rich import print
from unicodedata import lookup


MESH = Path(".").absolute()


def lambda_shear(E, G):
    return G*(E-2*G)/(3*G-E)


def lambda_poisson(E, nu):
    return E*nu/((1 + nu)(1 - 2*nu))


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


fname = 'output'
order = 1
# MFEM cannot handle pathlib objects
meshfile = str(MESH / f'{fname}.msh')
#meshfile = str(MESH / f'../nb/beam-tet.mesh')
print(meshfile)

mesh = mfem.Mesh(meshfile, 1, 1)
#mesh.UniformRefinement()
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
pwj_force = -31.03E6 # Pa
#pwj_force = -13.97E6 # Pa

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

young_mod = {}
young_mod['CP-Ti-G2']    = 102.7E9  # GPa
young_mod['Ti6Al4V-G5']  = 96.5E9   # GPa
young_mod['Ti6Al4V-G23'] = 113.8E9  # GPa
young_mod['Al 6061-T6']  = 68.9E9   # GPa

shear_mod = {}
shear_mod['CP-Ti-G2']    = 45E9
shear_mod['Ti6Al4V-G5']  = 43E9 # GPa
shear_mod['Ti6Al4V-G23'] = 44E9 # GPa
shear_mod['Al 6061-T6']  = 26E9 # GPa

lamb_0 = lambda_shear(young_mod['Al 6061-T6'], shear_mod['Al 6061-T6'])
lamb_1 = lambda_shear(young_mod['Ti6Al4V-G23'], shear_mod['Ti6Al4V-G23'])

mu_0 = shear_mod['Al 6061-T6']
mu_1 = shear_mod['Ti6Al4V-G23']

print(f"Al 6061-T6  | {lookup('GREEK SMALL LETTER LAMDA')}_0 : {lamb_0:0.3g} | {lookup('GREEK SMALL LETTER MU')}_0 : {mu_0:0.3g}")
print(f"Ti6Al4V-G23  | {lookup('GREEK SMALL LETTER LAMDA')}_1 : {lamb_1:0.3g} | {lookup('GREEK SMALL LETTER MU')}_1 : {mu_1:0.3g}")


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
#     "glvis -m displaced.mesh -g sol.gf"
x.Neg()

data = {}
data["displacement"] = get_components((6.35, 0.0, 31.825), mesh, x)

# Required for applied forces to render negative
x.Neg()

scalar_dg_space = mfem.FiniteElementSpace(mesh, fec)

strain = mfem.GridFunction(scalar_dg_space)
strain_coef = StrainCoefficient()
strain_coef.SetDisplacement(x)

stress = mfem.GridFunction(scalar_dg_space)
stress_coef = StressCoefficient(lamb_coef, mu_coef)
stress_coef.SetDisplacement(x)

x_hat, y_hat, z_hat = [0, 1, 2]
for component in [x_hat, y_hat, z_hat]:
    strain_coef.SetComponent(component, component)
    strain.ProjectCoefficient(strain_coef)
    data["strain" + f"_{component}"] = get_components((6.35, 0.0, 31.825), mesh, strain)

    stress_coef.SetComponent(component, component)
    stress.ProjectCoefficient(stress_coef)
    data["stress" + f"_{component}"] = get_components((6.35, 0.0, 31.825), mesh, stress)

# Reset displacement
x.Neg()

print(data)

save_data = False 
if save_data == True:
    mesh.Print(f'{fname}.mesh', 8)
    x.Save(f'{fname}.gf', 8)
    stress.Save(f'{fname}_stress.gf', 8)
    strain.Save(f'{fname}_stress.gf', 8)

    paraview_dc = mfem.ParaViewDataCollection(f"{fname}", mesh)
    paraview_dc.SetPrefixPath("ParaView")
    paraview_dc.SetLevelsOfDetail(1)
    paraview_dc.SetCycle(0)
    paraview_dc.SetDataFormat(mfem.VTKFormat_BINARY)
    paraview_dc.SetHighOrderOutput(True)
    paraview_dc.SetTime(0.0)
    paraview_dc.RegisterField("displacement", x)
    paraview_dc.Save()
