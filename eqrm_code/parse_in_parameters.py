#!/usr/bin/python
"""
  Author:  Duncan Gray, duncan.gray@ga.gov.au

  Description: This module reads in the EQRM control file which
  describes the settings of a simulation.  The control file is a
  python file, so vectors can be passed in easily and if necessary a
  scripting language can be used.

  For verification purposes the settings are read and added to a
  dictionary (eqrm_flags), rather than just being used as is.

  Notes on the EQRM control file format.

  All attributes are specified in CONV_DIC_NEW.

  If an attribute is not present in the set_data.py file and the
  attribute has a default value, this value will be used in eqrm_flags.

  Setting an attribute to None is not equivaluent to removing the
  attribute from the set_data.py file, since not all attributes default
  to None.

  If an attribute does not have to be defined it is given a default
  value of None.  An attribute without a default has to be defined.

  Lists are automatically converted to arrays.

  Copyright 2007 by Geoscience Australia
 """

import sys
import os
import socket
import imp
import base64
from os.path import join
from time import strftime, localtime
from scipy import allclose, array, sort, asarray, ndarray
import copy
try:
    from eqrm_code.ANUGA_utilities import log
    log_imported = True
except ImportError:
    log_imported = False

try:
    from eqrm_code.util import convert_path_string_to_join
except ImportError:
    def convert_path_string_to_join(path):
        """
        This is to modify python scripts, changing r"./foo/bar" to
        'join('.','foo','bar')'

        Args:
        path: The string value to change to a join

        Returns:
        A join statement, as a string.
        """

        seps = ['/', '\\']
        out = multi_split(path, seps)
        out = [x for x in out if x != '']
        out = "', '".join(out)
        out = "join('" + out + "')"
        return out

    def multi_split(split_this, seps):
        """
        Split a string based on multiple seperators.

        Args:
          split_this: the string to split.
          seps: A list of seperators.

        Returns:
          A list of strings.
        """
        results = [split_this]
        for seperator in seps:
            so_far, results = results, []
            for seq in so_far:
                results += seq.split(seperator)
        return results

from eqrm_code import file_store

ENV_EQRMDATAHOME = 'EQRMDATAHOME'
VAR_NAME_IN_SET_DATA_FILE = 'sdp'
SECOND_LINE = '  EQRM parameter file'

# A list of parameter names and title names.
#
# Originally used to convert old attribute values, to the new
# attribute values.  Now it is used to describe the attributes default
# values and describing how to print out the attributes.
# new_para - the attribute name
# order - The order in which an EQRM control file is automatically generated.
#         Lower numbers printed first.
# values - Obsolete. Used to convert from the old style to the new.
# default - default value if not set
# default_to_attr - default to another parameter in this list. The parameter
# must be defined in an item in a lower order in the list.

