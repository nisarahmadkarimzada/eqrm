"""
  EQRM parameter file
All input files are first searched for in the input_dir,then in the
resources/data directory, which is part of EQRM.

All distances are in kilometers.
Acceleration values are in g.
Angles, latitude and longitude are in decimal degrees.

If a field is not used, set the value to None.


"""

from os.path import join
from eqrm_code.parse_in_parameters import eqrm_data_home, get_time_user


# Operation Mode
run_type = "risk_csm" 
is_scenario = False
max_width = 15
site_tag = "newc" 
site_db_tag = "" 
return_periods = [10, 50, 100, 200, 250, 474.56, 500, 974.78999999999996, 1000, 2474.9099999999999, 2500, 5000, 7500, 10000]
input_dir = join('.', 'input')
output_dir = join('.', 'output', 'plot_prob_risk')
use_site_indexes = False
zone_source_tag = ""
event_control_tag = ""

# Scenario input

# Probabilistic input
prob_number_of_events_in_zones = [500, 100, 100, 300, 100, 100]

# Attenuation
atten_models = ['Toro_1997_midcontinent']
atten_model_weights = [1]
atten_collapse_Sa_of_atten_models = True
atten_variability_method = 2
atten_periods = [0.0, 0.17544000000000001, 0.35088000000000003, 0.52632000000000001, 0.70174999999999998, 0.87719499999999995, 1.0526, 1.2281, 1.4035, 1.5789, 1.7544, 1.9298, 2.1053500000000001, 2.2806999999999999, 2.4561199999999999, 2.6316000000000002, 2.8067000000000002, 2.9824999999999999, 3.1579000000000002, 3.3330000000000002]
atten_threshold_distance = 400
atten_override_RSA_shape = None
atten_cutoff_max_spectral_displacement = False
atten_pga_scaling_cutoff = 2
atten_smooth_spectral_acceleration = False
atten_log_sigma_eq_weight = 0

# Amplification
use_amplification = True
amp_variability_method = 2
amp_min_factor = 0.6
amp_max_factor = 10000

# Buildings
buildings_usage_classification = "HAZUS" 
buildings_set_damping_Be_to_5_percent = False

# Capacity Spectrum Method
csm_use_variability = True
csm_variability_method = 2
csm_standard_deviation = 0.3
csm_damping_regimes = 0
csm_damping_modify_Tav = True
csm_damping_use_smoothing = True
csm_hysteretic_damping = "Error" 
csm_SDcr_tolerance_percentage = 1
csm_damping_max_iterations = 7

# Loss
loss_min_pga = 0.05
loss_regional_cost_index_multiplier = 1.4516
loss_aus_contents = 0

# Save
save_hazard_map = False
save_total_financial_loss = True
save_building_loss = False
save_contents_loss = False
save_motion = False
save_prob_structural_damage = False

file_array = False

# If this file is executed the simulation will start.
# Delete all variables that are not EQRM attributes variables. 
if __name__ == '__main__':
    from eqrm_code.analysis import main
    main(locals())
