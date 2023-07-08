# coding: utf-8

from mfem._ser.gridfunc import GridFunction
import numpy as np

# MFEM v4.5 uses deprecated numpy variable numpy.long
major, minor, micro = [int(v) for v in np.__version__.split('.')]
if major == 1 and micro > 23:
    np.long = np.longlong

import mfem.ser as mfem
from typing import Union


class StrainCoefficient(mfem.PyCoefficientBase):
    def __init__(
            self, 
            si=0, 
            sj=0):
        super(StrainCoefficient, self).__init__(0)
        self.si = si
        self.sj = sj
        self.u: Union[mfem.GridFunction, None] = None   # displacement GridFunction
        self.grad = mfem.DenseMatrix()

    def SetComponent(self, i, j):
        self.si = i
        self.sj = j

    def SetDisplacement(self, u):
        self.u = u

    def Eval(self, T, ip):
        si, sj = self.si, self.sj
        self.u.GetVectorGradient(T, self.grad)
        if si == sj:
            # epsilon = 0.5 * (u[i, j] + u[j, i])
            epsilon = self.grad[si, si]
        else:
            epsilon = 0.5 * (self.grad[si, sj] + self.grad[sj, si])
        return epsilon 


class StressCoefficient(mfem.PyCoefficientBase):
    def __init__(
            self, 
            lambda_coef, 
            mu_coef, 
            si=0, 
            sj=0):
        super(StressCoefficient, self).__init__(0)
        self.lam = lambda_coef   # coefficient
        self.mu = mu_coef       # coefficient
        self.si = si
        self.sj = sj     # component
        self.u: Union[mfem.GridFunction, None] = None   # displacement GridFunction
        self.grad = mfem.DenseMatrix()

    def SetComponent(self, i, j):
        self.si = i
        self.sj = j

    def SetDisplacement(self, u):
        self.u = u

    def Eval(self, T, ip):
        si, sj = self.si, self.sj
        L = self.lam.Eval(T, ip)
        M = self.mu.Eval(T, ip)
        self.u.GetVectorGradient(T, self.grad)
        if (self.si == self.sj):
            div_u = self.grad.Trace()
            sigma = L * div_u + 2 * M * self.grad[si, si]
        else:
            sigma = M * (self.grad[si, sj] + self.grad[sj, si])
        return sigma


class StrainVectorCoefficient(mfem.VectorPyCoefficient):
    def __init__(
            self, 
            dim: int):
        super(StrainVectorCoefficient, self).__init__(dim)
        self.dim = dim
        self.u: Union[mfem.GridFunction, None] = None
        self.grad = mfem.DenseMatrix()
        self.v = mfem.Vector()

    def SetDisplacement(self, u: mfem.GridFunction):
        self.u = u

    def Eval(self,
             v: mfem.Vector, 
             T: mfem.ElementTransformation, 
             ip: mfem.IntegrationPoint,):
        # grad(u)
        self.u.GetVectorGradient(T, self.grad)
        # (grad(u) + grad(u)^T) / 2
        self.grad.Symmetrize()

        size = self.grad.Size()
        if size == 2:
            # Set the principle strains xx, yy, xy
            v[0] = self.grad[0, 0]
            v[1] = self.grad[1, 1]
            v[2] = self.grad[0, 1]
        elif size == 3:
            # Set the principle strains xx, yy, zz, xy, xz, yz
            v[0] = self.grad[0, 0]
            v[1] = self.grad[1, 1]
            v[2] = self.grad[2, 2]
            v[3] = self.grad[0, 1]
            v[4] = self.grad[0, 2]
            v[5] = self.grad[1, 2]
        
        return self.grad


class StressVectorCoefficient(mfem.VectorPyCoefficient):
    def __init__(
            self, 
            lambda_coef: mfem.PWConstCoefficient, 
            mu_coef: mfem.PWConstCoefficient,
            dim: int):
        super(StressVectorCoefficient, self).__init__(dim)
        self.dim = dim
        self.lam = lambda_coef   # coefficient
        self.mu = mu_coef       # coefficient
        self.u = None   # displacement GridFunction
        self.grad = mfem.DenseMatrix()
        self.sigma = mfem.DenseMatrix()

    def SetDisplacement(self, u: mfem.GridFunction):
        self.u = u

    def Eval(
            self, v: mfem.Vector, 
            T: mfem.ElementTransformation, 
            ip: mfem.IntegrationPoint):
        L = self.lam.Eval(T, ip)
        M = self.mu.Eval(T, ip)
        
        self.u.GetVectorGradient(T, self.grad)
        self.grad.Symmetrize()
        
        # sigma = lambda * div_u * I = lambda * trace(grad(u)) * I
        self.sigma.Diag(L * self.grad.Trace(), self.grad.Size())
        # sigma += 2 * mu * grad(u)
        self.sigma.Add(2 * M, self.grad)
        
        size = self.sigma.Size()
        # Set the principle strains xx, yy, zz, xy, xz, yz
        if size == 2:
            v[0] = self.sigma[0, 0]
            v[1] = self.sigma[1, 1]
            v[2] = self.sigma[0, 1]
        elif size == 3:
            v[0] = self.sigma[0, 0]
            v[1] = self.sigma[1, 1]
            v[2] = self.sigma[2, 2]
            v[3] = self.sigma[0, 1]
            v[4] = self.sigma[0, 2]
            v[5] = self.sigma[1, 2]

        return self.sigma
