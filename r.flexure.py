#! /usr/bin/python

"""
Started 11 March 2012 as a GRASS interface for Flexure (now gFlex)
Revised 15 November 2014 after significantly improving the model
by Andy Wickert
"""

#%module
#%  description: Lithospheric flexure
#%end
#%flag
#%  description: Allows running in lat/lon, assumes 1deg lat = 111.32 km, 1 deg lon is f(lat) at grid N-S midpoint
#%end
#%option
#%  key: method
#%  type: string
#%  description: Solution method: FD (finite difference) or SAS (superposition of analytical solutions)
#%  options: FD, SAS
#%  required : yes
#%end
#%option
#%  key: q
#%  type: string
#%  gisprompt: old,cell,raster
#%  description: Raster map of loads (thickness * density * g)
#%  required : yes
#%end
#%option
#%  key: te
#%  type: string
#%  gisprompt: old,cell,raster
#%  description: Elastic thicnkess: constant value or raster map (~constant ) name [km]
#%  required : yes
#%end
#%option
#%  key: output
#%  type: string
#%  gisprompt: old,cell,raster
#%  description: Output raster map of vertical deflections [m]
#%  required : yes
#%end
#%option
#%  key: rho_fill
#%  type: double
#%  description: Density of material that fills flexural depressions [kg/m^3]
#%  answer: 0
#%  required : no
#%end
#%option
#%  key: n
#%  type: string
#%  description: Northern boundary condition
#%  options: Dirichlet0, 0Moment0Shear, 0Slope0Shear, Mirror, Periodic
#%  answer: NoOutsideLoads
#%  required : no
#%end
#%option
#%  key: s
#%  type: string
#%  description: Southern boundary condition
#%  options: Dirichlet0, 0Moment0Shear, 0Slope0Shear, Mirror, Periodic
#%  answer: NoOutsideLoads
#%  required : no
#%end
#%option
#%  key: w
#%  type: string
#%  description: Western boundary condition
#%  options: Dirichlet0, 0Moment0Shear, 0Slope0Shear, Mirror, Periodic
#%  answer: NoOutsideLoads
#%  required : no
#%end
#%option
#%  key: e
#%  type: string
#%  description: Eastern boundary condition
#%  options: Dirichlet0, 0Moment0Shear, 0Slope0Shear, Mirror, Periodic
#%  answer: NoOutsideLoads
#%  required : no
#%end


# PATH
import sys
# Path to Flexure model - hard-coded here
sys.path.append("/home/awickert/models/flexure/trunk")

# FLEXURE
from base import *
from f1d import *
from f2d import *
from prattairy import *

# GRASS
import numpy as np
from grass.script import core as grass
from grass.script import mapcalc
from grass.script import db as db
import grass.script.array as garray
import time

