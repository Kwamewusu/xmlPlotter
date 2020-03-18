# Modules for GUI
from os import getcwd
from tkinter import Tk, Frame, Checkbutton, IntVar, StringVar, Entry
from tkinter import filedialog
from tkinter.ttk import Button, LabelFrame

# Modules for interactive plotting in GUI
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg as FigCanvas
from matplotlib.backends.backend_tkagg import NavigationToolbar2Tk as NavTb2
from matplotlib.figure import Figure

from matplotlib.animation import FuncAnimation
from PlotAnimator import unpick_board, board_waveform, ShotAnimator
from GUIFileRetrieve import GetXMLPath
from backend_parser import xml_root


def get_file(window):
    # starting from user's home folder, pick directory in
    # which XMLs exist.
    file_loc = filedialog.askdirectory(parent=window, initialdir=getcwd(),
                                       title="Please select the XML directory")

    return file_loc


# def on_off_actions(event, canvas, fig, ax, boards, board_num, waveform, shot_count):
#     # state = [var.get() for var in self.check_vars]
#     # all_states = [self.board_set.append(i) for i, board in enumerate(state) if board == 1]
#     x, y = board_waveform(waveform, board_num, shot_count)
#
#     if event:
#         pick_board(canvas, fig, ax, x, y, boards, board_num)
#     else:
#         unpick_board(fig)


class CheckBar(Frame):

    def __init__(self, parent=None, picks=None):
        Frame.__init__(self, parent)

        picks = picks or list()

        self.check_btn = dict()
        self.check_vars = list()

        self.board_num = IntVar()
        self.boards_shown = 0

        self.fig = object()
        self.canvas = object()
        self.animator_obj = object()

        self.xml_info = dict()
        self.axes_dict = dict()

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
            self.animator_obj.add_subplot(self.check_btn[id_num], self.boards_shown)
            self.play_choice()
            # self.test_plot(shot_data, board_obj)
            # self.animator(board_obj)

            # board.bind('<ButtonRelease-1>', self.send_to_animator(board, shot_data))
        else:
            board.set(0)
            self.boards_shown -= 1
            unpick_board(self.axes_dict[id_num])
            self.axes_dict.pop(self.check_btn[id_num])
            self.animator_obj.remove_shots(self.check_btn[id_num])
            self.animator_obj.remove_subplot(self.check_btn[id_num], self.boards_shown)

    def data_gen(self, board_num):
        # Provides the x, y information from all shot for a board
        exciter_data = board_waveform(self.xml_info["waveforms"][0], board_num,
                                      self.xml_info["xml_count"])
        return exciter_data

    def play_choice(self):
        iterator = self.animator_obj.new_frame_seq()
        for t in iterator:
            self.animator_obj._draw_frame(t)
            self.animator_obj._post_draw(t)
            self.canvas.draw()
#        for i, button in enumerate(self.check_btn):
#            self.btn_bind.append(self.check_btn[i].bind("<Button-1>", func))

#     def test_plot(self, shot_data, num):
#         x_val, y_val = wave_to_plot(shot_data, self.xml_info["xml_count"]-1)
#         self.xml_info["axes"][self.axes_list[self.board_num.get()]][0].set_data(x_val, y_val)
#         self.axes_list[self.board_num.get()].set_xlabel('Time (us)')
#         self.axes_list[self.board_num.get()].set_ylabel('Amplitude (a.u.)')
#         self.axes_list[self.board_num.get()].autoscale(enable=True, axis='x')
#         self.axes_list[self.board_num.get()].set_xlabel('Sequence {0} Board'.format(self.boards[num]))
#
#         self.fig.subplots_adjust(hspace=1.5)
#         self.canvas.draw()

#     def play_choice(self, func):
#         for i, button in enumerate(self.check_btn):
#             self.btn_bind.append(self.check_btn[i].bind("<Button-1>", func))

#     def player(self, data):
#         x_val, y_val = [], []
#         for wave in data:
#             x_data, y_data = wave_to_plot(wave, self.xml_info["xml_count"])
#             x_val.append(x_data)
#             y_val.append(y_data)
#             ylim = [min(y_data), max(y_data)]
#             xlim = [min(x_data), max(x_data)]
#             self.axes_list[self.board_num.get()].set_xlim(xlim[0], xlim[1])
#             self.axes_list[self.board_num.get()].set_ylim(ylim[0], ylim[1])
#             self.axes_list[self.board_num.get()].set_xlabel('Time (us)')
#             self.axes_list[self.board_num.get()].set_ylabel('Amplitude (a.u.)')
#             self.axes_list[self.board_num.get()].autoscale(enable=True, axis='x')
#             self.axes_list[self.board_num.get()].set_xlabel('Sequence {0} Board'.
#                                                             format(self.boards[self.board_num.get()]))
#
#         self.xml_info["axes"][self.axes_list[self.board_num.get()]][0].set_data(x_val, y_val)
        # self.after(500, self.fig.clear())

#         return self.xml_info["axes"][self.axes_list[self.board_num.get()]]

#     def animator(self, board_num):
#         animate = FuncAnimation(self.fig, self.player, self.data_gen(board_num),
#                                 blit=False, interval=50, repeat=False)
#
#         self.canvas.draw()


class StartPage(Frame):
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
        self.checkbox_frame.grid(row=1, column=0, columnspan=2, sticky="ew")

        self.seq_list = ['SSP', 'XGRAD', 'YGRAD', 'ZGRAD',
                         'RHO1', 'RHO2', 'THETA1', 'THETA2']

        # Event handler for selecting desired boards
        self.board_options = CheckBar(self.checkbox_frame, picks=self.seq_list)
        self.show_options()

        # Instance variable for third row of widgets
        self.canvas_frame = Frame(self.window, relief="sunken")
        self.canvas_frame.grid(row=2, column=0, pady=5, sticky="ew")

        # Instance variables for the figure, canvas and navigation of plots
        self.plot_fig = Figure(figsize=[7.0, 7.50])
        self.canvas = FigCanvas(self.plot_fig, self.canvas_frame)
        self.toolbar = NavTb2(self.canvas, self.canvas_frame)

        self.canvas_setup()
        self.animator = ShotAnimator(self.plot_fig, self.canvas)

        # self.board_options.play_choice(self.animator)

        # Instance variable for third row of widgets
        self.control_frame = Frame(self.window, relief="sunken")
        self.control_frame.grid(row=3, column=0, pady=5, sticky="ew")

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
        self.toolbar.update()
        self.toolbar.pack()

        self.canvas.get_tk_widget().pack(side='top', fill='both')
        self.canvas._tkcanvas.pack(side='top', fill='both', expand=1)

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

        self.animator.shot_len = self.xml.stop_condition
        self.board_options.animator_obj = self.animator

        self.board_options.fig = self.plot_fig
        self.board_options.canvas = self.canvas


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
