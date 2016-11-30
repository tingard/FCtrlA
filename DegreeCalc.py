import numpy

print('Right Ascension')
hours = float(raw_input('Hours: '))
minutes = float(raw_input('Minutes: '))
seconds = float(raw_input('Seconds: '))

TotalHours = (seconds/3600.0) + (minutes/60.0) + hours
print(TotalHours)
print(str(TotalHours*15))

print('Declination')
deg = float(raw_input('Degrees: '))
minutes = float(raw_input('Minutes: '))
seconds = float(raw_input('Seconds: '))

TotalDegrees = (seconds/3600.0) + (minutes/60.0) + deg

print(str(TotalHours))