CONV_NEW = [{'order': 10.0,
             'title': '\n# Operation Mode\n'},
            {'old_para': 'run_type',
             'values': {None: None,
                        1: 'hazard',
                        2: 'risk_csm',
                        3: 'fatality',
                        4: 'bridge',
                        5: 'risk_mmi'},
             'order': 10.01,
             'new_para': 'run_type'},
            {'old_para': 'determ_flag',
             'values': {None: None,
                        1: True,
                        0: False},
             'order': 10.02,
             'new_para': 'is_scenario'},
            {'old_para': 'reset_seed_using_time',
             'order': 10.05,
             'new_para': 'reset_seed_using_time',
             'default': True},
            {'old_para': 'compress_output',
             'order': 10.06,
             'new_para': 'compress_output',
             'default': False},
            {'old_para': 'site_loc',
             'order': 10.07,
             'new_para': 'site_tag'},
            {'old_para': 'site_db_tag',
             'order': 10.08,
             'new_para': 'site_db_tag',
             'default': ""},
            {'old_para': 'rtrn_per',
             'order': 10.10,
             'new_para': 'return_periods'},
            {'old_para': 'inputdir',
             'order': 10.11,
             'new_para': 'input_dir'},
            {'old_para': 'savedir',
             'order': 10.12,
             'new_para': 'output_dir'},
            {'old_para': 'small_site_flag',
             'values': {None: None,
                        1: True,
                        0: False},
             'order': 10.13,
             'new_para': 'use_site_indexes',
             'default': False},
            {'old_para': 'SiteInd',
             'order': 10.14,
             'new_para': 'site_indexes',
             'default': None},
            {'old_para': 'fault_source_tag',
             'order': 10.15,
             'new_para': 'fault_source_tag',
             'default': None},
            {'old_para': 'zone_source_tag',
             'order': 10.16,
             'new_para': 'zone_source_tag',
             'default': None},
            {'old_para': 'event_control_tag',
             'order': 10.17,
             'new_para': 'event_control_tag',
             'default': None},
            {'order': 30.0,
             'title': '\n# Scenario input\n'},
            {'old_para': 'determ_azi',
             'order': 30.02,
             'new_para': 'scenario_azimuth',
             'default': None},
            {'old_para': 'determ_r_z',
             'order': 30.03,
             'new_para': 'scenario_depth',
             'default': None},
            {'old_para': 'determ_lat',
             'order': 30.04,
             'new_para': 'scenario_latitude',
             'default': None},
            {'old_para': 'determ_lon',
             'order': 30.05,
             'new_para': 'scenario_longitude',
             'default': None},
            {'old_para': 'determ_mag',
             'order': 30.06,
             'new_para': 'scenario_magnitude',
             'default': None},
            {'order': 30.07,
             'new_para': 'scenario_dip',
             'default': None},
            {'old_para': 'determ_ntrg',
             'order': 30.08,
             'new_para': 'scenario_number_of_events',
             'default': None},
            {'order': 30.09,
             'new_para': 'scenario_width',
             'default': None},
            {'order': 30.10,
             'new_para': 'scenario_length',
             'default': None},
            {'order': 30.11,
             'new_para': 'scenario_max_width',
             'default': None},
            {'order': 40.0,
             'title': '\n# Probabilistic input\n'},
            {'old_para': 'azi',
             'order': 40.01,
             'new_para': 'prob_azimuth_in_zones',
             'default': None},
            {'old_para': 'd_azi',
             'order': 40.015,
             'new_para': 'prob_delta_azimuth_in_zones',
             'default': None},
            {'old_para': 'min_mag_cutoff',
             'order': 40.02,
             'new_para': 'prob_min_mag_cutoff',
             'default': None},
            {'old_para': 'nbins',
             'order': 40.03,
             'new_para': 'prob_number_of_mag_sample_bins',
             'default': None},
            {'old_para': 'ntrgvector',
             'order': 40.05,
             'new_para': 'prob_number_of_events_in_zones',
             'default': None},
            {'order': 10.18,
             'new_para': 'prob_number_of_events_in_faults',
             'default': None},
            {'old_para': 'dip',
             'order': 40.07,
             'new_para': 'prob_dip_in_zones',
             'default': None},
            {'order': 50.0,
             'title': '\n# Attenuation\n'},
            {'order': 50.01,
             'new_para': 'atten_models',
             'default': None},
            {'order': 50.02,
             'new_para': 'atten_model_weights',
             'default': None},
            {'order': 50.03,
             'new_para': 'atten_collapse_Sa_of_atten_models',
             'default': False},
            {'old_para': 'var_attn_method',
             'order': 50.05,
             'new_para': 'atten_variability_method',
             'default': 2},
            {'old_para': 'periods',
             'order': 50.06,
             'new_para': 'atten_periods'},
            {'old_para': 'Rthrsh',
             'order': 50.07,
             'new_para': 'atten_threshold_distance',
             'default': 400},
            {'order': 50.08,
             'new_para': 'atten_spawn_bins',
             'default': 1},  # Needed to get array dimensions right.
            {'old_para': 'resp_crv_flag',
             'values': {0: None,
                        2: 'Aust_standard_Sa',
                        4: 'HAZUS_Sa'},
             'order': 50.09,
             'new_para': 'atten_override_RSA_shape',
             'default': None,
             'run_type': ['risk_csm']},
            {'order': 50.10,
             'new_para': 'atten_cutoff_max_spectral_displacement',
             'default': False,
             'run_type': ['risk_csm']},
            {'old_para': 'pgacutoff',
             'order': 50.11,
             'new_para': 'atten_pga_scaling_cutoff',
             'default': 2},
            {'old_para': 'smoothed_response_flag',
             'values': {None: None,
                        1: True,
                        0: False},
             'order': 50.12,
             'new_para': 'atten_smooth_spectral_acceleration',
             'default': False},
            {'old_para': 'log_sigma_eq_weight',
             'order': 50.13,
             'new_para': 'atten_log_sigma_eq_weight',
             'default': 0},
            {'order': 60.0,
             'title': '\n# Amplification\n'},
            {'old_para': 'amp_switch',
             'values': {None: None,
                        1: True,
                        0: False},
             'order': 60.01,
             'new_para': 'use_amplification'},
            {'old_para': 'var_amp_method',
             'order': 60.03,
             'new_para': 'amp_variability_method',
             'default': 2},
            {'old_para': 'MinAmpFactor',
             'order': 60.04,
             'new_para': 'amp_min_factor',
             'default': None},
            {'old_para': 'MaxAmpFactor',
             'order': 60.05,
             'new_para': 'amp_max_factor',
             'default': None},
            {'order': 70.0,
             'title': '\n# Buildings\n'},
            {'old_para': 'b_usage_type_flag',
             'values': {None: None,
                        1: 'HAZUS',
                        2: 'FCB'},
             'order': 70.01,
             'new_para': 'buildings_usage_classification',
             'default': None,
             'run_type': ['risk_csm', 'risk_mmi']},
            {'old_para': 'hazus_dampingis5_flag',
             'values': {None: None,
                        1: True,
                        0: False},
             'order': 70.02,
             'new_para': 'buildings_set_damping_Be_to_5_percent',
             'default': None,
             'run_type': ['risk_csm']},
            {
                'order': 75.01,
                'new_para': 'bridges_functional_percentages',
                'default': None,
                'run_type': ['bridge']},
            {'order': 80.0,
             'title': '\n# Capacity Spectrum Method\n'},
            {'old_para': 'var_bcap_flag',
             'values': {None: None,
                        1: True,
                        0: False},
             'order': 80.01,
             'new_para': 'csm_use_variability',
             'default': None,
             'run_type': ['risk_csm']},
            {'old_para': 'bcap_var_method',
             'order': 80.02,
             'new_para': 'csm_variability_method',
             'default': 3,
             'run_type': ['risk_csm']},
            {'old_para': 'stdcap',
             'order': 80.03,
             'new_para': 'csm_standard_deviation',
             'default': None,
             'run_type': ['risk_csm']},
            {'order': 80.04,
             'new_para': 'csm_damping_regimes',
             'default': None,
             'run_type': ['risk_csm']},
            {'order': 80.05,
             'new_para': 'csm_damping_modify_Tav',
             'default': None,
             'run_type': ['risk_csm']},
            {'order': 80.06,
             'new_para': 'csm_damping_use_smoothing',
             'default': None,
             'run_type': ['risk_csm']},
            {'old_para': 'Harea_flag',
             'values': {None: None,
                        1: 'Error',
                        2: 'trapezoidal',
                        3: 'curve'},
             'order': 80.08,
             'new_para': 'csm_hysteretic_damping',
             'default': None,
             'run_type': ['risk_csm']},
            {'old_para': 'SDRelTol',
             'order': 80.09,
             'new_para': 'csm_SDcr_tolerance_percentage',
             'default': None,
             'run_type': ['risk_csm']},
            {'old_para': 'max_iterations',
             'order': 80.10,
             'new_para': 'csm_damping_max_iterations',
             'default': None,
             'run_type': ['risk_csm']},
            {'order': 80.11,
             'new_para': 'building_classification_tag',
             'default': '',
             'run_type': ['risk_csm']},
            {'order': 80.12,
             'new_para': 'damage_extent_tag',
             'default': '',
             'run_type': ['risk_csm']},
            {'order': 90.0,
             'title': '\n# Loss\n',
             'default': None},
            {'old_para': 'pga_mindamage',
             'order': 90.01,
             'new_para': 'loss_min_pga',
             'default': None,
             'run_type': ['risk_csm']},
            {'old_para': 'ci',
             'order': 90.02,
             'new_para': 'loss_regional_cost_index_multiplier',
             'default': None,
             'run_type': ['risk_csm']},
            {'old_para': 'aus_contents_flag',
             'order': 90.03,
             'new_para': 'loss_aus_contents',
             'default': None,
             'run_type': ['risk_csm']},
            {'order': 95.0,
             'title': '\n# Vulnerability\n'},
            {'order': 95.01,
             'new_para': 'vulnerability_variability_method',
             'default': 2,  # random sampling
             'run_type': ['risk_mmi']},
            {'order': 97.0,
             'title': '\n# Fatalities\n'},
            {'order': 97.01,
             'new_para': 'fatality_beta',
             'default': 0.17,
             'run_type': ['fatality']},
            {'order': 97.02,
             'new_para': 'fatality_theta',
             'default': 14.05,
             'run_type': ['fatality']},
            {'order': 100.0,
             'title': '\n# Save\n',
             'default': None},
            {'old_para': 'hazard_map_flag',
             'values': {None: None,
                        1: True,
                        0: False},
             'order': 100.01,
             'new_para': 'save_hazard_map',
             'default': False},
            {'old_para': 'save_total_financial_loss',
             'order': 100.02,
             'new_para': 'save_total_financial_loss',
             'default': False,
             'run_type': ['risk_csm']},
            {'old_para': 'save_building_loss',
             'order': 100.03,
             'new_para': 'save_building_loss',
             'default': False,
             'run_type': ['risk_csm', 'risk_mmi']},
            {'old_para': 'save_contents_loss',
             'order': 100.04,
             'new_para': 'save_contents_loss',
             'default': False,
             'run_type': ['risk_csm']},
            {'old_para': 'save_motion_flag',
             'values': {None: None,
                        1: True,
                        0: False},
             'order': 100.05,
             'new_para': 'save_motion',
             'default': False},
            {'old_para': 'save_deagecloss_flag',
             'values': {None: None,
                        1: True,
                        0: False},
             'order': 100.06,
             'new_para': 'save_prob_structural_damage',
             'default': False,
             'run_type': ['risk_csm', 'bridge']},
            {'old_para': 'save_fatalities',
             'order': 100.07,
             'new_para': 'save_fatalities',
             'default': False,
             'run_type': ['fatality']},
            {'order': 110.02,
             'new_para': 'event_set_handler',
             'default': 'generate'},
            {'order': 110.04,
             'new_para': 'data_array_storage',
             'default_to_attr': 'output_dir'},  # see _add_default_values
            {'order': 110.05,
             'new_para': 'file_array',
             'default': False},
            {'order': 110.06,
             'new_para': 'event_set_load_dir',
             'default': None},  # see _verify_eqrm_flags
            {'order': 120.01,
             'new_para': 'file_log_level',
             'default': 'debug'},
            {'order': 120.02,
             'new_para': 'console_log_level',
             'default': 'info'},
            {'order': 120.03,
             'new_para': 'file_parallel_log_level',
             'default': 'warning'},
            {'order': 120.04,
             'new_para': 'console_parallel_log_level',
             'default': 'warning'}
            ]

