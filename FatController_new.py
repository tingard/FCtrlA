
"""
FatController.py is the main code for the project. It will be the one compiling the shell scripts and
running them to produce a mass. See README.md for program flow and examples.
For usage run:
python FatController.py --help
"""
# TODO: add checking of presence of files required for each step

import os
import sys
import json
import getopt
import shutil
import subprocess
import re
import string
import numpy as np
from operator import itemgetter
from datetime import datetime
from time import time, sleep
from threading import Thread, active_count

try:
    from astropy.io import fits
    from astropy.cosmology import Planck15 as Cosmo
    import astropy.units as u
except ImportError as e:
    print 'Import error:', e
    print '\nModule requirements:\n\tAstropy v1.1.1 or newer\n\tNumpy v1.10.4 or newer'
    sys.exit(0)


def usage(v=False):  # print usage and quit
    print 'usage: python FatController.py [-f json_input_file.json]'
    print '       python FatController.py [-o ObsID] [-r right ascension (degrees)]'
    print '                               [-d <declination> (degrees)> OR --dec <...> for negative declination]'
    print '                               [-z <redshift>]'
    print '                               [-R <r500 (kpc)>] [-T temperature] [-n nH value] [-j enable job submission]'
    print '                               [-m force monotonic shell density]'
    print '       python FatController.py --help'

    if v:
        print 'If json file input provided, required keys inside json file:'
        print '\t"ObsID"     : XMM Observation ID of target cluster'
        print '\t"ra"        : Right Ascension of target cluster in degrees (fk5 system)'
        print '\t"dec"       : Declination of target cluster in degrees (fk5 system)'
        print '\t"z"         : Redshift of cluster'
        print '\t"r500"      : r500 of target cluster in kpc'
       
        print
        print 'If no file provided, required keyword arguments:'
        print '\t"-o": XMM Observation ID of target cluster'
        print '\t"-r": Right Ascension of target cluster in degrees (fk5 system)'
        print '\t"-d": Declination of target cluster in degrees (fk5 system) (cannot be negative)'
        print '\t\tOR "--dec": Declination of target (can be negative)'
        print '\t"-z": Redshift of target cluster in degrees (fk5 system)'
        print '\t"-R": R500 of cluster in kiloparsecs'
        print
        print 'Additional Optional arguments:'
        print '\t"-j": enable job submission (see README for when this should be used)'
        print '\t\tThis corresponds to a JSON flag of "enable jobs" being True'
        print '\t"-m": Constrain shell density to be monotonically decreasing with radius'
        print '\t\tThis corresponds to a JSON flag of "monotonic" being True'
        print '\t"-N <number of shells>": Number of shells to use (default is 8)'
        print '\t\tThis corresponds to a JSON keyword of N'
        print '\t"-F <shell factor>": Rate of increase of shell boundaries (default 1.5)'
        print '\t\tThis corresponds to a JSON keyword of F'
        print
        print '\nExamples:'
        print '  python FatController.py -o 0201903501 -r 149.5916 --dec -11.0642 -z 0.1605 -R 1095 -T 3.15 -n 0.001'
        print '    ^^ Abell 907 cluster ^^'
        print '  python FatController.py -j session_log1463267285.96.log'
        print
        print 'More information can be found in T. Lingard\'s MPhys report (albeit code outdated),'
        print 'or in the README.md file'

    sys.exit(0)


loc = os.path.abspath(os.path.dirname(__file__))
try:
    with open(loc+'/templateCommands.json') as templates_file:
        templates = json.load(templates_file)
except IOError:
    print 'ERROR: Require templateCommands.json file in same location as FatController.py'
    sys.exit(0)


