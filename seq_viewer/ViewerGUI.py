# Author: Nana K. Owusu
# This module contains classes and functions that inherit from
# tkinter classes. The graphical user-interface window, buttons,
# and labels are defined here.

# Modules for GUI
from os import getcwd
from tkinter import Tk, Frame, Checkbutton, IntVar, StringVar, \
    Entry, Canvas, Label, filedialog
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
    """ Get full path to desired directory starting from user's
    home folder; pick desired directory
    :param window: Tk Frame object
    :return: file_loc: string containing the full path to desired directory
    """
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

        self.frame = parent

        picks = picks or list()

        self.check_btn = dict()
        self.check_vars = list()

        self.board_num = IntVar()
        self.boards_shown = 0

        self.fig = object()
        self.cnv = object()
        self.shot = object()
        self.shot_label = object()
        self.animator_obj = object()

        self.xml_info = dict()

        self.boards = {0: 'SSP', 1: 'XGRAD', 2: 'YGRAD', 3: 'ZGRAD',
                       4: 'RHO1', 5: 'RHO2', 6: 'THETA1', 7: 'THETA2'}

        for i, pick in enumerate(picks):
            self.check_vars.append(IntVar())
            self.check_vars[i].set(0)
            self.check_btn[i] = Checkbutton(self.frame, text=pick, variable=self.check_vars[i])

        for i, button in enumerate(self.check_btn):
            self.check_btn[i]["command"] = \
                lambda board=self.check_vars[i], id_num=button: self.toggle(board, id_num)

            self.check_btn[i].pack(side="left", anchor="nw", fill="x", expand=True)

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
        self.cnv()
        for t in iterator:
            self.shot.set(t)
            self.shot_label.update()
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

    def __init__(self, frame, fig, width=16):

        # Base class initialization
        Frame.__init__(self, frame)

        self.frame = frame
        self.fig = fig

        # Instance variable for tkinter canvas
        self.tk_cnv = Canvas(self.frame, highlightthickness=0)
        self.tk_cnv.pack(side="left", anchor="nw", fill="both", expand=True)

        # Instance variable for the scroll-bar
        v_scroll = Scrollbar(self.frame)
        v_scroll.pack(side="right", anchor="ne", fill="y", expand=False)
        v_scroll.config(command=self.tk_cnv.yview, width=width)
        v_scroll.activate("slider")

        # Instance variable for the matplotlib canvas
        self.mpl_cnv = FigCanvas(fig, self.frame)
        self.mpl_cnv_widget = self.mpl_cnv.get_tk_widget()

        self.tk_cnv.config(yscrollcommand=v_scroll.set)
        self.tk_cnv.bind("<Configure>", self.__fill_canvas)

        # self.bind("<Enter>", self._bound_to_mousewheel)
        # self.bind("<Leave>", self._unbound_to_mousewheel)

        # Assign frame generated by the class to the canvas
        # and create a scrollable window for it.
        self.windows_item = \
            self.tk_cnv.create_window(-80, 900, window=self.mpl_cnv_widget,
                                      anchor="nw", tag="self.mpl_widget")

        self.tk_cnv.config(scrollregion=self.tk_cnv.bbox("all"))

    def _bound_to_mousewheel(self, event):
        self.tk_cnv.bind_all("<MouseWheel>", self._on_mousewheel)
        # self.frame.tk_cnv.bind_all("<MouseWheel>", self._on_mousewheel)

    def _unbound_to_mousewheel(self, event):
        self.tk_cnv.unbind_all("<MouseWheel>")

    def _on_mousewheel(self, event):
        self.tk_cnv.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def __fill_canvas(self, event):
        """update the scrollbars to match the size of the inner frame"""
        # Enlarge the windows item to the canvas width
        canvas_width = event.width
        canvas_height = event.height * 2.825

        self.tk_cnv.itemconfig(self.windows_item, width=canvas_width,
                               height=canvas_height)

    def update_canvas(self):
        """Update the canvas and the scroll-region"""
        self.update_idletasks()


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

        # Instance variables for widgets showing/picking user's desired #
        # directory.                                                    #
        self.entry_frame = Frame(self.controller, relief="raised", height=15)
        self.entry_frame.pack(side="top", anchor="nw", padx=2, pady=2, fill="x")

        # -Event handler for displaying user's desired directory
        self.choice_display = Entry(self.entry_frame, width=105)

        self.xml_dir = StringVar(self.controller)
        self.xml_dir.set(getcwd())

        self.user_choice()

        # -Object that contains XML paths and file counts
        self.xml = GetXMLPath()

        # Instance variables for the CheckButton widgets #
        self.checkbox_frame = LabelFrame(self.controller, text="Boards",
                                         relief="sunken")
        self.checkbox_frame.pack(side="top", anchor="nw", padx=2, pady=2,
                                 fill="x")

        self.seq_list = ['SSP', 'XGRAD', 'YGRAD', 'ZGRAD',
                         'RHO1', 'RHO2', 'THETA1', 'THETA2']

        # -Event handler for selecting desired boards
        self.board_options = CheckBar(self.checkbox_frame, picks=self.seq_list)
        self.show_options()

        # Instance variable for Scrollable frame widgets #
        self.canvas_frame = Frame(self.controller, relief="sunken")
        self.canvas_frame.pack(side="top", anchor="nw", padx=2, pady=2, fill="both",
                               expand=True)

        # -Instance variables for the figure to be populated
        params = SubplotParams(left=0.25, right=0.95, top=0.98, bottom=0.02)
        self.plot_fig = Figure(figsize=[14.0, 18.0], subplotpars=params,
                               constrained_layout=False)

        self.plot_fig.subplots_adjust(hspace=1.0)

        # -Setup for changing the size of the axes in the plot
        widths = [1]
        heights = self.get_repeat_list([0.65], 8)
        self.plot_fig.add_gridspec(nrows=8, ncols=1, width_ratios=widths,
                                   height_ratios=heights)

        # -Instance variable for the frame with scrolling functionality
        self.canvas_body = Scrollable(self.canvas_frame, self.plot_fig)
        self.mpl_canvas = self.canvas_body.mpl_cnv

        # Instance variables for the widgets controlling the animation #
        self.control_frame = Frame(self.controller, relief="sunken")
        self.control_frame.pack(side="bottom", anchor="sw", fill="x")

        # -Instance variables for the animation and navigation of plots
        self.shot_num = IntVar(self.controller)
        self.shot_info = StringVar(self.controller)
        self.shot_num.set(0)
        self.show_shot_num = Label(self.control_frame, textvariable=self.shot_info)

        # -Instance variables for the animation and navigation of plots
        self.toolbar = NavTb2(self.mpl_canvas, self.control_frame)

        self.canvas_setup()
        self.animator = ShotAnimator(self.plot_fig)
        self.animator.step_up_button(self.control_frame)
        self.animator.stop_button(self.control_frame)
        self.animator.step_dwn_button(self.control_frame)
        self.show_shot_num.pack(side="right", anchor="sw", fill="x")

    @staticmethod
    def get_repeat_list(repeat_list, num_of_times):
        return [num for num in repeat_list for i in range(num_of_times)]

    def user_choice(self):
        self.choice_display.delete(first=0, last="end")

        # Event handler for selecting desired directory
        choice = Button(self.entry_frame, text="Select directory",
                        command=lambda: self.file_name())
        choice.pack(side="left")

        self.choice_display.pack(side="top", fill="x", expand=True)

    def show_options(self):
        """Set in label for the check-box frame"""
        self.board_options.pack(side="left", expand=False)

    def canvas_setup(self):
        self.canvas_body.pack(side="top", anchor="nw", fill="both", expand=True)
        self.toolbar.pack(side="left", anchor="sw", fill="x")
        self.toolbar.update()

    def choice_show(self):
        self.choice_display.insert(index=0, string=self.xml_dir.get())

    def file_name(self):
        self.xml_dir.set(get_file(self.window))
        self.choice_show()

        self.choice_display.config(state="disable")
        self.get_info()
        self.checkbox_frame.after(10, self.update_checkbox())

    def get_info(self):
        self.xml.get_xml_list(self.xml_dir.get())
        self.get_waveforms(self.xml.xml_full_path, self.xml.stop_condition)

    def get_waveforms(self, xml_paths, shot_count):
        self.xml.waveforms.append(xml_root(xml_paths, shot_count))

    def update_checkbox(self):
        """Taking advantage of the order of executions
        in the events, this function passes information to
        objects of respective application components for
        starting and controlling the animation
        """
        self.board_options.xml_info["waveforms"] = self.xml.waveforms
        self.board_options.xml_info["xml_count"] = self.xml.stop_condition

        self.board_options.cnv = self.canvas_body.update_canvas

        self.show_shot_num.config(textvariable=self.shot_info.
                                  set("Shot #: {0}/{1}".format(self.shot_num.get(),
                                                               self.xml.stop_condition)))

        self.animator.shot = self.shot_num
        self.animator.shot_len = self.xml.stop_condition
        self.animator.shot_label = self.show_shot_num
        self.animator.frame_seq = self.animator.new_frame_seq()
        self.animator.step_up_dwn = PrevNextIterator(
            [x for x in self.animator.frame_seq])

        self.board_options.fig = self.plot_fig
        self.board_options.shot = self.shot_num
        self.board_options.shot_label = self.show_shot_num
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
        container.pack_configure(side="top", anchor="nw", fill="both")

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
