#!/usr/bin/python
import serial

def swrite(text):
    ser.write(text.encode() + b'\r\n')

ser = serial.Serial('COM1', timeout=1)
ser.write(b'*IDN?\r\n')
response = ser.readline()
print(response)
'''
swrite('*RST')                     # Return 6485/6487 to RST defaults.
swrite('TRIG:DEL 0')          # Set trigger delay to zero seconds.
swrite('TRIG:COUN 1')           # Set trigger count to 1.
swrite('NPLC 25')                 # Set integration rate to 25 PLC.
swrite('RANG .002')               # Use 2mA range.
swrite('SYST:ZCH OFF')             # Turn zero check off.
swrite('SYST:AZER:STAT OFF')       # Turn auto-zero off.
#swrite('DISP:ENAB OFF')            # Turn display off.
swrite('*CLS')                     # Clear status model.
swrite('TRAC:POIN 3')           # Set buffer size to 2.
swrite('TRAC:CLE')                 # Clear buffer.
swrite('TRAC:FEED:CONT NEXT')      # Set storage control to start on next
# reading.
swrite('STAT:MEAS:ENAB 512')       # Enable buffer full measurement event.
swrite('*SRE 1')                   # Enable SRQ on buffer full measurement 
# event.
swrite('*OPC?')
response = ser.readline()
print(response)                    # Operation complete query
# (synchronize completion of commands).
swrite('TRAC:CLE')                 
swrite('INIT')                     # Start taking and storing readings.
# Wait for GPIB SRQ line to go true.

swrite('TRAC:DATA?')
response = ser.readline()
print(response)


swrite('TRAC:FEED:CONT NEXT')
swrite('MEAS')                     # Start taking and storing readings.
# Wait for GPIB SRQ line to go true.

swrite('TRAC:DATA?')
response = ser.readline()
print(response)


swrite('TRAC:FEED:CONT NEXT')
swrite('INIT')                     # Start taking and storing readings.
# Wait for GPIB SRQ line to go true.
swrite('TRAC:DATA?')
response = ser.readline()
print(response)
'''
swrite('*RST') 
swrite('SYST:ZCH ON')
swrite('RANG .002')
swrite('NPLC 5')
swrite('INIT')
swrite('SYST:ZCOR:ACQ')
swrite('SYST:ZCOR ON')
swrite('RANG:AUTO ON')
swrite('SYST:ZCH OFF')
swrite('READ?')
response = ser.read(43)
print(response)
swrite('READ?')
response = ser.read(43)
print(response)
swrite('READ?')
response = ser.read(43)
print(response)
swrite('READ?')
response = ser.read(43)
print(response)
swrite('READ?')
response = ser.read(43)
print(response)
swrite('READ?')
response = ser.read(43)
print(response)
response = ser.read(43)
print(response)
ser.close()