# Old style attributes that have not been removed yet.
OLD_STYLE_PARAS_HARD_WIRED = {'grid_flag': 1}

# 'attributes' that are added to eqrm_flags when executed on the command-line.
KNOWN_KWARGS = {'use_determ_seed': None,
                'compress_output': None,
                'eqrm_dir': None,
                'is_parallel': None,
                'default_input_dir': None}


# CONV_DIC_NEW has all allowable eqrm_flags attributes
CONV_DIC_NEW = {}
for item in CONV_NEW:
    if 'new_para' in item:
        CONV_DIC_NEW[item['new_para']] = item
CONV_DIC_NEW.update(KNOWN_KWARGS)
CONV_DIC_NEW.update(OLD_STYLE_PARAS_HARD_WIRED)


class AttributeSyntaxError(Exception):
    pass


def eqrm_data_home():
    """Return the EQRM data directory
    """
    results = os.getenv(ENV_EQRMDATAHOME)
    if results is None:
        print 'The environmental variable ' + ENV_EQRMDATAHOME + \
              ' , used by ParameterData.eqrm_data_home() is not set.'
        print 'Define this variable error before continuing.'
        # FIXME raise an error instead
        sys.exit(1)
    return results


def get_time_user():
    """Return string of date, time and user.  Used to create
    time and user stamped directories.

    WARNING: Does not work in parallel runs.
    """
    time = strftime('%Y%m%d_%H%M%S', localtime())
    if sys.platform == "win32":
        cmd = "USERNAME"
    elif sys.platform == "linux2":
        cmd = "USER"
    user = os.getenv(cmd)
    return "_".join((time, user))


