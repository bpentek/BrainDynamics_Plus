import braindynamics_starprotocol as bd
import numpy as np
import os
import json
from ._trialdata import _TrialData
import mne

# CONSTANTS
SAMPLE_DTYPE = np.float32 # data type of samples
EVENT_DTYPE = np.int32 # data type of event timestamps & markers/codes

class BrainData:
    """ Abstract class for storing raw brain activity recordings.
    """

    def __init__(self):
        self.chan_nr = 0 # number of channels (variables, e.g. electrodes, ROIs)
        self.samp_nr = 0 # number of samples
        self.samp_freq = 0.0 # sampling frequency (in Hz!!)
        self.samp_mat = np.empty((self.chan_nr, self.samp_nr), dtype=SAMPLE_DTYPE) # matrix of samples
        self.event_nr = 0 # number of events
        self.event_code_arr = np.empty(self.event_nr, dtype=EVENT_DTYPE) # array of event codes/markers
        self.event_time_arr = np.empty(self.event_nr, dtype=EVENT_DTYPE) # array of event timestamps
        self.trial_nr = 0 # number of trials
        self.trial_list = list() # list of trials (_TrialData objects)
        self.info_dict = dict() # dictionary of other infos (metadata)

    def __str__(self)->str:
        return f"Brain activity recording of {self.samp_nr} from {self.chan_nr} channels and a {self.samp_freq}Hz sampling frequency."

    def clear(self):
        """ Function that clears all data.
        """
        self.chan_nr = 0
        self.samp_nr = 0
        self.samp_freq = 0.0
        self.samp_mat = np.empty((self.chan_nr, self.samp_nr), dtype=SAMPLE_DTYPE)
        self.event_nr = 0
        self.event_code_arr = np.empty(self.event_nr, dtype=EVENT_DTYPE)
        self.event_time_arr = np.empty(self.event_nr, dtype=EVENT_DTYPE)
        self.trial_nr = 0
        self.trial_list.clear()
        self.info_dict.clear()

    def add_events(self, event_time_arr:np.ndarray, event_code_arr:np.ndarray) -> None:
        """ Add new event markers to the data.

        Args:
            event_time_arr: array of new event marker timestamps
            event_code_arr: array of new event marker codes

        Raises:
            ValueError: dimension mismatch between timestamp and code arrays
        """
        if len(event_time_arr) != len(event_code_arr):
            raise ValueError(f"Dimension mismatch between array of event timestamps ({len(event_time_arr)}) and codes ({len(event_code_arr)})")
        
        self.event_time_arr = np.append(self.event_time_arr, event_time_arr)
        self.event_code_arr = np.append(self.event_code_arr, event_code_arr)
        self.event_time_arr, self.event_code_arr = zip(*sorted(zip(self.event_time_arr, self.event_code_arr)))
        self.event_nr = len(self.event_time_arr)

    def divide_into_trials(self, start_mark_list:list[int], end_mark_list:list[int]) -> None:
        """ Divide the experimental timeline into trials based on markers.

        Args:
            start_mark_list: list of codes marking start of trial
            end_mark_list: list of codes marking end of trial
        """
        self.trial_list.clear()
        self.trial_nr = 0
        trial = _TrialData()
        trial.clear()

        event_idx = 0
        while event_idx < self.event_nr:

            event_code = self.event_code_arr[event_idx]
            event_time = self.event_time_arr[event_idx]

            if event_code in start_mark_list:
                trial.clear()
                trial.insert_mark((event_time, event_code))
                prev_event_idx = event_idx - 1
                while prev_event_idx > -1 and self.event_time_arr[prev_event_idx] == event_time:
                    trial.insert_mark((self.event_time_arr[prev_event_idx], self.event_code_arr[prev_event_idx]))
                    prev_event_idx -= 1
            else:
                trial.insert_mark((event_time, event_code))

            if event_code in end_mark_list:
                prev_event_idx = event_idx + 1
                while prev_event_idx < self.event_nr and self.event_time_arr[prev_event_idx]  == event_time:
                    trial.insert_mark((self.event_time_arr[prev_event_idx], self.event_code_arr[prev_event_idx]))
                    event_idx = prev_event_idx
                    prev_event_idx += 1
                
                self.trial_nr += 1
                self.trial_list.append(trial)
                trial = _TrialData()

            event_idx += 1

    def get_trial_samples(self, start_mark_list:list[int]=None, end_mark_list:list[int]=None)->list:
        """ Fetch trial samples (from all the samples).

        Args:
            start_mark_list: event codes marking start of trial. Defaults to None, in which case it is assumed that trials were already divided.
            end_mark_list: event codes marking end of trial. Defaults to None, in which case it is assumed that trials were already divided.
 
        Returns:
            list of numpy arrays representing trial samples
       
        Raises:
            ValueError: no marker lists provided and also not divided into trials prior.
        """
        if start_mark_list is not None and end_mark_list is not None:
            self.divide_into_trials(start_mark_list, end_mark_list)

        if self.trial_nr == 0 or len(self.trial_list) == 0:
            raise ValueError('Make sure to either divide into trials before or provide trial marker lists.')

        trial_samp_list = [] # using list for uneven trial lengths
    
        for trial_idx in range(self.trial_nr):
            start_time = self.trial_list[trial_idx].start_time
            end_time = self.trial_list[trial_idx].end_time
            trial_samp_list.append(self.samp_mat[:, start_time:end_time]) # NOTE: end_time or end_time + 1??!

        return trial_samp_list
    
    def get_event_samples(self, event_code:EVENT_DTYPE, window_len:EVENT_DTYPE)->list:
        """ Get samples around a specific event in the experiment.

        Args:
            event_code: code of the event of interesnt
            window_len: length of the time window relative to the event (can be negative as well to get samples before and event).

        Returns:
            list of numpy arrays representing samples around the given event
        """
        event_timestamps = self.event_time_arr[np.where(self.event_code_arr == event_code)[0]]

        event_samp_list = []

        if window_len < 0:
            for event_idx, event_timestamps in enumerate(event_timestamps):
                start_time = event_timestamps + window_len
                end_time = event_timestamps
                event_samp_list.append(self.samp_mat[:, start_time:end_time])
        else:
            for event_idx, event_timestamps in enumerate(event_timestamps):
                start_time = event_timestamps
                end_time = event_timestamps + window_len
                event_samp_list.append(self.samp_mat[:, start_time:end_time])

        return event_samp_list
        
    def get_trial_brain_data(self, start_mark_list:list[int]=None, end_mark_list:list[int]=None)->bd.TrialBrainData:
        """ Get `braindynamics_starprotocol.BrainData` instance based on defined trials.

        Args:
            start_mark_list: event codes marking start of trial. Defaults to None, in which case it is assumed that trials were already divided.
            end_mark_list: event codes marking end of trial. Defaults to None, in which case it is assumed that trials were already divided.
         
        Returns:
            `braindynamics_starprotocl.BrainData` instance storing trial samples & infos.

        Raises:
            ValueError: no marker lists provided and also not divided into trials prior.
        """
        samp_mat_list = self.get_trial_samples(start_mark_list=start_mark_list, end_mark_list=end_mark_list)
        trialbraindata = bd.TrialBrainData()
        if self.info_dict is None:
            info_dict = None
        else:
            info_dict = self.info_dict
        trialbraindata.load(samp_mat_list, self.samp_freq, info_dict=info_dict)
        return trialbraindata

    def set_event_descriptions(self, event_desc_dict:dict)->None:
        """ Set description of event codes.

        Args:
            event_desc_dict: dictionary with keys being event codes, and the values their description,
        """
        self.info["event_description_dict"] = event_desc_dict

    def convert_to_mne_raw(self, unit:float=1.0e-6):
        """ Convert data to the MNE Raw format

        Args:
            unit: voltage unit multiplier

        Returns:
            MNE Raw instance of the samples.

        Raises:
            ValueError: error occuring, mostly due to insufficient data.
            Warning: event descriptions not set
        """
        if self.samp_nr == 0 or self.chan_nr == 0:
            raise ValueError("EEG data not loaded, no samples/channels were found.")

        if "chan_name_list" not in self.info_dict:
            raise ValueError("Please load channel names into BrainData.info_dict['chan_name_list'].")

        if len(self.info_dict["chan_name_list"]) != self.chan_nr:
            raise ValueError("Make sure that all loaded channels have their name in the info dict.")

        info = mne.create_info(ch_names=self.info_dict["chan_name_list"], sfreq=self.samp_freq, ch_types="eeg")
        raw = mne.io.RawArray(unit*self.samp_mat, info)
        if self.event_nr > 0:
 
            events = np.column_stack((self.event_time_arr, np.zeros(self.event_nr, EVENT_DTYPE), self.event_code_arr))
            unique_events = np.unique(self.event_code_arr)

            info = mne.create_info(ch_names=["STI 014"], sfreq=self.samp_freq, ch_types=["stim"])
            stim_raw = mne.io.RawArray(np.zeros((1, len(raw.times)), dtype=int), info)
            raw.add_channels([stim_raw], force_update_info=True)

            if "event_description_dict" in self.info_dict:
                if len(self.info_dict["event_description_dict"]) < len(unique_events):
                    raise ValueError("Make sure that all loaded events have their name/description set in the info dict.")
            else:
                raise Warning("Event descriptions not found. Resulting to default names for events (string versions of the codes)")
            
            raw.add_events(events, stim_channel="STI 014")

        return raw


