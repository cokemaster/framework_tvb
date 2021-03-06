# -*- coding: utf-8 -*-
#
#
# TheVirtualBrain-Framework Package. This package holds all Data Management, and 
# Web-UI helpful to run brain-simulations. To use it, you also need do download
# TheVirtualBrain-Scientific Package (for simulators). See content of the
# documentation-folder for more details. See also http://www.thevirtualbrain.org
#
# (c) 2012-2013, Baycrest Centre for Geriatric Care ("Baycrest")
#
# This program is free software; you can redistribute it and/or modify it under 
# the terms of the GNU General Public License version 2 as published by the Free
# Software Foundation. This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied warranty of 
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public
# License for more details. You should have received a copy of the GNU General 
# Public License along with this program; if not, you can download it here
# http://www.gnu.org/licenses/old-licenses/gpl-2.0
#
#
#   CITATION:
# When using The Virtual Brain for scientific publications, please cite it as follows:
#
#   Paula Sanz Leon, Stuart A. Knock, M. Marmaduke Woodman, Lia Domide,
#   Jochen Mersmann, Anthony R. McIntosh, Viktor Jirsa (2013)
#       The Virtual Brain: a simulator of primate brain network dynamics.
#   Frontiers in Neuroinformatics (in press)
#
#

"""
A Javascript displayer for time series, using SVG.

.. moduleauthor:: Marmaduke Woodman <mw@eml.cc>

"""

import json
import tvb.datatypes.time_series as tsdata
from tvb.basic.filters.chain import FilterChain
from tvb.core.adapters.abcdisplayer import ABCDisplayer



class TimeSeries(ABCDisplayer):
    _ui_name = "Time Series Viewer (SVG/d3)"
    _ui_subsection = "timeseries"

    MAX_PREVIEW_DATA_LENGTH = 200


    def get_input_tree(self):
        """
        Inform caller of the data we need as input.
        """
        return [{"name": "time_series",
                 "type": tsdata.TimeSeries,
                 "label": "Time series to be displayed in a 2D form.",
                 "required": True,
                 "conditions": FilterChain(fields=[FilterChain.datatype + '.type'],
                                           operations=["!="], values=["TimeSeriesVolume"])
                 }]


    def get_required_memory_size(self, **kwargs):
        """Return required memory."""
        return -1


    def launch(self, time_series, preview=False, figsize=None):
        """Construct data for visualization and launch it."""

        ts = time_series.get_data('time')
        shape = time_series.read_data_shape1()

        ## Assume that the first dimension is the time since that is the case so far
        if preview and shape[0] > self.MAX_PREVIEW_DATA_LENGTH:
            shape[0] = self.MAX_PREVIEW_DATA_LENGTH

        state_variables = time_series.labels_dimensions.get(time_series.labels_ordering[1], [])
        labels = time_series.get_space_labels()

        pars = {'baseURL': ABCDisplayer.VISUALIZERS_URL_PREFIX + time_series.gid,
                'labels': labels, 'labels_json': json.dumps(labels),
                'ts_title': time_series.title, 'preview': preview, 'figsize': figsize,
                'shape': repr(list(shape)), 't0': ts[0],
                'dt': ts[1] - ts[0] if len(ts) > 1 else 1,
                'channelsPage': '../commons/channel_selector.html' if not preview else None,
                'labelsStateVar': state_variables, 'labelsModes': range(shape[3]),
                }

        return self.build_display_result("time_series/view", pars, pages=dict(controlPage="time_series/control"))


    def generate_preview(self, time_series, figure_size):
        return self.launch(time_series, preview=True, figsize=figure_size)

