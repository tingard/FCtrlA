# fcTemplates.py
"""
This file is used to write the default template strings to a json file to be read in by fatcontroller.
 Should only need to be run once.
"""
import json

arfgen_job = """
# Job template
# qsub job_template.job obsid /path/to/pn /path/to/spectrum /path/to/rmf /path/to/arf

#$ -S /bin/bash
#$ -cwd
#$ -o output.txt

echo "Running job script"

my_die () {{
    echo >&2 "$@"
    exit 1
}}
[ "$#" -eq 5 ] || my_die "5 arguments required, $# provided"
OBSID="${{1:-""}}"
PN_TABLE="${{2:-""}}"
INPUT_SPECTRUM="${{3:-""}}"
INPUT_RMF="${{4:-""}}"
OUTPUT_ARF="${{5:-""}}"
export SAS_DIR=/lustre/scratch/astro/pr83/code/sas_dir/xmmsas_20141104_1833
. $SAS_DIR/setsas.sh
export SAS_CCFPATH=/lustre/scratch/astro/pr83/code/ccf
export SAS_ODF=/lustre/scratch/astro/pr83/$OBSID/odf/*SUM.SAS
export SAS_CCF=/lustre/scratch/astro/pr83/$OBSID/odf/ccf.cif

echo $OUTPUT_ARF >> {dir}/lock_arf.lock
mkdir {dir}/tmp_$OUTPUT_ARF
cd {dir}/tmp_$OUTPUT_ARF
arfgen spectrumset=$INPUT_SPECTRUM arfset={dir}/tmp_$OUTPUT_ARF/$OUPUT_ARF.arf withrmfset=yes rmfset=$INPUT_RMF \
badpixlocation=$PN_TABLE detmaptype=psf &> {dir}/output/$OUTPUT_ARF.log
cd {dir}
mv {dir}/tmp_$OUTPUT_ARF/$OUPUT_ARF.arf {dir}/$OUTPUT_ARF.arf
rm -r tmp_$OUTPUT_ARF
sed -i.bak '/$OUTPUT_ARF/d' {dir}/lock_arf.lock

""" # template job file, to be written into each spectrum directory. Requires dir of spec_folder. n.b. OUTPUT ARF should be just a name, with no path or extension

pn_file = "/lustre/scratch/astro/pr83/{obsID}/eclean/{pn_table}"  # location of pn table, requires: obsID, pn_table

regions_file = "/lustre/scratch/astro/pr83/code/xapa/1412/{obsID}/{file}"  # location of region file requires: obsID, file

sas_setup_string ="""export SAS_DIR=/lustre/scratch/astro/pr83/code/sas_dir/xmmsas_20141104_1833
. $SAS_DIR/setsas.sh
export SAS_CCFPATH=/lustre/scratch/astro/pr83/code/ccf
export SAS_ODF=/lustre/scratch/astro/pr83/{obsID}/odf/*SUM.SAS
export SAS_CCF=/lustre/scratch/astro/pr83/{obsID}/odf/ccf.cif""" # string to initialise SAS, requires obsID

reg_string = '''# Region file format: DS9 version 4.1
global color=green dashlist=8 3 width=1 font="helvetica 10 normal roman" select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1
fk5
circle({x},{y},{r500_as}")
'''
sas_image_extract = "evselect table={pn_table} imagebinning=binSize imageset={pn_image} withimageset=yes xcolumn=X ycolumn=Y ximagebinsize=80 yimagebinsize=80" # requires: pn_table, pn_image

xwindow_start = "Xvfb :1 &\nexport DISPLAY=:1;\nsleep 2"

ds9_to_fk5 = "ds9 -fits {pn_image}  -regions {input_regions} -regions system wcs -regions sky fk5 -regions save {output_regions} -quit" # requires: pn_image, input_regions, output_regions

ds9_to_physical = "ds9 -fits {pn_image} -regions {input_regions} -regions system physical -regions save {output_regions} -quit" # requires: pn_image, input_regions, output_regions

sas_circle_gen = "evselect table={pn_table} withspectrumset=yes spectrumset={outfile} energycolumn=PI spectralbinsize=5 withspecranges=yes specchannelmin=0 specchannelmax=20479 expression='(FLAG==0) && (PATTERN<=4) && ((X,Y) IN circle({x_pos},{y_pos},{radius})) &&! {masking_string}'"  # string to generate circular spectra, requires: pn_table, outfile, x_pos, y_pos, radius, masking_string

