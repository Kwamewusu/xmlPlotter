# Module for math #
from numpy import zeros, delete

# Module for extracting shots #
from backend_parser import extract_wfm


# Procedures for extracting exciter waveforms #

def ssp_end_time(wave_objects, shot_count):
    """ Input:
            - wave_objects: list of sequencer ElementTree objects for each time point.
            - shot_count: XML file count.
        Output:
            - last_time: list of first time points > the stop time for each time point.
    """

    # Waveform of the SSP board
    ssp_wave = extract_wfm(wave_objects, 0, shot_count)

    # Empty list for true final time points
    last_time = []

    for t in range(0, shot_count):

        # copy SSP waveform for each time point
        iter_time = ssp_wave[t][0][:].copy()

        # last time point for the sequencer
        # corresponding to the repetition time
        time_stamp: object = ssp_wave[t][0][-1]

        # take the 2nd through 5th to last time point
        # and iterate over them for comparison
        for i, time in enumerate(iter_time.flat[-2:-6:-1]):
            if (time < time_stamp) & ((time_stamp % time) > 1.0):
                last_time.append(time)
            else:
                continue

            time_stamp = time

    return last_time


def scale_time(wave, ssp_ending, shot_count):
    """ Input:
            - wave: waveform of a sequencer.
            - ssp_ending: vector of repetition times (TR) across shots from
            the SSP board.
            - shot_count: XML file count.
        Output:
            - modified_wave: waveform of a sequencer with end time points
            matching that of the SSP board.
            - idx_to_cut: count of the number of indices greater than the TR
            with the least number of significant figures.
    """

    # Length of the input waveform
    wave_len = len(wave[0][0][:])

    # Placeholder for index of time values >= the repetition time the
    # least number of significant figures.
    idx_to_cut = int()

    # Count and store the number of time values >= the repetition
    # time with the least number of sig. figs. This code assumes
    # the count is consistant across time.
    for t in range(0, shot_count):

        # copy waveform for each time point
        iter_time = wave[t][0][:].copy()

        # last time point for the sequencer (TR)
        time_stamp = wave[t][0][-1]
        count: int = 0

        # take the 2nd through 5th to last time point
        # and iterate over them for comparison
        for i, time in enumerate(iter_time.flat[-2:-6:-1]):
            if (time < time_stamp) & ((time_stamp % time) > 1.0):

                # replace the first time point most different
                # from the subsequent one with another.
                wave[t][0][wave_len - 1 - i] = ssp_ending[t]
                break
            else:

                # add to count if the present time point is
                # not much different from the one before
                count = count + 1

            time_stamp = time

        idx_to_cut = count

    modified_wave = wave.copy()

    del wave_len, time_stamp, iter_time

    return modified_wave, idx_to_cut


def wave_truncate(wave, cols_to_cut, shot_count):
    """ Input:
            - wave: waveform of a sequencer.
            - cols_to_cut: number of time values >= the repetition time with
            the least number of significant figures.
            - shot_count: XML file count.
        Output:
            - short_wave: truncated waveform of a sequencer.
    """

    # length of input waveform
    wave_len = len(wave[0][0][:])

    # Empty Numpy array for shortened input waveform
    short_wave = zeros((shot_count, 2, wave_len - cols_to_cut))

    for t in range(0, shot_count):
        short_wave[t] = delete(wave[t], range(wave_len - cols_to_cut, wave_len), axis=1)

    return short_wave
