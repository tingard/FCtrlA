


# Outline

FCtrlA is a package of tools for X-ray hydrostatic mass calculation of XCS clusters using the Clmass extension to XSPEC. 
Package Contents:

* FatController.py
* ThomasTemplates.py
* HaroldHelper.py
* PercyPlotter.py
* MavisMassTemp.py
* DaisyDegreeCalc.py

------

# Requirements
FCtrlA requires the installation of a number of other packages:

* Astropy v1.1.1 or newer
* SAS
* HEASoft 6.17 (with Xspec)
* Clmass (a version which has been edited to work with HEASoft 6.17

Installation of these packages can be done by following their respective guides. Good luck!

------

# Code

###FatController
FatController requires an Observation ID, right-ascension, declination, redshift and R<sub>500</sub> of a cluster, as well as a number of optional arguments detailed below, and makes use of the Clmass package to calculate a cluster's M<sub>500</sub>.

The process is as follows:
 
* Phase 1a:
    * Generate a local image
    * Convert XAPA regions from image coordinates to degrees (using the fk5 reference frame, Fricke et al., 1988)
    * Identify the XAPA source region corresponding to the cluster of interest, and flag this region with a comment
* Phase 1b:
  * Convert the provided R<sub>500</sub> to physical coordinates (after converting it to degrees when it is read in)
  * Convert XAPA regions from degrees to physical coordinates
  * Calculate shell boundaries
  * Identify physical coordinates of cluster in observation from the flag in the XAPA region file
  * Generate a masking string of non-cluster XAPA sources, to be ignored in spectal extraction
*  Phase 2a:
  * Extract spectra from N concentric annuli, with outer radiuses increasing by factor F each time
  * Extract a background spectrum
  * Backscale the extracted regions
  * Generate an RMF file from the innermost annulus
* Phase 2b:
  * Generate ARF files for each extracted spectrum
* Phase 2c:
  * Group spectrum, background, ARF and RMF files
  * Add XFLT keyword to the FITS headers containing shell outer boundary in arcseconds
* Phase 3:
  * Symlink files from Clmass package to working directory
  * Find initial values for cluster temperature and fraction of neutral Hydrogen
  * Format a template XSPEC script and save to an <code>xcm</code> script
  * Run the <code>xcm</code> script and log the output
  * Scrape the output for cluster M<sub>500</sub> in model mass units, and model mass unit to solar mass conversion.

####FatController arguments:

* <code>-o < ></code>: XMM Observation ID of target cluster
* <code>-r < ></code>: Right ascension of cluster in degrees in the fk5 reference system
* <code>-d < ></code>: Declination of cluster in degrees in the fk5 reference system
* <code>-z < ></code>: Redshift of cluster
* <code>-r500</code>: R<sub>500</sub> of cluster in kiloparsecs
* Optional flags:
  * <code>-j</code>:  Enable Apollo job submission
  * <code>-m</code>:  Constrain density function to be monotonic
* Optional additional arguments:
  * <code>-N < ></code>: Number of annuli to use
  * <code>-F < ></code>: Shell radius factor (r<sub>i</sub> = R<sub>500</sub>/F<sup>N-i-2</sup>, i in [0,N))

Note that shells go out beyond R<sub>500</sub>
A907 cluster example:
python FatController.py -o 0201903501 -r 149.5916 --deg 11.0642 -z 0.1605 -R 1095 -


##ThomasTemplates

ThomasTemplates provides an easy way of generating a syntactically correct json file containing all required template commands for FatController. It need only be edited to add a template command, or to update commands for updated software packages.


##HaroldHelper

HaroldHelper contains a series of functions designed to assist in the generation of FatController configurations. For example, <code>fc_from_csv</code> accepts a path to a csv file, and an optional delimiter, and will return a list of FatController commands for the provided clusters.


## PercyPlotter

PercyPlotter takes two arguments and creates a cluster mass profile.
1) The R500 radius of the cluster. 
2) The path to the clmass_script.xcm file. This file is located in the /code directory of the spec_... directory created by FatController.py

This program should be run from the directory above the spec_... folder of the cluster in question. 
<b> NB: It is likely that three errors pertaining to clmass files will be displayed when running PercyPlotter, this is not an issue! </b>


## MavisMassTemp

Currently, this code creates a plot of M<sub>500</sub> (cluster mass) vs kT (cluster temperature)

It does not require arguments, it only needs to be executed in a directory of FatController.py output folders (of the form spec_xxxx.)

It can identify clusters that failed to run, and will also avoid using data from spec_xxxx folders with more than one session_log file


## DaisyDegreeCalc

This is a small tool, designed to convert Ra and Dec from their standard forms to degrees

It takes 6 arguments:
1) The Right Ascension Hours measurement
2) The Right Ascension Minutes measurement
3) The Right Ascension Seconds measurement
4) The Declination Degrees measurement
5) The Declination Minutes measurement
6) The Declination Seconds measurement

It can also be run <b> without </b> any arguments, and the user will be asked for them in the program
Any number of arguments other than 0 or 6 will return an error

---