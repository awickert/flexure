#! /usr/bin/env python

import gflex
import numpy as np
from matplotlib import pyplot as plt

flex = gflex.F1D()

flex.Quiet = True

flex.Method = 'FD' # Solution method: * FD (finite difference)
                   #                  * SAS (superposition of analytical solutions)
                   #                  * SAS_NG (ungridded SAS)

flex.Solver = 'direct' # direct or iterative
# convergence = 1E-3 # convergence between iterations, if an iterative solution
                     # method is chosen

flex.g = 9.8 # acceleration due to gravity
flex.E = 65E9 # Young's Modulus
flex.nu = 0.25 # Poisson's Ratio
flex.rho_m = 3300. # MantleDensity
flex.rho_fill = 0. # InfiillMaterialDensity

flex.Te = 5000.*np.ones(50) # Elastic thickness -- scalar but may be an array
#flex.Te[-3:] = 0
flex.qs = np.zeros(50); flex.qs[10:50] += 1E6 # surface load stresses
flex.dx = 5000. # grid cell size [m]
flex.BC_W = '0Displacement0Slope' # west boundary condition
flex. BC_E = '0Moment0Shear' # east boundary condition

flex.initialize()
flex.run()
flex.finalize()

# If you want to plot the output
flex.plotChoice='combo'
# An output file for deflections could also be defined here
# flex.wOutFile = 
flex.output() # Plots and/or saves output, or does nothing, depending on
              # whether flex.plotChoice and/or flex.wOutFile have been set