def check_arguments():
    if len(sys.argv[1:]):
        try:
            opts, args = getopt.getopt(sys.argv[1:], 'f:o:r:d:z:R:T:n:jmN:F:', ['help', 'dec='])
        except getopt.GetoptError:
            # unrecognized argument passed
            print 'getopt error'
            opts, args = None, None
            usage()
        provided_args = [i[0] for i in opts]
        if '--help' in provided_args:  # print verbose help
            usage(v=True)
        if '-f' not in provided_args:  # user has not provided an input json file (batch running for instance)
            if not all(a in provided_args for a in ['-o', '-r', '-z', '-R','-T','-n']) and not \
                    (('-d' in provided_args) or ('--dec' in provided_args)):  # check correct provided arguments
                print 'Missing argument, require -o -r -d -z -R -Tx -n all with values in this mode.'
                usage()
            else:
                try:
                    args_obsid = re.match('^[0-9]+$', opts[provided_args.index('-o')][1]).group()
                    args_ra = float(opts[provided_args.index('-r')][1])
                    if '-d' in provided_args:
                        args_dec = float(opts[provided_args.index('-d')][1])
                    elif '--dec' in provided_args:
                        args_dec = float(opts[provided_args.index('--dec')][1])
                    else:
                        args_dec = None
                        usage()  # this should never happen
                    args_z = float(opts[provided_args.index('-z')][1])
                    args_r500 = u.Quantity(float(opts[provided_args.index('-R')][1]), u.kpc)
                    d_a = Cosmo.angular_diameter_distance(args_z)
                    args_r500_arcseconds = (180.0/np.pi)*float(args_r500/d_a)*3600
                    args_temp = float(opts[provided_args.index('-T')][1])
                    args_n = float(opts[provided_args.index('-n')][1])
                    return_dict = {
                        'ObsID': args_obsid,
                        'ra': args_ra,
                        'dec': args_dec,
                        'z': args_z,
                        'r500 kpc': float(args_r500/u.Quantity(1.0, u.kpc)),
                        'r500 arcseconds': args_r500_arcseconds,
                        'T': args_temp,
                        'n': args_n
                    }
                    if '-j' in provided_args:
                        return_dict['enable jobs'] = True
                    else:
                        return_dict['enable jobs'] = False
                    if '-N' in provided_args:
                        return_dict['N'] = int(opts[provided_args.index('-N')][1])
                    if '-F' in provided_args:
                        return_dict['N'] = float(opts[provided_args.index('-F')][1])

                    return return_dict  # return a dictionary with session information

                except ValueError as err:
                    print err
                    usage()
        else:  # user has provided an input json file, check it has all required keywords
            json_args = {}
            try:
                if os.path.isfile(opts[provided_args.index('-f')][1]):
                    with open(opts[provided_args.index('-f')][1]) as json_args_file:
                        json_args = json.load(json_args_file)
                else:
                    print "Could not find JSON file, check the file path"
            except ValueError as err:
                print err
                usage()
            json_keys = json_args.keys()
            if all(k in json_keys for k in ['ObsID', 'ra', 'dec', 'z', 'r500']):
                return_dict = {k: v for k, v in json_args}
                valid_file = True
                valid_file &= re.match('^[0-9]+$', json_args['ObsID']).group()  # ensure a valid ObsID is provided
                try:
                    # ensure all provided core arguments valid
                    # TODO: make this more robust - check or ignore other arguments
                    float(json_args['ra'])
                    float(json_args['dec'])
                    float(json_args['z'])
                    float(json_args['r500'])
                    int(json_args.get('N', 1))
                    float(json_args.get('F', 1.0))
                except ValueError:
                    valid_file &= False

                if not valid_file:
                    print 'Invalid JSON file'
                    usage()

                if '-j' in provided_args:
                    return_dict['enable jobs'] = True
                else:
                    return_dict['enable jobs'] = return_dict.get('enable jobs', False)

                return return_dict

            else:
                print 'Invalid json input'
                usage()
    else:
        usage()


def make_working_directory(obs_id):
    working_dir = loc + '/FCtrlA_{}'.format(obs_id)
    i = 0
    while os.path.exists(working_dir):
        working_dir = loc + '/FCtrlA_{}{}'.format(obs_id, ('_' + str(i) if i else ''))
        i += 1
    print 'Working in folder:', working_dir

    if not os.path.exists(working_dir):  # this should always happen, it's just a failsafe
        os.mkdir(working_dir)
    if not os.path.exists(working_dir+'/code'):  # same here
        os.mkdir(working_dir+'/code')
    if not os.path.exists(working_dir+'/output'):  # and here
        os.mkdir(working_dir+'/output')
    return working_dir


def save_session(session):
    """Dump the current session to a JSON file in the spec_{ObsID} folder
    :param session: dictionary, current session information (ra, dec, masking string, run options)
    :return: None
    """
    with open(session['cwd']+'/session_log{}.log'.format(time()), 'w') as f:
        json.dump(session, f, indent=2)


