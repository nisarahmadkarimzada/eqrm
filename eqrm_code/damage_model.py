"""
 Title: damage model

  Author:  Peter Row, peter.row@ga.gov.au


  Description: A class to convert csv files to arrays.


  Version: $Revision: 1716 $
  ModifiedBy: $Author: rwilson $
  ModifiedDate: $Date: 2010-06-18 13:58:01 +1000 (Fri, 18 Jun 2010) $

  Copyright 2007 by Geoscience Australia
"""

from scipy.stats import norm
from scipy import where, newaxis, array, asarray, log, shape, seterr
import numpy as np

from eqrm_code.capacity_spectrum_model import Capacity_spectrum_model, \
    CSM_DAMPING_REGIMES_USE_ALL, CSM_DAMPING_MODIFY_TAV
from eqrm_code.capacity_spectrum_functions import CSM_DAMPING_USE_SMOOTHING
from . import bridge_damage
from .bridge_time_complete import time_to_complete


class Damage_model(object):

    """
    attributes:
      structure_state: only created after get_building_states is called.
        Axis of sites, model_generated_psudo_events, 4 (# of damage states)
    """

    def __init__(
            self, structures, SA, periods, magnitudes, csm_use_variability,
            csm_standard_deviation, csm_params=None):
        """Class to determine the damage and economic loss.

        structures  a Structures instance - But what is actually needed from it?
        SA          array of Spectral Acceleration, in g, with axis;
                        sites, pseudo_events, atten_periods
                    the site axis usually has a size of 1
        periods     array, 1 axis
        magnitudes  array, 1 axis
        csm_params  capacity spectrum method params

        One Damage_model instance is created for each site, in
        calc_total_loss().  The structures value will be different for each
        site.
        """

        self.structures = structures
        self.periods = periods
        self.magnitudes = magnitudes
        self.SA = SA
        self.csm_use_variability = csm_use_variability
        self.csm_standard_deviation = csm_standard_deviation

        if csm_params is None:
            csm_params = {'csm_damping_regimes': CSM_DAMPING_REGIMES_USE_ALL,
                          'csm_damping_modify_Tav': CSM_DAMPING_MODIFY_TAV,
                          'csm_damping_use_smoothing':
                          CSM_DAMPING_USE_SMOOTHING,
                          'rtol': 0.01,
                          'csm_damping_max_iterations': 7,
                          'sdtcap': 0.3,
                          'csm_use_variability': False,
                          'csm_variability_method': None,
                          'csm_hysteretic_damping': 'trapezoidal',
                          'atten_override_RSA_shape': None,
                          'atten_cutoff_max_spectral_displacement': False,
                          'loss_min_pga': 0.0}

        csm_params['periods'] = periods
        csm_params['building_parameters'] = structures.building_parameters
        csm_params['magnitudes'] = magnitudes
        self.capacity_spectrum_model = Capacity_spectrum_model(**csm_params)

    def get_building_states(self):
        """
        Determine the cumulative probability of a building being in or
        exceeding a given damage state for 3 types of damage;
        structure, non_structural, acceleration_sensitive.
        """

        csm_use_variability = self.csm_use_variability
        csm_standard_deviation = self.csm_standard_deviation

        beta_th_sd = 0.4
        beta_th_nsd_d = 0.5
        beta_th_nsd_a = 0.6
        beta_bridge = 0.6

        if (csm_use_variability is False):
            # incorporate buiding cap variability into the beta
            # (may not be correct!)
            beta_sd = (
                beta_th_sd ** 2 + csm_standard_deviation ** 2) ** (0.5)
            beta_nsd_d = (
                beta_th_nsd_d ** 2 + csm_standard_deviation ** 2) ** (0.5)
            beta_nsd_a = (
                beta_th_nsd_a ** 2 + csm_standard_deviation ** 2) ** (0.5)
        elif (csm_use_variability is True):  # normal case:
            beta_sd = beta_th_sd  # This does nothing
            beta_nsd_d = beta_th_nsd_d
            beta_nsd_a = beta_th_nsd_a
  # warning: this option will cause divide by zero warnings in make_fragility.m
        else:
            msg = ('ERROR in prep_build_vun: '
                   'csm_use_variability not properly defined')
            raise RuntimeError(msg)

        (SA, SD) = self.get_building_displacement()
        SA = SA.round(4)
        SD = SD.round(4)

        building_parameters = self.structures.building_parameters
        threshold = building_parameters['structural_damage_threshold']

        # reshape threshold so it is [sites,magnitudes,damage_states]
        threshold = threshold[:, newaxis, :]
        assert len(threshold.shape) == 3
        # threshold is [sites,1,damage_states]
        #
        SA = SA[:, :, newaxis]
        SD = SD[:, :, newaxis]
        assert len(SA.shape) == 3
        assert len(SD.shape) == 3
        structure_state = state_probability(threshold, beta_th_sd, SD)
        # The above could be a typo.  Is this what we want?
        # It will change scenario results.
        # Is it beta_sd or beta_th_sd that we want?

        threshold = building_parameters['drift_threshold']
        threshold = threshold[:, newaxis, :]
        non_structural_state = state_probability(threshold, beta_nsd_d, SD)

        threshold = building_parameters['acceleration_threshold']
        threshold = threshold[:, newaxis, :]
        acceleration_sensitive_state = state_probability(threshold,
                                                         beta_nsd_a, SA)
        self.structure_state = structure_state  # for writing to file

        return (structure_state, non_structural_state,
                acceleration_sensitive_state)

    def get_building_displacement(self):
        point = self.capacity_spectrum_model.building_response(self.SA)

        return point

    def building_loss(self, ci=None, loss_aus_contents=0):
        damage_states = self.get_building_states()
        total_costs = self.structures.cost_breakdown(ci=ci)

        (structure_state, non_structural_state,
            acceleration_sensitive_state) = damage_states
        (structure_cost, non_structural_cost,
            acceleration_cost, contents_cost) = total_costs

        # hardwired loss for each damage state
        f1 = array((0.02, 0.1, 0.5, 1.0))[newaxis, newaxis, :]
        f2 = array((0.02, 0.1, 0.5, 1.0))[newaxis, newaxis, :]
        f3 = array((0.02, 0.1, 0.3, 1.0))[newaxis, newaxis, :]
        f4 = array((0.01, 0.05, 0.25, 0.5))[newaxis, newaxis, :]
        if loss_aus_contents == 1:
            f4 = f4 * 2  # 100% contents loss if building collapses

        structure_ratio = (f1 * structure_state)  # .sum(axis=-1)
        nsd_ratio = (f2 * non_structural_state)  # .sum(axis=-1)
        accel_ratio = (f3 * acceleration_sensitive_state)  # .sum(axis=-1)
        contents_ratio = (f4 * acceleration_sensitive_state)  # .sum(axis=-1)
        loss_ratio = (structure_ratio, nsd_ratio, accel_ratio, contents_ratio)

        structure_loss = structure_ratio * structure_cost[:, newaxis, newaxis]
        nsd_loss = nsd_ratio * non_structural_cost[:, newaxis, newaxis]
        accel_loss = accel_ratio * acceleration_cost[:, newaxis, newaxis]
        contents_loss = contents_ratio * contents_cost[:, newaxis, newaxis]

        total_loss = (structure_loss, nsd_loss, accel_loss, contents_loss)

        return (loss_ratio, total_loss)

    def aggregated_building_loss(self, ci=None, loss_aus_contents=0):
        (loss_ratio, total_loss) = \
            self.building_loss(ci=ci, loss_aus_contents=loss_aus_contents)
        total_loss = tuple([loss.sum(axis=-1) for loss in total_loss])

        return total_loss

    def annualised_loss(self, event_activity):
        event_activity = event_activity[:, newaxis]

        building_loss = self.aggregated_building_loss()

        raise NotImplementedError('Annualised Loss is not implemented')


