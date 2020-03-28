# Author: Nana K. Owusu
# This module contains classes and functions that inherit from
# tkinter classes. The graphical user-interface window, buttons,
# and labels are defined here.

# Modules for GUI
from os import getcwd
from tkinter import Tk, Frame, Checkbutton, IntVar, StringVar, \
    Entry, Canvas
from tkinter import filedialog
from tkinter.ttk import Button, LabelFrame, Scrollbar

# Modules for interactive plotting in GUI
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigCanvas
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavTb2
from matplotlib.figure import Figure, SubplotParams

# Custom modules for plotting setting and extracting xml info
from PlotAnimator import board_waveform, ShotAnimator, PrevNextIterator
from GUIFileRetrieve import GetXMLPath
from backend_parser import xml_root


def get_file(window):
    # starting from user's home folder, pick directory in
    # which XMLs exist.
    file_loc = filedialog.askdirectory(parent=window, initialdir=getcwd(),
                                       title="Please select the XML directory")

    return file_loc


class CheckBar(Frame):
    """ Tkinter based class for generating a row of check-buttons
    which a user can select. The methods used to generate the plots
    are called from here.
    """

    def __init__(self, parent=None, picks=None):
        Frame.__init__(self, parent)

        picks = picks or list()

        self.check_btn = dict()
        self.check_vars = list()

        self.board_num = IntVar()
        self.boards_shown = 0

        self.fig = object()
        self.cnv = object()
        self.animator_obj = object()

        self.xml_info = dict()

        self.boards = {0: 'SSP', 1: 'XGRAD', 2: 'YGRAD', 3: 'ZGRAD',
                       4: 'RHO1', 5: 'RHO2', 6: 'THETA1', 7: 'THETA2'}

        for i, pick in enumerate(picks):
            self.check_vars.append(IntVar())
            self.check_vars[i].set(0)
            self.check_btn[i] = Checkbutton(self, text=pick, variable=self.check_vars[i])

        for i, button in enumerate(self.check_btn):
            self.check_btn[i]["command"] = \
                lambda board=self.check_vars[i], id_num=button: self.toggle(board, id_num)

            self.check_btn[i].pack(side="left", anchor="w", expand=True)

    def toggle(self, board, id_num):

        self.board_num.set(id_num)

        if board.get() == 1:
            board.set(1)
            self.boards_shown += 1
            shot_data = self.data_gen(id_num)
            self.animator_obj.add_shots(self.check_btn[id_num], shot_data)
            self.animator_obj.add_subplot(self.check_btn[id_num], self.boards_shown,
                                          self.boards[id_num])
            self.play_choice()

        else:
            board.set(0)
            self.boards_shown -= 1
            self.animator_obj.remove_shots(self.check_btn[id_num])
            self.animator_obj.remove_subplot(self.check_btn[id_num])

    def data_gen(self, board_num):
        # Provides the x, y information from all shot for a board
        exciter_data = board_waveform(self.xml_info["waveforms"][0], board_num,
                                      self.xml_info["xml_count"])
        return exciter_data

    def play_choice(self):
        iterator = self.animator_obj.new_frame_seq()
        self.animator_obj.pause = False
        self.animator_obj.display_state.set("Stop")

        self.animator_obj._start()
        self.cnv.update()
        for t in iterator:
            self.animator_obj._draw_frame(t)
            self.animator_obj._post_draw(t)


