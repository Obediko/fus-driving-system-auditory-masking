# -*- coding: utf-8 -*-
"""
Copyright (c) 2024 Margely Cornelissen, Stein Fekkes (Radboud University) and Erik Dumont (Image
Guided Therapy)

MIT License

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

**Attribution Notice**:
If you use this kit in your research or project, please refer to the 'How to Cite' section in the
README.md file of https://github.com/Donders-Institute/Radboud-FUS-driving-system-software.
"""

# IGT example
# Note: you can click on each parameter to get more information


##############################################################################
# initialize logging.
##############################################################################

from fus_driving_systems.config.config import config_info as config

from fus_driving_systems.config.logging_config import initialize_logger

log_dir = "C://Temp"
filename = "standalone_igt_pmErC"
logger = initialize_logger(log_dir, filename)

# When this code is embedded in other code with logging, ignore above commands and sync the logger
# in the following way:

# from fus_driving_systems.config.logging_config import sync_logger
# sync_logger(logger)  # logger needs to be created with logging.getLogger()

##############################################################################
# import the 'fus_driving_systems - sequence' into your code
##############################################################################

import os
import sys
from pathlib import Path

from fus_driving_systems import driving_system, transducer
from fus_driving_systems import sequence
from fus_driving_systems.auditory_masking import (
    MaskedIGTSession,
    MaskingConfig,
    generate_mask,
    save_mask,
)
from fus_driving_systems.utils import get_config_value

# pmErC protocol parameters (shown individually in Spyder's Variable Explorer)
DRIVING_SYSTEM = 'IGT-32-ch_comb_1x10-ch_DORTMUND'
USE_TWO_TRANSDUCERS = False
TRANSDUCER = 'IS_PCD15287_01005'
OPERATING_FREQUENCY_KHZ = 300
FOCUS_WRT_EXIT_PLANE_MM = 80.6
PRESSURE_MPA = 1.09
PULSE_DURATION_MS = 20
PULSE_REPETITION_INTERVAL_MS = 200
PULSE_OFF_TIME_MS = PULSE_REPETITION_INTERVAL_MS - PULSE_DURATION_MS
PULSE_RAMP_SHAPE = 'Rectangular - no ramping'
PULSE_RAMP_DURATION_MS = 0
PULSE_TRAIN_DURATION_MS = 200
WAIT_FOR_TRIGGER = False
TRIGGER_OPTION = 'TriggerSequence'
PULSE_TRAIN_REPETITION_INTERVAL_MS = 200
SESSION_DURATION_S = 90
PULSE_REPETITION_FREQUENCY_HZ = 1000 / PULSE_REPETITION_INTERVAL_MS
DUTY_CYCLE = PULSE_DURATION_MS / PULSE_REPETITION_INTERVAL_MS
TOTAL_PULSES = int(SESSION_DURATION_S * PULSE_REPETITION_FREQUENCY_HZ)

# Auditory masking and allocation controls. Keep the default as sham until the
# complete headphone and IGT workflow has been approved for human use.
# Active and sham MUST use the same masking configuration and random seed.
SESSION_CONDITION = os.environ.get('FUS_SESSION_CONDITION', 'sham').strip().lower()
MASKING_CONFIG_PATH = Path(__file__).with_name('masking_config_pmErC.json')
MASKING_OUTPUT_DIRECTORY = Path(log_dir) / 'pmErC_auditory_masking'
SAVE_FROZEN_MASK = True

##############################################################################
# create a sequence for an IGT driving system
# a sequence can be created in advance and a new sequence can be defined
# later on in the code
##############################################################################

seq1 = sequence.Sequence()

# Number of sequence starting at zero. Currently only used to differentiate and send multiple
# sequences to the IGT system. Only 0 and 1 are possible. Don't change this value if you only
# using one sequence definition.
seq1.seq_num = 0

# equipment
# to check available driving systems: print(driving_system.get_ds_serials())
# choose one driving system from that list as input
seq1.driving_sys = DRIVING_SYSTEM
use_two_transducers = USE_TWO_TRANSDUCERS  # true for simultaneous or interleaved transducers

# to check available transducers: print(transducer.get_tran_serials())
# choose one transducer from that list as input
seq1.transducer = TRANSDUCER

# set general parameters
seq1.oper_freq = OPERATING_FREQUENCY_KHZ  # [kHz], operating frequency

# NOTE: Due to compensation equations, the focus has to be set first when using amplitude or
# voltage as power input.
seq1.focus_wrt_exit_plane = FOCUS_WRT_EXIT_PLANE_MM  # [mm], w.r.t. exit plane and FWHM middle
# seq1.focus_wrt_mid_bowl = 69.1  # [mm], focal depth w.r.t. the radiating surface and FWHM middle

