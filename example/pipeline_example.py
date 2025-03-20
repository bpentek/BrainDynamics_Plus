"""
    This is an example file on how BrainDynamics_Plus package can be integrated into the protocol.
    Full EEG samples are read from .epd file, and converted to TrialBrainData objects, based on the trial event markers given by the user.

    The idea behind this code is to run the pipeline for one subject, one part of the trial (e.g. before/after Stimulus) and for one SCA parameter, and use tools like GNU parallels to run for all combinations.
"""
import sys
import json
import os
import braindynamics_plus as bdp
import braindynamics_starprotocol as bd
import numpy as np

#####################################
# STEP 0: Reading input arguments
if len(sys.argv) != 3:
    print(f'USAGE: {sys.argv[0]} <subject name (str)> </path/to/config/file.cfg>')
    sys.exit(1)
SUBJECT_NAME = sys.argv[1] # name of the subject (usually corresponds to the .epd filename)
CONFIG_FILE_PATH = sys.argv[2] # path to a config file in .json format

#####################################
# STEP 1: Reading configuration file
with open(CONFIG_FILE_PATH, 'r') as FILE:
    CONFIG_DICT = json.load(FILE)
OUTPUT_ROOT = CONFIG_DICT['OUTPUT_ROOT'] # output root directory
## dataset infos
DATASET_ROOT = CONFIG_DICT['DATASET']['ROOT_DIR'] # root directory of dataset
TRIAL_NAME = CONFIG_DICT['DATASET']['TRIAL']['NAME'] # name of trial, can be used as output directory name as well
TRIAL_START_CODE = CONFIG_DICT['DATASET']['TRIAL']['START_CODE'] # event codes marking the start of the trial of interest (NOTE: usually a single value, but can be list as well)
TRIAL_END_CODE = CONFIG_DICT['DATASET']['TRIAL']['END_CODE'] # event codes marking the end of the trial of interest (NOTE: can be multiple values, e.g. different type of responses from the subject)
## SCA infos
SCA_SCALE_SIZE = CONFIG_DICT['SCA']['SCALE_SIZE_S'] # SCA scale size parameter IN SECONDS
SCA_SHIFT_SIZE = CONFIG_DICT['SCA']['MAX_SHIFT_S'] # SCA max shift size parameter IN SECONDS

#####################################
# STEP 2: Loading whole dataset
data = bdp.BrainData()
bdp.load_epd(data, os.path.join(DATASET_ROOT, SUBJECT_NAME, f'{SUBJECT_NAME}.epd'))
print('> Loading all of the samples from the experiment..\n\n', data, '\n')
# STEP 3: Extracting trial data from the whole dataset
trial_data = data.get_trial_brain_data(start_mark_list=TRIAL_START_CODE, end_mark_list=TRIAL_END_CODE)
print('> Extracting pre-defined trials based on event markers..\n\n', trial_data, '\n')
trial_samples = trial_data.samp_mat_list

## NOTE: additional event markers can be added to the whole dataset
##       for example, I need only 0.5 second after `TRIAL_START_CODE`
##       code would look like the following:
trial_start_indices = np.where(np.isin(data.event_code_arr, TRIAL_START_CODE))[0]
offset = int(0.5*data.samp_freq) # 0.5 seconds in sampling units
new_trial_end_code = [515] # give any value you want, just make sure it's not already used; it should be list remember!
if np.isin(new_trial_end_code, data.event_code_arr)[0]:
    raise Warning(f'Newly defined trial end code ({new_trial_end_code}) is already present in the original dataset!')
data.add_events(data.event_time_arr[trial_start_indices] + offset, np.full(len(trial_start_indices), new_trial_end_code, dtype=np.int32))
trial_data = data.get_trial_brain_data(start_mark_list=TRIAL_START_CODE, end_mark_list=new_trial_end_code)
print('> Adding new event markers to define trials..\n\n', trial_data, '\n')
trial_samples = trial_data.samp_mat_list
##        conclusion would be that event markers in the original data
##        can be extended easily in the BrainData object

#####################################
# STEP 4: Creating correlogram
corrgram = bd.CrossCorrelogram(int(SCA_SHIFT_SIZE*trial_data.samp_freq), scale_size=int(SCA_SCALE_SIZE*trial_data.samp_freq))

#####################################
# STEP 5: Extracting networks
networks = bd.NetworkData()
networks.extract(trial_samples, corrgram,
                 export_to_filelists=(os.path.join(OUTPUT_ROOT, "networks", TRIAL_NAME, "networks.filelist"),
                                      os.path.join(OUTPUT_ROOT, "lags", TRIAL_NAME, "lags.filelist"))
                 )

#####################################
# STEP 6: Calculate distribution of network properties

#  ... tutorial ends here :-)
# for more, refer to github.com/vlewir/BrainDynamics_STARProtocols