def print_save_run(phase, code, session, blocking=True):
    """
    Print the shell code to be called to the screen, and run it inside a subprocess/as a job on Apollo
    :param phase: string, phase of code being run (1a, 1b, 2a...)
    :param code: list of strings, list of commands to be run
    :param session: dictionary, current session information (ra, dec, masking string, run options)
    :param blocking:
    :return: None
    """
    # TODO: change this to an apollo job submission, which waits for the job to be complete
    # print a concatenated version of the code to the screen (full version still in output files)
    print "\n------ Phase {} Code: ------".format(phase)
    print '\n'.join(map(lambda x: x[:min(len(x), 150)]+('...' if len(x) > 150 else ''), code)), '\n', '-'*28

    # save the session code in a shell script
    with open(session['cwd'] + '/code/phase{}_code.sh'.format(phase), 'w') as f:
        f.write('# phase {phase}, generated by FatController.py on {timestamp}\n'.format(
            phase=phase,
            timestamp=datetime.now())
        )
        f.write('\n\n'.join(code))

    # check if the user wants us to submit these as jobs to apollo
    if session.get('enable jobs', False) and not blocking:
        # submit the code as a job to apollo (UNFINISHED)
        if not os.path.exists(session['cwd']+'/job_submission'):
            pass
        with open(session['cwd'] + '/code/job_template.job', 'w') as job_file:
            # write out a job to a standard job file
            job_file.write(templates['job_maker'].format(
                output=session['cwd']+'/output/phase{}_out.log'.format(phase),
                phase=phase,
                wd=session['cwd'],
                command='sh {}/code/phase{}_code.sh'.format(session['cwd'], phase)
            ))

        with open(session['cwd'] + '/output/job_sub_out.log', 'a') as job_out:
            subprocess.call(
                ['qsub', session['cwd'] + '/code/job_template.job'],
                stdout=job_out,
                stderr=job_out
            )

        # check that the job has been successfully submitted
        with open(session['cwd']+'/output/job_sub_out.log', 'r') as job_out:
            if not re.match(r'Your job .*? has been submitted',
                            filter(lambda x: x, job_out.read().split('\n'))[-1]
                            ):
                print 'Could not submit job - phase {}'.format(phase)
                print json.dumps(session, indent=2)
                sys.exit(0)

    elif not blocking:  # set the code running on a thread
        def background_task(wd, phase):
            with open(wd + '/output/phase{}_out.log'.format(phase), 'w') as code_out:
                subprocess.call(
                    ['sh', wd + '/code/phase{}_code.sh'.format(phase)],
                    stdout=code_out,
                    stderr=code_out
                )

        t = Thread(target=background_task, args=[session['cwd'], phase])
        t.start()
    else:
        with open(session['cwd'] + '/output/phase{}_out.log'.format(phase), 'w') as code_out:
            subprocess.call(
                ['sh', session['cwd'] + '/code/phase{}_code.sh'.format(phase)],
                stdout=code_out,
                stderr=code_out
            )

    # TODO: introduce error checking here, will need to be smart as some expected strings contain "error" (evselect)


def phase1a(session):
    """
    We extract an image from the events list, and convert the XAPA region file from image coordinates to degrees.
    We then identify and flag the XAPA source corresponding to the cluster of interest.
    :param session: dictionary, current session information (ra, dec, masking string, run options)
    :return: None
    """
    wd = session['cwd']

    # compile shell scripts to be run in the first bit of this phase
    shell_code = [
        templates['sas_setup_string'].format(
            obsID=session['ObsID']
        ),
        templates['sas_image_extract'].format(
            pn_table=session['events list'],
            pn_image=wd+'/pn_image.fits'
        ),
        templates['xwindow_start'],
        templates['ds9_to_fk5'].format(
            pn_image=templates['regions_file'].format(
                obsID=session['ObsID'],
                file='image.fits'
            ),
            input_regions=session['XAPA regions'],
            output_regions=wd+'/fk5_regions.reg'
        )
    ]

    # print the generated shell code to the screen, save it, run it and log the output
    print_save_run('1a', shell_code, session)

    # We now need to remove (and store) the region containing the cluster of interest.
    # To do this, we find the region in the provided region file which is closest to our
    # cluster centre

    # read in the generated regions
    with open(wd + '/fk5_regions.reg') as f:
        regions = f.read().split('\n')

    coords = []

    for reg in regions:
        r = re.match(r'.*?\((-?[0-9]+\.[0-9]+),(-?[0-9]+\.[0-9]+).*?\).*?', reg)  # extract coordinates
        if r:
            # if we have a regular expression match, convert to float and add to a list
            coords += [map(float, r.groups())]
        else:
            # otherwise add a value which is miles away from anything
            coords += [[-1E6, -1E6]]

    distances = map(lambda x: (x[0]-session['ra'])**2+(x[1]-session['dec'])**2, coords)

    # remove the region nearest the provided cluster center
    # TODO: ensure this is an extended source
    cluster_reg = regions.pop(min(enumerate(distances), key=itemgetter(1))[0])

    with open(wd + '/fk5_regions_edited.reg', 'w') as f:
        # write to a local region file
        f.write('\n'.join(regions))

        # we leave a marker to identify the cluster of interest (we will use its position for
        # centring the extracted spectra in Phase 2)
        f.write('\n{} # <-- this one here'.format(cluster_reg))


