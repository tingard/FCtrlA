#################################
#A code to plot the temperature profiles for all the clusters in one directory. The path name has to be changed as per the directory
#an example of the way to run the code python reshmaTR.py FCtrlA_0020540401	FCtrlA_0020540401/output/clmass_output.log FCtrlA_0020540401/session_log1491905834.89.log -t2.72242
#so basically it creates two new files, one with the radius of each shell and the other with the temperatures and its errors and plots the Temp profile from those files.
##########################

import numpy as np
import sys
import os
import re
import matplotlib.pyplot as plt
import time
import subprocess
from collections import OrderedDict
import pylab as py
from statistics import mean
from matplotlib import style
####################
if __name__ == "__main__":
   print sys.argv

   if len(sys.argv)>0:
       print sys.argv[1]
       obsid = (sys.argv[1])
       print(obsid)
       T = float(sys.argv[4][2:])
       clmass_outputlog = sys.argv[2]
       print clmass_outputlog
       radius_script = sys.argv[3]
       print radius_script
tempo = float(T)
######################################################
def readFile(filename):
    filehandle = open(filename)
    #print filehandle.read()
    filehandle.close()
fileDir = os.path.dirname(os.path.realpath('/home/robineappen/Desktop/Robin_project/spec/rmv12anewF/with mass'))
print fileDir
filename = os.path.join(fileDir, clmass_outputlog)
readFile(filename)
###############################################################
def readFile(filename2):
    filehandle = open(filename2)
    #print filehandle.read()
    filehandle.close()
fileDir = os.path.dirname(os.path.realpath('/home/robineappen/Desktop/Robin_project/spec/rmv12anewF/with mass'))
print fileDir
filename2 = os.path.join(fileDir, radius_script)
readFile(filename2)
###############################################################
path = (sys.argv[2][:len(sys.argv[2]) - 17])
pthsec = path.split('/')
os.chdir(pthsec[0])
print(os.getcwd())
fname = pthsec[1] + '/' + 'kTs.txt'.format(int(time.time()))
path2 = (sys.argv[1])
pthsec = path.split('/')
#os.chdir(pthsec[0])
#print(os.getcwd())
fname2 = pthsec[1] + '/' + 'rs.txt'.format(int(time.time()))
searchquery = '   4    1   clmass     switch              0            frozen'

with open(filename) as f1:
    with open(fname, 'a') as f2:
        lines = f1.readlines()
        for i, line in enumerate(lines):
            if line.startswith(searchquery):
                f2.write(lines[i + 1])
                f2.write(lines[i + 2])
                f2.write(lines[i + 3])
                f2.write(lines[i + 4])
                f2.write(lines[i + 5])
                f2.write(lines[i + 6])
                f2.write(lines[i + 7])
                f2.write(lines[i + 8])

f1.close()
f2.close()

lines = open(fname).readlines()
open(fname, 'w').writelines(lines[16:24])

searchquery2 = '  "shells": ['
with open(filename2) as f3:
    with open(fname2,'a') as f4:
        lines = f3.readlines()
        for k, line in enumerate(lines):
            #line.replace(',','')
            if line.startswith(searchquery2):
                f4.write(lines[k + 1])
                f4.write(lines[k + 2])
                f4.write(lines[k + 3])
                f4.write(lines[k + 4])
                f4.write(lines[k + 5])
                f4.write(lines[k + 6])
                f4.write(lines[k + 7])
                f4.write(lines[k + 8])  
                

f3.close()
f4.close()

with open(fname2, 'r+') as f:
    text = f.read()
    f.seek(0)
    f.truncate()
    f.write(text.replace(',' , ''))

##################################################################

temp = (clmass_outputlog [:len(sys.argv[2]) - 17])
print (temp)
############################################################################
def readFile(filename3):
    filehandle = open(filename3)
    #print filehandle.read()
    filehandle.close()



fileDir3 = os.path.dirname(os.path.realpath('/home/robineappen/Desktop/Robin_project/spec/rmv12anewF/with mass/lol'))
print fileDir3
filename3 = os.path.join(fileDir3, temp + 'kTs.txt')
readFile(filename3)

#################################################################
def readFile(filename4):
    filehandle = open(filename4)
    #print filehandle.read()
    filehandle.close()



fileDir = os.path.dirname(os.path.realpath('/home/robineappen/Desktop/Robin_project/spec/rmv12anewF/with mass/mol'))
print fileDir
filename4 = os.path.join(fileDir, temp + 'rs.txt')
readFile(filename4)

#############################################################
style.use('fivethirtyeight')
t = np.genfromtxt(filename3, usecols=(12), delimiter='  ', dtype=None)
r = np.genfromtxt(filename4, usecols=(0), delimiter='   ', dtype=None)

#xmin=0
#xmax=10
#ymin=10**13
#ymax=10**15
#plt.axis([xmin,xmax,ymin,ymax])
fig, ax1 = plt.subplots()


np.random.seed(5)
slp = np.random.uniform(1,5)  # slope
intc = np.random.uniform(0,50) # y intercept
#y = slp*r + intc + np.random.normal(0,60,100) # scatter data
#plt.plot(r,y,'o') # scatter plot

m,b = py.polyfit(r,t,1)   #linear fit



#plt.yscale('log')
#plt.xscale('log')
plt.xlabel(r'Radius (Kpc)')
plt.ylabel(r'Temp (Kev)')
plt.title('Temp Profile')
plt.plot(r,t,'g*',r, m*r+b, 'r') # plot best fit
ax1.plot(r, t, c='r', marker='o', markeredgewidth=0, linewidth=0, markersize=7)
#plt.plot(r,T,'g*')
plt.axhline(y=tempo)
#ax1.errorbar(t, m,yerr = 0, xerr=[terr1,terr2], linestyle=' ', c= 'r')
#ax1.plot(r, r, c='b', marker='>', markeredgewidth=0, linewidth=0, markersize=7)
#ax1.errorbar(t, mcalc,yerr = 0, xerr=[terr1,terr2], linestyle=' ', c= 'b')
#plt.axis([xmin,xmax,ymin,ymax])
#plt.show()
plt.grid(True)
plt.savefig(obsid+'_TR.png')
#################################
