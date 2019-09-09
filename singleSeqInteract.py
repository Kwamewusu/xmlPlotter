#!/usr/bin/env python
#######################################################################
# This script was written by Nana Owusu, it is meant to visualize     #
# waveform information from XML files produced by the GE scanner's    #
# plotter tool.                                                       #
#######################################################################
# Modules for text interpretation and math
import os, sys, re, fnmatch
import numpy as np
# Modules for plotting and reading xmls
import matplotlib

matplotlib.use("TkAgg")
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from matplotlib.figure import Figure
from matplotlib import style
from matplotlib.widgets import Slider
import xml.etree.ElementTree as ET
# %matplotlib inline
# Module for GUI
import tkinter as tk
from tkinter import filedialog
from tkinter import ttk
# Modules for interactive plotting in GUI
import matplotlib.backends.backend_tkagg
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigCanvas
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavTb2

# ## Load XML files

LARGE_FONT = ("Verdana", 12)
style.use("ggplot")


# Function for picking XML file order
def xmlItemize(convention, text):
    # Regular expressions for naming convention of shots
    # recorded by the scanner
    if convention == 0:
        pattern = '\w+\.xml\.(\d+)'
        # Identify the time point of each shot/time-point recorded
        token = re.search(pattern, text)
    elif convention == 1:
        pattern = '\w+\.xml'
        # Identify the time point of each shot/time-point recorded
        token = re.search(pattern, text)
    elif convention == 2:
        noExt = 1

    if token:
        return int(token.group(1))
    elif noExt:
        return text
    else:
        raise UserWarning('The naming convention must match the regular expression {0}'.format(pattern))


def xmlSort(order, fileList):
    idxNList = zip(order, fileList)
    sortedList = [x for x in idxNList]
    sortedList.sort(key=lambda sortedList: sortedList[0])
    return list(sortedList)


# ## Load files

# load an XML for info on first plotter time-point
def xmlRoot(xmlSets, numOfShots):
    """Takes:
            list of XML global addresses (xmlSets),
            file count representing the shots
            acquired (numOfShots).
        Returns:
            sequencer information for each shot (root)."""

    # Sequencer information can be learnt from the 
    # code below.
    # for child in root:
    #    print(child.tag, child.attrib)
    # "root" here is from having the ElementTree instance
    # call the getroot() function.

    # Placeholders for XML section headers (tree) and
    # the Sequencer section header (root) info
    tree = []
    root = [[] for x in range(numOfShots)]

    # Fill placeholder with ElementTree objects
    # which represent section headers
    for x, y in enumerate(xmlSets):
        tree.append(ET.parse(y))

    # Fill placeholder with data for each Sequencer 
    for i, j in enumerate(tree):
        root[i] = j.getroot()

    del tree
    return root


def extractWvfm(waveObjs, seq, numOfShots):
    """Takes:
            list of sequencer ElementTree objects for
            each time point (waveObjs),
            Sequencer name (seq),
            and XML file count (numOfShots).
        Returns:
            Numpy array with abscissa and range of a
            particular Sequencer for all time points."""

    # Placeholder of the data points for each Sequencer.
    oneDimStore = [[] for x in range(numOfShots)]
    twoDimStore = []

    # Use splitlines utility to interperate whitespace
    # notation in waveform values for a particular Sequencer.
    # Fill nested list with time/amplitude data for each time point.
    t = 0
    while t != numOfShots:
        for x in waveObjs[t][seq][0].itertext():
            oneDimStore[t].append(x.splitlines())
        t += 1

    # Placeholder for time and amplitude of the Sequencer at
    # each time point.

    shotLen = 0
    t = 0
    while t != numOfShots:
        # Find the max length of the lists
        for i in iter(oneDimStore[t][0]):
            twoDimStore.append(i.split(' '))

        nextShotLen = len(twoDimStore)

        if nextShotLen > shotLen:
            shotLen = nextShotLen

        twoDimStore.clear()
        t += 1

    waveToPlot = np.zeros((numOfShots, 2, shotLen - 1))

    # Use split utility to place time (abscissa) and amplitude
    # (range) values into separate rows for each time point.
    t = 0
    while t != numOfShots:
        for x, y in enumerate(oneDimStore[t][0]):
            twoDimStore.append(y.split(' '))
        for x in range(1, len(twoDimStore)):
            waveToPlot[t][0][x - 1] = float(twoDimStore[x][0])
            waveToPlot[t][1][x - 1] = float(twoDimStore[x][1])
        twoDimStore.clear()
        t += 1

    del oneDimStore, twoDimStore
    return waveToPlot


