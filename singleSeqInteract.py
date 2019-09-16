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
# import matplotlib.animation as animation
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
def xmlItemize(convention,text):
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

def xmlSort(order,fileList):
    idxNList = zip(order, fileList)
    sortedList = [x for x in idxNList]
    sortedList.sort(key=lambda sortedList:sortedList[0])
    return list(sortedList)


# ## Load files
# load an XML for info on first plotter time-point
def xmlRoot(xmlSets, numOfShots):
    """ Takes:
            -list of XML global addresses (xmlSets)
            -file count representing the shots
            acquired (numOfShots).
        Returns: 
            -sequencer information for each shot (root)."""
    
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
    for x,y in enumerate(xmlSets):
        tree.append(ET.parse(y))
    
    # Fill placeholder with data for each Sequencer 
    for i,j in enumerate(tree):
        root[i] = j.getroot()
    
    del tree
    return root

def extractWvfm(waveObjs, seq, numOfShots):
     """Takes:
            -list of sequencer ElementTree objects for
            each time point (waveObjs).
            -Sequencer name (seq).
            - XML file count (numOfShots).
        Returns:
            -Numpy array with abscissa and range of a
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
        
    waveToPlot = np.zeros((numOfShots,2,shotLen-1))
    
    # Use split utility to place time (abscissa) and amplitude
    # (range) values into separate rows for each time point.
    t = 0
    while t != numOfShots:
        for x,y in enumerate(oneDimStore[t][0]):
            twoDimStore.append(y.split(' '))
        for x in range(1,len(twoDimStore)):
            waveToPlot[t][0][x-1] = float(twoDimStore[x][0])
            waveToPlot[t][1][x-1] = float(twoDimStore[x][1])
        twoDimStore.clear()
        t += 1
           
    del oneDimStore, twoDimStore
    return waveToPlot


# ## Plot extracted sequencer waveform

# ### Procedures for comparing waveforms

## find from the end of an array the contiguous time-point that is < 799.0
def sspStopTime(waveObjs,numOfShots):
     """Takes:
            -list of sequencer ElementTree objects for
            each time point (waveObjs)
            -XML file count (numOfShots)
        Returns:
            -list of first time points
            > 799.0 for each shot (lTime)"""
    
    # Waveform of the SSP board
    sspWv = extractWvfm(waveObjs, 0, numOfShots)
    
    # Storage for true final time points
    lTime = []
    
    for t in range(0,numOfShots):
        
        # copy SSP waveform for each shot
        iterTime = sspWv[t][0][:].copy()
        
        # last time point for the sequencer
        # this value can be 799.0
        lTimeStamp = sspWv[t][0][-1]
        
        # take the 2nd through 5th to last time point
        # and iterate over them for comparison
        for i,j in enumerate(iterTime.flat[-2:-6:-1]):
            if (j < lTimeStamp) & ((lTimeStamp % j) > 1.0):
                lTime.append(j)
            else:
                continue

            lTimeStamp = j
            
    return lTime

def scaleTime(wave,sspEndTimes,numOfShots):
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
    # consistant accross time.
    for t in range(0,numOfShots):
        
        # copy waveform for each shot
        iterTime = wave[t][0][:].copy()
        
        # last time point for the sequencer
        # this value can be 799.0
        lTimeStamp = wave[t][0][-1]
        count = 0
        
        # take the 2nd through 5th to last time point
        # and iterate over them for comparison
        for i,j in enumerate(iterTime.flat[-2:-6:-1]):
            
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

def waveTruncate(wave,cols2Cut,numOfShots):
     """Takes:
            -waveform of a sequencer (wave)
            -number of time values >= 799.0 (cols2Cut)
            -XML file count (numOfShots)
        Returns:
            -truncated waveform of a sequencer (truncatedWv)"""
    
    # length of input waveform
    waveLen = len(wave[0][0][:])
    
    # Placeholder with compensation for
    # decreased sizes of the input waveform
    truncatedWv = np.zeros((numOfShots,2,waveLen-cols2Cut))

    for t in range(0,numOfShots):
        iterTime = wave[t][0][:].copy()
        lTimeStamp = wave[t][0][-1]
        truncatedWv[t] = np.delete(wave[t],range(waveLen-cols2Cut,waveLen),axis=1)
            
    return truncatedWv


# ### Show waveforms on the same time scale
def waveToPlot(wave,t):
    x = wave[t,0,:]
    y = wave[t,1,:]
    
    return x, y


# ### Interactive plots


'''https://stackoverflow.com/questions/46325447/animated-interactive-plot-using-matplotlib'''

class Checkbar(tk.Frame):
    def __init__(self, parent=None, picks=[]):
        tk.Frame.__init__(self, parent)

	self.board_set = []

	self.boards = {0: 'SSP', 1: 'XGRAD', 2: 'YGRAD', 3: 'ZGRAD',\
        4: 'RHO1', 5: 'RHO2', 6: 'THETA1', 7: 'THETA2'}

        self.check_vars = []
	self.check_btn = []
        
        for i,pick in enumerate(picks):
            self.check_vars.append(tk.IntVar())
            self.check_btn.append(tk.Checkbutton(self, text=pick, variable=self.check_vars[i],
                                command=lambda: self.toggle(self.check_vars[i])))
            self.check_vars[i].pack(side="left", anchor="w", expand=True)
            
    
    def toggle(self, board):
	if board.get == 0:
            board.set(1)
	else:
            board.set(0)
        
    def state(self):
	state = []
	for board in self.check_vars:
           state.append(board.get())

	for i,board in enumerate(state):
            if board == 1:
                self.board_set.append(self.boards[i]) 
                continue

class GetXMLPath:
    
    def __init__(self):
        self.xmlList = []
        
        # Create placeholder and fill list for xmls
        self.tempList = []
        self.xmlFiles = []
        self.filesInDir = []
        
        self.wont = int()
        self.stopCond = int()
        self.xmlFullPath = list()
        
        self.wvm = list()
    
    def getXmlList(self, file):
        self.xmlList.append(file)
        
        # provide the absolute path of the current directory
        imLoc = self.xmlList[0] + '/'
        # list all files in the XML directory
        dirList = os.listdir(imLoc)
        
        # store only XML files
        if len(fnmatch.filter(dirList,'*.xml*')) > 1:
            self.filesInDir.append(fnmatch.filter(dirList,'*.xml.*[^0-9]'))
            self.wont = 0
        elif len(fnmatch.filter(dirList,'*.xml*')) == 1:
            self.filesInDir.append(fnmatch.filter(dirList,'*.xml*'))
            self.wont = 1
        elif len(fnmatch.filter(dirList,'*')) > 0:
            self.wont = 2
            files = fnmatch.filter(dirList,'*')
            for x in files:
                if (ET.parse(x)):
                    self.filesInDir.append(x)
                else:
                    continue
        else :
            raise UserWarning('Found no XML files or the directory was empty.\n')
            
        del dirList, imLoc
            
    def xmlPaths(self):
        convention = self.wont
        for j,k in enumerate(self.filesInDir):
            self.tempList.append(xmlItemize(self.wont,k))
            self.xmlFiles.append(k)

        sortedFiles = xmlSort(self.tempList, self.xmlFiles)

        # Fill array with XML abs. paths
        self.stopCond = len(sortedFiles)

        for i,j in sortedFiles:
        # Array for the sorted abs. path for each XML file
            self.xmlFullPath.append(xmlList[0] + '/' + j)
        
        # Garbage collection of unused variables
        del self.tempList, self.xmlFiles, sortedFiles
        
        self.wave_info(self.xmlFullPath, self.stopCond)
        
    def wave_info(self, xml_path, shot_count):
        self.wvm = get_xml_root(xml_path, shot_count)
        

def file_name(initial_win):
    # starting from user's home folder, pick directory in which XMLs exist
    fileLoc = filedialog.askdirectory(parent=initial_win, initialdir=os.getcwd(), 
                                            title="Please select the XML directory")

    return fileLoc

class StartPage(tk.Frame):
    
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)
        
        self.controller = controller
        self.window = parent
        
        self.fileLoc = tk.StringVar()
        self.fileLoc.set(os.getcwd())
        
        label = tk.Label(self, text="Start Page", font=LARGE_FONT)
        label.pack(padx=10,pady=10)

        button1 = ttk.Button(self, text="Select directory", 
                            command=lambda: self.get_file(self.window))
        
        button2 = ttk.Button(self, text="View Sequencers", 
                            command=lambda: controller.show_frame(PlotterWithZoom))

        button1.pack()
        button2.pack()
                
        self.seqrList = \
            ['SSP','XGRAD','YGRAD', 'ZGRAD','RHO1','RHO2','THETA1','THETA2']
        self.boardStates = list()
        
        self.boardChoice = Checkbar(self,picks=self.seqrList)
        self.boardChoice.pack(side="bottom", fill="x")
        self.boardChoice.config(relief="groove", bd=2)

        button3 = ttk.Button(self, text="Enter Board Choices", 
                                     command=lambda: self.allstates())
        button3.pack(side="bottom")
        
    def allstates(self):
        self.boardStates.clear()
        self.boardStates.append(list(self.boardChoice.state())) 
        
    def get_file(self,window):
        self.fileLoc.set(file_name(window))

    
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

def board_list(board_set):
    board_names = {0: 'SSP', 1: 'XGRAD', 2: 'YGRAD', 3: 'ZGRAD',\
        4: 'RHO1', 5: 'RHO2', 6: 'THETA1', 7: 'THETA2'}
    
    boards_to_play = []
    
    for i,board in enumerate(board_set):
        if board == 1:
            board_to_play.append(boards_names[i])
        else:
            continue
            
    return board_names, boards_to_play

def get_xml_root(xml_path, shot_count):
    waveforms = xmlRoot(xml_path,shot_count)
    
    return waveforms

def plot_board(app_canvas, app_fig, waveforms, board_set, boards, board, count, shot):
    
    l = len(board_set)
    lastSspTimes = sspStopTime(waveforms, shot)
    npStore = extractWvfm(waveforms, board, shot)

    wv, toCut = scaleTime(npStore,lastSspTimes,shot)

    xtr = waveTruncate(wv,toCut,shot)

    xVal, yVal = waveToPlot(xtr,shot)

    subPlt = app_fig.add_subplot(l,1,count)            
    subPlt.plot(xVal,yVal,'b-')
    subPlt.set_xlabel('Time (us)')
    subPlt.set_ylabel('Amplitude (a.u.)')
    subPlt.autoscale(enable=True,axis='x')
    subPlt.set_title('Sequence {0} Board'.format(boards[board]))

    app_fig.subplots_adjust(hspace=1.5)
    plt.rc('font', size=8)
    plt.rc('axes', titlesize=8)
    app_canvas.draw()


class PlotterWithZoom(tk.Frame):
    
    def __init__(self, parent, controller):
        tk.Frame.__init__(self,parent)
        
        self.controller = controller
        
        label = tk.Label(self, text="Interactive Plot", font=LARGE_FONT)
        label.pack(padx=10, pady=10)
        
        startpage = self.controller.get_page(StartPage)
        file = startpage.fileLoc.get()
        
        boards, board_set = board_list(startpage.boardStates)
        
        self.xmls = GetXMLPath()
        button1 = ttk.Button(self, text="Show Plot", 
                            command=lambda: self.xmls.getXmlList(file))
        button1.bind('<Button-1>',self.xmls.xmlPaths())
#         button1.bind('<Button-1>',self.get_waveforms())
        button1.pack()
        
        # load an XML for info on first plotter time-point
        seqPlots = Figure()
        
        canvas = FigCanvas(seqPlots, self)
        canvas.draw()
        canvas.get_tk_widget().pack(side='top', fill='both')
        canvas._tkcanvas.pack(side='top', fill='both', expand=1)

        for i,board in enumerate(board_set):
            plot_board(canvas, seqPlots, xmls.wvm, board_set, boards, board, i, 5)
            
        toolbar = NavTb2(canvas, self)
        toolbar.update()
        toolbar.pack()
        
        button2 = ttk.Button(self, text="Start Page", 
                            command=lambda: controller.show_frame(StartPage))
        button2.pack(side="bottom")


class genericGUI(tk.Tk):
    
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)
        
        tk.Tk.wm_title(self, "singleSeqInteract")
        
        container = tk.Frame(self)
        container.pack(side="top", fill="both", expand = True)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)
        
        self.frames = {}
        
        for F in (StartPage, PlotterWithZoom):
            
            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)
        self.centerWindow()

    def show_frame(self, frameToAdd):        
        frame = self.frames[frameToAdd]
        frame.tkraise()
        
    def get_page(self, frame_name):
        return self.frames[frame_name]
        
    def centerWindow(self):
        w = 800
        h = 1150
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w)/2
        y = (sh - h)/2
        self.geometry('%dx%d+%d+%d' % (w, h, x, y))       

            
#         plt.rcParams.update({'font.size':8})


# ### Pick the location of the XML
# Call GUI window for selection of XML directories
# for storage of their full paths
app = genericGUI()
# ani = animation.FuncAnimation(seqPlots,playSequencer, interval=stopCond)
app.mainloop()