def create_parameter_data(handle, **kwargs):
    """
    Given an EQRM control file, return a DictKeyAsAttributes instance which
    has all the information of the control file.

    Args:
      handle: A string of the .py file to load
        OR an instance with the required attributes.
      **kwargs:  These are additional attributes that are attached to
        eqrm_flags.  Examples of **kwargs are;
          use_determ_seed
          compress_output
          eqrm_dir
          is_parallel
          default_input_dir

    Returns:
      eqrm_flags, which is a DictKeyAsAttributes object.
    """

    if isinstance(handle, str) and handle[-3:] == ".py":
        attributes = _from_file_get_params(handle)
    elif isinstance(handle, dict):
        attributes = _filter_local_dictionary(handle)
    else:
        attributes = introspect_attribute_values(handle)

    # attributes is now a dictionary

    # The attributes value have presidence/overwrite the kwargs
    kwargs.update(attributes)
    eqrm_flags = DictKeyAsAttributes(kwargs)

    # Add Hard-wired results
    eqrm_flags.update(OLD_STYLE_PARAS_HARD_WIRED)

    # Remove or fix deprecated attributes
    deprecated_attributes(eqrm_flags)

    _add_default_values(eqrm_flags)

    # Check attribute names
    for key in eqrm_flags:
        if key not in CONV_DIC_NEW:
            msg = ("Attribute Error: Attribute " + key + " is unknown.")
            raise AttributeSyntaxError(msg)

    # Do attribute value fixes
    _att_value_fixes(eqrm_flags)

    # Check if values are consistant
    _verify_eqrm_flags(eqrm_flags)

    return eqrm_flags


