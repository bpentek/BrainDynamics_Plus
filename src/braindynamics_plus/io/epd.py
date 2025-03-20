from ..braindata import *
import numpy as np
import os

def _line_skip_read(file, skip_nr:int) -> str:
    skip_nr = max(0, skip_nr)
    for i in range(0, skip_nr):
        file.readline()
    return file.readline().replace('\n', '')

def load_epd_header(data:BrainData, epd_file_path:str) -> None:
    """ Load .epd header file only.

    Args:
        data: `braindynamics_plus.BrainData` instance used for storing brain activity recordings
        epd_file_path: path to .epd file

    Raises:
        ValueError: error occuring during .epd parsing; dimension mismatch between event timestamps & markers 
    """
    data.clear()
        
    data.info_dict["epd_dir"] = os.path.dirname(epd_file_path)

    EVENT_DTYPE = np.int32

    with open(epd_file_path, "r") as epd_file:
        try:
            data.info_dict["epd_ver"] = float(_line_skip_read(epd_file, 2))
            data.chan_nr = int(_line_skip_read(epd_file, 2))
            data.samp_freq = float(_line_skip_read(epd_file, 2))
            data.samp_nr = int(_line_skip_read(epd_file, 2))

            _line_skip_read(epd_file, 1)
            data.info_dict["chan_fnames"] = []
            for _ in range(data.chan_nr):
                data.info_dict["chan_fnames"].append(epd_file.readline().replace('\n', ''))

            if data.info_dict["epd_ver"] == 1.0:
                _line_skip_read(epd_file, 2)

            data.info_dict["event_time_fname"] = _line_skip_read(epd_file, 2)
            data.info_dict["event_code_fname"] = _line_skip_read(epd_file, 2)
            data.event_nr = int(_line_skip_read(epd_file, 2))

            _line_skip_read(epd_file, 1)
            data.info_dict["chan_name_list"] = []
            for _ in range(data.chan_nr):
                data.info_dict["chan_name_list"].append(epd_file.readline().replace('\n', ''))
        except:
            raise ValueError(f"Unable to parse EPD data from {epd_file_path}")
            
        try:
            data.event_time_arr = np.fromfile(os.path.join(data.info_dict["epd_dir"], data.info_dict["event_time_fname"]), dtype=EVENT_DTYPE, sep="")
            data.event_code_arr = np.fromfile(os.path.join(data.info_dict["epd_dir"], data.info_dict["event_code_fname"]), dtype=EVENT_DTYPE, sep="")
            if len(data.event_time_arr) != len(data.event_code_arr):
                raise ValueError(f"Dimension mismatch between array of event timestamps ({len(data.event_time_arr)}) and codes ({len(data.event_code_arr)})")
        except:
            raise ValueError(f"Unable to load event data")
            
def load_epd_samples(data:BrainData) -> None:
    """ Load samples based on .epd file.

    Args:
        data: `braindynamics_plus.BrainData` instance used for storing brain activity recording

    Raises:
        ValueError: error occurs during reading samples from binaries.
    """
    try:
        data.samp_mat = np.empty((data.chan_nr, data.samp_nr), dtype=SAMPLE_DTYPE)
        for i, chan_fname in enumerate(data.info_dict["chan_fnames"]):
            data.samp_mat[i, :] = np.fromfile(os.path.join(data.info_dict["epd_dir"], chan_fname), dtype=SAMPLE_DTYPE, sep="")
    except:
        raise ValueError("Unable to load sample data")

def load_epd(data:BrainData, epd_file_path:str) -> None:
    """ Loading .epd header and data (samples) as well.

    Args:
        data: `braindynamics_plus.BrainData` instance used for storing brain activity recording
        epd_file_path: path to .epd file
    """
    load_epd_header(data, epd_file_path)
    load_epd_samples(data)
