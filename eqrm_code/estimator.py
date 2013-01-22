"""
  Title: estimator.py
  
  Author:  Duncan Gray, Duncan.gray@ga.gov.au 

  Description: Estimate the maximum memory needed, for each node,
  of an EQRM simulation.
  
  Copyright 20012 by Geoscience Australia
"""
from copy import copy
from eqrm_code.ANUGA_utilities.log import EVENTS_J, MAXGMPE_J, BLOCKSITES_J, \
    PARALLELSIZE_J, TOTALMEM_J, INITIAL_J, LOOPING_J, MEM_J, RECMOD_J
from eqrm_code.ANUGA_utilities import log

# fixme check the atten_var_method is 1 to spawn?

                    

def estimate_mem_log_format(log_pair): # = log_pair[]
    events = log_pair[EVENTS_J]
    atten_periods = log_pair['len_atten_periods']
    return_periods= log_pair['len_return_periods']
    parallel_size = log_pair[PARALLELSIZE_J]
    sites = log_pair[BLOCKSITES_J] * parallel_size
    run_type = log_pair['run_type']
    spawning = log_pair['atten_spawn_bins']
    gmm_dimensions = log_pair[MAXGMPE_J]
    rec_mod  = log_pair[RECMOD_J]
    atten_collapse_Sa_of_atten_models = \
        log_pair['atten_collapse_Sa_of_atten_models']
    save_total_financial_loss = log_pair['save_total_financial_loss']
    save_building_loss = log_pair['save_building_loss']
    save_contents_loss = log_pair['save_contents_loss']
    save_hazard_map = log_pair['save_hazard_map']
    save_motion = log_pair['save_motion']
    use_amplification = log_pair['use_amplification']
    
    results = estimate_mem(events, 
                           atten_periods, 
                           return_periods,
                           sites,
                           run_type,
                           parallel_size,
                           spawning,
                           gmm_dimensions,
                           rec_mod,
                           atten_collapse_Sa_of_atten_models,
                           save_total_financial_loss,
                           save_building_loss,
                           save_contents_loss,
                           save_hazard_map,
                           save_motion,
                           use_amplification)
    return results
  

def estimate_mem_param_format(param): 
    # Half started
    events = param[EVENTS_J]
    atten_periods = param['len_atten_periods']
    return_periods= param['len_return_periods']
    parallel_size = param[PARALLELSIZE_J]
    sites = param[BLOCKSITES_J] * parallel_size
    run_type = param['run_type']
    spawning = param['atten_spawn_bins']
    gmm_dimensions = param[MAXGMPE_J]
    rec_mod  = param[RECMOD_J]
    atten_collapse_Sa_of_atten_models = \
        param['atten_collapse_Sa_of_atten_models']
    save_total_financial_loss = param['save_total_financial_loss']
    save_building_loss = param['save_building_loss']
    save_contents_loss = param['save_contents_loss']
    save_hazard_map = param['save_hazard_map']
    save_motion = param['save_motion']
    use_amplification = param['use_amplification']
    
    results = estimate_mem(events, 
                           atten_periods, 
                           return_periods,
                           sites,
                           run_type,
                           parallel_size,
                           spawning,
                           gmm_dimensions,
                           rec_mod,
                           atten_collapse_Sa_of_atten_models,
                           save_total_financial_loss,
                           save_building_loss,
                           save_contents_loss,
                           save_hazard_map,
                           save_motion,
                           use_amplification)
    return results
    