class Scrollable(Frame):
    """
       This framework was copied from the url below and adapted
       for this project.
https://stackoverflow.com/questions/3085696/adding-a-scrollbar-to-a-group-of-widgets-in-tkinter/3092341#3092341
       Make a frame scrollable with scrollbar on the right.
       After adding or removing widgets to the scrollable frame,
       call the update() method to refresh the scrollable area.
    """

    def __init__(self, frame, fig, width=16, parent=None):

        # Base class initialization
        Frame.__init__(self, parent)

        fig_size = fig.get_size_inches()
        self.frame = frame

        # Instance variable for tkinter canvas
        self.tk_cnv = Canvas(frame, highlightthickness=0)
        self.tk_cnv.pack(side='left', fill='both', expand=True)
        # self.tk_cnv.config(width=fig_size[0], height=fig_size[1])

        # Instance variable for the scroll-bar
        v_scroll = Scrollbar(frame, width=width)
        v_scroll.pack(side='right', fill='y', expand=False)

        # Instance variable for the matplotlib canvas
        self.canvas = FigCanvas(fig, self.tk_cnv)
        self.cnv_widget = self.canvas.get_tk_widget()

        self.cnv_widget.config(yscrollcommand=v_scroll.set)
        self.cnv_widget.bind("<Configure>", self.__fill_canvas)

        v_scroll.config(command=self.tk_cnv.yview)
        self.bind("<Enter>", self._bound_to_mousewheel)
        self.bind("<Leave>", self._unbound_to_mousewheel)

        # Assign frame generated by the class to the canvas
        # and create a scrollable window for it.
        self.windows_item = \
            self.tk_cnv.create_window((0, 0), window=self.cnv_widget, anchor='e',
                                      tag='self.canvas')

        self.tk_cnv.config(scrollregion=self.tk_cnv.bbox("all"))

    def _bound_to_mousewheel(self, event):
        self.tk_cnv.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.tk_cnv.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.tk_cnv.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def __fill_canvas(self, event):
        # update the scrollbars to match the size of the inner frame
#        size = (self.frame.winfo_reqwidth(), self.frame.winfo_reqheight())
#        print(size, self.tk_cnv.winfo_reqheight(), self.tk_cnv.winfo_reqwidth())
#        self.tk_cnv.config(scrollregion='0 0 %s %s' % size)
#        if self.frame.winfo_reqwidth() != self.tk_cnv.winfo_width():
#            # update the canvas's width to fit the inner frame
#            self.tk_cnv.config(width=self.winfo_reqwidth())
#        if self.frame.winfo_reqheight() != self.tk_cnv.winfo_height():
#            # update the canvas's width to fit the inner frame
#            self.tk_cnv.config(height=self.frame.winfo_reqheight())
        # Enlarge the windows item to the canvas width
        canvas_width = event.width
        canvas_height = event.height
        print(canvas_height,canvas_width)
        self.tk_cnv.itemconfig(self.windows_item, width=canvas_width,
                               height=canvas_height)

    def update(self):
        # Update the canvas and the scroll-region
        self.update_idletasks()
        self.tk_cnv.config(
            scrollregion=self.tk_cnv.bbox("self.canvas"))