class Bridge_damage_model(object):

    """Class to model bridge damage."""

    def __init__(self, structures, model, SA, periods, sa_indices):
        """Class to determine the damage and economic loss for a bridge.

        structures  a Structures instance
        model       the bridge damage model to use
        SA          array of Spectral Acceleration, in g, with axis;
                        site, period, return_period
                    the site axis usually has a size of 1
        periods     array, 1 axis
        sa_indices  tuple (0.3, 1.0) of column indices for the 0.3s and 1.0s
                    period SA values in SA
        """

        self.structures = structures
        self.model = model
        self.SA = SA
        self.periods = periods
        self.sa_indices = sa_indices

    def get_states(self):
        """Get the array of state probability tuples for this bridge.

        Returns a tuple (struct_state, non_struct_state, accel_state)
        where each element of the tuple is an array of shape (S, E, ST)
            S  is the number of sites
            E  is the number of events
            ST is the number of states for the bridge (4 in this case)

        For bridges, non_struct_state and accel_state are arrays full of zeros.
        """

        # get SA slices for periods 0.3s and 1.0s
        (i03, i10) = self.sa_indices
        sa_0_3 = self.SA[..., i03]
        sa_1_0 = self.SA[..., i10]

        # go calculate bridge states for events
        ssa = self.structures.attributes
        structure_state = \
            bridge_damage.bridge_states(ssa['STRUCTURE_CLASSIFICATION'][0],
                                        sa_0_3, sa_1_0,
                                        ssa['SKEW'][0], ssa['SPAN'][0],
                                        model=self.model)

        self.structure_state = structure_state

        # we assume non-structural and acceleration-sensitive states are
        # 'undamaged'.  create '0' arrays with same shape as 'structure_state'.
        non_structural_state = np.zeros(structure_state.shape)
        acceleration_sensitive_state = np.zeros(structure_state.shape)

        return (structure_state, non_structural_state,
                acceleration_sensitive_state)


def state_probability(threshold, beta, value):
    """Calculate the state probabilities for a given threshold, beta and value.

    Threshold = [0.2, 0.5, 0.8] = low, mid, extreme, complete

    value is actually the SD - Spectral displacement(mm)
    Returns p(low), p(mid), ...
    """

    p = cumulative_state_probability(threshold, beta, value)

    reduce_cumulative_to_pdf(p)
    return p


def reduce_cumulative_to_pdf(p):
    """Change cum. state probabilities to distribution (discretized pdf)"""

    p[..., :-1] -= p[..., 1:]


def cumulative_state_probability(threshold, beta, value):
    """Fragility curve calculation EQRM manual 7.8
    (Note eqn in manual is wrong.  Is is correct here.)

    Calcultate the cumulative state probability.

    P_cumulative(slight) = P(slight)+P(mid)+P(high)...

    Note that value/threshold is the median, not the mean.

    Since this is cumulative and the values are descending;
    column 0 is Slight
    column 1 is Moderate
    column 2 is Extreme
    column 3 is Complete

    parameters
      threshold - median damage state threshold
      beta - represents uncertainty in the damage state
      value - motion of the structure
          for buildings - either peak spectral displacement ,
                              peak spectrial acceleration or
          for bridges - spectral acceleration at t = 1 sec
    """

    oldsettings = seterr(divide='ignore')
    temp = (1 / beta) * log(value / threshold)
    seterr(**oldsettings)
    return norm.cdf(temp)