def phase1b(session):
    """
    Convert XAPA coordinates and r500 to physical units, and create a masking string for Phase 2
    Requires phase1a
    :param session: dictionary, current session information (ra, dec, masking string, run options)
    :return: None
    """
    wd = session['cwd']
    N = session['N']
    F = session['F']

    # write the r500 to a region file so we can use ds9 to convert coordinates
    with open(wd + '/cluster_r500_fk5.reg', 'w') as f:
        f.write(templates['reg_string'].format(
            x=session['ra'],
            y=session['dec'],
            r500_as=session['r500 arcseconds'])
        )

    shell_code = [
        templates['xwindow_start'],
        templates['ds9_to_physical'].format(
            pn_image=wd+'/pn_image.fits',
            input_regions=wd+'/fk5_regions_edited.reg',
            output_regions=wd+'/physical_regions.reg'
        ),
        templates['ds9_to_physical'].format(
            pn_image=wd+'/pn_image.fits',
            input_regions=wd+'/cluster_r500_fk5.reg',
            output_regions=wd+'/cluster_r500_physical.reg'
        )
    ]

    # print the generated shell code to the screen, save it, run it and log the output
    print_save_run('1b', shell_code, session)

    # read in the generated region file in physical coords to obtain masking values and the
    # position to put the cluster in
    with open(wd+'/cluster_r500_physical.reg', 'r') as f:
        f_cont = f.read().replace('\n', '')
        r500_physical = float(re.findall(r'-?[0-9]+\.[0-9]+', f_cont)[-1])

    # calculate shell boundaries in physical and arcsecond coordinates
    shells = [float(r500_physical)/F**(N-i-1) for i in range(N)]
    shells_asec = [float(session['r500 arcseconds'])/session['F']**(session['N']-i-1)
                   for i in range(N)]

    # read in the converted XAPA regions in physical coordinates
    with open(wd+'/physical_regions.reg') as f:
        physical_regions = f.read().split('\n')

    # identify the previously flagged region (comments are kept by ds9)
    centre_index, centre_physical_coords = [i for i in enumerate(physical_regions) if "<-- this one here" in i[1]][0]

    # grab the physical coordinate from the string
    centre_physical_coords = re.match(r'.*?\(([0-9]+\.[0-9]+),([0-9]+\.[0-9]+).*?\).*?',
                                      centre_physical_coords).groups()
    centre_physical_coords = map(float, centre_physical_coords)

    # get rid of the region corresponding to the XAPA source of the cluster
    physical_regions.pop(centre_index)

    # combine the remaining regions into a masking string
    masking_string = ' &&! '.join(
        map(lambda x: '((X,Y) IN {})'.format(x),
            re.findall('ellipse\(.*?\)', '    '.join(physical_regions))
            )
    )

    # save all generated results to the session
    session['ra physical'], session['dec physical'] = centre_physical_coords
    session['r500 physical'] = r500_physical
    session['shells'] = shells
    session['shells arcseconds'] = shells_asec
    session['masking string'] = masking_string
    return


