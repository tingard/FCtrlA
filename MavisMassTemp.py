import subprocess
import os
from matplotlib import pyplot


"""
This section of the FCtrlA project will cycle through a large number of spec_xxxx directories and create the mass-temp
relation graph.
It will also attempt to fit this and provide a mathematical relation

AnnoteFinder credit to: AndrewStraw, GaelVaroquaux, Unknown[99], AngusMcMorland, newacct, danielboone
"""

global loc
loc = os.path.abspath(os.path.dirname(__file__))


def DirSearch():   # This function looks for spec_ directories and extracts data from sessionlogs
    proc = subprocess.Popen('ls', stdout=subprocess.PIPE)
    output = proc.stdout.read()
    Thing = output.split('\n')
    SpecDirs = []
    ObsID = []
    for i in range(0, len(Thing)):
        if 'spec_' in Thing[i]:
            SpecDirs.append(Thing[i])
            ObsID.append((Thing[i].split('_'))[1])

    return SpecDirs


def FindLog(SpecDirs):
    LogName = []
    MassLineAr = []
    TempLineAr = []

    for i in range(0, len(SpecDirs)):
        os.chdir(loc + '/' + SpecDirs[i])
        proc = subprocess.Popen('ls', stdout=subprocess.PIPE)
        output = proc.stdout.read()
        FileList = output.split('\n')

        if len(FileList) > 0:
            indices = [y for y, elem in enumerate(FileList) if 'session' in elem]

            if len(indices) == 1:
                LogName.append(FileList[indices[0]])
            else:
                LogName.append('Fail.txt')

        else:
            print("There's nowt there")
            LogName.append('Fail.txt')

        try:
            cwd = os.getcwd()
            f = open(cwd + '/' + LogName[i])

            for line in f:
                if 'm500' in line:
                    MassLineAr.append(line)
                if 'kT' in line:
                    TempLineAr.append(line)

        except IOError:
            print('No such file')

        os.chdir(loc)

    return MassLineAr, TempLineAr


def DataExtract(MassRaw, TempRaw):
    Mass = []
    Temp = []

    if len(MassRaw) != len(TempRaw):
        print("There's some buggery occuring")

    else:
        for i in range(0, len(MassRaw)):
            Stage1 = MassRaw[i].split(':')
            Stage2 = Stage1[1].split(' ')
            Stage3 = Stage2[1].split(',')
            Mass.append(float(Stage3[0]))

            Stage1 = TempRaw[i].split(':')
            Stage2 = Stage1[1].split('"')
            Temp.append(float(Stage2[1]))

    return Mass, Temp


def MTPlot(Mass, Temp):
    global plot

    fig = pyplot.figure()
    plot = fig.add_subplot(111)

    line, = plot.plot(Temp, Mass, 'x', color='r', picker=5)
    pyplot.yscale('log')
    pyplot.ylabel('Mass ($M_{\odot}$)')
    pyplot.xlabel('kT ($keV$) [Probably]')

    fig.canvas.mpl_connect('pick_event', onpick)
    pyplot.show()


def onpick(event):
    thisline = event.artist
    xdata = thisline.get_xdata()
    ydata = thisline.get_ydata()
    ind = event.ind
    pointx = xdata[ind]
    pointy = ydata[ind]



Directories = DirSearch()
m, t = FindLog(Directories)
M, T = DataExtract(m, t)
MTPlot(M, T)