def update_control_file(file_name_path, new_file_name_path=None):
    """Open an EQRM control file and then save it again,
    applying the CONV_NEW rules to order the lines
    and depreciation rules.

    Used to move attributes position around for all of the
    set_data.py files in the sandpit.

    WARNING: This function is not very robust.
    For example if you run it on any EQRM control files that use
    functions the updated files will not use functions.


    Args:
      file_name_path: The EQRM control file.
      new_file_name_path: The new EQRM control file.
    """

    if new_file_name_path is None:
        new_file_name_path = file_name_path
    attributes = _from_file_get_params(file_name_path)

    # Remove deprecated attributes
    deprecated_attributes(attributes)
    eqrm_flags_to_control_file(new_file_name_path, attributes)


def _filter_local_dictionary(attributes):
    """
    Filter out all callable or special atts.

    Args:
      attributes - dictionary of varriables and functions in a file namespace.
    """
    # Assume locals() has been called.
    local_paras = copy.copy(attributes)
    for key in local_paras.keys():
        if key[-1:] == '_' or callable(local_paras[key]):
            del local_paras[key]
    return local_paras


def _add_default_values(eqrm_flags):
    """Add default values

    Args:
      eqrm_flags: A DictKeyAsAttributes instance.
    """
    for param in CONV_NEW:
        if 'new_para' in param and \
                param['new_para'] not in eqrm_flags:
            if 'default' in param:
                eqrm_flags[param['new_para']] = param['default']
            elif 'default_to_attr' in param and \
                    param['default_to_attr'] in eqrm_flags and \
                    eqrm_flags[param['default_to_attr']] is not None:
                eqrm_flags[param['new_para']] = eqrm_flags[
                    param['default_to_attr']]
            else:
                raise AttributeSyntaxError(
                    "Attribute Error: Attribute " + param['new_para']
                    + " must be defined.")

    if eqrm_flags.file_array and sys.platform != 'win32':
        file_store.SAVE_METHOD = 'npy'
    else:
        file_store.SAVE_METHOD = None

    file_store.DATA_DIR = eqrm_flags.data_array_storage

# In the dictionary DEPRECATED_PARAS
# the key is the deprecated attribute.
# the value is
# None, which means the only action is a warning,
#   OR
# a string, which replaces the depreciated attribute,
#   OR
# the value has a dictionary where the the keys are the value of the
# deprecated attribute and the values are attribute and value pairs
# to use, based on the value of the attribute.
#   OR
# True, which means a warning, and deleting the attribute.

DEPRECATED_PARAS = {
    'atten_use_variability': {True: None,
                              False: (
                                  'atten_variability_method', None)},
    'amp_use_variability': {True: None,
                            False: (
                                'amp_variability_method', None)},
    'atten_use_rescale_curve_from_pga': {True: None,  # Do nothing
                                         False: (
                                             'atten_override_RSA_shape', None)},
    'csm_use_hysteretic_damping': {True: None,  # Do nothing
                                   False: (
                                       'csm_hysteretic_damping', None)},
    'atten_use_pga_scaling_cutoff': {True: None,  # Do nothing
                                     False: (
                                         'atten_pga_scaling_cutoff', None)},
    'atten_aggregate_Sa_of_atten_models':
    'atten_collapse_Sa_of_atten_models',
    'atten_rescale_curve_from_pga': 'atten_override_RSA_shape',
    'scenario_azimith': 'scenario_azimuth',
    'determ_azimith': 'scenario_azimuth',
    'determ_depth': 'scenario_depth',
    'determ_latitude': 'scenario_latitude',
    'determ_longitude': 'scenario_longitude',
    'determ_magnitude': 'scenario_magnitude',
    'determ_dip': 'scenario_dip',
    'determ_number_of_events': 'scenario_number_of_events',
    'is_deterministic': 'is_scenario',
    'prob_azimuth_in_zones': None,
    'prob_delta_azimuth_in_zones': None,
    'prob_dip_in_zones': None,
    'prob_number_of_mag_sample_bins': None,
    'save_prob_strucutural_damage': 'save_prob_structural_damage',
    'prob_min_mag_cutoff': True,
    'max_width': 'scenario_max_width',
    'event_set_name': True,
    'data_dir': True,
    'simulation_name': True
}

# In the dictionary DEPRECATED_VALUES
# the key is the attribute where its value has been deprecated
# the value is a second dictionary where
#     - the key is the old value
#     - the value is either a replacement value or None (remove attribute)
DEPRECATED_VALUES = {
    'run_type': {'risk': 'risk_csm'}
}