def phase2a(session):
    """
    We start the process of Spectra extraction, up to the generation of RMF files
    Requires phase 1b
    :param session: dictionary, current session information (ra, dec, masking string, run options)
    :return: None
    """
    wd = session['cwd']

    # we generate the commands to extract our concentric annular spectra
    # write these to a region file for sanity checking
    reg_file = 'global color=green dashlist=8 5 width=2 font="helvetica 10 normal roman" ' + \
               'select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1\nphysical\n'

    reg_file += '\n'.join(['ellipse({x},{y},{r1},{r2},0)'.format(
        x=session['ra physical'],
        y=session['dec physical'],
        r1=i,
        r2=i
    ) for i in session['shells']])

    reg_file += '\nellipse({x},{y},{r1},{r2},0) # color=red dash=1\n'.format(
        x=session['ra physical'],
        y=session['dec physical'],
        r1=session['shells'][-1]*1.2,
        r2=session['shells'][-1]*1.2
    )

    with open(wd+'/output/annuli.reg', 'w') as f:
        f.write(reg_file)

    shell_code = [
        templates['sas_setup_string'].format(
            obsID=session['ObsID']
        ),
        templates['sas_circle_gen'].format(
            pn_table=session['events list'],
            outfile=wd+"/annulus0.fits",
            x_pos=session['ra physical'],
            y_pos=session['dec physical'],
            radius=session['shells'][0],
            masking_string=session['masking string']
        )
    ]

    for i in range(1, len(session['shells'])):
        shell_code += [
            templates['sas_annulus_gen'].format(
                pn_table=session['events list'],
                outfile=wd+"/annulus{}.fits".format(i),
                x_pos=session['ra physical'],
                y_pos=session['dec physical'],
                inner_radius=session['shells'][i-1],
                outer_radius=session['shells'][i],
                masking_string=session['masking string']
            )
        ]

    # and extract the background spectra, which is an annulus around r500 (not best
    # practise, but will do for now)
    shell_code += [
        templates['sas_annulus_gen'].format(
            pn_table=session['events list'],
            outfile=wd+"/background_spectrum.fits",
            x_pos=session['ra physical'],
            y_pos=session['dec physical'],
            inner_radius=float(session['shells'][-1]),
            outer_radius=float(session['shells'][-1])*1.2,
            masking_string=session['masking string']
        )
    ]

    # we then add commands to backscale the generated inner spectra
    shell_code += [
        templates['sas_backscale'].format(
            input_spectrum=wd+'/annulus{}.fits'.format(i),
            pn_table=session['events list']
        ) for i in range(session['N'])]

    # and add the backscale command for the background spectrum, then to generate an
    # rmf file
    shell_code += [
        templates['sas_backscale'].format(
            input_spectrum=wd+'/background_spectrum.fits',
            pn_table=session['events list']
        ),
        templates['sas_rmfgen'].format(
            input_spectra=wd+'/annulus0.fits',
            output_rmf=wd+'/rmf_annulus0.rmf'
        )
    ]

    # send the code off to run
    print_save_run('2a', shell_code, session, blocking=(not session['enable jobs']))

    # if the session is running on apollo, we need to wait for it to finish (might be worth adding some sort of ticker?)
    if session['enable jobs']:
        sleep(1)
        print 'Waiting for phase 2a to run on Apollo'
        for i in xrange(18000):
            sys.stdout.write(
                '\b'*30+'last checked {}'.format(
                    '{:%H:%M:%S}'.format(
                        datetime.now()
                    )
                )
            )
            sys.stdout.flush()
            try:
                with open(wd+'/running_jobs.lock', 'r') as f:
                    if '2a' in f.read():
                        sleep(2)
                    else:
                        print
                        return
            except IOError:
                sleep(2)


