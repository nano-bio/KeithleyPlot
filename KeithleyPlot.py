#!/usr/bin/python
from keithley import Keithley

import tkinter as tk
import tkinter.ttk as ttk

import sys
import glob
import serial

import threading

import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2TkAgg
from matplotlib.figure import Figure

def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

class KeithleyPlot(tk.Frame):
    def __init__(self, master=None):
        super().__init__(master)
        self.grid()
        
        self.comport = tk.StringVar(master)
        self.portlist = serial_ports()
        
        self.create_widgets()
        self.i = 0

    def create_widgets(self):
        self.comportselector = ttk.OptionMenu(self.master, self.comport, self.portlist)
        self.comportselector.grid(row = 2, column = 0, sticky='W')
        
        self.connectb = ttk.Button(self.master, text="Connect", command=self.connectkeithley)
        self.connectb.grid(row = 2, column = 2, sticky='W')
        
        self.clearb = ttk.Button(self.master, text="Clear", command=self.clearplot)
        self.clearb.grid(row = 2, column = 1, sticky='W')
        
        self.zerocorrectb = ttk.Button(self.master, text="Zero Correct", command=self.zerocorrect)
        self.zerocorrectb.grid(row = 2, column = 3, sticky='W')
        
        self.startb = ttk.Button(self.master, text="Start", command=self.start)
        self.startb.grid(row = 2, column = 4, sticky='W')
        
        self.stopb = ttk.Button(self.master, text="Stop", command=self.stop)
        self.stopb.grid(row = 2, column = 5, sticky='W')
        
        self.f = Figure(figsize=(5,5), dpi=100)
        self.a = self.f.add_subplot(111)
        self.a.plot([1,2,3,4,5,6,7,8],[5,6,1,3,8,9,3,5])

        self.canvas = FigureCanvasTkAgg(self.f, self)
        self.canvas.show()
        self.canvas.get_tk_widget().grid(row = 0, columnspan=2, sticky='NSWE')

        self.toolbar_frame = ttk.Frame(self.master)
        toolbar = NavigationToolbar2TkAgg(self.canvas, self.toolbar_frame)
        toolbar.update()
        self.toolbar_frame.grid(row=1, columnspan = 2, sticky='WE')
        self.grid_rowconfigure(0,weight=1)
        self.grid_columnconfigure(0,weight=1)
        
    def clearplot(self):
        self.a.cla()
        self.canvas.draw()
        
    def zerocorrect(self):
        self.keithley.zerocorrect()
        
    def connectkeithley(self):
        self.keithley = Keithley('COM1')
        
    def printvalue(self):
        if self.running is True:
            threading.Timer(0.5, self.printvalue).start ()
            #print(self.keithley.read_value())
            self.a.plot(self.i, self.keithley.read_value(), 'r.')
            self.i = self.i + 1
            self.canvas.draw()

    def start(self):
        self.running = True
        self.printvalue()
        self.i = 0
        
    def stop(self):
        self.running = False
        
root = tk.Tk()
root.minsize(300,300)
root.geometry("800x570")
app = KeithleyPlot(master=root)
app.mainloop()
        
#ke = Keithley(port = 'COM1')
#ke.zerocorrect()
#print(ke.read_value())
#print(ke.read_value())