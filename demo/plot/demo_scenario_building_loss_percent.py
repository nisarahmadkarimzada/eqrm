#!/usr/bin/env python

"""
Demonstration of using the fig_scenario_building_loss_percent function.

Copyright 2010 by Geoscience Australia

"""

######
# You *can't* run this from IDLE.  Use a command line.
######

import sys

from eqrm_code.plotting import plot_api
from eqrm_code.eqrm_filesystem import Demo_Output_ProbRisk_Path, \
     Demo_Output_PlotProbRisk_Path # this is slower


input_dir = Demo_Output_PlotProbRisk_Path
site_tag = 'newc'
bins = 30

# plot histogram wil auto-decided ranges
plot_file = 'demo_scenario_building_loss_percent.pdf'
savefile = None
title = 'demo_scenario_building_loss_percent.py'
title = ''
xlabel = 'percent of building value (including contents)'
ylabel = 'frequency'
xrange = 10
yrange = 1000
show_graph = len(sys.argv) > 1


plot_api.fig_scenario_building_loss_percent(input_dir, site_tag,
                                            plot_file=plot_file,
                                            savefile=None, title=title,
                                            xlabel=xlabel, ylabel=ylabel,
                                            xrange=xrange, yrange=yrange,
                                            bins=bins, bardict=None,
                                            show_graph=show_graph)
