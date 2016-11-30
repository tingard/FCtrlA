# HaroldHelper.py
"""
This file contains a series of helper functions which can be used to trigger and configure FatController.py runs
"""

import os
import sys
import json
import subprocess
import time

loc = os.path.dirname(os.path.abspath(__file__))

template_job = """#$ -S /bin/bash
#$ -cwd
#$ -j y
#$ -o {output}
{command}
"""  # template job file, requires output, phase, wd, command


def makeFCCommand(d):
    # TODO enable changing of shell factor and number of annuli
    if not type(d) == dict:
        print d
        print "Invalid type"
        sys.exit(0)
    if all(d.get(i, False) for i in ['ObsID', 'ra', 'dec', 'z', 'r500']):
        command_str = 'python {loc}/FatController.py -o {ObsID} -r {ra} --dec {dec} -z {z} -R {r500}'
        if d.get('enable jobs', 'False') != 'False':
            command_str += ' -j'
        if d.get('monotonic', 'False') != 'False':
            command_str += ' -m'
        if not d.get('loc', False):
            d['loc'] = loc
        return command_str.format(**d)


def fc_from_csv(csv_path, wd, delimiter=',', submit=False):
    """
    Takes in a csv list containing required information and returns a list of fatController commands.
    The csv must have headers on line one. Note that space-seperated csvs will not work if using the
    "enable jobs" option.
    :param csv_path: path to input csv (or dat) file
    :param delimiter: csv file delimiter
    :param wd: working directory of HaroldHelper
    :param submit: flag specifying whether to trigger jobs on Apollo
    :return:
    """
    print '-'*15+' submit_from_csv says: '+'-'*15
    print 'working in', wd
    r = []
    with open(csv_path, 'r') as f:
        headers = f.readline().replace('\r', '').replace('\n', '').split(delimiter)
        for line in f:
            r += [{i: j for i, j in zip(headers, line.replace('\r', '').replace('\n', '').split(delimiter))}]
    print 'Identified Headers:\n\t', ', '.join(headers)
    print '\tWith {} clusters'.format(len(r))
    if all(i in headers for i in ['ObsID', 'ra', 'dec', 'z', 'r500']):
        if submit is True:
            for i in r:
                sub_job(i, wd)
                time.sleep(1)
            return []
        else:
            return map(makeFCCommand, r)
    else:
        l = ['ObsID', 'ra', 'dec', 'z', 'r500']
        print zip(l, [i in headers for i in l])
        print headers
        print 'ERROR - Not all required headers present'
        print 'Minimum required headers: \n\tObsID, ra, dec, z, r500'
        return []


def sub_job(d, wd):
    command = makeFCCommand(d)
    fname = wd+'/tmp_job{}'.format(d['ObsID'])
    print command
    j = template_job.format(
        output=fname+'.log',
        command=command
    )

    with open(fname+'.job', 'w') as f:
        f.write(j)

    subprocess.call(['qsub', '-q', 'parallel.q', fname+'.job'])

if __name__ == "__main__":
    csv = loc+'/nulsenClusters.csv'
    working_dir = loc + '/HaroldHelperLogs_{}'.format(int(time.time()))
    os.mkdir(working_dir)
    print '\n'.join(fc_from_csv(csv, working_dir, submit=True))