# ## Plot extracted sequencer waveform

# ### Procedures for comparing waveforms

## find from the end of an array the contiguous time-point that is < 799.0
def sspStopTime(waveObjs, numOfShots):
    """Takes:
            list of sequencer ElementTree objects for
            each time point (waveObjs),
            XML file count (numOfShots)
        Returns:
            list of first time points
            > 799.0 for each shot (lTime)"""

    # Waveform of the SSP board
    sspWv = extractWvfm(waveObjs, 0, numOfShots)

    # Storage for true final time points
    lTime = []

    for t in range(0, numOfShots):

        # copy SSP waveform for each shot
        iterTime = sspWv[t][0][:].copy()

        # last time point for the sequencer
        # this value can be 799.0
        lTimeStamp = sspWv[t][0][-1]

        # take the 2nd through 5th to last time point
        # and iterate over them for comparison
        for i, j in enumerate(iterTime.flat[-2:-6:-1]):
            if (j < lTimeStamp) & ((lTimeStamp % j) > 1.0):
                lTime.append(j)
            else:
                continue

            lTimeStamp = j

    return lTime


def scaleTime(wave, sspEndTimes, numOfShots):
    """Takes:
            waveform of a sequencer (wave),
            vector of end times < 799.0 from the SSP
            board (sspEndTimes),
            XML file count (numOfShots)
        Returns:
            waveform of a sequencer with end time points
            matching that of the SSP board (modifiedWave),
            count of the number of indices greater than 799.0"""

    # Length of input waveform
    waveLen = len(wave[0][0][:])

    # Placeholder for index of time values >= 799.0
    idx2Cut = int()

    # Count and store the number of time values
    # >= 799.0. This code assumes the count is
    # consistent across time.
    for t in range(0, numOfShots):

        # copy waveform for each shot
        iterTime = wave[t][0][:].copy()

        # last time point for the sequencer
        # this value can be 799.0
        lTimeStamp = wave[t][0][-1]
        count = 0

        # take the 2nd through 5th to last time point
        # and iterate over them for comparison
        for i, j in enumerate(iterTime.flat[-2:-6:-1]):

            if (j < lTimeStamp) & ((lTimeStamp % j) > 1.0):

                # replace the first time point most different 
                # from the subsequent one with another.
                wave[t][0][waveLen - 1 - i] = sspEndTimes[t]
                break
            else:

                # add to count if the present time point is 
                # not much different from the one before
                count += 1
                continue

            lTimeStamp = j

        idx2Cut = count

    modifiedWave = wave.copy()
    del waveLen, lTimeStamp, iterTime

    return modifiedWave, idx2Cut


def waveTruncate(wave, cols2Cut, numOfShots):
    """Takes:
            waveform of a sequencer (wave),
            number of time values >= 799.0 (cols2Cut),
            XML file count (numOfShots)
        Returns:
            truncated waveform of a sequencer (truncatedWv)"""

    # length of input waveform
    waveLen = len(wave[0][0][:])

    # Placeholder with compensation for
    # decreased sizes of the input waveform
    truncatedWv = np.zeros((numOfShots, 2, waveLen - cols2Cut))

    for t in range(0, numOfShots):
        iterTime = wave[t][0][:].copy()
        lTimeStamp = wave[t][0][-1]
        truncatedWv[t] = np.delete(wave[t], range(waveLen - cols2Cut, waveLen), axis=1)

    return truncatedWv


# ### Show waveforms on the same time scale

def waveToPlot(wave, t):
    x = wave[t, 0, :]
    y = wave[t, 1, :]

    return x, y


# ### Interactive plots

'''https://stackoverflow.com/questions/46325447/animated-interactive-plot-using-matplotlib'''


class Checkbar(tk.Frame):
    def __init__(self, parent=None, picks=[]):
        tk.Frame.__init__(self, parent)
        self.vars = []

        for i, pick in enumerate(picks):
            var = tk.IntVar()
            chk = tk.Checkbutton(self, text=pick, variable=var,
                                 command=lambda: self.toggle(var))
            chk.pack(side="left", anchor="w", expand=True)
            self.vars.append(var)

    def toggle(self, board):
        board.set(not board.get())

    def state(self):
        somevar = tk.IntVar()
        return map((lambda somevar: somevar.get()), self.vars)