def main():

  # Flags
  latlon_override = flags['l']
  
  # Inputs
  # Solution selection
  method = options['method']
  # Parameters
  q = options['q']
  Te = options['te']
  rho_fill = float(options['rho_fill'])
  bcn = options['n']
  bcs = options['s']
  bcw = options['w']
  bce = options['e']
  # Output
  output = options['output']
  
  # Is Te raster or scalar?
  TeIsRast = False
  try:
    Te = float(Te)
  except:
    TeIsRast = True

  # This code is for 2D flexural isostasy
  obj = F2D()
  obj.set_value('model', 'flexure')
  obj.set_value('dimension', 2)
  
  obj.set_value('GravAccel', 9.8)
  if method == SAs:
    obj.set_value('method', 'SAS')
  if method == SAS:
    obj.set_value('method', 'FD')
    obj.set_value('Solver', 'direct')
    # Always use the van Wees and Cloetingh (1994) solution type.
    # It is the best.
    obj.set_value('PlateSolutionType', 'vWC1994')

  # No filename: getter/setter interface isn't totally worked out
  # FIX THIS!!!!
  obj.filename = None

  # Make a bunch of standard selections
  # CHANGE THESE INTO PARAMETERS THAT CAN BE CHOSEN!
  obj.set_value('YoungsModulus', 65E9)#70E6/(600/3300.))#
  obj.set_value('PoissonsRatio', 0.25)
  obj.set_value('GravAccel', 9.8)
  obj.set_value('MantleDensity', 3300)

  # Set all boundary conditions
  obj.set_value('BoundaryCondition_East', bce)
  obj.set_value('BoundaryCondition_West', bcw)
  obj.set_value('BoundaryCondition_North', bcn)
  obj.set_value('BoundaryCondition_South', bcs)

  # Get grid spacing from GRASS
  # Check if lat/lon
  if grass.region_env()[6] == '3':
    if latlon_override:
      print "Latitude/longitude grid."
      print "Setting y-resolution [m] to 111,320 * [degrees]"
      obj.set_value('GridSpacing_x', grass.region()['ewres']*111000.)
      print "Setting y-resolution [m] to 111,320 * [degrees]"
      obj.set_value('GridSpacing_y', grass.region()['nsres']*111000.)
    else:
      sys.exit("Need projected coordinates, or the '-l' flag to approximate.")
  else:
    obj.set_value('GridSpacing_x', grass.region()['ewres'])
    obj.set_value('GridSpacing_y', grass.region()['nsres'])


  # Get raster grids from GRASS
  q0rast = garray.array()
  q0rast.read('q0resamp')
  if TeIsRast:
    FlexureTe = garray.array() # FlexureTe is the one that is used by Flexure
    FlexureTe.read('Teresamp')

  # Change these grids into basic numpy arrays for easier use with Flexure
  q0rast = np.array(q0rast)
  if TeIsRast:
    FlexureTe = np.array(FlexureTe * 1000) # *1000 for km-->m
  else:
    FlexureTe = Te * 1000 # km --> m (scalar)

  # Values set by user
  obj.set_value('Loads', q0rast[1:-1,1:-1]) # Te needs to be 1 cell bigger on each edge
  obj.set_value('ElasticThickness', FlexureTe)# np.ones(Te.shape)*20000)#
  obj.set_value('InfillMaterialDensity', rho_fill) # defaults to 0

  # Calculated values
  obj.drho = obj.rho_m - obj.rho_fill

  # CALCULATE!
  #obj.initialize(None)
  obj.run()
  obj.finalize()

  # Write to GRASS
  # First, shrink the region by 1 cell so it accepts the flexural solution
  n = grass.region()['n'] - grass.region()['nsres']
  s = grass.region()['s'] + grass.region()['nsres']
  e = grass.region()['e'] - grass.region()['ewres']
  w = grass.region()['w'] + grass.region()['ewres']
  nrows = grass.region()['rows']-2
  ncols = grass.region()['cols']-2
  grass.run_command('g.region', n=n, s=s, w=w, e=e, rows=nrows, cols=ncols) 
  # Then create a new garray buffer and write to it
  outbuffer = garray.array() # Instantiate output buffer
  outbuffer[...] = obj.w
  outbuffer.write(output, overwrite=True) # Write it with the desired name
  # And create a nice colormap!
  grass.run_command('r.colors', map=output, color='rainbow', quiet=True)#, flags='e')
  # Then revert to the old region
  grass.run_command('g.region', n=n, s=s, w=w, e=e) 
  n = grass.region()['n'] + grass.region()['ewres']
  s = grass.region()['s'] - grass.region()['ewres']
  e = grass.region()['e'] + grass.region()['ewres']
  w = grass.region()['w'] - grass.region()['ewres']
  grass.run_command('g.region', n=n, s=s, w=w, e=e)

  # Finally, return to original resolution (overwrites previous region selection)
  grass.run_command('g.region', rast=Te)
  grass.run_command('r.resamp.interp', input=output, output=output + '_interp', method='lanczos', overwrite=True, quiet=True)
  grass.run_command('r.colors', map=output + '_interp', color='rainbow', quiet=True)#, flags='e')

  #imshow(obj.w, interpolation='nearest'), show()

if __name__ == "__main__":
  options, flags = grass.parser()
  main()