def estimate_mem(events, 
                 atten_periods, 
                 return_periods,
                 sites,
                 run_type='hazard',
                 parallel_size=1,
                 spawning=1,
                 gmm_dimensions=1,
                 rec_mod=1,
                 atten_collapse_Sa_of_atten_models=False,
                 save_total_financial_loss=False,
                 save_building_loss=False,
                 save_contents_loss=False,
                 save_hazard_map=False,
                 save_motion=False,
                 use_amplification=False,
                 loop_sites=1,
                 item_size=8):
    """
    Estimate the total memory used in an EQRM simulation.  
    Give the results in bytes
    
    rec_mod - recurance models 

    """
    mem_bytes = {}
    gmm_max = gmm_dimensions
    
    if atten_collapse_Sa_of_atten_models:
        gmm_after_collapsing = 1
    else:
        gmm_after_collapsing = gmm_max

    # calculate number of bytes for each data structure
    site_block = sites/parallel_size

    mem_bytes["event_mem"] = 16 * events 


    mem_bytes[log.EVENTACTIVITY_J] = (spawning * gmm_after_collapsing * 
                                       rec_mod * events ) * item_size

    if save_hazard_map is True:
        mem_bytes[log.BEDROCKHAZ_J] = (site_block *
                                       atten_periods *
                                       return_periods) * item_size
    else:
         mem_bytes[log.BEDROCKHAZ_J] = 0
    if save_hazard_map is True and \
           use_amplification is True:
        mem_bytes[log.SOILHAZ_J] = mem_bytes[log.BEDROCKHAZ_J]
    else:
        mem_bytes[log.SOILHAZ_J] = 0

    
    # FIXME gmm_dimensions_motion hardcoded
    gmm_dimensions_motion = 1

    if save_motion is True:
        mem_bytes[log.BEDROCKALL_J] = (spawning * gmm_dimensions_motion * 
                                       rec_mod *
                                       site_block * events *
                                       atten_periods) * item_size
        #print "gmm_dimensions",gmm_dimensions_motion
        #print "spawning",spawning
        #print "rec_mod",rec_mod
        #print "site_block",site_block
        #print "events",events
        #print "atten_periods",atten_periods
    else:
        mem_bytes[log.BEDROCKALL_J] = 0
        
    if save_motion is True and \
           use_amplification is True:
         mem_bytes[log.SOILALL_J] =  mem_bytes[log.BEDROCKALL_J]
    else:
         mem_bytes[log.SOILALL_J] = 0

    #if save_fatalities is True:
     #   total_fatalities = zeros((num_site_block, num_pseudo_events),
      #                              dtype=float)
   # if (eqrm_flags.save_prob_structural_damage is True and
   #      num_pseudo_events == 1):
   #      # total_structure_damage, given as a non-cumulative
   #      # probability. The axis are  sites, model_generated_psudo_events,
   #      # damage_states
   #      # (the damage_states are slight, moderate, extensive and complete.
   #      # subtract all of these from 1 to get the prob of no damage.)
   #      total_structure_damage = zeros((num_site_block, 4), dtype=float)
   # if eqrm_flags.bridges_functional_percentages is not None:
   #      saved_days_to_complete = zeros((
   #          num_site_block, num_pseudo_events,
   #          len(eqrm_flags.bridges_functional_percentages)))
   #  if eqrm_flags.save_hazard_map is True:
   #      data.bedrock_hazard = zeros((num_site_block,
   #                                   len(eqrm_flags.atten_periods),
   #                                   len(eqrm_flags.return_periods)),
   #                                  dtype=float)
   #  else:
   #      data.bedrock_hazard = None
        
    if save_total_financial_loss is True:
         mem_bytes['total_building_loss_qw'] = (site_block * spawning *
                                  gmm_max * rec_mod * events) * item_size
    else:
         mem_bytes['total_building_loss_qw'] = 0

    if save_building_loss is True:
         mem_bytes['building_loss_qw'] =  (site_block * spawning *
                                  gmm_max * rec_mod * events) * item_size
    else:
         mem_bytes['building_loss_qw'] = 0

    if save_contents_loss is True:
         mem_bytes['contents_loss_qw'] =  (site_block * spawning *
                                  gmm_max * rec_mod * events) * item_size
    else:
         mem_bytes['contents_loss_qw'] = 0

    mem_bytes[log.COLLROCKSAE_J] = (spawning * gmm_after_collapsing *
                                            rec_mod *
                                             loop_sites * events * 
                                            atten_periods) * item_size

    #print "mem_bytes[log.COLLROCKSAE_J]",mem_bytes[log.COLLROCKSAE_J]
    if not run_type == "hazard":
        mem_bytes[log.ROCKOVERLOADED_J] = (loop_sites *
                                           events * gmm_max *
                                           spawning * rec_mod *
                                           atten_periods) * item_size
    else:
        mem_bytes[log.ROCKOVERLOADED_J] = 0
    #print "gmm_after_collapsing",gmm_after_collapsing
    #print "gmm_max",gmm_max
    #mem_bytes[log.ROCKOVERLOADED_J]


    #print " mem_bytes[log.ROCKOVERLOADED_J] ", mem_bytes[log.ROCKOVERLOADED_J] 
    if use_amplification is True:
        mem_bytes['coll_soil_SA_all_events'] = mem_bytes[log.COLLROCKSAE_J]
        
        if not run_type == "hazard":
            mem_bytes['soil_SA_overloaded'] = mem_bytes[log.ROCKOVERLOADED_J]
        else:
            mem_bytes['soil_SA_overloaded'] = 0
    else:
        mem_bytes['coll_soil_SA_all_events'] = 0           
        mem_bytes['soil_SA_overloaded'] = 0

    return mem_bytes