class StartPage(Frame):
    """ Tkinter based class for single frame upon which widgets
    such as buttons, check-buttons, and entry are used as a
    simple graphical user interface.
    """
    LARGE_FONT = ("Veranda", 12)

    def __init__(self, parent, controller):
        Frame.__init__(self, parent)

        # Instance variables with page/window info of current frame
        self.controller = controller
        self.window = parent

        # Instance variables fro the first row of widgets
        self.entry_frame = Frame(self.window, relief="raised")
        self.entry_frame.grid(row=0, column=0, sticky="ew")

        # Event handlers for displaying user's desired directory
        self.choice_display = Entry(self.entry_frame, width=105)

        self.xml_dir = StringVar(self.window)
        self.xml_dir.set(getcwd())

        self.user_choice()

        # Object that contains XML paths and file counts
        self.xml = GetXMLPath()

        # Instance variables for the second row of widgets
        self.checkbox_frame = LabelFrame(self.window, text="Boards", relief="sunken")
        self.checkbox_frame.grid(row=1, column=0, sticky="ew")

        self.seq_list = ['SSP', 'XGRAD', 'YGRAD', 'ZGRAD',
                         'RHO1', 'RHO2', 'THETA1', 'THETA2']

        # Event handler for selecting desired boards
        self.board_options = CheckBar(self.checkbox_frame, picks=self.seq_list)
        self.show_options()

        # Instance variable for third row of widgets
        self.canvas_frame = Frame(self.window, relief="sunken")
        self.canvas_frame.grid(row=2, column=0, pady=5, sticky="ew")

        # Instance variables for the figure
        params = SubplotParams(left=0.35, right=0.95, top=0.98, bottom=0.02)
        self.plot_fig = Figure(figsize=[14.0, 18.0], subplotpars=params,
                               constrained_layout=False)
        # self.plot_fig = Figure(figsize=[12.0, 10.0], constrained_layout=False)

        self.plot_fig.subplots_adjust(hspace=1.0)
        # Setup for changing the size of the axes in the plot
        widths = [1]
        heights = self.get_repeat_list([0.65], 8)
        self.plot_fig.add_gridspec(nrows=8, ncols=1, width_ratios=widths,
                                   height_ratios=heights)
        self.canvas_body = Scrollable(self.canvas_frame, self.plot_fig)
        self.canvas = self.canvas_body.canvas

        # Instance variable for third row of widgets
        self.control_frame = Frame(self.window, relief="sunken")
        self.control_frame.grid(row=3, column=0, columnspan=2,
                                pady=5, sticky="ew")

        # Instance variables for the animation and navigation of plots
        self.toolbar = NavTb2(self.canvas, self.control_frame)

        self.canvas_setup()
        self.animator = ShotAnimator(self.plot_fig)
        self.animator.step_up_button(self.control_frame)
        self.animator.stop_button(self.control_frame)
        self.animator.step_dwn_button(self.control_frame)

    @staticmethod
    def get_repeat_list(repeat_list, num_of_times):
        return [num for num in repeat_list for i in range(num_of_times)]

    def user_choice(self):
        self.choice_display.delete(first=0, last="end")

        # Event handler for selecting desired directory
        choice = Button(self.entry_frame, text="Select directory",
                        command=lambda: self.file_name())
        choice.grid(row=0, column=0, sticky="e")

        self.choice_display.grid(row=0, column=1)

    def show_options(self):
        # Set in label for the check-box frame
        self.board_options.grid(row=1, column=0, columnspan=2, sticky="ew")
        self.board_options.grid_configure(row=2, column=0)

    def canvas_setup(self):
        # self.canvas.get_tk_widget().config(scrollregion=(0, 0, 1000, 1000),
        #                                    yscrollcommand=self.v_scroll.set)
        # self.canvas.get_tk_widget().pack(side='left', fill='both', expand=True)
        # self.canvas.get_tk_widget().create_window((1000, 1000), window=self.canvas_frame)

        # self.v_scroll.config(command=self.canvas.get_tk_widget().yview())
        # self.v_scroll.pack(side='right', fill='y')

        self.toolbar.update()
        self.toolbar.pack(side="left")

        # self.plot_fig.set_figwidth(10.0)
        # self.plot_fig.set_figheight(32.0)

    def choice_show(self):
        self.choice_display.insert(index=0, string=self.xml_dir.get())

    def file_name(self):
        self.xml_dir.set(get_file(self.window))
        self.choice_show()

        self.choice_display.config(state="disable")
        self.setup_plot()
        self.checkbox_frame.after(10, self.update_checkbox())

    def setup_plot(self):
        self.xml.get_xml_list(self.xml_dir.get())
        self.get_waveforms(self.xml.xml_full_path, self.xml.stop_condition)

    def get_waveforms(self, xml_paths, shot_count):
        self.xml.waveforms.append(xml_root(xml_paths, shot_count))

    def update_checkbox(self):
        self.board_options.xml_info["waveforms"] = self.xml.waveforms
        self.board_options.xml_info["xml_count"] = self.xml.stop_condition

        self.board_options.cnv = self.canvas_body.cnv_widget

        self.animator.shot_len = self.xml.stop_condition
        self.animator.frame_seq = self.animator.new_frame_seq()
        self.animator.step_up_dwn = PrevNextIterator(
            [x for x in self.animator.frame_seq])

        self.board_options.fig = self.plot_fig
        self.board_options.animator_obj = self.animator


class MainContainer(Tk):
    """ Tkinter based class used to generate a single window
    and contain a single frame. The frame contains multiple
    widgets for user choice and visualization.
    """

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
