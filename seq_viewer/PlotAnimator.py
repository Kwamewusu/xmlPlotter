# Author: Nana K. Owusu
# This module contains functions and classes that aid in plotting and
# animating the axes, lines and waveform information that are populated
# by tkinter events in the ViewerGUI module.

# Modules for GUI #
from tkinter import StringVar
from tkinter.ttk import Button

# Modules for extracting waveforms #
from backend_exciters import ssp_end_time, extract_wfm, scale_time, \
    wave_truncate

# Modules for finding min and #
# max of an array object #
from numpy import amin, amax

# Module for animation #
from matplotlib.animation import TimedAnimation


def wave_to_plot(wave, t):
    x = wave[t, 0, :]
    y = wave[t, 1, :]

    return x, y


def board_waveform(waveforms, board_num, shot_count):
    """ Extracts relevant x and y information to be plotted

    :param waveforms: ElementTree object for sequencer chosen
    :param board_num: Integer representing sequencer board number (0-7)
    :param shot_count: Integer representing the count of XML files read in
    :return: Array of exciter/sequencer information for all shots
    """
    ssp_endings = ssp_end_time(waveforms, shot_count)
    wave_store = extract_wfm(waveforms, board_num, shot_count)

    wave, idx_to_cut = scale_time(wave_store, ssp_endings, shot_count)

    xtr = wave_truncate(wave, idx_to_cut, shot_count)

    return xtr


class ShotAnimator(TimedAnimation):
    """ Class that controls the animation of sequencer boards
    the user chooses. It allows for repeated play as well as
    single step incrementing and decrementing.
    """
    def __init__(self, fig):
        # Instance variables for storing plotting
        # information. With exception to self.fig,
        # most of the variables will be filled in
        # after the constructor has been initialized.
        self.boards_to_animate = dict()
        self.axes_to_animate = dict()
        self.line_of_axes = dict()
        self.shot_len = int()
        self.fig = fig

        self.board_names = dict()

        # Instance variables for stopping the animation
        self.pause = False
        self.stop_btn = object()
        self.display_state = StringVar()

        # Instance variable for stepping the animation
        # forward and backward
        self.step_up_dwn = object()
        self.frame_seq = object()
        self.current_frame = None

        TimedAnimation.__init__(self, self.fig, interval=1000, blit=False)

    def _stop(self, *args):
        # Stops the animation
        self.event_source.stop()

    def _post_draw(self, framedata, blit=False):
        # Draws the plot after each axis has been filled
        # with a line
        self.fig.canvas.draw_idle()

    def _draw_frame(self, framedata):
        # Fills in the desired number of axes and lines with the
        # representative x, y, and sequencer board information.
        self.current_frame = framedata
        self._drawn_artists = []
        self.boards_picked = list(self.boards_to_animate.keys())

        for board in self.boards_picked:
            x_data, y_data = wave_to_plot(self.boards_to_animate[board], self.current_frame)

            y_lim = [amin(y_data, axis=0), amax(y_data, axis=0)]
            x_lim = [amin(x_data, axis=0), amax(x_data, axis=0)]

            self.axes_to_animate[board].set_xlim(xmin=x_lim[0], xmax=x_lim[1])
            self.axes_to_animate[board].set_ylim(ymin=y_lim[0], ymax=y_lim[1])
            self.axes_to_animate[board].set_ylabel('Amplitude \n(a.u.)')
            self.axes_to_animate[board].autoscale(enable=True, axis='x')
            self.axes_to_animate[board].set_title('Sequence {0} Board'.format(self.board_names[board]))

            self.line_of_axes[board][0].set_data(x_data, y_data)

        self._drawn_artists.append(self.line_of_axes.values())

    def _draw_next_frame(self, framedata, blit):
        self._draw_frame(framedata)
        self._post_draw(framedata)

    def draw_prev_frame(self, framedata):
        self._drawn_artists.clear()
        self._draw_frame(framedata)
        self._post_draw(framedata)

    def new_frame_seq(self):
        # Returns an iterator which determines how long the
        # long sequencer data is and how long till the
        # sequence repeats
        return iter(range(self.shot_len))

    def add_shots(self, board, exciter_data):
        self.boards_to_animate[board] = exciter_data

    def remove_shots(self, board):
        self.boards_to_animate.pop(board)

    def add_subplot(self, board, idx, name):
        self.axes_to_animate[board] = self.fig.add_subplot(8, 1, idx)
        self.line_of_axes[board] = self.axes_to_animate[board].plot([], [], 'b-', lw=1)

        self.board_names[board] = name

    def remove_subplot(self, board):
        self.fig.delaxes(self.axes_to_animate[board])
        self.axes_to_animate.pop(board)
        self.board_names.pop(board)

    def stop_button(self, some_frame):
        self.display_state.set("Stop")
        self.stop_btn = Button(some_frame, textvariable=self.display_state,
                               command=lambda: self.pause_play())
        self.stop_btn.pack(side="right", anchor="sw", fill="x")
        # self.stop_btn.pack(side="bottom", anchor="sw", fill="x")

    def step_up_button(self, some_frame):
        step_up_btn = Button(some_frame, text="Forward",
                             command=lambda: self.forward())
        step_up_btn.pack(side="right", anchor="sw", fill="x")
        # step_up_btn.pack(side="bottom", anchor="sw", fill="x")

    def step_dwn_button(self, some_frame):
        step_dwn_btn = Button(some_frame, text="Backward",
                              command=lambda: self.backward())
        step_dwn_btn.pack(side="right", anchor="sw", fill="x")
        # step_dwn_btn.pack(side="bottom", anchor="sw", fill="x")

    def pause_play(self, event=None):
        if not self.pause:
            self.pause = True
            self.display_state.set("Play")
            self._stop()
            self.stop_btn.config(textvariable=self.display_state)
        else:
            self.pause = False
            self.display_state.set("Stop")
            self._start()
            self.stop_btn.config(textvariable=self.display_state)

    def forward(self):
        self.step_up_dwn.index = self.current_frame
        next_frame = self.step_up_dwn.next()
        self._draw_next_frame(next_frame, blit=False)

    def backward(self):
        self.step_up_dwn.index = self.current_frame
        prev_frame = self.step_up_dwn.prev()
        self.draw_prev_frame(prev_frame)


class PrevNextIterator:
    """ Copied from
    https://stackoverflow.com/questions/2777188/making-a-python-iterator-go-backwards
    This class allows for the increment and decrement of
    a list or tuple of integers.
    """
    def __init__(self, collection=None):
        self.collection = None or collection
        self.index = 0

    def next(self):
        try:
            self.index += 1
            result = self.collection[self.index]
        except IndexError:
            raise StopIteration
        return result

    def prev(self):
        self.index -= 1
        if self.index < 0:
            raise StopIteration
        return self.collection[self.index]

    def __iter__(self):
        return self
