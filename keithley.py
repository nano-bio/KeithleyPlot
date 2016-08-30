#!/usr/bin/python
import serial
import re

class Keithley():
    def __init__(self, port = 'COM1'):
        self.port = port
        self.ser = serial.Serial(self.port, timeout=1)
        
        # check whether we are actually connecting to a 6485
        self.ser.write(b'*IDN?\r\n')
        response = self.ser.readline()
        if u'KEITHLEY INSTRUMENTS INC.,MODEL 6485' not in response.decode():
            raise RuntimeError(u'This does not seem to be a Keithley 6485!')
        
        # compile the regex to parse read out values
        self.valuepattern = re.compile('^([+|-][0-9]{1}\.[0-9]{2,6}E-[0-9]{2}A).*$')
        
        # save connected state
        self.connected = True

    def read_value(self):
        if self.connected:
            self.serialwrite('READ?')
            # read 43 bytes and decode to unicode
            response = self.ser.read(43).decode()
            match = self.valuepattern.match(response)
            
            # check whether we match the expected output
            value = u''
            if match:
                value = match.group(1)

            value = value.replace('E', 'e').replace('A', '')

            return value

    def serialwrite(self, text):
        if self.connected:
            self.ser.write(text.encode() + b'\r\n')

    def zerocorrect(self):
        if self.connected:
            self.serialwrite('*RST') 
            self.serialwrite('SYST:ZCH ON')
            self.serialwrite('RANG .002')
            self.serialwrite('NPLC 5')
            self.serialwrite('INIT')
            self.serialwrite('SYST:ZCOR:ACQ')
            self.serialwrite('SYST:ZCOR ON')
            self.serialwrite('RANG:AUTO ON')
            self.serialwrite('SYST:ZCH OFF')
            self.read_value()
        
    def close(self):
        if self.connected:
            self.ser.close()