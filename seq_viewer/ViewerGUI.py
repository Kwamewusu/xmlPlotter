# Modules for GUI
from os import getcwd
from tkinter import Tk, Frame, Checkbutton, IntVar, StringVar, Label, Entry
from tkinter import filedialog
from tkinter.ttk import Button

# Modules for interactive plotting in GUI
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigCanvas
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavTb2
from matplotlib.figure import Figure

# from PlotAnimator import AnimateShots
from GUIFileRetrieve import GetXMLPath
from backend_parser import xml_root


def get_file(window):
    # starting from user's home folder, pick directory in
    # which XMLs exist.
    file_loc = filedialog.askdirectory(parent=window, initialdir=getcwd(),
                                       title="Please select the XML directory")

    return file_loc


class CheckBar(Frame):

    def __init__(self, parent=None, picks=None):
        Frame.__init__(self, parent)

        picks = picks or []

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
            self.check_btn[i].pack(side="left", anchor="w", expand=True)

    @staticmethod
    def toggle(board):

        if board.get() == 1:
            board.set(1)
        else:
            board.set(0)

    def state(self):

        state = [var.get() for var in self.check_vars]

        all_states = [self.board_set.append(i) for i, board in enumerate(state) if board == 1]

        yield all_states

#        for i, board in enumerate(state):
#            if board == 1:
#                self.board_set.append(i)
#                continue

    @staticmethod
    def boards_picked(boards):
        states = [board.get() for board in boards]
        count = sum(states)

        return count


class StartPage(Frame):
    LARGE_FONT = ("Veranda", 12)

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)

        # Instance variables with page/window info of current frame
        self.controller = controller
        self.window = parent

        # Instance variables fro the first row of widgets
        self.entry_frame = Frame(self.window, relief="raised")
        self.entry_frame.grid(row=0, column=0, pady=10, sticky="ew")

        # Event handlers for displaying user's desired directory
        self.choice_display = Entry(self.entry_frame, width=105)

        self.xml_dir = StringVar(self.window)
        self.xml_dir.set(getcwd())

        self.user_choice()

        # Instance variables for the second row of widgets
        self.checkbox_frame = Frame(self.window, relief="sunken")
        self.checkbox_frame.grid(row=1, column=0, ipady=20, sticky="ew")

        self.seq_list = \
            ['SSP', 'XGRAD', 'YGRAD', 'ZGRAD', 'RHO1', 'RHO2', 'THETA1', 'THETA2']

        # Event handler for selecting desired boards
        self.board_choice = CheckBar(self.entry_frame, picks=self.seq_list)
        self.play_choice()

        # Instance variable for third row of widgets
        self.canvas_frame = Frame(self.window, relief="sunken")
        self.canvas_frame.grid(row=2, column=0, pady=5, sticky="ew")

        self.plot_fig = Figure()

        self.canvas = FigCanvas(self.plot_fig, self.canvas_frame)

        self.toolbar = NavTb2(self.canvas, self.canvas_frame)

        # Object that contains XML paths and file counts
        self.xml = GetXMLPath()

        # Instance variable for third row of widgets
        self.control_frame = Frame(self.window, relief="sunken")
        self.control_frame.grid(row=3, column=0, pady=5, sticky="ew")

        self.canvas_setup()

    def user_choice(self):
        self.choice_display.delete(first=0, last="end")

        # Event handler for selecting desired directory
        choice = Button(self.entry_frame, text="Select directory",
                        command=lambda: self.file_name())
        choice.grid(row=0, column=0, sticky="e")

        self.choice_display.grid(row=0, column=1)

    def play_choice(self):
        # Label for the check-box frame
        checkbox_label = Label(self.window, text="Boards")
        checkbox_label.grid(row=0, column=0, ipady=0, sticky="w")

        self.board_choice.grid(row=2, column=0, pady=20, sticky="ew")
        self.board_choice.grid_configure(row=3, column=0, columnspan=2)

    def canvas_setup(self):
        self.toolbar.update()
        self.toolbar.pack()

        self.canvas.get_tk_widget().pack(side='top', fill='both')
        self.canvas._tkcanvas.pack(side='top', fill='both', expand=1)

        board_count = self.board_choice.boards_picked(self.board_choice.check_vars)


#    def all_states(self):
#        self.board_choice.state()

    def choice_show(self):
        self.choice_display.insert(index=0, string=self.xml_dir.get())

    def file_name(self):
        self.xml_dir.set(get_file(self.window))
        self.choice_show()

        self.choice_display.config(state="disable")

    def get_waveforms(self, xml_paths, shot_count):
        self.xml.waveforms.append(xml_root(xml_paths, shot_count))


# class Plotter(Frame):
#
#    LARGE_FONT = ("Veranda", 12)
#
#    def __init__(self, parent, controller):
#        Frame.__init__(self, parent)
#
#        self.controller = controller
#        self.window = parent
#
#        self.start_page = self.controller.get_page(StartPage)
#
#        # Label to appear at the top of this frame
#        label = Label(self, text="Interactive Plot", font=self.LARGE_FONT)
#        label.pack(padx=10, pady=10)
#
#        # Object that contain XML paths and file counts
#        self.xml = GetXMLPath()
#
#        # Event handler for method that set up and plots the sequencers
#        button1 = Button(self, text="Show Plot",
#                         command=lambda: self.setup_plot())
#        button1.pack()
#
#        # Event handler for returning to starting page
#        button2 = Button(self, text="Start Page",
#                         command=lambda: controller.show_frame(StartPage))
#        button2.pack(side="bottom")
#
#        self.seq_plots = Figure()
#        self.canvas = FigCanvas(self.seq_plots, self)
#
#        toolbar = NavTb2(self.canvas, self)
#        toolbar.update()
#        toolbar.pack()
#
#        self.canvas.draw()
#        self.canvas.get_tk_widget().pack(side='top', fill='both')
#        self.canvas.tkcanvas.pack(side='top', fill='both', expand=True)
#
#    def setup_plot(self):
#        self.xml.get_xml_list(self.start_page.xml_dir.get())
#        self.get_waveforms(self.xml.xml_full_path, self.xml.stop_condition)
#
#    def get_waveforms(self, xml_paths, shot_count):
#        self.xml.waveforms.append(xml_root(xml_paths, shot_count))


class MainContainer(Tk):

    def __init__(self, *args, **kwargs):
        Tk.__init__(self, *args, **kwargs)

        Tk.wm_title(self, "Sequence Viewer")

        Tk.wm_resizable(self, width=True, height=True)

        container = Frame(self)
        container.grid_configure(row=0, column=0, sticky="nsew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        frame = StartPage(container, self)

        self.frames[StartPage] = frame

        self.show_frame(StartPage)

        self.center_window()

    def show_frame(self, frame_to_add):
        frame = self.frames[frame_to_add]
        frame.tkraise()

    def get_page(self, frame_name):
        return self.frames[frame_name]

    def center_window(self):
        w = 1100
        h = 900
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()
        x = (sw - w) / 2
        y = (sh - h) / 2

        self.geometry('%dx%d+%d+%d' % (w, h, x, y))