sas_annulus_gen = "evselect table={pn_table} withspectrumset=yes spectrumset={outfile} energycolumn=PI spectralbinsize=5 withspecranges=yes specchannelmin=0 specchannelmax=20479 expression='(FLAG==0) && (PATTERN<=4) && ((X,Y) IN annulus({x_pos},{y_pos},{inner_radius},{outer_radius})) &&! {masking_string}'"  # string to generate annular spectra, requires: pn_table, outfile, x_pos, y_pos, inner_radius, outer_radius, masking_string

sas_backscale = "backscale spectrumset={input_spectrum} badpixlocation={pn_table}" # requires: input_spectrum, pn_table

sas_rmfgen = "rmfgen spectrumset={input_spectra} rmfset={output_rmf}"  # can take some time, requires: input_spectra, output_rmf

sas_arfgen = "arfgen spectrumset={input_spectra} arfset={output_arf} withrmfset=yes rmfset={input_rmf} badpixlocation={pn_table} extendedsource=yes detmaptype=flat" # this is the longest of the commands, and needs to be run for each annulus. requires:  input_spectra, output_arf, input_rmf

sas_group_spectra = "specgroup spectrumset={input_spectrum} mincounts=25 oversample=3 rmfset={rmf} arfset={arf} backgndset={background_spectrum} groupedset={output_spectrum}"  # requires: input_spectrum, rmf, arf, background_spectrum, output_spectrum

job_maker = """#$ -S /bin/bash
#$ -cwd
#$ -j y
#$ -o {output}
echo {phase} >> {wd}/running_jobs.lock
{command}
sed -i '/{phase}/d' {wd}/running_jobs.lock"""  # template job file, requires output, phase, wd, command

clmass_script = """{data_groups}
\nset clmroot {model_path}
lmod clmass ${{clmroot}}/model
ignore bad
ignore **-0.3
ignore 7.9-**
model {model} ( wabs * mekal )
/*
newpar 37 {nH}
freeze 37
#newpar 38 {kT}
newpar 40 0.3
newpar 41 {z}
freeze 41
newpar 43 1e-3 1e-5
xset delta 0.01
source ${{clmroot}}/tcl/mixcommon.tcl
source ${{clmroot}}/tcl/phyconst.tcl
source ${{clmroot}}/tcl/{model}.tcl
massmod_start 0 0 1.1 0
setscales 1.0 rbounds runit Munit rhocritmodel
mixNFWstartPars rbounds {kT} 6 $runit $rhocritmodel
query yes
fit 100
breakLinks {{{{Abundanc ""}}}}
fit
puts $runit
puts [massOfR {r500} rbounds]
fit
log
puts [MassConf radius {r500} rbounds 0.01]
log none

set result {#Better fit found.  Rerun fit now.}
set term {#Better fit found.  Rerun fit now.}
 while {$result==$term} {
    set fp [open xspec.log]
    set data [split [read $fp] \n]
    set result [lsearch -exact -inline $data $term]
    puts $result
    close $fp

    if {$result==$term} {
      fit
      log
      puts [MassConf radius {r500} rbounds 0.01]
      log none
      puts success
    }
 }
exit
"""  # template clmass script, requires: data_groups, model_path, model, nH, kT, z, r500

d = {#'arfgen_job': arfgen_job,
     'pn_file': pn_file,
     'regions_file': regions_file,
     'reg_string': reg_string,
     'sas_setup_string': sas_setup_string,
     'sas_image_extract': sas_image_extract,
     'xwindow_start': xwindow_start,
     'ds9_to_fk5': ds9_to_fk5,
     'ds9_to_physical': ds9_to_physical,
     'sas_circle_gen': sas_circle_gen,
     'sas_annulus_gen': sas_annulus_gen,
     'sas_backscale': sas_backscale,
     'sas_rmfgen': sas_rmfgen,
     'sas_arfgen': sas_arfgen,
     'sas_group_spectra': sas_group_spectra,
     'job_maker': job_maker,
     'clmass_script': clmass_script
}

if __name__=="__main__":
    with open('templateCommands.json', 'w') as f:
        json.dump(d, f, indent=2)