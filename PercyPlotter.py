import numpy as np
import sys
import re
import matplotlib.pyplot as plt
if len(sys.argv[1:])==0:
    print 'No outer radius given, exiting'
    sys.exit(0)
else:
    try:
        float(sys.argv[1])
    except:
        print 'Invalid argument, exiting'
        sys.exit(0)
print sys.argv[1]
x = np.logspace(1,np.log10(float(sys.argv[1])),70)
#x = np.linspace(10, float(sys.argv[1]), 30)
print '\n'.join('massOfR {} rbounds'.format(i) for i in x)
s = []
inpt = ''
while inpt != 'end':
    inpt = raw_input('Input result: ')
    if re.match(r'^[0-9]+\.[0-9]+$', inpt):
        s.append(float(inpt))
try:
    mass_unit = float(raw_input('Input mass unit: '))
    distance_unit = float(raw_input('Input distance unit: '))
    ms = [i*mass_unit for i in s]
    rs = [i*distance_unit for i in x]
    plt.plot(rs, ms)
    shells = raw_input('Paste shellBounds output: ')
    print shells
    if len(shells):
        sbs = [i.split()[1] for i in shells.split('} {')]
        print "Identified: \n\t"+'\n\t'.join(map(str,sbs))
        for s in sbs:
            plt.axvline(x=float(s)*distance_unit, linestyle='--', color='#ff1111')
    plt.xscale('log')
    plt.yscale('log')
    plt.xlabel('Radius (kpc)')
    plt.xlim((10, 1e4))
    plt.ylim((4.4e12, 1e16))
    plt.ylabel(r'Mass (r) $M_\odot$')
    plt.grid(True)
    plt.show()
except ValueError as e:
    print e
    sys.exit(0)