class GetFileInfo:

    def __init__(self):
        self.fileLoc = str()

    def file(self):
        initWin = tk.Tk()
        # starting from user's home folder, pick directory in which XMLs exist
        self.fileLoc = filedialog.askdirectory(parent=initWin, initialdir=os.getcwd(),
                                               title="Please select the XML directory")

        initWin.withdraw()

    def file(self):
        return self.fileLoc


class GetXMLPath:

    def __init__(self):

        self.xmlList = []

        # Create placeholder and fill list for xmls
        self.tempList = []
        self.xmlFiles = []

        self.wont = int()
        self.stopCond = int()

        self.filesInDir = []
        self.xmlFullPath = []

    def getXmlList(self, file):

        self.xmlList.append(file)

        # provide the absolute path of the current directory
        imLoc = self.xmlList[0] + '/'
        # list all files in the XML directory
        dirList = os.listdir(imLoc)

        #         print(self.xmlList)
        # print(self.dirList)
        # store only XML files
        if len(fnmatch.filter(dirList, '*.xml*')) > 1:
            self.filesInDir.append(fnmatch.filter(dirList, '*.xml.*[^0-9]'))
            self.wont = 0
        elif len(fnmatch.filter(dirList, '*.xml*')) == 1:
            self.filesInDir.append(fnmatch.filter(dirList, '*.xml*'))
            self.wont = 1
        elif len(fnmatch.filter(dirList, '*')) > 0:
            self.wont = 2
            files = fnmatch.filter(dirList, '*')
            for x in files:
                if ET.parse(x):
                    self.filesInDir.append(x)
                else:
                    continue
        else:
            raise UserWarning('Found no XML files or the directory was empty.\n')

    def xmlPaths(self):
        for j, k in enumerate(self.filesInDir):
            self.tempList.append(xmlItemize(self.wont, k))
            self.xmlFiles.append(k)

        sortedFiles = xmlSort(self.tempList, self.xmlFiles)

        # Fill array with XML abs. paths
        stopCond = len(sortedFiles)

        for i, j in sortedFiles:
            # Array for the sorted abs. path for each XML file
            self.xmlFullPath.append(self.xmlList[0] + '/' + j)

        # Garbage collection of unused variables
        del self.tempList, self.xmlFiles, sortedFiles


def set_filename(initial_win):
    # The method to transfer file-names across classes was found in the link below
    # https://stackoverflow.com/questions/50074610/passing-data-between-multiple-tkinter-frame-objects

    # starting from user's home folder, pick directory in which XMLs exist
    fileLoc = filedialog.askdirectory(parent=initial_win, initialdir=os.getcwd(),
                                      title="Please select the XML directory")

    return fileLoc
    # self.fileInfo.set(self.fileLoc)


class StartPage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.controller = controller
        self.window = parent

        # self.askDirObj = GetFileInfo()
        self.fileInfo = tk.StringVar(self.window)
        self.fileInfo.set(os.getcwd())
        self.fileLoc = str()

        label = tk.Label(self, text="Start Page", font=LARGE_FONT)
        label.pack(padx=10, pady=10)

        button1 = ttk.Button(self, text="Select directory",
                             command=lambda: self.get_file())

        button2 = ttk.Button(self, text="View Sequencers",
                             command=lambda: controller.show_frame(PlotterWithZoom))
        # button2.bind('<Button-1>', self.refresh)

        button1.pack()
        button2.pack()

        self.seqrList = ['SSP', 'XGRAD', 'YGRAD', 'ZGRAD', 'RHO1', 'RHO2', 'THETA1', 'THETA2']
        self.boardStates = []

        self.boardChoice = Checkbar(self, picks=self.seqrList)
        self.boardChoice.pack(side="bottom", fill="x")
        self.boardChoice.config(relief="groove", bd=2)

        button3 = ttk.Button(self, text="Enter Board Choices",
                             command=lambda: self.allstates())
        button3.pack(side="bottom")

    def allstates(self):
        self.boardStates.clear()
        self.boardStates.append(list(self.boardChoice.state()))

    def get_file(self):
        self.fileInfo.set(set_filename(self.window))


# # class PageOne(tk.Frame):

# #     def __init__(self, parent, controller):
# #         tk.Frame.__init__(self, parent)
# #         label = tk.Label(self, text="Plotter", font=LARGE_FONT)
# #         label.pack(padx=10, pady=10)

# #         menubar = tk.Menu(self)
# #         filemenu = tk.Menu(menubar, tearoff=0)
# #         filemenu.add_command(label="New")
# #         filemenu.add_command(label="Open")                    
# #         menubar.add_cascade(label="Settings", menu=filemenu)
# #         controller.config(menu=menubar)