def phase2b(session):
    """
    Generate ARF files for each annulus. This needs to be parallelised as much as possible
    :param session: dictionary, current session information (ra, dec, masking string, run options)
    :return: None
    """
    wd = session['cwd']
    # for each generated annulus, create an arf file
    for i in range(session['N']):
        # if jobs are enabled
        if session['enable jobs']:
            shell_code = [
                templates['sas_setup_string'].format(
                    obsID=session['ObsID']
                ),
                'mkdir {}/tmp_annulus{}'.format(wd, i),
                'cd {}/tmp_annulus{}'.format(wd, i),
                templates['sas_arfgen'].format(
                    input_spectra=wd+'/annulus{}.fits'.format(i),
                    output_arf=wd+'/arf_annulus{}.arf'.format(i),
                    input_rmf=wd+'/rmf_annulus0.rmf',
                    pn_table=session['events list']
                ),
                'cd '+wd,
                'rm -r {}/tmp_annulus{}'.format(wd, i)
            ]
            print_save_run('2b.ARF{}'.format(i), shell_code, session, blocking=False)
        else:
            shell_code = [
                templates['sas_setup_string'].format(
                    obsID=session['ObsID']
                ),
                'mkdir {}/tmp_annulus{}'.format(wd, i),
                'cd {}/tmp_annulus{}'.format(wd, i),
                templates['sas_arfgen'].format(
                    input_spectra=wd+'/annulus{}.fits'.format(i),
                    output_arf=wd+'/arf_annulus{}.arf'.format(i),
                    input_rmf=wd+'/rmf_annulus0.rmf',
                    pn_table=session['events list']
                ),
                'cd '+wd,
                'rm -r {}/tmp_annulus{}'.format(wd, i)
            ]
            # attempting to run this
            print_save_run('2b.ARF{}'.format(i), shell_code, session, blocking=True)

    if session['enable jobs']:
        # we now wait for the arfgen jobs to be done
        print 'Submitted arfgen jobs, waiting for completion'
        for i in xrange(18000):
            sys.stdout.write(
                '\b'*30+'last checked {}'.format(
                    '{:%H:%M:%S}'.format(
                        datetime.now()
                    )
                )
            )
            sys.stdout.flush()
            with open(wd+'/running_jobs.lock', 'r') as f:
                if 'arfgen' in f.read():
                    pass
                else:
                    if sum('arf_annulus' in i for i in os.listdir(wd)) >= session['N']:
                        print
                        return
            sleep(2)
    else:
        print 'Running arfgen jobs as background processes. Waiting on completion'
        generated_arfs = {re.match(r'^arf_annulus([0-9]+).arf$', i).group(1) for i in os.listdir(wd) if 'arf_' in i}
        while active_count() > 1 and not generated_arfs == set(map(str, range(session['N']))):
            sys.stdout.write(
                '\b'*30+'last checked {}'.format(
                    '{:%H:%M:%S}'.format(
                        datetime.now()
                    )
                )
            )
            sys.stdout.flush()
            sleep(2)
            generated_arfs = {re.match(r'^arf_annulus([0-9]+).arf$', i).group(1) for i in os.listdir(wd) if 'arf_' in i}
        print 'Active thread count', active_count()


def phase2c(session):
    """
    Group spectrum files and add XFLT keywords
    :param session: dictionary, current session information (ra, dec, masking string, run options)
    :return:
    """
    wd = session['cwd']

    # check files have been generated
    generated_spectra = {re.match(r'^annulus([0-9]+).fits$', i).group(1) for i in os.listdir(wd) if i[:7] == 'annulus'}
    if not generated_spectra == set(map(str, range(session['N']))):
        print 'Could not find all expected spectra'
        print '\tFound:', {re.search('[0-9]+', i).group() for i in generated_spectra}
        print '\tExpected:', set(range(session['N']))
        sys.exit(0)

    generated_arfs = {re.match(r'^arf_annulus([0-9]+).arf$', i).group(1) for i in os.listdir(wd) if 'arf_' in i}
    if not generated_arfs == set(map(str, range(session['N']))):
        print 'Could not find all generated ARF files'
        print '\tFound:', generated_arfs
        print '\tExpected:', set(range(session['N']))
        sys.exit(0)

    shell_code = [templates['sas_setup_string'].format(obsID=session['ObsID'])] + \
        [
            templates['sas_group_spectra'].format(
                input_spectrum='{}/annulus{}.fits'.format(wd, i),
                rmf=wd+'/rmf_annulus0.rmf',
                arf=wd+'/arf_annulus{}.arf'.format(i),
                background_spectrum=wd+'/background_spectrum.fits',
                output_spectrum=wd+'/spectrum_group{}.fits'.format(i)
            )
            for i in range(session['N'])
        ]

    # print and run the code (this is blocking as we have not passed submit=True)
    print_save_run('2c', shell_code, session)

    # check that we have all the expected spectryn groups, and add XFLT keyword headers
    expected_groups = {'spectrum_group{}.fits'.format(i) for i in range(session['N'])}
    if {i for i in os.listdir(wd) if 'spectrum_group' in i} == expected_groups:
        for i in range(session['N']):
            f = fits.open(wd+'/spectrum_group{}.fits'.format(i), mode='update')
            # at a later date this can become more complicated to take into account portions
            # of clusters which are outside the observation. I'm ignoring that for now
            f[1].header['XFLT0001'] = session['shells arcseconds'][i]
            f[1].header['XFLT0002'] = session['shells arcseconds'][i]
            f.flush()
            f.close()


