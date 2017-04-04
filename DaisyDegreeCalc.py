import sys


def no_arg():
    print('Right Ascension')
    hours = float(raw_input('Hours: '))
    minutes = float(raw_input('Minutes: '))
    seconds = float(raw_input('Seconds: '))
    Ra = [hours, minutes, seconds]

    print('')
    print('Declination')
    deg = float(raw_input('Degrees: '))
    minutes = float(raw_input('Minutes: '))
    seconds = float(raw_input('Seconds: '))
    Dec = [deg, minutes, seconds]

    CalcPrint(Ra, Dec)


def full_args():
    Ra = [float(i) for i in sys.argv[1:4]]
    Dec = [float(i) for i in sys.argv[4:7]]
    CalcPrint(Ra, Dec)


def CalcPrint(Ra, Dec):
    RaHour, RaMin, RaSec = Ra
    DecDeg, DecMin, DecSec = Dec

    TotalHours = (RaSec / 3600.0) + (RaMin / 60.0) + RaHour
    print('')
    print('The Right Ascension in degrees is ' + str(TotalHours * 15))

    TotalDegrees = (DecSec/3600.0) + (DecMin/60.0) + DecDeg
    print('')
    print('The Declination in degrees is ' + str(TotalDegrees))
    print('')

if __name__ == "__main__":
    if len(sys.argv[1:]) == 0:
        no_arg()
        sys.exit(0)
    elif len(sys.argv[1:]) == 6:
        try:
            float(sys.argv[1])
            full_args()
        except:
            print 'Invalid radius argument, exiting'
            sys.exit(0)

    elif len(sys.argv[1:]) != 6:
        print('Please enter three arguments each for Ra and Dec')
        sys.exit()