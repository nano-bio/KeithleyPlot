#!/usr/bin/python
from keithley import Keithley

import tkinter as tk
import tkinter.ttk as ttk

import sys
import glob
import serial

import threading

import numpy as np

import matplotlib
matplotlib.use("GTKAgg")
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
        # we use the grid type of aligning things
        self.grid()
        
        # initialize a numpy array for the values
        self.i = 0
        self.time = np.zeros((100000,1))
        self.time[:] = np.nan
        self.values = np.zeros((100000,1))
        self.values[:] = np.nan
        
        # empty object for the keithley
        self.keithley = None
        
        # variable for the connected port
        self.comport = tk.StringVar(master)
        self.portlist = serial_ports()
        self.frequency = tk.StringVar(master)
        self.frequencies = ['0.1 Hz', '0.5 Hz', '1 Hz', '2 Hz', '3 Hz',]
        
        self.create_widgets()

    def create_widgets(self):
        #configure the grid - the first line and row should expand
        self.grid_rowconfigure(0,weight=1)
        
        # create a drop down menu for the comport
        self.comportselector = ttk.OptionMenu(self.master, self.comport, self.portlist)
        self.comportselector.grid(row = 2, column = 0, sticky='W')
        
        # create a drop down menu for the update frequency
        self.frequencyselector = ttk.OptionMenu(self.master, self.frequency, self.frequencies[2], *self.frequencies)
        self.frequencyselector.grid(row = 2, column = 1, sticky='W')
        
        # clear button
        self.clearb = ttk.Button(self.master, text="Clear", command=self.clearplot)
        self.clearb.grid(row = 2, column = 2, sticky='W')
        
        # connect button
        self.connectb = ttk.Button(self.master, text="Connect", command=self.connectkeithley)
        self.connectb.grid(row = 2, column = 3, sticky='W')

        # zero correct button
        self.zerocorrectb = ttk.Button(self.master, text="Zero Correct", command=self.zerocorrect)
        self.zerocorrectb.grid(row = 2, column = 4, sticky='W')
        self.zerocorrectb.config(state='disabled')
        
        # start and stop button
        self.startb = ttk.Button(self.master, text="Start", command=self.start)
        self.startb.grid(row = 2, column = 5, sticky='W')
        
        self.stopb = ttk.Button(self.master, text="Stop", command=self.stop)
        self.stopb.grid(row = 2, column = 6, sticky='W')
        
        self.startb.config(state='disabled')
        self.stopb.config(state='disabled')
        
        # label for the current value
        self.valuelabel = ttk.Label(self.master, text='0A', font = 'bold')
        self.valuelabel.grid(row=1, column = 6, sticky='W')
        
        # make a figure and axes in the figure
        self.f = Figure(figsize=(10,5), dpi=100)
        self.f.set_facecolor('#f0f0ed')
        self.f.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        self.a = self.f.add_subplot(111)
        
        # already plot a "line" because we only want to update (not replot every time)
        self.line, = self.a.plot(self.time,self.values,'r-')

        self.canvas = FigureCanvasTkAgg(self.f, self.master)
        self.canvas.get_tk_widget().grid(row = 0, columnspan=7)
        self.canvas.show()

        # add a toolbar
        self.toolbar_frame = ttk.Frame(self.master)
        toolbar = NavigationToolbar2TkAgg(self.canvas, self.toolbar_frame)
        toolbar.update()
        self.toolbar_frame.grid(row=1, columnspan = 6, sticky='W')
        
    def clearplot(self):
        # clear the axes of everything
        self.a.cla()
        self.canvas.draw()
        
        # overwrite variables 
        self.i = 0
        self.time = np.zeros((100000,1))
        self.time[:] = np.nan
        self.values = np.zeros((100000,1))
        self.values[:] = np.nan
        
        # plot the line again, so we have something to update
        self.line, = self.a.plot(self.time,self.values,'r-')

    def zerocorrect(self):
        self.keithley.zerocorrect()
        
    def connectkeithley(self):
        comoption = self.comport.get().replace('(','').replace(')','').replace('\'','').replace(',','')
        self.keithley = Keithley(comoption)
        self.startb.config(state='normal')
        self.stopb.config(state='normal')
        self.zerocorrectb.config(state='normal')
        self.connectb.config(state='disabled')
        
    def printvalue(self):
        # only do this if we are running
        if self.running is True:
            # immediately schedule the next run of this function
            frequency = float(self.frequency.get().replace(' Hz', ''))
            delay = 1 / frequency
            threading.Timer(delay, self.printvalue).start ()
            
            # write the current time and value in the corresponding arrays
            #self.time = np.append(self.time, self.i)
            if self.i == 0:
                self.time[self.i, 0] = 0
            else:
                self.time[self.i,0] = self.time[self.i - 1, 0] + delay
                
            #self.values = np.append(self.values, self.keithley.read_value())
            value = self.keithley.read_value()
            self.valuelabel['text'] = value + 'A'
            self.values[self.i,0] = value

            # plot - note that we don't use plt.plot, because it is horribly slow
            self.line.set_ydata(self.values[~np.isnan(self.values)])
            self.line.set_xdata(self.time[~np.isnan(self.time)])
            
            self.i = self.i + 1

            # rescale axes every tenth run
            if self.i %10 == 1:
                self.a.relim()
                self.a.autoscale_view(scalex=False)
                self.a.set_xlim(0, self.i + 20)
            
            # draw the new line
            self.canvas.draw()

    def start(self):
        # clear the plot before we start a new measurement
        self.running = True
        self.clearplot()
        self.printvalue()
        self.startb.config(state='disabled')
        self.stopb.config(state='normal')
        
    def stop(self):
        self.running = False
        self.stopb.config(state='disabled')
        self.startb.config(state='normal')
        
    def on_closing(self):
        # we should disconnect before we close the program
        self.stop()
        if self.keithley is not None:
            self.keithley.close()
        self.master.destroy()
        
root = tk.Tk()
root.minsize(300,300)
root.geometry("980x560")
app = KeithleyPlot(master=root)
root.protocol("WM_DELETE_WINDOW", app.on_closing)
root.wm_title("Keithley Plot")
app.mainloop()
