# Author: Nana K. Owusu
# This module coalesces the list of files in the user's chosen
# directory and processes the files.

# Module for storing integers
# during run-time
from tkinter import IntVar

# Modules for listing and
# filtering file names
from os import listdir
from fnmatch import filter

# Module for reading XML files
from xml.etree.ElementTree import parse
from backend_parser import xml_itemize, xml_sort


class GetXMLPath:
    """ Class for extracting and concatenating file names
    from the desired directory.
    """
    def __init__(self):
        self.xml_list = []

        # Create empty lists for file paths
        self.temp_list = []
        self.xml_files = []
        self.files_in_dir = []
        self.xml_full_path = []

        self.wont = IntVar()
        self.wont.set(0)
        self.stop_condition = IntVar()
        self.stop_condition.set(0)

        self.waveforms = []

    def get_xml_list(self, file):
        """ Accepts the file location and checks which naming
        convention is used for the XMLs. Stores naming convention
        and passes file contents to xml_paths()

        :param file: Full-path to the user's desired directory
        """
        self.xml_list.append(file)

        # provide the absolute path of the current directory
        file_loc = self.xml_list[0] + '/'
        # list all files in the XML directory
        dir_list = listdir(file_loc)

        # store only XML files
        if len(filter(dir_list, '*.xml*')) > 1:
            self.files_in_dir.append(filter(dir_list, '*.xml.*[^0-9]'))
            self.wont.set(0)
        elif len(filter(dir_list, '*.xml*')) == 1:
            self.files_in_dir.append(filter(dir_list, '*.xml*'))
            self.wont.set(1)
        elif len(filter(dir_list, '*')) > 0:
            self.wont.set(2)
            files = filter(dir_list, '*')
            for x in files:
                if parse(file_loc + x):
                    self.files_in_dir.append(x)
                else:
                    continue
        else:
            raise UserWarning('Found no XML files or the directory was empty.\n')

        self.xml_paths(self.files_in_dir, self.wont.get(), file)

    def xml_paths(self, chosen_dir, convention, root_dir):
        """ Called by get_xml_list(). Stores naming convention and sorted
        list of full-paths to the XML files in instance variables

        :param chosen_dir: List containing the XML files from the chosen
        directory
        :param convention: Integer identifying the naming convention for the
        files in the given directory
        :param root_dir: Full-path to the chosen directory
        """
        if convention == 2:
            for j, k in enumerate(chosen_dir):
                self.temp_list.append(xml_itemize(convention, k))
                self.xml_files.append(k)
        else:
            for j, k in enumerate(chosen_dir[0]):
                self.temp_list.append(xml_itemize(convention, k))
                self.xml_files.append(k)

        sorted_files = xml_sort(self.temp_list, self.xml_files)

        # Fill array with XML absolute paths.
        self.stop_condition = len(sorted_files)

        for count, file in sorted_files:
            # Array for the sorted abs. path for each XML file
            self.xml_full_path.append(root_dir + '/' + file)

        # Clear unused variables
        self.temp_list.clear()
        self.xml_files.clear()
