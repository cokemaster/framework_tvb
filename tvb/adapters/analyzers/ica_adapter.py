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
Adapter that uses the traits module to generate interfaces for ICA Analyzer.

.. moduleauthor:: Paula Sanz Leon

"""
import numpy
from tvb.analyzers.ica import fastICA
from tvb.core.adapters.abcadapter import ABCAsynchronous
from tvb.datatypes.time_series import TimeSeries
from tvb.datatypes.mode_decompositions import IndependentComponents
from tvb.basic.traits.util import log_debug_array
from tvb.basic.filters.chain import FilterChain
from tvb.basic.logger.builder import get_logger
from tvb.basic.config.settings import TVBSettings
LOG = get_logger(__name__)


class ICAAdapter(ABCAsynchronous):
    """ TVB adapter for calling the ICA algorithm. """
    
    _ui_name = "Independent Component Analysis"
    _ui_description = "ICA for a TimeSeries input DataType."
    _ui_subsection = "ica"
    
    
    def get_input_tree(self):
        """
        Return a list of lists describing the interface to the analyzer. This
        is used by the GUI to generate the menus and fields necessary for
        defining a simulation.
        """
        algorithm = fastICA()
        algorithm.trait.bound = self.INTERFACE_ATTRIBUTES_ONLY
        tree = algorithm.interface[self.INTERFACE_ATTRIBUTES]
        for node in tree:
            if node['name'] == 'time_series':
                node['conditions'] = FilterChain(fields = [FilterChain.datatype + '._nr_dimensions'], 
                                            operations = ["=="], values = [4])
        return tree
        #tree[0]['conditions'] = FilterChain(fields = [FilterChain.datatype + '._nr_dimensions'], operations = ["=="], values = [4])
        #return tree
    
    
    def get_output(self):
        return [IndependentComponents]
    
    def configure(self, time_series, n_components=None):
        """
        Store the input shape to be later used to estimate memory usage. Also
        create the algorithm instance.
        """
        self.input_shape = time_series.read_data_shape()
        log_debug_array(LOG, time_series, "time_series")
        
        ##-------------------- Fill Algorithm for Analysis -------------------##
        algorithm = fastICA()
        if n_components is not None:
            algorithm.n_components = n_components
        else:
            ## TODO LD: Is this correct? when no number is specified, the number of nodes is taken
            ## It will only work for Simulator results. SK: Correct, the same thing is already done in the Analyser.
            algorithm.n_components = self.input_shape[2]
        self.algorithm = algorithm
        
    def get_required_memory_size(self, **kwargs):
        """
        Return the required memory to run this algorithm.
        """
        used_shape = (self.input_shape[0], 1, self.input_shape[2], self.input_shape[3])
        input_size = numpy.prod(used_shape) * 8.0
        output_size = self.algorithm.result_size(used_shape)
        return input_size + output_size  
    
    def get_required_disk_size(self, **kwargs):
        """
        Returns the required disk size to be able to run the adapter (in kB).
        """
        used_shape = (self.input_shape[0], 1, self.input_shape[2], self.input_shape[3])
        return self.algorithm.result_size(used_shape) * TVBSettings.MAGIC_NUMBER / 8 / 2 ** 10
    
    def launch(self, time_series, n_components=None):
        """ 
        Launch algorithm and build results. 
        """
        ##--------- Prepare a IndependentComponents object for result ----------##
        ica_result = IndependentComponents(source = time_series, 
                                           n_components = int(self.algorithm.n_components),
                                           storage_path = self.storage_path)
        
        ##------------- NOTE: Assumes 4D, Simulator timeSeries. --------------##
        node_slice = [slice(self.input_shape[0]), None, slice(self.input_shape[2]), slice(self.input_shape[3])]
        
        ##---------- Iterate over slices and compose final result ------------##
        small_ts = TimeSeries(use_storage=False)
        for var in range(self.input_shape[1]):
            node_slice[1] = slice(var, var + 1)
            small_ts.data = time_series.read_data_slice(tuple(node_slice))
            self.algorithm.time_series = small_ts 
            partial_ica = self.algorithm.evaluate()
            ica_result.write_data_slice(partial_ica)
        ica_result.close_file()
        return ica_result


