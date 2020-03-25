# Author: Nana K. Owusu
# This script runs the application which is setup in the
# MainContainer class of the ViewerGUI module. The MainContainer
# class generates the tkinter window and contains the frame that
# houses the widgets with which the user will be interacting.

from ViewerGUI import MainContainer

if __name__ == '__main__':
    app = MainContainer()
    app.mainloop()