def deprecated_attributes(eqrm_flags):
    """
    Remove/fix/Give a warning about deprecated attributes.

    Args:
      eqrm_flags: A DictKeyAsAttributes instance.
    """
    for param in DEPRECATED_PARAS:
        if param in eqrm_flags:

            msg = 'WARNING: ' + param + \
                  ' term in EQRM control file is deprecated.'

            handle_logic = DEPRECATED_PARAS[param]
            if handle_logic is None:
                pass
            elif isinstance(handle_logic, str):
                # handle_logic is a replacement string
                # for the attribute name
                eqrm_flags[handle_logic] = eqrm_flags[param]

                msg = '%s Replaced with %s=%s.' % (msg,
                                                   handle_logic,
                                                   eqrm_flags[param])

                del eqrm_flags[param]
            elif handle_logic is True:
                # Delete the attribute
                msg = '%s Ignoring.' % msg

                del eqrm_flags[param]
            else:
                # handle_logic is a dictionary
                what_to_do = handle_logic[eqrm_flags[param]]
                if what_to_do is not None:
                    # The value is a tuple.
                    # the first value is the att name
                    # the second value is the att value
                    eqrm_flags[what_to_do[0]] = what_to_do[1]

                    msg = '%s Replaced with %s=%s.' % (msg,
                                                       what_to_do[0],
                                                       what_to_do[1])

                del eqrm_flags[param]

            # logging is only set-up after the para file has been passed.
            # So these warnings will not be in the logs.
            if log_imported:
                log.warning(msg)

    for param in DEPRECATED_VALUES:
        if param in eqrm_flags:
            param_value = eqrm_flags.get(param)
            param_to_replace = DEPRECATED_VALUES[param].get(param_value)
            if param_to_replace is not None:

                eqrm_flags[param] = param_to_replace

                msg = 'WARNING: %s=%s is deprecated.' % (param,
                                                         param_value)
                msg = '%s Replaced with %s=%s.' % (msg,
                                                   param,
                                                   param_to_replace)

                # logging is only set-up after the para file has been passed.
                # So these warnings will not be in the logs.
                if log_imported:
                    log.warning(msg)


def _att_value_fixes(eqrm_flags):
    """
    Change the attribute values so they are in the correct format for EQRM
      e.g. scaler values into arrays

    Args:
      eqrm_flags: A DictKeyAsAttributes instance.
    """
    # convert all lists into arrays
    for att in eqrm_flags:
        att_val = getattr(eqrm_flags, att)
        if isinstance(att_val, list):
            eqrm_flags[att] = asarray(eqrm_flags[att])

    if eqrm_flags.atten_model_weights is not None:
        eqrm_flags['atten_model_weights'] = check_sum_1_normalise(
            eqrm_flags.atten_model_weights)

    # if periods is collapsed (into a scalar), turn it into a vector
    if not isinstance(eqrm_flags.atten_periods, ndarray):
        eqrm_flags['atten_periods'] = array([eqrm_flags.atten_periods])

    # Fix the string specifying the directory structure
    if not eqrm_flags.output_dir[-1] == '/':
        eqrm_flags['output_dir'] = eqrm_flags.output_dir + '/'
    if not eqrm_flags.input_dir[-1] == '/':
        eqrm_flags['input_dir'] = eqrm_flags.input_dir + '/'
    if not eqrm_flags.data_array_storage[-1] == '/':
        eqrm_flags['data_array_storage'] = eqrm_flags.data_array_storage + '/'
    eqrm_flags['output_dir'] = _change_slashes(eqrm_flags.output_dir)
    eqrm_flags['input_dir'] = _change_slashes(eqrm_flags.input_dir)
    eqrm_flags['data_array_storage'] = _change_slashes(
        eqrm_flags.data_array_storage)

    if eqrm_flags.atten_variability_method is None:
        eqrm_flags.atten_spawn_bins = None


def check_sum_1_normalise(weights, msg=None):
    """
    Check that a list or array basically sums to one. Normalise so it
    exactly sums to one.

    Args:
      weights: A numpy.ndarray that should sum to 1.
      msg: An error message if the array is not close to summing to 1.

    Returns:
      A 1D array that sums to one.
    """
    # test if attenuation weights are close to 1 (with 0.01 absolute tolerance)
    # this means that 3 weights with 0.33 passes
    if not allclose(weights.sum(), 1.0, atol=0.01):
        if msg is None:
            msg = 'Weights should sum to 1.0, got ', weights
        raise ValueError(msg)

    # Re-normalise weights so they do sum to 1
    return weights / abs(weights.sum())  # normalize


def _change_slashes(path):
    """Swap from windows to linux file slashes

    Arg:
      path: A string representing a file path.
    """
    if sys.platform == 'linux2':
        split_path = path.split('\\')
        if len(split_path) >= 2:
            path = join(*split_path)
    return path


