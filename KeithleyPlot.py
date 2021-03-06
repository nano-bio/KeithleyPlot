#!/usr/bin/python
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox, filedialog

import sys
import glob
import datetime

try:
    import serial
except ImportError:
    print('Please install pyserial!')
    sys.exit()

import threading

try:
    import numpy as np
except ImportError:
    print('Please install numpy!')
    sys.exit()

try:
    import matplotlib
except ImportError:
    print('Please install matplotlib!')
    sys.exit()

matplotlib.use("TKAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from keithley import Keithley


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
        self.time = np.zeros((100000, 1))
        self.time[:] = np.nan
        self.values = np.zeros((100000, 1))
        self.values[:] = np.nan

        # empty object for the keithley
        self.keithley = None

        # variable for the connected port
        self.comport = tk.StringVar(master)
        self.portlist = serial_ports()

        # check for COM ports
        if len(self.portlist) == 0:
            sys.exit('No COM ports found!')

        self.frequency = tk.StringVar(master)
        self.frequencies = ['0.1 Hz', '0.5 Hz', '1 Hz', '2 Hz', '3 Hz', ]

        # default value for starttime
        self.starttime = None

        self.create_widgets()

    def create_widgets(self):
        # configure the grid - the first line and row should expand
        self.grid_rowconfigure(0, weight=1)

        # create a drop down menu for the comport
        self.comportselector = ttk.OptionMenu(self.master, self.comport, self.portlist[0], *self.portlist)
        self.comportselector.grid(row=2, column=0, sticky='W')

        # create a drop down menu for the update frequency
        self.frequencyselector = ttk.OptionMenu(self.master, self.frequency, self.frequencies[2], *self.frequencies)
        self.frequencyselector.grid(row=2, column=1, sticky='W')

        # clear button
        self.clearb = ttk.Button(self.master, text="Clear", command=self.clearplot)
        self.clearb.grid(row=2, column=2, sticky='W')

        # connect button
        self.connectb = ttk.Button(self.master, text="Connect", command=self.connectkeithley)
        self.connectb.grid(row=2, column=3, sticky='W')

        # zero correct button
        self.zerocorrectb = ttk.Button(self.master, text="Zero Correct", command=self.zerocorrect)
        self.zerocorrectb.grid(row=2, column=4, sticky='W')
        self.zerocorrectb.config(state='disabled')

        # start and stop button
        self.startb = ttk.Button(self.master, text="Start", command=self.start)
        self.startb.grid(row=2, column=5, sticky='W')

        self.stopb = ttk.Button(self.master, text="Stop", command=self.stop)
        self.stopb.grid(row=2, column=6, sticky='W')

        self.startb.config(state='disabled')
        self.stopb.config(state='disabled')

        # button to save the data
        self.saveb = ttk.Button(self.master, text='Save data', command=self.savedata)
        self.saveb.grid(row=2, column=7, sticky='W')

        # label for the current value
        self.valuelabel = ttk.Label(self.master, text='0A', font='bold')
        self.valuelabel.grid(row=1, column=7, sticky='W')

        # make a figure and axes in the figure
        self.f = Figure(figsize=(10, 5), dpi=100)
        self.f.set_facecolor('#f0f0ed')
        self.f.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        self.a = self.f.add_subplot(111)

        # already plot a "line" because we only want to update (not replot every time)
        self.line, = self.a.plot(self.time, self.values, 'r-')

        self.canvas = FigureCanvasTkAgg(self.f, self.master)
        self.canvas.get_tk_widget().grid(row=0, columnspan=8)
        self.canvas.draw()

        # add a toolbar
        self.toolbar_frame = ttk.Frame(self.master)
        toolbar = NavigationToolbar2Tk(self.canvas, self.toolbar_frame)
        toolbar.update()
        self.toolbar_frame.grid(row=1, columnspan=7, sticky='W')

    def clearplot(self):
        # clear the axes of everything
        self.a.clear()
        self.canvas.draw()

        # overwrite variables 
        self.i = 0
        self.time = np.zeros((100000, 1))
        self.time[:] = np.nan
        self.values = np.zeros((100000, 1))
        self.values[:] = np.nan

        # plot the line again, so we have something to update
        self.line, = self.a.plot(self.time, self.values, 'r-')

    def zerocorrect(self):
        self.keithley.zerocorrect()

    def connectkeithley(self):
        # get the selected com port
        comoption = self.comport.get()
        # connect
        try:
            self.keithley = Keithley(comoption)
        except RuntimeError as e:
            messagebox.showerror("COM Port error", e)
            return

        # adjust the GUI elements
        self.startb.config(state='normal')
        self.stopb.config(state='normal')
        self.zerocorrectb.config(state='normal')
        self.connectb.config(state='disabled')
        self.comportselector.config(state='disabled')

    def printvalue(self):
        # only do this if we are running
        if self.running is True:
            # immediately schedule the next run of this function
            frequency = float(self.frequency.get().replace(' Hz', ''))
            delay = 1 / frequency
            threading.Timer(delay, self.printvalue).start()

            # write the current time and value in the corresponding arrays
            # self.time = np.append(self.time, self.i)
            if self.i == 0:
                self.time[self.i, 0] = 0
            else:
                self.time[self.i, 0] = self.time[self.i - 1, 0] + delay

            # self.values = np.append(self.values, self.keithley.read_value())
            value = self.keithley.read_value()
            #print(value)
            self.valuelabel['text'] = value + 'A'
            self.values[self.i, 0] = float(value)

            # plot - note that we don't use plt.plot, because it is horribly slow
            self.line.set_ydata(self.values[~np.isnan(self.values)])
            self.line.set_xdata(self.time[~np.isnan(self.values)]) 
            
            # rescale axes every hundredth run
            if self.i % 10 == 1:
                self.a.relim()
                self.a.autoscale_view(scalex=False)
                self.a.set_xlim(0, self.time[self.i, 0] + self.time[self.i, 0] / 10 + 10 * delay)

            # draw the new line
            self.canvas.draw_idle()
            self.i = self.i + 1

    def start(self):
        # clear the plot before we start a new measurement
        self.running = True
        self.clearplot()
        self.printvalue()
        self.startb.config(state='disabled')
        self.stopb.config(state='normal')
        self.starttime = datetime.datetime.now()

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

    def savedata(self):
        # no measurement has been recorded yet
        if self.starttime is None:
            return

        f = filedialog.asksaveasfilename(defaultextension=".txt", initialfile='PicoAmpValues_' + self.starttime.strftime('%Y-%m-%d_%H-%M'))
        print(f)
        if f is None:  # asksaveasfile return `None` if dialog closed with "cancel".
            return
        comments = u'Starttime: ' + self.starttime.strftime('%Y/%m/%d - %H:%M')
        ydata = self.values[~np.isnan(self.values)]
        xdata = self.time[~np.isnan(self.values)]

        np.savetxt(f, np.dstack((xdata, ydata))[0], fmt=['%1.0d', '%1.14e'], delimiter='\t', header=comments)


root = tk.Tk()
root.geometry("980x640")
app = KeithleyPlot(master=root)
root.protocol("WM_DELETE_WINDOW", app.on_closing)
root.wm_title("Keithley Plot")
app.mainloop()

