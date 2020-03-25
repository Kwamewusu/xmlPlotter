# Modules for GUI #
from tkinter import Frame, StringVar
from tkinter.ttk import Button

# Modules for extracting waveforms #
from backend_exciters import ssp_end_time, extract_wfm, scale_time, \
    wave_truncate

# Modules for finding min and
# max of an array object #
from numpy import amin, amax

# Module for animation
import matplotlib.pyplot as plt
from matplotlib.animation import TimedAnimation, FuncAnimation


def wave_to_plot(wave, t):
    x = wave[t, 0, :]
    y = wave[t, 1, :]

    return x, y


def board_waveform(waveforms, board_num, shot_count):
    ssp_endings = ssp_end_time(waveforms, shot_count)
    wave_store = extract_wfm(waveforms, board_num, shot_count)

    wave, idx_to_cut = scale_time(wave_store, ssp_endings, shot_count)

    xtr = wave_truncate(wave, idx_to_cut, shot_count)

    return xtr


def pick_board(app_canvas, app_fig, fig_axes, x_val, y_val, boards, board_num):

    fig_axes.plot(x_val, y_val, 'b-')
    fig_axes.set_xlabel('Time (us)')
    fig_axes.set_ylabel('Amplitude (a.u)')
    fig_axes.autoscale(enable=True, axis='x')
    fig_axes.set_title('Sequence {0} Board'.format(boards[board_num]))

    app_fig.subplots_adjust(hspace=1.5)
    plt.rc('font', size=8)
    plt.rc('axes', titlesize=8)

    app_canvas.draw()


def unpick_board(fig_axes):
    fig_axes.set_visible(False)


class AnimateShots(FuncAnimation, Frame):
    def __init__(self, fig, func, parent, frames=None, init_func=None, fargs=None,
                 save_count=None, mini=0, maxi=1, interval=500, **kwargs):

        FuncAnimation.__init__(self, self.fig, self.func, frames=self.play(),
                               init_func=init_func, fargs=fargs, interval=interval,
                               save_count=save_count, **kwargs)
        Frame.__init__(self, parent=None)

        self.i = 0
        self.min = mini
        self.max = maxi
        self.runs = True
        self.forwards = True
        self.fig = fig
        self.window = parent
        self.func = func
        self.setup()

    def play(self):
        while self.runs:
            self.i = self.i + self.forwards - (not self.forwards)
            if self.i > self.min & self.i < self.max:
                yield self.i
            else:
                self.stop()
                yield self.i

    def start(self):
        self.runs = True
        self.event_source.start()

    def stop(self):
        self.runs = False
        self.event_source.stop()

    def forward(self, event=None):
        self.forwards = True
        self.start()

    def backward(self, event=None):
        self.forwards = False
        self.start()

    def one_forward(self, event=None):
        self.forwards = True
        self.one_step()

    def one_backward(self, event=None):
        self.forwards = False
        self.one_step()

    def one_step(self):
        if self.min < self.i < self.max:
            self.i = self.i + self.forwards - (not self.forwards)
        elif self.i == self.min and self.forwards:
            self.i += 1
        elif self.i == self.max and not self.forwards:
            self.i -= 1
        self.func(self.i)
        self.fig.canvas.draw_idle()

    def setup(self):
        btn_one_up = Button(self.window, text='Step up', command=self.one_forward)
        btn_stop = Button(self.window, text='Stop', command=self.stop)
        btn_one_down = Button(self.window, text='Step down', command=self.one_backward)

        btn_one_up.grid(row=1, column=2)
        btn_stop.grid(row=1, column=1)
        btn_one_down.grid(row=1, column=0)


class ShotAnimator(TimedAnimation):
    def __init__(self, fig):
        self.boards_to_animate = dict()
        self.axes_to_animate = dict()
        self.line_of_axes = dict()
        self.shot_len = int()
        self.fig = fig

        self.board_names = dict()

        # Instance variables for stopping the animation
        self.pause = False
        self.stop_btn = object()
        self.step_up_dwn = object()
        self.display_state = StringVar()

        # Instance variable for stepping the animation
        # forward and backward
        self.frame_seq = object()
        self.current_frame = None

        TimedAnimation.__init__(self, self.fig, interval=1000, blit=False)

    def _stop(self, *args):
        self.event_source.stop()

    def _post_draw(self, framedata, blit=False):
        self.fig.canvas.draw_idle()

    def _draw_frame(self, framedata):
        shot = framedata
        self.current_frame = framedata
        self._drawn_artists = []
        self.boards_picked = list(self.boards_to_animate.keys())

        for board in self.boards_picked:
            x_data, y_data = wave_to_plot(self.boards_to_animate[board], shot)
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
        self.stop_btn.pack(side="right", anchor="e")

    def step_up_button(self, some_frame):
        step_up_btn = Button(some_frame, text="Forward",
                             command=lambda: self.forward())
        step_up_btn.pack(side="right", anchor="e")

    def step_dwn_button(self, some_frame):
        step_dwn_btn = Button(some_frame, text="Backward",
                              command=lambda: self.backward())
        step_dwn_btn.pack(side="right", anchor="e")

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
    """
    def __init__(self, collection=None):
        self.collection = None or collection
        self.index = 0

    def next(self):
        try:
            result = self.collection[self.index]
            self.index += 1
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