# #         button1 = ttk.Button(self, text="Back to Home", 
# #                             command=lambda: controller.show_frame(StartPage))

# #         button1.pack()


""" This snippet of code was copied from 
https://stackoverflow.com/questions/3877774/updating-a-graphs-coordinates-in-matplotlib
 
Additional help for this section should be taken from this YouTube channel
https://www.youtube.com/watch?v=Zw6M-BnAPP0
"""


# def animate(i):
#     pass

class PlotterWithZoom(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        self.controller = controller

        start_page = self.controller.get_page(StartPage)

        label = tk.Label(self, text="Interactive Plot", font=LARGE_FONT)
        label.pack(padx=10, pady=10)

        # print(start_page.fileInfo.get())

        xmls = GetXMLPath()
        button1 = ttk.Button(self, text="Show Plot",
                             command=lambda: xmls.getXmlList(start_page.fileInfo.get()))
        button1.bind('<Button-1>', xmls.xmlPaths())
        button1.pack()

        button2 = ttk.Button(self, text="Start Page",
                             command=lambda: controller.show_frame(StartPage))
        button2.pack(side="bottom")

        # load an XML for info on first plotter time-point
        wvm = xmlRoot(xmls.xmlFullPath, xmls.stopCond)

        seqPlots = Figure()

        canvas = FigCanvas(seqPlots, self)

        toolbar = NavTb2(canvas, self)
        toolbar.update()
        toolbar.pack()

        canvas.draw()
        canvas.get_tk_widget().pack(side='top', fill='both')
        canvas._tkcanvas.pack(side='top', fill='both', expand=1)


class MainApplication(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        tk.Tk.wm_title(self, "singleSeqInteract")

        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand=True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}
        # self.pages = (StartPage, PlotterWithZoom)

        for F in (StartPage, PlotterWithZoom):
            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)
        self.centerWindow()

    def get_page(self, frame_name):
        return self.frames[frame_name]

    def show_frame(self, frameToAdd):
        frame = self.frames[frameToAdd]
        frame.tkraise()

    def centerWindow(self):
        w = 800
        h = 1150
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) / 2
        y = (sh - h) / 2
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))


# class RetrieveShots(GetXmlPath):

#         self.seqr = {0: 'SSP', 1: 'XGRAD', 2: 'YGRAD', 3: 'ZGRAD',\
#                 4: 'RHO1', 5: 'RHO2', 6: 'THETA1', 7: 'THETA2'}


#         print(list(boardChoice.state()))

#         seqs2Show = [0,1,2,3,4]
#         l = len(seqs2Show)
#         lastSspTimes = sspStopTime(wvm, info[1])

#         tLimit = plt.axes([0.25, .03, 0.50, 0.02])
#         shot = Slider(tLimit,'shot #', 0, info[1], valinit=0)
#         shot = 0

#         for i,p in enumerate(seqs2Show):
#             npStore = extractWvfm(wvm, p, info[1])

#             wv, toCut = scaleTime(npStore,lastSspTimes,info[1])

#             xtr = waveTruncate(wv,toCut,info[1])

#             xVal, yVal = waveToPlot(xtr,shot)

#             subPlt = seqPlots.add_subplot(l,1,i+1)            
#             subPlt.plot(xVal,yVal,'b-')
#             subPlt.set_xlabel('Time (us)')
#             subPlt.set_ylabel('Amplitude (a.u.)')
#             subPlt.autoscale(enable=True,axis='x')
#             subPlt.set_title('Sequence {0} Board'.format(seqr[p]))

#             seqPlots.subplots_adjust(hspace=1.5)
#             plt.rc('font', size=8)
#             plt.rc('axes', titlesize=8)
#             canvas.draw()


#         plt.rcParams.update({'font.size':8})


# ### Pick the location of the XML

# In[58]:


# if len(sys.argv) != 5:
#    sys.exit('Usage: python t1rProcessing.py <spinLockImLocation> minTSL maxTSL numTSL')

# print 'Script Name: ', sys.argv[0]
# print 'Input File: ', sys.argv[1]
# print 'Minimum TSL: ', sys.argv[2]
# print 'Maximum TSL: ', sys.argv[3]
# print 'TSL Quantity: ', sys.argv[4]

# min_TSL = sys.argv[2]
# max_TSL = sys.argv[3]
# tslPlayed = sys.argv[4]

# Call GUI window for selection of XML directories
# for storage of their full paths
app = MainApplication()
# ani = animation.FuncAnimation(seqPlots,playSequencer, interval=stopCond)
app.mainloop()