def phase3(session, path_to_model='/lustre/scratch/inf/tl229/new_massmod'):
    """
    Identify initial parameters. Create a template XSPEC script, run it and scrape the output
    :param session: dictionary, current session information (ra, dec, masking string, run options)
    :param path_to_model: path to Clmass root model package
    :return: None
    """
    wd = session['cwd']

    # we need to symlink some of the files required for apollo
    subprocess.call('ln -s {} {}'.format(path_to_model+'/support/Basic_Constants', wd+'/'), shell=True)
    subprocess.call('ln -s {} {}'.format(path_to_model+'/support/stdcosmo.pars', wd+'/'), shell=True)
    subprocess.call('ln -s {} {}'.format(path_to_model+'/support/cosinfo', wd+'/'), shell=True)

    # check if we have been provided with initial parameters
    if ('n' in session.keys()) and ('T' in session.keys()):
        nH = session['n']
        kT = session['T']


    # cd into the working directory
    os.chdir(wd)

    # create the XSPEC command to load the data groups (to be put inside the xcm script)
    data_groups = ['data {0[1]}:{0[1]} {1}/spectrum_group{0[0]}.fits'.format([i, i+1], wd) for i in range(session['N'])]

    # edit a template clmass xcm script
    xspec_script = templates['clmass_script'].format(
        data_groups='\n'.join(data_groups),
        model_path=path_to_model,
        model='monomass' if session.get('monotonic', False) else 'clmass',
        nH=nH,
        kT=kT,
        z=session['z'],
        r500=session['r500 arcseconds']
    )

    # write the script out to a file
    with open(wd+'/code/clmass_script.xcm', 'w') as f:
        f.write(xspec_script)

    # create the command to run the generated xcm script in XSPEC
    shell_code = 'xspec - {wd}/code/clmass_script.xcm &> {wd}/output/clmass_output.log'.format(
        wd=wd
    )

    # run the clmass script
    print_save_run('3', [shell_code], session)

    m500 = -1.0
    try:
        # open the log file
        with open(wd+'/output/clmass_output.log', 'r') as f:
            clmass_out = f.read().split('\n')
        model_mass_unit = 0
        # search the log file for the model mass unit
        mass_str = re.search('[0-9]+.[0-9]+', [i for i in clmass_out if 'Model mass unit' in i][-1])
        if mass_str is not None:
            print 'Identified mass unit as', mass_str.group()
            model_mass_unit = float(mass_str.group())
        # search the log file for the m500 (in model units)
        model_mass = float(clmass_out[[i for i, j in enumerate(clmass_out) if 'puts [massOfR' in j][-1]+1])

        # if we find values for both the model mass unit in solar masses, and the m500 in model mass units
        if model_mass_unit != 0 and model_mass != 0:
            m500 = model_mass_unit*model_mass
            # print "Identified mass of {} M_solar".format(model_mass_unit*model_mass)
        else:
            print 'Could not find model mass' + (' unit' if model_mass_unit != 0 else '')

    except IOError:
        print 'Could not find xpsec log file'

    # if we have a value, save the m500 to the session
    if m500 != -1.0:
        session['m500'] = m500


def main():
    cluster_info = check_arguments()  # check command-line arguments passed to the script
    cluster_info['cwd'] = make_working_directory(cluster_info['ObsID'])  # make a directory to work in

    # set default values for cluster shell count and growth if not provided
    if not cluster_info.get('N'):
        cluster_info['N'] = 8  # define number of annuli to use
    if not cluster_info.get('F'):
        cluster_info['F'] = 1.4  # define shell growth parameter

    cluster_info['events list'] = templates['pn_file'].format(
        obsID=cluster_info['ObsID'], pn_table="pn_exp1_clean_evts.fits"
    )
    cluster_info['XAPA regions'] = templates['regions_file'].format(
        obsID=cluster_info['ObsID'], file="final_class_regions_REDO.reg"
    )

    phase1a(cluster_info)  # conduct phase 1a
    phase1b(cluster_info)  # conduct phase 1b

    phase2a(cluster_info)  # conduct phase 2a
    phase2b(cluster_info)  # conduct phase 2b
    phase2c(cluster_info)  # conduct phase 2c

    phase3(cluster_info)   # conduct phase 3

    if cluster_info.get('m500'):
        print 'Identified Cluster mass of {} M_solar'.format(cluster_info['m500'])
    save_session(cluster_info)  # save the result of this session to a timestamped JSON file


if __name__ == '__main__':
    main()
