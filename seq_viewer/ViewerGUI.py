# Modules for GUI
from os import getcwd
from tkinter import Tk, Frame, Checkbutton, IntVar, StringVar, Label
from tkinter import filedialog
from tkinter.ttk import Button

from PlotAnimator import AnimateShots
from GUIFileRetrieve import GetXMLPath
from backend_parser import xml_root
from backend_exciters import ssp_end_time, extract_wfm, scale_time, \
    wave_truncate

# Modules for interactive plotting in GUI
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigCanvas
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavTb2


def get_file(window):
    # starting from user's home folder, pick directory in
    # which XMLs exist.
    file_loc = filedialog.askdirectory(parent=window, initialdir=getcwd(),
                                       title="Please select the XML directory")

    return file_loc


def plot_board(app_canvas, app_fig, waveforms, board_set, boards, board_num, count, shot):
    l = len(board_set)
    ssp_endings = ssp_end_time(waveforms, shot)
    wave_store = extract_wfm(waveforms, board_num, shot)

    wave, idx_to_cut = scale_time(wave_store, ssp_endings, shot)

    xtr = wave_truncate(wave, idx_to_cut, shot)


class CheckBar(Frame):

    def __init__(self, parent=None, picks=[]):
        Frame.__init__(self, parent)

        self.board_set = []
        self.check_btn = []
        self.check_vars = []

        self.boards = {0: 'SSP', 1: 'XGRAD', 2: 'YGRAD', 3: 'ZGRAD',
                       4: 'RHO1', 5: 'RHO2', 6: 'THETA1', 7: 'THETA2'}

        for i, pick in enumerate(picks):
            self.check_vars.append(IntVar())
            self.check_vars[i].set(0)
            self.check_btn.append(Checkbutton(self, text=pick,
                                              variable=self.check_vars[i],
                                              command=lambda: self.toggle(self.check_vars[i])))
            self.check_btn[i].pack(side="left", fill="x", expand=True)

    @staticmethod
    def toggle(board):

        if board.get() == 1:
            board.set(1)
        else:
            board.set(0)

    def state(self):

        state = []
        for var in self.check_vars:
            state.append(var.get())

        for i, board in enumerate(state):
            if board == 1:
                self.board_set.append(i)
                continue


class StartPage(Frame):

    def __init__(self, parent, controller):
        Frame.__init__(self, parent, width=700, height=1000)

        self.controller = controller
        self.window = parent

        label = Label(self, tex="Start Page", font=LARGE_FONT)
        label.pack(padx=10, pady=10)

        self.xml_dir = StringVar(self.window)
        self.xml_dir.set(getcwd())

        button1 = Button(self, text="Select directory",
                         command=lambda: self.file_name())

        button2 = Button(self, text="View Sequencers",
                         command=lambda: controller.show_frame(Plotter))

        button1.pack(side="top")
        button2.pack(side="top")

        self.seqr_list = \
            ['SSP', 'XGRAD', 'YGRAD', 'ZGRAD', 'RHO1', 'RHO2', 'THETA1', 'THETA2']

        self.board_choice = CheckBar(self, picks=self.seqr_list)
        self.board_choice.pack(side="left", fill="x", expand=True)
        self.board_choice.config(relief="groove", bd=2)

        button3 = Button(self, text="Enter Board Choices",
                         command=lambda: self.all_states())
        button3.pack(side="bottom")

    def all_states(self):
        self.board_choice.state()

    def file_name(self):
        self.xml_dir.set(get_file(self.window))


class Plotter(Frame):

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)

        self.controller = controller
        self.window = parent

        self.start_page = self.controller.get_page(StartPage)

        # Label to appear at the top of this frame
        label = Label(self, text="Interactive Plot", font=LARGE_FONT)
        label.pack(padx=10, pady=10)

        # Object that contain XML paths and file counts
        self.xml = GetXMLPath()

        # Event handler for method that set up and plots the sequencers
        button1 = Button(self, text="Show Plot",
                         command=lambda: self.setup_plot())
        button1.pack()

        # Event handler for returning to starting page
        button2 = Button(self, text="Start Page",
                         command=lambda: controller.show_frame(StartPage))
        button2.pack(side="bottom")

        self.seq_plots = Figure()
        self.canvas = FigCanvas(self.seq_plots, self)

        toolbar = NavTb2(self.canvas, self)
        toolbar.update()
        toolbar.pack()

        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side='top', fill='both')
        self.canvas._tkcanvas.pack(side='top', fill='both', expand=True)

    def setup_plot(self):
        self.xml.get_xml_list(self.start_page.xml_dir.get())
        self.get_waveforms(self.xml.xml_full_path, self.xml.stop_condition)

    def get_waveforms(self, xml_paths, shot_count):
        self.xml.waveforms.append(xml_root(xml_paths, shot_count))


class MainContainer(Tk):

    LARGE_FONT = ("Veranda", 12)

    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        Tk.wm_title(self, "Sequence Viewer")

        container = Frame(self)
        container.grid(row=0, column=0, sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (StartPage, Plotter):
            frame = F(container, self)

            self.frames[F] = frame

            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)
        self.center_window()

    def show_frame(self, frame_to_add):
        frame = self.frames[frame_to_add]
        frame.tkraise()

    def get_page(self, frame_name):
        return self.frames[frame_name]

    def center_window(self):
        w = 800
        h = 1150
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) / 2
        y = (sh - h) / 2

        self.geometry('%dx%d+%d+%d' % (w, h, x, y))
