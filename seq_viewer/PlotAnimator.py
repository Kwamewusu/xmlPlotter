# Modules for GUI
from tkinter import Frame
from tkinter.ttk import Button

# Modules for extracting waveforms
from backend_exciters import ssp_end_time, extract_wfm, scale_time, \
    wave_truncate

# Module for animation
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


def wave_to_plot(wave, t):
    x = wave[t, 0, :]
    y = wave[t, 1, :]

    return x, y


def board_waveform(waveforms, board_num, shot):
    ssp_endings = ssp_end_time(waveforms, shot)
    wave_store = extract_wfm(waveforms, board_num, shot)

    wave, idx_to_cut = scale_time(wave_store, ssp_endings, shot)

    xtr = wave_truncate(wave, idx_to_cut, shot)

    x_val, y_val = wave_to_plot(xtr, shot)

    return x_val, y_val


def setup_axes(app_fig):
    fig_axes = (app_fig.add_subplot(1, 8, i+1) for i in range(8))

    yield fig_axes


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