def _from_file_get_params(path_file):
    """
    Convert an EQRM control file to dictionary of attributes.

    para:
      path_file - the eqrm control file, which is a python file.

    returns:
      A dictionary of attribute values from the path_file file.
    """
    name = 'name_' + base64.urlsafe_b64encode(os.urandom(32))
    try:
        para_imp = imp.load_source(name, path_file)
    except IOError as exc:
        print "Problem with file " + path_file
        raise
    attributes = introspect_attribute_values(para_imp)

    return attributes


def _verify_eqrm_flags(eqrm_flags):
    """
    Check that the values in eqrm_flags are consistant with how EQRM works.

    Args:
      eqrm_flags: A DictKeyAsAttributes instance.
    """
    if not allclose(eqrm_flags.atten_periods,
                    sort(eqrm_flags.atten_periods)):
        raise AttributeSyntaxError(
            "Syntax Error: Period values are not ascending")

    if eqrm_flags.save_hazard_map == True and eqrm_flags.is_scenario == True:
        raise AttributeSyntaxError(
            'Cannot save the hazard map for a scenario.')

    if eqrm_flags.atten_variability_method == 1 and \
            eqrm_flags.run_type == 'risk_csm':
        raise AttributeSyntaxError(
            'Cannot use spawning when doing a risk_csm simulation.')

    if eqrm_flags.amp_variability_method == 1:
        raise AttributeSyntaxError(
            'Cannot spawn on amplification.')

    if eqrm_flags.event_set_handler == 'load' and \
            eqrm_flags.event_set_load_dir is None:
        raise AttributeSyntaxError(
            'event_set_load_dir must be set if event_set_handler is load.')

    if eqrm_flags.event_set_handler == 'load' and \
            not os.path.exists(eqrm_flags.event_set_load_dir):
        raise AttributeSyntaxError(
            'event_set_load_dir %s must exist if event_set_handler is load.' %
            eqrm_flags.event_set_load_dir)

    # Only do these checks if different from output_dir
    # (output_dir gets created if not exists)
    if eqrm_flags.data_array_storage != eqrm_flags.output_dir and \
            not os.path.exists(eqrm_flags.data_array_storage):
        raise AttributeSyntaxError(
            'data_array_storage %s must exist and be accessible from %s' %
            (eqrm_flags.data_array_storage, socket.gethostname()))

    if eqrm_flags.fault_source_tag is None and \
            eqrm_flags.zone_source_tag is None:
        raise AttributeSyntaxError(
            'Either fault_source_tag or zone_source_tag must be set.')

    # Check to see if a parameter is defined that is incompatible with the
    # defined run_type
    # Note: _add_default_values should have already dealt with adding
    # incompatible defaults
    for param in CONV_NEW:
        if not is_param_compatible(param, eqrm_flags):
            raise AttributeSyntaxError(
                "Attribute " + param['new_para'] +
                " not compatible with run_type=" + eqrm_flags['run_type'] +
                " - compatible run_type values are " + str(param['run_type']))


def is_param_compatible(param, eqrm_flags):
    """
    A parameter is not compatible if
    - it is not None, and
    - it is non-default, and
    - is not compatible with the run_type specified
    """

    # these parameters needed might not exist but _add_default_values should
    # take care of this
    if 'run_type' not in eqrm_flags or \
            'new_para' not in param:
        return True

    # If no run_type configured the parameter is ok
    if 'run_type' not in param:
        return True

    run_type = param['run_type']
    param_name = param['new_para']

    run_type_supported = eqrm_flags['run_type'] in run_type
    is_default = 'default' in param and \
        eqrm_flags[param_name] == param['default']
    is_none = eqrm_flags[param_name] is None

    if not is_none and not is_default and not run_type_supported:
        return False
    else:
        return True


def find_set_data_py_files(path):
    """Return a list of all the set_data .py files in a path directory.

    Based on the file having a .py extension and
    the second line in the file being == SECOND_LINE.

    Args:
      path: directory to search in.
    """
    extension = '.py'

    set_data_files = []
    for root, _, files in os.walk(path):
        for afile in files:
            if afile[-3:] == extension:
                file_path_name = join(root, afile)
                fref = open(file_path_name, 'r')
                _ = fref.readline()
                snd_line = fref.readline()
                if SECOND_LINE in snd_line:
                    set_data_files.append(file_path_name)
                fref.close()
    return set_data_files