# Degree used to dephase every nth elemen based on chosen degree. None = no dephasing
# One value (>0) is the degree of dephasing, for example [90] with 4 elements: 1 elem: 0 dephasing,
# 2 elem: 90 dephasing, 3 elem: 180 dephasing, 4 elem: 270 dephasing.
# When the amount of values match the amount of elements, it will override the calculated phases
# based on the set focus.
seq1.dephasing_degree = None  # [degrees]: None, [120] or [0, 135, 239, 90]

# Set maximum pressure in free water [MPa]. NOTE: DIFFERENT THAN SC
seq1.press = PRESSURE_MPA  # [MPa], maximum pressure in free water (40 W/cm2 protocol setting)

seq2 = None  # seq2 is None of a second transducer isn't used
if use_two_transducers:
    seq2 = sequence.Sequence()

    seq2.driving_sys = seq1.driving_sys.serial

    # to check available transducers: print(transducer.get_tran_serials())
    # choose one transducer from that list as input
    seq2.transducer = 'IS_PCD15287_01002'

    # Check if available channels is equal to the number of elements of the transducers combined
    n_comb_elem = seq1.transducer.elements + seq2.transducer.elements
    if seq1.driving_sys.available_ch != n_comb_elem:
        logger.error(f'Number of available channels ({seq1.driving_sys.available_ch}) is not ' +
                     f'equal to the number of elements of the transducers combined ({n_comb_elem}' +
                     f'). Equipment configuration {seq1.driving_sys.name} - ' +
                     f'{seq1.transducer.name} & {seq2.transducer.name} does ' +
                     'not seem to be compatible or use_two_transducers is incorrectly True.')
        sys.exit()

    # set general parameters
    seq2.oper_freq = 300  # [kHz], operating frequency

    # NOTE: Due to compensation equations, the focus has to be set first when using amplitude or
    # voltage as power input.
    seq2.focus_wrt_exit_plane = 80  # [mm], focal depth w.r.t. the exit plane and FWHM middle
    # seq2.focus_wrt_mid_bowl = 69.1  # [mm], focal depth w.r.t. the radiating surface and FWHM middle

    # Degree used to dephase every nth elemen based on chosen degree. None = no dephasing
    # One value (>0) is the degree of dephasing, for example [90] with 4 elements: 1 elem: 0
    # dephasing. 2 elem: 90 dephasing, 3 elem: 180 dephasing, 4 elem: 270 dephasing.
    # When the amount of values match the amount of elements, it will override the calculated phases
    # based on the set focus.
    seq2.dephasing_degree = None  # [degrees]: None, [120] or [0, 135, 239, 90]

    # Set maximum pressure in free water [MPa]. NOTE: DIFFERENT THAN SC
    seq2.press = 0.3  # [MPa], maximum pressure in free water

# Check if available channels is equal to the number of elements of the transducer
elif seq1.driving_sys.available_ch != seq1.transducer.elements:
    logger.error(f'Number of available channels ({seq1.driving_sys.available_ch}) is not equal to' +
                 f' the number of elements of the transducer ({seq1.transducer.elements}). ' +
                 f'Equipment configuration {seq1.driving_sys.name} - {seq1.transducer.name} does ' +
                 'not seem to be compatible or use_two_transducers is incorrectly False.')
    sys.exit()

# # timing parameters # #
# you can use the TUS Calculator to visualize the timing parameters:
# https://www.socsci.ru.nl/fusinitiative/tuscalculator/

# ## pulse ## #
seq1.pulse_dur = PULSE_DURATION_MS  # [ms], pulse duration
seq1.pulse_rep_int = PULSE_REPETITION_INTERVAL_MS  # [ms], pulse repetition interval

# pulse ramping
# to check available ramp shapes: print(seq1.get_ramp_shapes())
# choose one ramp shape from that list as input
seq1.pulse_ramp_shape = PULSE_RAMP_SHAPE

# ramping up and ramping down duration are equal and are equal to ramp duration
seq1.pulse_ramp_dur = PULSE_RAMP_DURATION_MS  # [ms], ramp duration

# ## pulse train ## #
# if you only want one pulse train, keep the values equal to the pulse repetition interval
seq1.pulse_train_dur = PULSE_TRAIN_DURATION_MS  # [ms], pulse train duration

# set wait_for_trigger to true if you want to use trigger
seq1.wait_for_trigger = WAIT_FOR_TRIGGER

