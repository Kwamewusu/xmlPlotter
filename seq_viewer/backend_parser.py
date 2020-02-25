# Modules for text interpretation and math #
from re import search
from numpy import zeros

# Module for reading XML files #
from xml.etree.ElementTree import parse

# Load XML files #

# Function for picking XML file order


def xml_itemize(convention, text):
    # Regular expression for naming convention of shots
    # recorded by the scanner
    token: int = 0
    no_ext: int = 0
    pattern: str = ''

    if convention == 0:
        pattern = '\w+\.xml\.(\d+)'
        # Identify the time point of each shot/time-point recorded
        token = search(pattern, text)
    elif convention == 1:
        pattern = '\w+\.xml'
        # Identify the time point of each shot/time-point recorded
        token = search(pattern, text)
    elif convention == 2:
        no_ext: int = 1

    if token:
        return int(token.group(1))
    elif no_ext:
        return text
    else:
        raise UserWarning(
            'The naming convention must match the regular expression {0}'.format(pattern)
        )


def function(sorted_list):
    return sorted_list[0]


def xml_sort(order, file_list):
    idx_n_list = zip(order, file_list)
    sorted_list = [x for x in idx_n_list]

    sorted_list.sort(key=function)

    return list(sorted_list)


# Loading Files

def xml_root(xml_sets, shot_count):
    """ Input:
            - xml_sets: list of XML global addresses.
            - shot_count: file count representing the shots acquired.
        Output:
            - root: sequencer information for each shot. 
    """

    # Sequencer information can be learnt from the code below.
    # for child in root:
    #    print(child.tag, child.attrib)
    # "root" here is from having the ElementTree instance call
    # the getroot() function.

    # Placeholders for XML section headers (tree) and
    # the "Sequencer" section header (root) info.
    tree = []
    root = [[] for x in range(shot_count)]

    # Fill tree list with ElementTree objects which represent
    # section headers.
    for x, y in enumerate(xml_sets):
        tree.append(parse(y))

    # Fill root list with data for each Sequencer
    for i, j in enumerate(tree):
        root[i] = j.getroot()

    del tree

    return root


def extract_wfm(wave_objects, seq, shot_count):
    """ Input:
           - wave_objects: list of sequencer ElementTree objects for each
           time point.  
           - seq: sequencer name. 
           - shot_count: XML file count. 
        Output:
           - wave_to_plot: Numpy array with abscissa and range of a
           particular Sequencer for all time points.   
    """

    # Empty lists of the data points for each Sequencer.
    one_dim = [[] for x in range(shot_count)]
    two_dim = []

    # Use splitlines utility to interperate whitespace
    # notation in waveform values for a particular Sequencer.
    # Fill nested list with time/amplitude data for each time point.
    t = 0
    while t != shot_count:
        for x in wave_objects[t][seq][0].itertext():
            one_dim[t].append(x.splitlines())
        t += 1

        # Empty lists for time and amplitude of the Sequencer at
    # each time point.

    shot_len = 0
    t = 0
    while t != shot_count:
        # Find the max length of the lists
        for i in iter(one_dim[t][0]):
            two_dim.append(i.split(' '))

        next_shot_len = len(two_dim)

        if next_shot_len > shot_len:
            shot_len = next_shot_len

        two_dim.clear()
        t += 1

    wave_to_plot = zeros((shot_count, 2, shot_len - 1))

    # Use split utility to place time (abscissa) and amplitude
    # (range) values into separate rows for each time point.
    t = 0
    while t != shot_count:
        for x, y in enumerate(one_dim[t][0]):
            two_dim.append(y.split(' '))
        for x in range(1, len(two_dim)):
            wave_to_plot[t][0][x - 1] = float(two_dim[x][0])
            wave_to_plot[t][1][x - 1] = float(two_dim[x][1])
        two_dim.clear()
        t += 1

    del one_dim, two_dim

    return wave_to_plot
