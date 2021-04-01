#!/usr/bin/env python

'''
Evaluate the values of density, exchange-correlation functional and XC
potential on given grid coordinates.
'''

import numpy
from pyscf import gto, dft, lib
from pyscf.dft import numint
from pyscf.dft import r_numint

mol = gto.M(
    verbose = 0,
    atom = '''
    o    0    0.       0.
    h    0    -0.757   0.587
    h    0    0.757    0.587''',
    basis = '6-31g')

mf = dft.RKS(mol)
mf.kernel()
dm = mf.make_rdm1()

# Use default mesh grids and weights
coords = mf.grids.coords
weights = mf.grids.weights
ao_value = numint.eval_ao(mol, coords, deriv=1)
# The first row of rho is electron density, the rest three rows are electron
# density gradients which are needed for GGA functional
rho = numint.eval_rho(mol, ao_value, dm, xctype='GGA')
print(rho.shape)

#
# Evaluate XC functional one by one.
# Note: to evaluate only correlation functional, put ',' before the functional name
#
ex, vx = dft.libxc.eval_xc('B88', rho)[:2]
ec, vc = dft.libxc.eval_xc(',P86', rho)[:2]
print('Exc = %.12f' % numpy.einsum('i,i,i->', ex+ec, rho[0], weights))

#
# Evaluate XC functional together
#
exc, vxc = dft.libxc.eval_xc('B88,P86', rho)[:2]
print('Exc = %.12f' % numpy.einsum('i,i,i->', exc, rho[0], weights))

#
# Evaluate XC functional for user specified functional
#
exc, vxc = dft.libxc.eval_xc('.2*HF + .08*SLATER + .72*B88, .81*LYP + .19*VWN', rho)[:2]
print('Exc = %.12f  ref = -7.520014202688' % numpy.einsum('i,i,i->', exc, rho[0], weights))

#
# For density matrix computed with GKS in spin-orbital basis, plain density in
# real space is
#
mf = dft.GKS(mol).run()
dm_gks = mf.make_rdm1()
dm_a = dm_gks[:mol.nao, :mol.nao].real
dm_b = dm_gks[mol.nao:, mol.nao:].real
coords = mf.grids.coords
ao_value = mol.eval_gto('GTOval', coords)
rho = numint.eval_rho(mol, ao_value, dm_a + dm_b)
print(rho.shape)

#
# For complex density matrix computed using DKS, rho can be 
#
mf = dft.DKS(mol).run()
n2c = mol.nao * 2
dm = mf.make_rdm1()
dmLL = dm[:n2c,:n2c].copy()
dmSS = dm[n2c:,n2c:].copy()
coords = mf.grids.coords
# Large components
aoL_value = mol.eval_gto('GTOval_spinor', coords)
# Small components
aoS_value = 1/(2*lib.param.LIGHT_SPEED) * mol.eval_gto('GTOval_sp_spinor', coords)
# mL, mS are the spin-magentic moment at each point
rhoL, mL = r_numint.eval_rho(mol, aoL_value, dmLL)
rhoS, mS = r_numint.eval_rho(mol, aoS_value, dmSS)
rho = rhoL + rhoS
mx, my, mz = mL + mS