# When you only want to trigger a pulse train repetition once: 'TriggerOnePulseTrainRepetition'
# Multiple times triggering a pulse train repetition isn't supported.
# to check available trigger options: print(seq1.get_trigger_options())
seq1.trigger_option = TRIGGER_OPTION
if seq1.wait_for_trigger and seq1.trigger_option == get_config_value(logger, config, 'Trigger',
                                                                     'option.seq',
                                                                     'TriggerSequence'):
    seq1.n_triggers = 4  # number of timings above defined sequence will be triggered

else:
    seq1.pulse_train_rep_int = PULSE_TRAIN_REPETITION_INTERVAL_MS  # [ms], NOTE: DIFFERENT THAN SC

    # ## pulse train repetition ## #
    # if you only want one pulse train, keep the value equal to the pulse repetition interval
    # if you only want one pulse train repetition block, keep the value equal to the pulse train
    # repetition interval
    seq1.pulse_train_rep_dur = SESSION_DURATION_S  # [s], NOTE: DIFFERENT THAN SC

# to get a summary of your entered sequence: print(seq1)

##############################################################################
# connect with driving system and execute sequence
##############################################################################

# creating an IGT driving system instance, connecting to it and sending your first sequence can be
# done when initializing your experiment. When appropriate, execute your sequence by implementing
# 'execute_sequence()' into your code or by using the external trigger.

# when you want to change your sequence in the middle of your experimental code, create a new
# sequence as above and send the new sequence: 'send_sequence()'. When appropriate, execute your
# sequence by implementing 'execute_sequence()' into your code or by using the external trigger.

##############################################################################
# import the 'fus_driving_systems - ds' into your code
##############################################################################

from fus_driving_systems.igt import igt_ds

if SESSION_CONDITION not in ('active', 'sham'):
    raise ValueError("SESSION_CONDITION must be 'active' or 'sham'.")

masking_config = MaskingConfig.from_json(MASKING_CONFIG_PATH)
if abs(masking_config.stimulation_duration_s - SESSION_DURATION_S) > 1e-9:
    raise ValueError('Mask duration does not match the IGT stimulation duration.')
if abs(masking_config.pulse_repetition_frequency_hz - PULSE_REPETITION_FREQUENCY_HZ) > 1e-9:
    raise ValueError('Mask PRF does not match the IGT pulse repetition frequency.')
if abs(masking_config.pulse_duration_ms - PULSE_DURATION_MS) > 1e-9:
    raise ValueError('Mask pulse duration does not match the IGT pulse duration.')
if abs(masking_config.ultrasound_frequency_khz - OPERATING_FREQUENCY_KHZ) > 1e-9:
    raise ValueError('Mask metadata does not match the IGT operating frequency.')
if masking_config.enabled and not masking_config.headphones_calibrated:
    raise RuntimeError(
        'Test and calibrate the headphones first, then set '
        'headphones_calibrated=true in masking_config_pmErC.json.'
    )
if seq1.wait_for_trigger and masking_config.enabled:
    raise RuntimeError(
        'Software-synchronized masking does not support an uncontrolled external trigger.'
    )

generated_mask = generate_mask(masking_config) if masking_config.enabled else None
if SAVE_FROZEN_MASK and generated_mask is not None:
    frozen_mask_path, frozen_metadata_path = save_mask(
        generated_mask,
        MASKING_OUTPUT_DIRECTORY / 'pmErC_5Hz_20ms_90s_frozen_mask.wav',
    )
    logger.info('Frozen auditory mask: %s', frozen_mask_path)
    logger.info('Auditory mask metadata: %s', frozen_metadata_path)

masking_session = MaskedIGTSession(
    masking_config,
    log_path=MASKING_OUTPUT_DIRECTORY / 'pmErC_masking_events.jsonl',
    logger=logger,
)

igt_driving_sys = None
try:
    if SESSION_CONDITION == 'active':
        igt_driving_sys = igt_ds.IGT(log_dir)
        igt_driving_sys.connect(seq1.driving_sys.connect_info, log_dir, filename)
        igt_driving_sys.send_sequence(seq1, seq2)

    # The active condition calls execute_sequence exactly once after mask onset.
    # The sham condition never connects to or energizes the IGT generator.
    session_result = masking_session.run(
        igt_driving_sys,
        seq1,
        seq2,
        condition=SESSION_CONDITION,
        mask=generated_mask,
    )
    logger.info(
        'Masked session completed: %s pulses, mask SHA-256 %s',
        session_result.expected_pulses,
        session_result.audio_sha256,
    )
finally:
    if igt_driving_sys is not None and not seq1.wait_for_trigger:
        igt_driving_sys.disconnect()
