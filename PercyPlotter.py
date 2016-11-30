import numpy as np
import sys
import os
import re
import matplotlib.pyplot as plt
import time
import subprocess


def one_arg():  # When just the radius is input as an argument
    """
    Takes Radius argument, but requires manual modification and running of the clmass_script.xcm xspec script.
    Highly recommended to simply input the path to clmass_script.xcm as a second argument
    :return: None
    """
    print sys.argv[1]
    x = np.logspace(1,np.log10(float(sys.argv[1])), 70)  # x values for the plot
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
            print "Identified: \n\t"+'\n\t'.join(map(str, sbs))
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


def full_args():
    """
    Accept an outer radius and clmass script location as inputs, edit the script to output more stuff, then run it
    and scrape the output for values as above
    :return: None
    """
    radius = float(sys.argv[1])
    clmass_script = sys.argv[2]
    script = []
    with open(clmass_script) as f:
        for line in f:
            script.append(line.replace('\n',''))

    if script.pop(-1) != 'exit':
        print('wtf')
        sys.exit(0)
    x = np.logspace(1, np.log10(float(sys.argv[1])), 70)
    print(x)
    print('')
    script += ['fit']
    script += ['puts "~~Begin PercyPlotter Output~~"']
    script += ['puts ' + '[' + 'massOfR {} rbounds'.format(i) + ']' for i in x]
    script += ['puts ' + '[' + 'shellBounds' + ']']
    script += ['exit']

    path = (sys.argv[2][:len(sys.argv[2]) - 17])
    pthsec = path.split('/')
    os.chdir(pthsec[0])

    print(os.getcwd())

    # save the script to a new file in the local directory
    fname = pthsec[1] + '/' + 'PercyPlotter_script{}.xcm'.format(int(time.time()))
    with open(fname, 'w') as f:
        f.write('\n'.join(script))

    # run the code and trawl output
    output_name = pthsec[1] + '/' + 'PercyPlotter_output{}.log'.format(int(time.time()))
    subprocess.call('xspec - {} > {}'.format(fname, output_name), shell=True)

    #output_name = pthsec[1] + '/' + 'PercyPlotter_output1473433844.log'
    with open(output_name, 'r') as f:
        result = f.read().split('\n')
    i = result.index('~~Begin PercyPlotter Output~~')
    half1 = result[0:i]
    half2 = result[i:len(result)]
    half2 = [value for value in half2 if value != '']

    v = []
    for count in range(0, len(half2)):
        if re.match(r'^[0-9]+\.[0-9]+$', half2[count]):
            v.append(float(half2[count]))

    try:
        mass_unit_index = 5 + half1.index('!XSPEC12>setscales 1.0 rbounds runit Munit rhocritmodel;')
        splitm = half1[mass_unit_index].split(' ')
        mass_unit = float(splitm[3])
        try:
            float(mass_unit)
        except:
            print('The SetState mass unit line has not been read properly')
            sys.exit(0)

        distance_unit_index = mass_unit_index - 2
        splitd = half1[distance_unit_index].split(' ')
        distance_unit = float(splitd[2])
        try:
            float(distance_unit)
        except:
            print('The SetState distance unit line has not been read properly')
        ms = [i*mass_unit for i in v]
        rs = [i for i in x] #*distance_unit
        print(rs)
        plt.plot(rs, ms)

        shells_index = half2.index('!XSPEC12>puts [shellBounds];')
        shells = half2[shells_index + 1]

        if len(shells):
            sbs = [i.split()[1] for i in shells.split('} {')]
            print "Identified: \n\t"+'\n\t'.join(map(str, sbs))
            for s in sbs:
                plt.axvline(x=float(s), linestyle='--', color='#ff1111')  #*distance_unit
        plt.xscale('log')
        plt.yscale('log')
        plt.xlabel('Radius (kpc)')
        plt.xlim((10, 1e4))
        plt.ylim((4.4e12, 1e16))
        plt.ylabel(r'Mass (r) $M_\odot$')
        plt.grid(True)
        #plt.show()
        plt.savefig('Mass-Radius.png')
    except ValueError as e:
        print e
        sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv[1:]) == 0:
        print 'No outer radius given, exiting'
        sys.exit(0)
    elif len(sys.argv[1:]) == 1:
        try:
            float(sys.argv[1])
            one_arg()
        except:
            print 'Invalid radius argument, exiting'
            sys.exit(0)
    elif len(sys.argv[1:]) == 2:
        try:
            float(sys.argv[1])
        except:
            print 'Invalid radius argument, exiting'
            sys.exit(0)

        if (sys.argv[2])[(len(sys.argv[2]) - 4):] == '.xcm':
            full_args()
        else:
            print('Secondary argument must be a valid XSPEC script')

