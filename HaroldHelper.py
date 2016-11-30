# HaroldHelper.py
"""
This file contains a series of helper functions which can be used to trigger and configure FatController.py runs
"""

import os


loc = os.path.dirname(os.path.abspath(__file__))


def makeFCCommand(d):
    if all(d.get(i, False) for i in ['ObsID', 'ra', 'dec', 'z', 'r500']):
        command_str = 'python {loc}/FatController.py -o {ObsID} -r {ra} --dec {dec} -z {z} -R {r500}'
        if d.get('enable jobs', '') != 'False':
            command_str += ' -j'
        if d.get('monotonic', '') != 'False':
            command_str += ' -m'
        if not d.get('loc', False):
            d['loc']=loc
        return command_str.format(**d)


def fc_from_csv(csv_path, delimiter=','):
    """
    Takes in a csv list containing required information and returns a list of fatController commands.
    The csv must have headers on line one. Note that space-seperated csvs will not work if using the
    "enable jobs" option.
    :param csv_path: path to input csv (or dat) file
    :param delimiter: csv file delimiter
    :return:
    """
    print '-'*15+' submit_from_csv says: '+'-'*15
    r = []
    with open(csv_path, 'r') as f:
        headers = f.readline().replace('\n','').split(delimiter)
        for line in f:
            r += [{i: j for i, j in zip(headers, line.replace('\n','').split(delimiter))}]
    print 'Identified Headers:\n\t', ' '.join(headers)
    print '\tWith {} clusters'.format(len(r))
    if all(i in headers for i in ['ObsID', 'ra', 'dec', 'z', 'r500']):
        return map(makeFCCommand, r)
    else:
        print 'ERROR - Not all required headers present'
        print 'Minimum required headers: \n\tObsID, ra, dec, z, r500'
        return []


if __name__=="__main__":
    print '\n'.join(submit_from_csv(loc+'/test.csv'))







