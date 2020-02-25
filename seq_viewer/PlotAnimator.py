# Modules for GUI
from tkinter import Frame
from tkinter.ttk import Button

# Module for animation
from matplotlib.animation import FuncAnimation


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