def introspect_attribute_values(instance):
    """
    Puts all the attribite values of the instance into a dictionary.

    Args:
      instance: The instance who's values will go into the return dictionary.
    """
    attributes = [att for att in dir(instance) if not callable(
        getattr(instance, att)) and not att[-2:] == '__']
    att_values = {}
    for att in attributes:
        att_values[att] = getattr(instance, att)
    return att_values


class DictKeyAsAttributes(dict):

    """ An object to hold the EQRM control file data.  It is created
    in this module and not changed afterwards.

    It is really a dictionary with the dictionary keys exposed as
    attributes where the attributes can not be set.
    """

    def __getattribute__(self, key):
        """
        Try to get the value from the dictionary first.
        """
        try:
            return self[key]
        except:
            # Used when calling dictionary functions.
            return object.__getattribute__(self, key)

    def __delattr__(self, name):
        if name in self:
            del self[name]
        else:
            raise AttributeError


class ParameterData(object):

    """
    Class to build the attribute_data 'onto'.
    The user will add attributes to this class.
    """

    def __init__(self):
        pass


def eqrm_flags_to_control_file(py_file_name, eqrm_flags):
    """ Given a dictionary of the EQRM flag values convert it
    to an EQRM control file.

    Args:
      py_file_name: Name of the EQRM control file.
      eqrm_flags: dictionary of EQRM attributes.
    """

     # paras2print is a list of lists.
     # The inner list is 2 elements long.
     #  index 0 is the attribute name
     #  index 1 is the value
    paras2print = []
    for para_dic in CONV_NEW:
        if 'new_para' not in para_dic:
            paras2print.append(para_dic['title'])
        elif para_dic['new_para'] in eqrm_flags:
            line = [para_dic['new_para']]
            val = eqrm_flags[para_dic['new_para']]
            if line[0] in ['input_dir',
                           'output_dir',
                           'data_array_storage',
                           'event_set_load_dir'] and val is not None:
                if not 'join' in val and not 'getenv' in val:
                    val = convert_path_string_to_join(val)
            line.append(val)
            paras2print.append(line)

    writer = WriteEqrmControlFile(py_file_name)
    writer.write_top()
    writer.write_middle(paras2print)
    writer.write_bottom()


class WriteEqrmControlFile(object):

    """
    Write an EQRM control file.

    """

    def __init__(self, file_name):
        """ Create the file handle.
        """
        self.handle = open(file_name, 'w')

    def write_top(self):
        """ Write the imports ect. at the beginning of the py file.
        """

        self.handle.write('"""\n')

        self.handle.write(SECOND_LINE)

        self.handle.write(
            '\n'
            'All input files are first searched for in the input_dir,'
            'then in the\n'
            'resources/data directory, which is part of EQRM.\n'
            '\n'
            'All distances are in kilometers.\n'
            'Acceleration values are in g.\n'
            'Angles, latitude and longitude are in decimal degrees.\n'
            '\n'
            'If a field is not used, set the value to None.\n'
            '\n'
            '\n'
            '"""\n'
            '\n'
            'from os import getenv\n'
            'from os.path import join\n')
        if log_imported:  # as a proxy for the PYTHONPATH being set up.
            self.handle.write('from eqrm_code.parse_in_parameters import '
                              'eqrm_data_home, get_time_user\n')

        self.handle.write('\n')

    def write_middle(self, para_data):
        """ Writes the attribute lines

        Args:
          para_data: A list of strings or lists.  If an element is a
            string it is written as one row.  If the element is a list,
            the element[0] is a variable name and element[1] is the
            variable value.
        """
        for line in para_data:
            if isinstance(line, list):
                self.handle.write(line[0] + ' = ' +
                                  add_value(line[1]) + '\n')
            else:
                self.handle.write(line)

            # self.handle.write('\n')

    def write_bottom(self):
        """ Write the end of the EQRM control file.
        """
        self.handle.write("\n\
# If this file is executed the simulation will start.\n\
# Delete all variables that are not EQRM attributes variables. \n\
if __name__ == '__main__':\n\
    from eqrm_code.analysis import main\n\
    main(locals())\n")
        self.handle.close()


def add_value(val):
    """
    Given a value of unknown type, write it in python syntax.
    This function is not very robust.

    Return:
      A string value, which will be written to represent the passed in value.
    """
    if isinstance(val, str):
        if 'join' in val or 'getenv' in val:
            # This is hacky.  Is is assuming the string join means
            # the join command is being used.
            val_str = val
        else:
            val_str = '"' + val + '" '
    else:
        if isinstance(val, ndarray):
            val_str = str(val.tolist())
        elif isinstance(val, list) and isinstance(val[0], ndarray):
            # Assume all elements are arrays, with one element
            val_str = str([x[0] for x in val])

        else:
            val_str = str(val)
    return val_str

#-------------------------------------------------------------
if __name__ == "__main__":
    pass
