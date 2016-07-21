#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#
#  This file is part of the `pypath` python module
#
#  Copyright (c) 2014-2016 - EMBL-EBI
#
#  File author(s): Dénes Türei (denes@ebi.ac.uk)
#
#  Distributed under the GPLv3 License.
#  See accompanying file LICENSE.txt or copy at
#      http://www.gnu.org/licenses/gpl-3.0.html
#
#  Website: http://www.ebi.ac.uk/~denes
#

# import main
import __main__

from future.utils import iteritems
from past.builtins import xrange, range, reduce

# external modules:
import os
import sys
import re
import imp
import math
import igraph
import cairo
import codecs
import random
import textwrap
import copy
import json
import operator
import locale
import heapq
import threading
import traceback
from itertools import chain
from collections import Counter
from scipy import stats
import numpy as np
try:
    import cPickle as pickle
except ImportError:
    import pickle

try:
    import pygraphviz as graphviz
except:
    sys.stdout.write('\nModule `pygraphviz` not found.\n'\
        'You don\'t need it unless you want to export dot files.\n')
    sys.stdout.flush()

try:
    import pandas
except:
    sys.stdout.write('\nModule `pandas` not found.\n\n')
    sys.stdout.flush()

# from this module:
import pypath.logn as logn
import pypath.data_formats as data_formats
import pypath.mapping as mapping
import pypath.descriptions as descriptions
import pypath.chembl as chembl
import pypath.mysql as mysql

import pypath.dataio as dataio
import pypath.uniprot_input as uniprot_input
import pypath.curl as curl
import pypath.intera as intera
import pypath.seq as se
import pypath.go as go
import pypath.gsea as gsea
import pypath.drawing as bdrawing
import pypath.proteomicsdb as proteomicsdb
import pypath.reflists as reflists
import pypath.input_formats as input_formats
import pypath.refs as _refs
import pypath.plot as plot

import pypath.ig_drawing as ig_drawing
import pypath.common as common
from pypath.gr_plot import *
from pypath.progress import *

omnipath = data_formats.omnipath

if 'long' not in __builtins__:
    long = int

if 'unicode' not in __builtins__:
    unicode = str

__all__ = ['PyPath', 'Direction', '__version__', 'a',
    'AttrHelper', 'ReferenceList']

class Direction(object):
    
    def __init__(self,nameA,nameB):
        self.nodes = [nameA, nameB]
        self.nodes.sort()
        self.straight = (self.nodes[0], self.nodes[1])
        self.reverse = (self.nodes[1], self.nodes[0])
        self.dirs = {
            self.straight: False,
            self.reverse: False,
            'undirected': False
            }
        self.sources = {
            self.straight: set([]),
            self.reverse: set([]),
            'undirected': set([])
        }
        self.positive = {
            self.straight: False,
            self.reverse: False
        }
        self.negative = {
            self.straight: False,
            self.reverse: False
        }
        self.positive_sources = {
            self.straight: set([]),
            self.reverse: set([])
        }
        self.negative_sources = {
            self.straight: set([]),
            self.reverse: set([])
        }
        self.mechanisms = {}
        self.methods = {}
    
    def __str__(self):
        s = 'Directions and signs of interaction between %s and %s\n\n' % \
            (self.nodes[0],self.nodes[1])
        if self.dirs[self.straight]:
            s += '\t%s ===> %s :: %s\n' % \
                (self.nodes[0], self.nodes[1], ', '.join(self.sources[self.straight]))
        if self.dirs[self.reverse]:
            s += '\t%s <=== %s :: %s\n' % \
                (self.nodes[0], self.nodes[1], ', '.join(self.sources[self.reverse]))
        if self.dirs['undirected']:
            s += '\t%s ==== %s :: %s\n' % \
                (self.nodes[0], self.nodes[1], ', '.join(self.sources['undirected']))
        if self.positive[self.straight]:
            s += '\t%s =+=> %s :: %s\n' % (self.nodes[0], self.nodes[1], \
                ', '.join(self.positive_sources[self.straight]))
        if self.positive[self.reverse]:
            s += '\t%s <=+= %s :: %s\n' % (self.nodes[0], self.nodes[1], \
                ', '.join(self.positive_sources[self.reverse]))
        if self.negative[self.straight]:
            s += '\t%s =-=> %s :: %s\n' % (self.nodes[0], self.nodes[1], \
                ', '.join(self.negative_sources[self.straight]))
        if self.negative[self.reverse]:
            s += '\t%s <=-= %s :: %s\n' % (self.nodes[0], self.nodes[1], \
                ', '.join(self.negative_sources[self.reverse]))
        return s
    
    def check_nodes(self, nodes):
        return not bool(len(set(self.nodes) - set(nodes)))
    
    def check_param(self, di):
        return (di == 'undirected' or (type(di) is tuple and self.check_nodes(di)))
    
    def set_dir(self, direction, source):
        '''
        Adds directionality information with 
        the corresponding data source named.
        '''
        if self.check_param(direction):
            self.dirs[direction] = True
            source = source if type(source) is set \
                else set(source) if type(source) is list \
                else set([source])
            self.sources[direction] = self.sources[direction] | source
    
    def get_dir(self, direction, sources = False):
        '''
        Returns boolean or list of sources
        '''
        if self.check_param(direction):
            if sources:
                return self.sources[direction]
            else:
                return self.dirs[direction]
        else:
            return None
    
    def get_dirs(self, src, tgt, sources=False):
        '''
        Returns all directions with boolean values
        or list of sources.
        '''
        query = (src,tgt)
        if self.check_nodes(query):
            if sources:
                return [self.sources[query], 
                        self.sources[(query[1],query[0])], 
                        self.sources['undirected']]
            else:
                return [self.dirs[query], 
                        self.dirs[(query[1],query[0])], 
                        self.dirs['undirected']]
        else:
            return None
    
    def which_dirs(self):
        return [d for d, s in iteritems(self.dirs) if s and d != 'undirected']
    
    def unset_dir(self, direction, source = None):
        '''
        Removes directionality information,
        or single source.
        '''
        if check_param(direction):
            if source is not None:
                try:
                    self.sources[direction].remove(source)
                except ValueError:
                    pass
            else:
                self.sources[direction] = []
            if len(self.sources[direction]) == 0:
                self.dirs[direction] = False
    
    def is_directed(self):
        return bool(sum([v for k,v in iteritems(self.dirs) if k != 'undirected']))
    
    def is_stimulation(self, direction = None):
        if direction is None:
            return bool(sum(self.positive.values()))
        else:
            return self.positive[direction]
    
    def is_inhibition(self, direction = None):
        if direction is None:
            return bool(sum(self.negative.values()))
        else:
            return self.negative[direction]
    
    def has_sign(self, direction = None):
        if direction is None:
            return bool(sum(self.positive.values() + self.negative.values()))
        else:
            return bool(sum(self.negative[direction] + self.postive[direction]))
    
    def set_sign(self, direction, sign, source):
        if self.check_nodes(direction):
            self.set_dir(direction, source)
            if sign == 'positive':
                self.positive[direction] = True
                if source not in self.positive_sources[direction]:
                    self.positive_sources[direction].add(source)
            else:
                self.negative[direction] = True
                if source not in self.negative_sources[direction]:
                    self.negative_sources[direction].add(source)
    
    def get_sign(self, direction, sign = None, sources = False):
        if self.check_nodes(direction):
            if sources:
                if sign == 'positive':
                    return self.positive_sources[direction]
                elif sign == 'negative':
                    return self.negative_sources[direction]
                else:
                    return [self.positive_sources[direction],
                            self.negative_sources[direction]]
            else:
                if sign == 'positive':
                    return self.positive[direction]
                elif sign == 'negative':
                    return self.negative[direction]
                else:
                    return [self.positive[direction],
                            self.negative[direction]]
    
    def unset_sign(self, direction, sign, source = None):
        if self.check_nodes(direction):
            if source is not None:
                try:
                    if sign == 'positive':
                        self.positive_sources[direction].remove(source)
                    if sign == 'negative':
                        self.negative_sources[direction].remove(source)
                except:
                    pass
            else:
                if sign == 'positive':
                    self.positive_sources[direction] = []
                if sign == 'negative':
                    self.negative_sources[direction] = []
            if len(self.positive_sources[direction]) == 0:
                self.positive[direction] = False
            if len(self.negative_sources[direction]) == 0:
                self.negative[direction] = False
    
    def src(self):
        '''
        Returns the IDs of effector molecules in this directed 
        interaction. If the interaction is bidirectional, the 
        list will contain 2 IDs. If the interaction is undirec-
        ted, an empty list will be returned.
        '''
        return [k[0] for k, v in iteritems(self.dirs) if k != 'undirected' and v]
    
    def tgt(self):
        '''
        Returns the IDs of the target moleculess in the inter-
        action. Same behaviour as `Direction.src()`.
        '''
        return [k[1] for k, v in iteritems(self.dirs) if k != 'undirected' and v]
    
    def src_by_source(self, source):
        return [k[0] for k, v in iteritems(self.sources) \
            if k != 'undirected' and source in v]
    
    def tgt_by_source(self, source):
        return [k[1] for k, v in iteritems(self.sources) \
            if k != 'undirected' and source in v]
    
    def sources_straight(self):
        return self.sources[self.straight]
    
    def sources_reverse(self):
        return self.sources[self.reverse]
    
    def sources_undirected(self):
        return self.sources['undirected']
    
    def positive_straight(self):
        return self.positive[self.straight]
    
    def positive_reverse(self):
        return self.positive[self.reverese]
    
    def negative_straight(self):
        return self.negative[self.straight]
    
    def negative_reverse(self):
        return self.negative[self.reverese]
    
    def negative_sources_straight(self):
        return self.negative_sources[self.straight]
    
    def negative_sources_reverse(self):
        return self.negative_sources[self.reverse]
    
    def positive_sources_straight(self):
        return self.positive_sources[self.straight]
    
    def positive_sources_reverse(self):
        return self.positive_sources[self.reverse]
    
    def merge(self,other):
        if other.__class__.__name__ == 'Direction' and self.check_nodes(other.nodes):
            self.dirs[self.straight] = self.dirs[self.straight] or \
                other.dirs[self.straight]
            self.dirs[self.reverse] = self.dirs[self.reverse] or \
                other.dirs[self.reverse]
            self.dirs['undirected'] = self.dirs['undirected'] or \
                other.dirs['undirected']
            self.sources[self.straight] = self.sources[self.straight] | \
                other.sources[self.straight]
            self.sources[self.reverse] = self.sources[self.reverse] | \
                other.sources[self.reverse]
            self.sources['undirected'] = self.sources['undirected'] | \
                other.sources['undirected']
            self.positive[self.straight] = self.positive[self.straight] or \
                other.positive[self.straight]
            self.negative[self.reverse] = self.negative[self.reverse] or \
                other.negative[self.reverse]
            self.positive_sources[self.straight] = \
                common.uniqList(self.positive_sources[self.straight] or \
                other.positive_sources[self.straight])
            self.negative_sources[self.reverse] = \
                common.uniqList(self.negative_sources[self.reverse] + \
                other.negative_sources[self.reverse])

class AttrHelper(object):
    
    def __init__(self, value, name = None, defaults = {}):
        self.name = name
        self.value = value
        self.defaults = defaults
        if type(self.value) is dict:
            self.id_type = type(self.value.keys()[0])
    
    def __call__(self, instance, thisDir = None,
        thisSign = None, thisDirSources = None, thisSources = None):
        _thisDir = 'directed' if type(thisDir) is tuple else thisDir
        # user supplied callback function:
        if hasattr(self.value, '__call__'):
            return self.value(instance)
        # special cases #1: by direction/effect
        elif self.value == 'DIRECTIONS' and self.defaults is not None and \
            self.name is not None and self.name in self.defaults:
            if _thisDir in self.defaults[self.name]:
                if thisSign in self.defaults[self.name][_thisDir]:
                    return self.defaults[self.name][_thisDir][thisSign]
        # special cases #2: by source category
        elif self.value == 'RESOURCE_CATEGORIES':
            for resource_type in ['pathway', 'ptm', 'reaction', 'interaction']:
                if len(getattr(data_formats, '%s_resources'%resource_type) & \
                    thisSources) > 0:
                    if self.name in self.defaults and \
                        resource_type in self.defaults[self.name]:
                        return self.defaults[self.name][resource_type]
            sys.stdout.wrtie('No category for %s\n' % thisSources)
            sys.stdout.flush()
        # if value is constant:
        elif type(self.value) in common.simpleTypes:
            return self.value
        # if a dictionary given to map some igraph attribute to values:
        elif type(self.value) is dict and self.attr_name is not None:
            if hasattr(instance, self.value['_name']):
                key_attr = getattr(instance, self.value['_name'])
            elif self.value['_name'] in instance.attributes():
                key_attr = instance[self.value['_name']]
            if key_attr in self.value:
                    return self.value[key_attr]
        # if default value has been given for this attribute:
        elif self.name is not None and self.defaults is not None and \
            self.name in self.defaults:
            return self.defaults[self.name]
        # ultimately, return None
        else:
            return None

class _NamedVertexSeq(object):
    
    def __init__(self, _vs, _nodNam, _nodLab):
        self._vs = _vs
        self._nodNam = _nodNam
        self._nodLab = _nodLab
    
    def __iter__(self):
        for v in self._vs:
            yield v
    
    def genesymbol(self):
        for v in self._vs:
            yield self._nodLab[v.index]
    
    def uniprot(self):
        for v in self._vs:
            yield self._nodNam[v.index]
    
    def ids(self):
        for v in self._vs:
            yield v.index
    
    gs = genesymbol
    up = uniprot
    vs = __iter__

class PyPath(object):
    
    ###
    ### main network object
    ###
    
    default_name_type = {
        'protein': 'uniprot', 
        'mirna': 'mirbase', 
        'drug': 'chembl'
    }
    
    def __init__(self, ncbi_tax_id = 9606, default_name_type = default_name_type,
                 copy = None, mysql = (None, 'mapping'), 
                 chembl_mysql = (None, 'chembl'),
                 name = 'unnamed', 
                 outdir = 'results', loglevel = 'INFO', loops = False):
        '''
        Currently only one organism molecular interaction networks
        are supported. Some functions supports multi-species networks,
        and maybe once the whole module will support that.
        
        @ncbi_tax_id : int
            The ID of the organism in NCBI Taxonomy. Defaults to human 
            (9606).
        @mysql
            The MySQL parameter used by the mapping module to load some
            ID conversion tables from MySQL. 
        @default_name_type : dict
            Dictionary of default ID types, what all identifiers of the
            given molecular species should be converted to. By default, 
            for protein it is UniProt. It could be any other, only then
            you need to supply the required format definitions for the 
            ID conversion tables.
        @copy : BioGraph object
            In case you copy an other instance.
        @name : str
            This is a custom session/project name.
        @outdir : str
            The directory where you wish to create all the output files.
        @loglevel : str
            Passed to logging module.
        @loops : bool
            Whether to allow loop edges in the graph. Default is False.
        '''
        self.__version__ = common.__version__
        for d in ['results', 'log', 'cache']:
            if not os.path.exists(d):
                os.makedirs(d)
        if copy is None:
            self.graph = igraph.Graph(0)
            g = self.graph
            g['entity_types'] = {}
            g['ncbi_tax_id'] = ncbi_tax_id
            g['name'] = name
            g['sources'] = {}
            g['references'] = {}
            g['directed'] = False
            g.vs['type'] = []
            g.vs['name'] = []
            g.vs['nameType'] = []
            g.vs['originalNames'] = [[] for _ in xrange(self.graph.vcount())]
            g.vs['ncbi_tax_id'] = []
            g.vs['exp'] = [{}]
            g.es['sources'] = [set([]) for _ in xrange(self.graph.ecount())]
            g.es['type'] = [[] for _ in xrange(self.graph.ecount())]
            g.es['references'] = [[] for _ in xrange(self.graph.ecount())]
            g.es['refs_by_source'] = [{} for _ in xrange(self.graph.ecount())]
            g.es['refs_by_dir'] = [{} for _ in xrange(self.graph.ecount())]
            g.es['refs_by_type'] = [{} for _ in xrange(self.graph.ecount())]
            g.es['sources_by_type'] = [{} for _ in xrange(self.graph.ecount())]
            g.es['negative_refs'] = [[] for _ in xrange(self.graph.ecount())]
            g.es['negative'] = [[] for _ in xrange(self.graph.ecount())]
            g.es['dirs'] = [None]
            g['layout_type'] = None
            g['layout_data'] = None
            g['only_directed'] = False
            # allow loop edges in the graph
            self.loops = loops
            self.dgraph = None
            self._undirected = self.graph
            self._directed = None
            self.failed_edges = []
            self.uniprot_mapped = []
            self.mysql_conf = mysql
            self.set_chembl_mysql(chembl_mysql[1], chembl_mysql[0])
            # self.mysql = mysql.MysqlRunner(self.mysql_conf)
            self.unmapped = []
            self.name = name
            self.outdir = outdir
            self.ncbi_tax_id = ncbi_tax_id
            self.data = {}
            self.reflists = {}
            self.negatives = {}
            self.raw_data = None
            self.lists = {}
            self.plots = {}
            self.proteomicsdb = None
            self.exp_samples = set([])
            self.sources = []
            self.db_dict = {}
            self.pathway_types = []
            self.pathways = {}
            self.vertexAttrs = {}
            self.edgeAttrs = {}
            self.u_pfam = None
            self.seq = None
            self.palette = ['#6EA945', '#007B7F', '#FCCC06', '#DA0025', '#000000']
            self.session = common.gen_session_id()
            self.session_name = ''.join([self.name,'-',self.session])
            self.loglevel = loglevel
            self.ownlog = logn.logw(self.session,self.loglevel)
            self.mapper = mapping.Mapper(self.ncbi_tax_id, 
                mysql_conf = self.mysql_conf, log = self.ownlog)
            self.disclaimer = '\n\n\t=== d i s c l a i m e r ===\n\n'\
                '\tAll data coming with this module\n'\
                '\teither as redistributed copy or downloaded using the\n'\
                '\tprogrammatic interfaces included in the present module\n'\
                '\tare available under public domain, are free to use at\n'\
                '\tleast for academic research or education purposes.\n'\
                '\tPlease be aware of the licences of all the datasets\n'\
                '\tyou use in your analysis, and please give appropriate\n'\
                '\tcredits for the original sources when you publish your\n'\
                '\tresults. To find out more about data sources please\n'\
                '\tlook at `pypath.descriptions` and\n'\
                '\t`pypath.data_formats.urls`.\n\n'
            self.licence()
            self.ownlog.msg(1, "PyPath has been initialized")
            self.ownlog.msg(1, "Beginning session '%s'" % self.session)
            sys.stdout.write(
                """\t» New session started,\n\tsession ID: '%s'\n\tlogfile:"""\
                """'./%s'.\n""" % \
                (self.session,self.ownlog.logfile))
            
        else:
            self.copy(copy)
    
    def set_chembl_mysql(self, title, config_file = None):
        '''
        Sets the ChEMBL MySQL config according to
        `title` section in `config_file` ini style config.
            
            title (str): section title in ini file
            config_file (str, NoneType): config file name; 
                if None, the `mysql_config/defaults.mysql`
                will be used
        '''
        self.chembl_mysql = (config_file, title)
    
    def copy(self,other):
        self.__dict__ = other.__dict__
        self.ownlog.msg(1, "Reinitialized", 'INFO')
    
    def init_network(self, lst = omnipath, exclude = [], 
        cache_files = {}, pfile = False, save = False,
        reread = False, redownload = False):
        '''
        This is a lazy way to start the module, load data 
        and build the high confidence, literature curated
        part of the signaling network.
        '''
        if pfile:
            pfile = pfile if type(pfile) is not bool \
                else os.path.join('cache', 'default_network.pickle')
            if os.path.exists(pfile):
                sys.stdout.write('\t:: Loading igraph object from file `%s`...' % pfile)
                sys.stdout.flush()
                graph = pickle.load(open(pfile, 'rb'))
                if type(graph) is igraph.Graph and graph.vcount() > 0:
                    self.graph = graph
                    sys.stdout.write('\r%s\r\t:: Network loaded from `%s`. %u nodes, '\
                        '%u edges.\n' % (' '*90, pfile, \
                            self.graph.vcount(), self.graph.ecount()))
                    sys.stdout.flush()
                    self.update_vname()
                    self.update_vindex()
                    self.update_sources()
                    return None
        self.load_reflists()
        self.load_resources(lst = lst, exclude = exclude,
            reread = reread, redownload = redownload)
        if save:
            sys.stdout.write('\t:: Saving igraph object to file `%s`...' % pfile)
            sys.stdout.flush()
            self.save_network()
            sys.stdout.write('\r%s\r\t:: Network saved successfully to file `%s`.\n' % \
                (' '*90, pfile))
            sys.stdout.flush()
    
    def save_network(self, pfile = None):
        pfile = pfile if pfile is not None \
            else os.path.join('cache', 'default_network.pickle')
        pickle.dump(self.graph, open(pfile, 'wb'))
    ###
    ### functions to read networks from text files or mysql
    ###
    
    def get_max(self, attrList):
        maxC = 0
        for val in attrList.values():
            if val.__class__ is tuple:
                val = val[0]
            if val > maxC:
                maxC = val
        return maxC
    
    def get_attrs(self,line,spec,lnum):
        attrs = {}
        for col in spec:
            # extraEdgeAttrs and extraNodeAttrs are dicts 
            # of additional parameters assigned to edges and nodes respectively;
            # key is the name of the parameter, value is the col number, 
            # or a tuple of col number and the separator, 
            # if the column contains additional subfields e.g. (5, ";")
            try:
                if spec[col].__class__ is tuple:
                    fieldVal = line[spec[col][0]].split(spec[col][1])
                else:
                    fieldVal = line[spec[col]]
            except:
                self.ownlog.msg(2,("""Wrong column index (%s) in extra attributes? 
                    Line #%u\n""" % (str(col), lnum)), 'ERROR')
                readError = 1
                break
            fieldName = col
            attrs[fieldName] = fieldVal
        return attrs
    
    def get_taxon(self, tax_dict, fields):
        if 'A' in tax_dict and 'B' in tax_dict:
            return (self.get_taxon(tax_dict['A'], fields), 
                    self.get_taxon(tax_dict['B'], fields))
        else:
            if fields[tax_dict['col']] in tax_dict['dict']:
                return tax_dict['dict'][fields[tax_dict['col']]]
            else:
                return None
    
    def numof_references(self):
        return len(common.uniqList(common.flatList(
            list(map(lambda e: e['references'], self.graph.es)))))
    
    def mean_reference_per_interaction(self):
        return np.mean(list(map(lambda e: len(e['references']), self.graph.es)))
    
    def numof_reference_interaction_pairs(self):
        return len(common.uniqList(common.flatList(
            list(map(lambda e:
                list(map(lambda r:
                    (e.index, r), e['references'])),
            self.graph.es)))))
    
    def curators_work(self):
        curation_effort = self.numof_reference_interaction_pairs()
        sys.stdout.write('\t:: Curators worked %.01f-%.01f years to accomplish '\
                         'what currently you have incorporated in this network!'\
                         '\n\n\tAmazing, isn\'t it?\n' % \
            (curation_effort * 15 / 60.0 / 2087.0,
             curation_effort * 60 / 60.0 / 2087.0))
        sys.stdout.flush()
    
    def reference_edge_ratio(self):
        return self.numof_references() / float(self.graph.ecount())
    
    def get_giant(self, replace = False, graph = None):
        '''
        Returns the giant component of the graph, or 
        replaces the igraph object with only the giant 
        component.
        '''
        g = graph if graph is not None else self.graph
        gg = g if replace else copy.deepcopy(g)
        cl = gg.components(mode = 'WEAK')
        cl_sizes = cl.sizes()
        giant_component_index = cl_sizes.index(max(cl_sizes))
        in_giant = [x == giant_component_index for x in cl.membership]
        common.console(':: Nodes in giant component: %u' % in_giant.count(True))
        toDel = [i for i in xrange(0, gg.vcount()) if not in_giant[i]]
        gg.delete_vertices(toDel)
        common.console(':: Giant component size: %u edges, %u nodes' % \
            (gg.ecount(), gg.vcount()))
        if not replace:
            return gg
    
    def update_vname(self):
        '''
        For fast lookup of node names and indexes, these are 
        hold in a list and a dict as well. However, every time
        new nodes are added, these should be updated. This 
        function is automatically called after all operations
        affecting node indices.
        '''
        self.genesymbol_labels()
        graph = self._get_undirected()
        self._already_has_directed()
        dgraph = self._directed
        if graph is not None:
            self.nodInd = set(graph.vs['name'])
            self.nodDct = dict(zip(graph.vs['name'], xrange(graph.vcount())))
            self.labDct = dict(zip(graph.vs['label'], xrange(graph.vcount())))
            self.nodNam = dict(zip(xrange(graph.vcount()), graph.vs['name']))
            self.nodLab = dict(zip(xrange(graph.vcount()), graph.vs['label']))
        if dgraph is not None:
            self.dnodInd = set(dgraph.vs['name'])
            self.dnodDct = dict(zip(dgraph.vs['name'], xrange(dgraph.vcount())))
            self.dlabDct = dict(zip(dgraph.vs['label'], xrange(dgraph.vcount())))
            self.dnodNam = dict(zip(xrange(dgraph.vcount()), dgraph.vs['name']))
            self.dnodLab = dict(zip(xrange(dgraph.vcount()), dgraph.vs['label']))
    
    def vsgs(self):
        return _NamedVertexSeq(self.graph.vs, self.nodNam, self.nodLab).gs()
    
    def vsup(self):
        return _NamedVertexSeq(self.graph.vs, self.nodNam, self.nodLab).gs()
    
    def update_vindex(self):
        '''
        This is deprecated.
        '''
        self.nodNam = dict(zip(range(0, self.graph.vcount()), 
            self.graph.vs['name']))
    
    def vertex_pathways(self):
        '''
        Some resources assignes interactions some others 
        proteins to pathways.
        This function converts pathway annotations from 
        edge attributes to vertex attributes.
        '''
        for eattr in self.graph.es.attributes():
            if eattr.endswith('pathways'):
                if eattr not in self.graph.vs.attributes():
                    self.graph.vs[eattr] = [[] for _ in self.graph.vs]
                for e in self.graph.es:
                    self.graph.vs[e.source][eattr] = e[eattr]
                    self.graph.vs[e.target][eattr] = e[eattr]
    
    def filters(self, line, positiveFilters = [], negativeFilters = []):
        for filtr in negativeFilters:
            # print 'Negative filter:'
            sep = filtr[2] if len(filtr) > 2 else None
            thisVal = set(line[filtr[0]].split(sep))
            filtrVal = set(filtr[1] if type(filtr[1]) is list else [filtr[1]])
            # print '\tthisVal: ', thisVal
            # print '\tfiltrVal: ', filtrVal
            if len(thisVal & filtrVal) > 0:
                # print '\tNegative filter matched, filter = True (skip this record)'
                return True
        for filtr in positiveFilters:
            # print 'Positive filter:'
            sep = filtr[2] if len(filtr) > 2 else None
            thisVal = set(line[filtr[0]].split(sep))
            filtrVal = set(filtr[1] if type(filtr[1]) is list else [filtr[1]])
            # print '\tthisVal: ', thisVal
            # print '\tfiltrVal: ', filtrVal
            if len(thisVal & filtrVal) == 0:
                # print '\tPositive filter matched, filter = True (skip this record)'
                return True
        # print '\tNo filter matched, filter = False (process this record)'
        return False
    
    def lookup_cache(self, name, cache_files, int_cache, edges_cache):
        infile = None
        edgeListMapped = []
        cache_file = cache_files[name] if name in cache_files else None
        if cache_file is not None and os.path.exists(cache_file):
            cache_type = cache_file.split('.')[-2]
            if cache_type == 'interactions':
                infile = self.read_from_cache(int_cache)
            elif cache_type == 'edges':
                edgeListMapped = self.read_from_cache(edges_cache)
        elif os.path.exists(edges_cache):
            edgeListMapped = self.read_from_cache(edges_cache)
        else:
            if os.path.exists(int_cache):
                infile = self.read_from_cache(int_cache)
        return infile, edgeListMapped
    
    def read_from_cache(self, cache_file):
        sys.stdout.write('\t:: Reading from cache: %s\n'%cache_file)
        sys.stdout.flush()
        self.ownlog.msg(2, 'Data have been read from cache: %s'%cache_file)
        return pickle.load(open(cache_file, 'rb'))
    
    def process_sign(self, signData, signDef):
        stim = False
        inh = False
        signSep = signDef[3] if len(signDef) > 3 else None
        signData = set(str(signData).split(signSep))
        pos = set(signDef[1] if type(signDef[1]) is list else [signDef[1]])
        neg = set(signDef[2] if type(signDef[2]) is list else [signDef[2]])
        if len(signData & pos) > 0:
            stim = True
        elif len(signData & neg) > 0:
            inh = True
        return stim, inh
    
    def process_direction(self, line, dirCol, dirVal, dirSep):
        if dirCol is None or dirVal is None:
            return False
        else:
            thisDir = set(line[dirCol].split(dirSep))
            return len(thisDir & dirVal) > 0
    
    def read_data_file(self, settings, keep_raw = False, cache_files = {},
        reread = False, redownload = False):
        '''
        Interaction data with node and edge attributes can be read 
        from simple text based files. This function works not only
        with files, but with lists as well. Any other function can 
        be written to download a preprocess data, and then give it
        to this function to finally attach to the network.
        
        @settings : ReadSettings instance
            The detailed definition of the input format. Instead of 
            the file name you can give a function name, which will 
            be executed, and the returned data will be used.
        @keep_raw : boolean
            To keep the raw data read by this function, in order for
            debugging purposes, or further use.
        '''
        listLike = set([list, tuple])
        edgeList = []
        nodeList = []
        edgeListMapped = []
        infile = None
        _name = settings.name.lower()
        int_cache = os.path.join('cache', '%s.interactions.pickle' % _name)
        edges_cache = os.path.join('cache', '%s.edges.pickle' % _name)
        if not reread and not redownload:
            infile, edgeListMapped = self.lookup_cache(_name, 
                cache_files, int_cache, edges_cache)
        if not len(edgeListMapped):
            if infile is None:
                if settings.__class__.__name__ != "ReadSettings":
                    self.ownlog.msg(2,("""No proper input file definition!\n\'settings\'
                        should be a \'ReadSettings\' instance\n"""), 'ERROR')
                    return None
                if settings.huge:
                    sys.stdout.write('\n\tProcessing %s requires huge memory.\n'\
                        '\tPlease hit `y` if you have at least 2G free memory,\n'\
                        '\tor `n` to omit %s.\n'\
                        '\tAfter processing once, it will be saved in \n'\
                        '\t%s, so next time can be loaded quickly.\n\n'\
                        '\tProcess %s now? [y/n]\n' % \
                        (settings.name, settings.name, edges_cache, settings.name))
                    sys.stdout.flush()
                    while True:
                        answer = raw_input().lower()
                        if answer == 'n':
                            return None
                        elif answer == 'y':
                            break
                        else:
                            sys.stdout.write('\n\tPlease answer `y` or `n`:\n\t')
                            sys.stdout.flush()
                inputFunc = self.get_function(settings.inFile)
                if inputFunc is None and hasattr(dataio, settings.inFile):
                    inputFunc = getattr(dataio, settings.inFile)
                # reading from remote or local file, or executing import function:
                if settings.inFile.startswith('http') or \
                    settings.inFile.startswith('ftp'):
                    curl_use_cache = not redownload
                    c = curl.Curl(settings.inFile, silent = False, large = True,
                        cache = curl_use_cache)
                    infile = c.result
                    infile = [x for x in infile.read().replace('\r', '').split('\n') \
                        if len(x) > 0]
                    self.ownlog.msg(2, "Retrieving data from%s ..." % \
                        settings.inFile)
                # elif hasattr(dataio, settings.inFile):
                elif inputFunc is not None:
                    self.ownlog.msg(2, "Retrieving data by dataio.%s() ..." % \
                        inputFunc.__name__)
                    _store_cache = curl.CACHE
                    curl.CACHE = not redownload
                    # this try-except needs to be removed
                    # once correct exception handling will
                    # be implemented in every input function
                    try:
                        infile = inputFunc(**settings.inputArgs)
                    except Exception as e:
                        sys.stdout.write('\n\t:: Error in `pypath.dataio.%s()`. '\
                            'Skipping to next resource.\n' % inputFunc.__name__)
                        sys.stdout.write('\t:: %s\n' % str(e.args))
                        sys.stdout.flush()
                        traceback.print_tb(e.__traceback__, file = sys.stdout)
                    curl.CACHE = _store_cache
                elif os.path.isfile(settings.inFile):
                    infile = codecs.open(settings.inFile, 
                        encoding='utf-8', mode='r')
                    self.ownlog.msg(2, "%s opened..." % settings.inFile)
                if infile is None:
                    self.ownlog.msg(2,"%s: No such file or "\
                        "dataio function! :(\n" % (settings.inFile), 'ERROR')
                    return None
            # finding the largest referred column number, 
            # to avoid references out of range
            isDir = settings.isDirected
            sign = settings.sign
            refCol = settings.refs[0] if type(settings.refs) is tuple \
                else settings.refs if type(settings.refs) is int else None
            refSep = settings.refs[1] if type(settings.refs) is tuple else ';'
            sigCol = None if type(sign) is not tuple else sign[0]
            dirCol = None
            dirVal = None
            dirSep = None
            if type(isDir) is tuple:
                dirCol = isDir[0]
                dirVal = isDir[1]
                dirSep = isDir[2] if len(isDir) > 2 else None
            elif type(sign) is tuple:
                dirCol = sign[0]
                dirVal = sign[1:3]
                dirVal = dirVal if type(dirVal[0]) in common.simpleTypes else common.flatList(dirVal)
                dirSep = sign[3] if len(sign) > 3 else None
            dirVal = set(dirVal if type(dirVal) is list else [dirVal])
            maxCol = max(
                filter(
                    lambda i:
                        i is not None,
                    [ 
                        settings.nameColA, 
                        settings.nameColB, 
                        self.get_max(settings.extraEdgeAttrs), 
                        self.get_max(settings.extraNodeAttrsA), 
                        self.get_max(settings.extraNodeAttrsB),
                        refCol,dirCol,sigCol
                    ]
                )
            )
            # iterating lines from input file
            lnum = 0
            lFiltered = 0
            rFiltered = 0
            tFiltered = 0
            readError = 0
            for line in infile:
                lnum += 1
                if len(line) <= 1 or (lnum == 1 and settings.header):
                    # empty lines
                    # or header row
                    continue
                if type(line) not in listLike:
                    if hasattr(line, 'decode'):
                        line = line.decode('utf-8')
                    line = line.replace('\n','').replace('\r','').\
                    split(settings.separator)
                else:
                    line = [x.replace('\n','').replace('\r','') \
                        if type(x) in common.charTypes else x 
                        for x in line]
                # in case line has less fields than needed
                if len(line) < maxCol:
                    self.ownlog.msg(2,(
                        "Line #%u has less than %u fields! :(\n" % (lnum, maxCol)),
                        'ERROR')
                    readError = 1
                    break
                else:
                    # applying filters:
                    if self.filters(line, settings.positiveFilters,
                        settings.negativeFilters):
                        lFiltered += 1
                        continue
                    # reading names and attributes:
                    if isDir and type(isDir) is not tuple:
                        thisEdgeDir = True
                    else:
                        thisEdgeDir = self.process_direction(line, dirCol, 
                            dirVal, dirSep)
                    refs = []
                    if refCol is not None:
                        refs = common.delEmpty(list(set(line[refCol].split(refSep))))
                    refs = dataio.only_pmids([r.strip() for r in refs])
                    if len(refs) == 0 and settings.must_have_references:
                        rFiltered += 1
                        continue
                    # to give an easy way:
                    if type(settings.ncbiTaxId) is int:
                        taxA = settings.ncbiTaxId
                        taxB = settings.ncbiTaxId
                    # to enable more sophisticated inputs:
                    elif type(settings.ncbiTaxId) is dict:
                        taxx = self.get_taxon(settings.ncbiTaxId, line)
                        if type(taxx) is tuple:
                            taxA = taxx[0]
                            taxB = taxx[1]
                        else:
                            taxA = taxB = taxx
                    else:
                        taxA = taxB = self.ncbi_tax_id
                    if taxA is None or taxB is None:
                        tFiltered += 1
                        continue
                    stim = False
                    inh = False
                    if type(sign) is tuple:
                        stim, inh = self.process_sign(line[sign[0]], sign)
                    resource = line[settings.resource] \
                        if type(settings.resource) is int else settings.resource
                    newEdge = {
                        "nameA": line[settings.nameColA].strip(),
                        "nameB": line[settings.nameColB].strip(),
                        "nameTypeA": settings.nameTypeA,
                        "nameTypeB": settings.nameTypeB,
                        "typeA": settings.typeA,
                        "typeB": settings.typeB,
                        "source": resource,
                        "isDirected": thisEdgeDir,
                        "references": refs,
                        "stim": stim,
                        "inh": inh,
                        "taxA": taxA,
                        "taxB": taxB,
                        "type": settings.intType}
                    #except:
                        #self.ownlog.msg(2,("""Wrong name column indexes (%u and %u), 
                            #or wrong separator (%s)? Line #%u\n""" 
                            #% (
                                #settings.nameColA, settings.nameColB, 
                                #settings.separator, lnum)), 'ERROR')
                        #readError = 1
                        #break
                    # getting additional edge and node attributes
                    attrsEdge = self.get_attrs(line, settings.extraEdgeAttrs, lnum)
                    attrsNodeA = self.get_attrs(line, settings.extraNodeAttrsA, lnum)
                    attrsNodeB = self.get_attrs(line, settings.extraNodeAttrsB, lnum)
                    # merging dictionaries
                    nodeAttrs = {
                        "attrsNodeA": attrsNodeA,
                        "attrsNodeB": attrsNodeB,
                        "attrsEdge": attrsEdge}
                    newEdge.update(nodeAttrs)
                if readError != 0:
                    break
                edgeList.append(newEdge)
            if hasattr(infile, 'close'):
                infile.close()
            ### !!!! ##
            edgeListMapped = self.map_list(edgeList)
            self.ownlog.msg(2, "%u lines have been read from %s,"\
            "%u links after mapping; \n\t\t"\
            "%u lines filtered by filters;\n\t\t"\
            "%u lines filtered because lack of references;\n\t\t"\
            "%u lines filtered by taxon filters." % \
            (lnum-1, settings.inFile, len(edgeListMapped), 
                lFiltered, rFiltered, tFiltered))
            if reread or redownload:
                pickle.dump(edgeListMapped, open(edges_cache, 'wb'))
                self.ownlog.msg(2, 'Mapped edge list saved to %s'%edges_cache)
        if keep_raw:
            self.data[settings.name] = edgeListMapped
        self.raw_data = edgeListMapped
    
    def load_list(self, lst, name):
        self.lists[name] = lst
    
    def receptors_list(self):
        self.lists['rec'] = common.uniqList(common.flatList([
            self.mapper.map_name(rec, 'genesymbol', 'uniprot') \
            for rec in dataio.get_hpmr()]))
    
    def druggability_list(self):
        self.lists['dgb'] = common.uniqList(common.flatList([
            self.mapper.map_name(dgb, 'genesymbol', 'uniprot') \
            for dgb in dataio.get_dgidb()]))
    
    def kinases_list(self):
        self.lists['kin'] = common.uniqList(common.flatList([
            self.mapper.map_name(kin, 'genesymbol', 'uniprot') \
            for kin in dataio.get_kinases()]))
    
    def tfs_list(self):
        tfs = dataio.get_tfcensus()
        utfs = [self.mapper.map_name(tf, 'ensg', 'uniprot') \
            for tf in tfs['ensg']]
        utfs += [self.mapper.map_name(h, 'hgnc', 'uniprot') \
            for h in tfs['hgnc']]
        self.lists['tfs'] = common.uniqList(common.flatList(utfs))
    
    def disease_genes_list(self, dataset = 'curated'):
        self.lists['dis'] = common.uniqList(common.flatList([
            self.mapper.map_name(dis['genesymbol'], 'genesymbol', 'uniprot') \
            for dis in dataio.get_disgenet(dataset = dataset)]))
    
    def proteome_list(self, swissprot = True):
        swissprot = 'yes' if swissprot else None
        self.lists['proteome'] = \
            dataio.all_uniprots(self.ncbi_tax_id, swissprot = swissprot)
    
    def coverage(self, lst):
        lst = lst if type(lst) is set \
            else set(lst) if type(lst) is list \
            else set(self.lists[lst]) \
                if type(lst) is str and lst in self.lists \
            else set([])
        return len(set(self.graph.vs['name']) & lst) / float(len(lst))
    
    def fisher_enrichment(self, lst, attr, ref = 'proteome'):
        cont = \
            np.array([
                [
                    len(self.lists[ref]),
                    self.graph.vcount()
                ],
                [
                    len(self.lists[lst]),
                    len([1 for v in self.graph.vs if len(v[attr]) > 0])
                ]
            ])
        return stats.fisher_exact(cont)
    
    def read_list_file(self, settings, **kwargs):
        _input = None
        if settings.__class__.__name__ != "ReadList":
            self.ownlog.msg(2,("""No proper input file definition!\n\'settings\'
                should be a \'readList\' instance\n"""), 'ERROR')
            return None
        if hasattr(dataio, settings.inFile):
            toCall = getattr(dataio, settings.inFile)
            _input = toCall(**kwargs)
        elif not os.path.isfile(settings.inFile):
            self.ownlog.msg(2,"%s: No such file! :(\n" % (settings.inFile), 'ERROR')
            return None
        else:
            _input = settings.inFile
        originalNameType = settings.nameType
        defaultNameType = self.default_name_type[settings.typ]
        mapTbl = ''.join([originalNameType,"_",defaultNameType])
        if type(_input) in common.charTypes and os.path.isfile(_input):
            _input = codecs.open(_input, encoding='utf-8', mode='r')
        if _input is None:
            self.ownlog.msg(2,("""Could not find '\
                'file or dataio function.\n"""), 'ERROR')
            return None
        self.ownlog.msg(2, "%s opened..." % settings.inFile)
        # finding the largest referred column number, 
        # to avoid references out of index
        maxCol = max(
            [   settings.nameCol,
                self.get_max(settings.extraAttrs) ])
        # iterating lines from input file
        lnum = 1
        readError = 0
        itemList = []
        for line in _input:
            if len(line) == 0 or (lnum == 1 and settings.header):
                # empty lines
                # or header row
                lnum += 1
                continue
            if type(line) in common.charTypes:
                line = line.rstrip().split(settings.separator)
            # in case line has less fields than needed
            if len(line) < maxCol:
                self.ownlog.msg(2,(
                    "Line #%u has less than %u fields! :(\n" % \
                        (lnum, maxCol)), 'ERROR')
                readError = 1
                break
            else:
                # reading names and attributes
                try:
                    newItem = {
                        "name": line[settings.nameCol], 
                        "nameType": settings.nameType, 
                        "type": settings.typ, 
                        "source": settings.name}
                except:
                    self.ownlog.msg(2,("""Wrong name column indexes (%u and %u), 
                        or wrong separator (%s)? Line #%u\n""" 
                        % ( settings.nameCol, settings.separator, lnum)), 'ERROR')
                    readError = 1
                    break
                # getting additional attributes
                attrsItem = self.get_attrs(line, settings.extraAttrs, lnum)
                # merging dictionaries
                newItem.update(attrsItem)
            if readError != 0:
                break
            itemList.append(newItem)
            lnum += 1
        if hasattr(_input, 'close'):
            _input.close()
        itemListMapped = self.map_list(itemList,singleList=True)
        itemListMapped = list(set(itemListMapped))
        self.ownlog.msg(2, "%u lines have been read from %s, %u '\
            items after mapping" %
            (lnum, settings.inFile, len(itemListMapped)))
        self.lists[settings.name] = itemListMapped
    
    def map_list(self,lst,singleList=False):
        '''
        Only a wrapper for map_edge()
        '''
        listMapped = []
        if singleList:
            for item in lst:
                listMapped += self.map_item(item)
        else:
            for edge in lst:
                listMapped += self.map_edge(edge)
        return listMapped
    
    def map_item(self,item):
        defaultNames = self.mapper.map_name(
            item['name'],
            item['nameType'],
            self.default_name_type[item['type']])
        if len(defaultNames) == 0:
            self.unmapped.append(item['name'])
        return defaultNames
    
    def map_edge(self, edge):
        edgeStack = []
        defaultNameA = self.mapper.map_name(
            edge['nameA'], 
            edge['nameTypeA'], 
            self.default_name_type[edge['typeA']])
        # print 'mapped %s to %s' % (str(edge['nameA']), str(defaultNameA))
        defaultNameB = self.mapper.map_name(
            edge['nameB'], 
            edge['nameTypeB'], 
            self.default_name_type[edge['typeB']])
        # print 'mapped %s to %s' % (str(edge['nameB']), str(defaultNameB))
        # this is needed because the possibility ambigous mapping
        # one name can be mapped to multiple ones
        # this multiplies the nodes and edges
        # in case of proteins this does not happen too often
        for dnA in defaultNameA:
            for dnB in defaultNameB:
                edge['defaultNameA'] = dnA
                edge['defaultNameTypeA'] = self.default_name_type[edge['typeA']]
                edge['defaultNameB'] = dnB
                edge['defaultNameTypeB'] = self.default_name_type[edge['typeB']]
                edgeStack.append(edge)
                # print 'new edge: %s' % str(edge)
        return edgeStack
    
    def merge_attrs(self,a,b,exc=["name"]):
        sys.stdout.write('.')
        for key, val in iteritems(b.attributes()):
            if key not in a.attributes():
                a[key] = val
            elif key not in exc:
                if key == 'signs':
                    a[key] = self.combine_signs(a[key],b[key])
                elif key == 'directions':
                    a[key] = self.combine_dirs(a[key],b[key])
                elif key == 'dirs_by_source':
                    a[key] = self.combine_dirsrc(a[key],b[key])
                else:
                    a[key] = self.combine_attr([a[key], val])
    
    def combine_signs(self,sigA,sigB):
        for out in [0,1]:
            for inn in [0,1]:
                sigA[out][inn] = common.uniqList(sigA[out][inn]+sigB[out][inn])
        return sigA
    
    def combine_dirs(self,dirA,dirB):
        newDir = [False,False,False]
        for i in [0,1,2]:
            newDir[i] = dirA[i] or dirB[i]
        return tuple(newDir)
    
    def combine_dirsrc(self,dirsA,dirsB):
        for i in [0,1,2]:
            dirsA[i] = common.uniqList(dirsA[i]+dirsB[i])
        return dirsA
    
    def combine_attr(self,lst):
        if len(lst) == 0:
            return None
        if len(lst) == 1:
            return lst[0]
        if lst[0] == lst[1]:
            return lst[0]
        if lst[0] is None:
            return lst[1]
        if lst[1] is None:
            return lst[0]
        if type(lst[0]) in common.numTypes and type(lst[1]) in common.numTypes:
            return max(lst)
        if type(lst[0]) is list and type(lst[1]) is list:
            try:
                return list(set(lst[0] + lst[1]))
            except:
                return lst[0] + lst[1]
        if type(lst[0]) is set:
            return common.addToSet(lst[0], lst[1])
        if type(lst[1]) is set:
            return common.addToSet(lst[1], lst[0])
        if type(lst[0]) is dict and type(lst[1]) is dict:
            return dict(lst[0].items() + lst[1].items())
        if (type(lst[0]) is str or type(lst[0]) is unicode) and \
            (type(lst[1]) is str or type(lst[1]) is unicode):
            if len(lst[0]) == 0:
                return lst[1]
            if len(lst[1]) == 0:
                return lst[0]
            return [lst[0],lst[1]]
        if (type(lst[0]) is list and type(lst[1]) in common.simpleTypes):
            if len(lst[1]) > 0:
                return common.addToList(lst[0],lst[1])
            else:
                return lst[0]
        if (type(lst[1]) is list and type(lst[0]) in common.simpleTypes):
            if len(lst[0]) > 0:
                return common.addToList(lst[1],lst[0])
            else:
                return lst[1]
        if lst[0].__class__.__name__ == 'Direction' and \
            lst[1].__class__.__name__ == 'Direction':
            lst[0].merge(lst[1])
            return lst[0]
    
    def uniq_node_list(self,lst):
        uniqLst = {}
        for n in lst:
            if n[0] not in uniqLst:
                uniqLst[n[0]] = n[1]
            else:
                uniqLst[n[0]] = self.merge_attrs(uniqLst[n[0]],n[1])
        return uniqLst
    
    def map_network(self, mapping = ('trembl', 'swissprot')):
        '''
        This function is not needed any more, will be removed soon.
        
        In the whole network changes every uniprot id to primary.
        '''
        self.ownlog.msg(1,"Mapping network by %s..." % mapping,'INFO')
        g = self.graph
        self.ownlog.msg(2,("Num of edges: %u, num of vertices: %u" %
            (g.ecount(),g.vcount())), 'INFO')
        fun = getattr(self,mapping)
        primNodes = {}
        secNodes = {}
        delNodes = []
        prg = Progress(
            total=len(g.vs),name="Mapping nodes",interval=30)
        for v in g.vs:
            if v["type"] == "protein" and v["nameType"] == "uniprot":
                prim = fun([v["name"]])
                if len(prim) > 0 and v["name"] not in prim:
                    delNodes.append(v["name"])
                for u in prim:
                    if u != v["name"]:
                        if u not in primNodes:
                            primNodes[u] = []
                        primNodes[u].append(v["name"])
                        if v["name"] not in secNodes:
                            secNodes[v["name"]] = []
                        secNodes[v["name"]].append(u)
            prg.step()
        prg.terminate()
        newNodes = list(set(primNodes.keys()) - set(g.vs["name"]))
        self.new_nodes(newNodes)
        self.update_vname()
        self.ownlog.msg(2,"New nodes have been created (%u)" % len(newNodes),'INFO')
        primEdges = {}
        newEdges = []
        prg = Progress(
            total=len(g.es),name="Processing edges",interval=200)
        for e in g.es:
            uA = g.vs[e.source]["name"]
            uB = g.vs[e.target]["name"]
            if uA in secNodes or uB in secNodes:
                uAlist = [uA] if uA not in secNodes else secNodes[uA]
                uBlist = [uB] if uB not in secNodes else secNodes[uB]
                for a in uAlist:
                    for b in uBlist:
                        ab = [a,b]
                        ab.sort()
                        if ab[0] not in primEdges:
                            primEdges[ab[0]] = {}
                        if ab[1] not in primEdges[ab[0]]:
                            primEdges[ab[0]][ab[1]] = []
                        primEdges[ab[0]][ab[1]].append((uA,uB))
                        abEdge = self.edge_exists(ab[0],ab[1])
                        if type(abEdge) is tuple:
                            newEdges.append(abEdge)
            prg.step()
        prg.terminate()
        newEdges = list(set(newEdges))
        self.new_edges(newEdges)
        self.ownlog.msg(2,"New edges have been created (%u)" % len(newEdges),'INFO')
        # copying node attributes
        prg = Progress(
            total=len(primNodes),name="Processing node attributes",interval=10)
        for k,v in iteritems(primNodes):
            prim = g.vs.find(name=k)
            for s in v:
                sec = g.vs.find(name=s)
                self.merge_attrs(prim,sec,exc=["name"])
            prg.step()
        prg.terminate()
        # copying edge attributes
        prg = Progress(
            total=len(primEdges),name="Processing edge attributes",interval=10)
        for a,bdict in iteritems(primEdges):
            primA = g.vs.find(name=a).index
            for b,originals in iteritems(bdict):
                primB = g.vs.find(name=b).index
                prim = g.es.select(_between=((primA,),(primB,)))[0]
                for o in originals:
                    secA = g.vs.find(name=o[0]).index
                    secB = g.vs.find(name=o[1]).index
                    sec = g.es.select(_between=((secA,),(secB,)))[0]
                    self.merge_attrs(prim,sec)
            prg.step()
        prg.terminate()
        # deleting old nodes
        delNodeInd = []
        for u in delNodes:
            delNodeInd.append(g.vs.find(name=u).index)
        self.ownlog.msg(2,"Removing old nodes (%u)" % len(delNodeInd),'INFO')
        if len(delNodeInd) > 0:
            g.delete_vertices(list(set(delNodeInd)))
        self.clean_graph()
        self.update_vname()
        self.ownlog.msg(2,"Network has been mapped.",'INFO')
        self.ownlog.msg(2,("Num of edges: %u, num of vertices: %u" %
            (g.ecount(),g.vcount())), 'INFO')
    
    def delete_by_taxon(self, tax):
        '''
        Removes the proteins of all organisms which are not listed.
        
        @tax : list
            List of NCBI Taxonomy IDs of the organisms of interest.
            E.g. [7227, 9606]
        '''
        g = self.graph
        toDel = []
        for v in g.vs:
            if v['ncbi_tax_id'] not in tax:
                toDel.append(v.index)
        g.delete_vertices(toDel)
        self.update_vname()
        self.update_db_dict()
    
    def delete_unknown(self, tax, typ = 'protein', defaultNameType = None):
        '''
        Removes those proteins which are not in the list of all default
        IDs of the organisms. By default, it means to remove all protein 
        nodes not having a human SwissProt ID. 
        
        @tax : list
            List of NCBI Taxonomy IDs of the organisms of interest.
            E.g. [7227, 9606]
        @typ : str
            Molecule type. E.g. 'protein' or 'mirna'
        @defaultNameType : str
            The default name type of the given molecular species.
            For proteins it's 'uniprot' by default.
        '''
        g = self.graph
        if not defaultNameType:
            defaultNameType = self.default_name_type[typ]
        toDel = []
        reflists = {}
        self.update_vname()
        for t in tax:
            idx = (defaultNameType,typ,t)
            if idx in self.reflists:
                reflists[t] = self.reflists[idx].lst
            else:
                msg = ('Missing reference list for %s (default name type: %s), in taxon %u'
                    ) % (idx[1],idx[0],t)
                self.ownlog.msg(2,msg,'ERROR')
                sys.stdout.write(''.join(['\t',msg,'\n']))
                return False
        sys.stdout.write(' :: Comparing with reference lists...')
        for t in tax:
            nt = g.vs['nameType']
            nt = [i for i, j in enumerate(nt) if j == defaultNameType]
            ty = g.vs['type']
            ty = [i for i, j in enumerate(ty) if j == typ]
            tx = g.vs['ncbi_tax_id']
            tx = [i for i, j in enumerate(tx) if j == t]
            vs = list((set(nt) & set(ty)) & set(tx))
            vn = [g.vs[i]['name'] for i in vs]
            toDelNames = list(set(vn) - set(reflists[t]))
            toDel += [self.nodDct[n] for n in toDelNames]
        g.delete_vertices(toDel)
        sys.stdout.write(' done.\n')
    
    def clean_graph(self):
        self.ownlog.msg(1,"Removing duplicate edges...",'INFO')
        g = self.graph
        if not g.is_simple():
            g.simplify(loops = not self.loops, multiple = True, combine_edges = self.combine_attr)
        self.delete_unmapped()
        ## TODO: multiple taxons ##
        if len(self.reflists) != 0:
            self.delete_by_taxon([self.ncbi_tax_id])
            self.delete_unknown([self.ncbi_tax_id])
        x = g.vs.degree()
        zeroDeg = [i for i, j in enumerate(x) if j == 0]
        g.delete_vertices(zeroDeg)
        self.update_vname()
    
    ###
    ### functions to integrate new data into the main igraph network object
    ###
    
    def count_sol(self):
        '''
        Counts nodes with zero degree.
        '''
        s = 0
        for i in self.graph.vs.degree():
            if i == 0:
                s += 1
        return s
    
    def add_update_vertex(
            self, defAttrs, originalName, 
            originalNameType, extraAttrs={}, add=False):
        '''
        Updates the attributes of one node in the network.
        Optionally it creates a new node and sets the attributes,
        but it is not efficient as igraph needs to reindex vertices 
        after this operation, so better to create new nodes and 
        edges in batch.
        '''
        g = self.graph
        if not defAttrs["name"] in g.vs["name"]:
            if not add:
                self.ownlog.msg(2,'Failed to add some vertices','ERROR')
                return False
            n = g.vcount()
            g.add_vertices(1)
            g.vs[n][key].originalNames = {originalName: originalNameType}
            thisNode = g.vs.find(name=defAttrs["name"])
        else:
            thisNode = g.vs.find(name=defAttrs["name"])
            if thisNode["originalNames"] is None:
                thisNode["originalNames"] = {}
            thisNode["originalNames"][originalName] = originalNameType
        for key, value in iteritems(defAttrs):
            thisNode[key] = value
        for key, value in iteritems(extraAttrs):
            if key not in g.vs.attributes():
                g.vs[key] = [[] for _ in xrange(self.graph.vcount())] \
                    if type(value) is list else [None]
            thisNode[key] = self.combine_attr([thisNode[key],value])
    
    def add_update_edge(self, nameA, nameB, source, 
                        isDir, refs, stim, inh, taxA, taxB, typ,
                        extraAttrs={}, add=False):
        g = self.graph
        if not hasattr(self, 'nodDct') or len(self.nodInd) != g.vcount():
            self.update_vname()
        edge = self.edge_exists(nameA, nameB)
        if type(edge) is list:
            if not add:
                sys.stdout.write('\tERROR: Failed to add some edges\n')
                self.ownlog.msg(2,'Failed to add some edges','ERROR')
                aid = self.nodDct[nameA]
                bid = self.nodDct[nameB]
                a = g.get_eid(aid,bid,error=False)
                b = g.get_eid(aid,bid,error=False)
                self.failed_edges.append([edge,nameA,nameB,aid,bid,a,b])
                return False
            g.add_edge(edge[0], edge[1])
            edge = self.edge_exists(nameA, nameB)
        # assigning source:
        self.add_set_eattr(edge, 'sources', source)
        # adding references:
        # if len(refs) > 0:
        refs = [_refs.Reference(pmid) for pmid in refs]
        self.add_list_eattr(edge, 'references', refs)
        # updating references-by-source dict:
        self.add_grouped_set_eattr(edge, 'refs_by_source', source, refs)
        # updating refrences-by-type dict:
        self.add_grouped_set_eattr(edge, 'refs_by_type', typ, refs)
        # setting directions:
        if not g.es[edge]['dirs']:
            g.es[edge]['dirs'] = Direction(nameA,nameB)
        if isDir:
            g.es[edge]['dirs'].set_dir((nameA,nameB),source)
            # updating references-by-direction dict:
            self.add_grouped_set_eattr(edge, 'refs_by_dir', (nameA, nameB), refs)
        else:
            g.es[edge]['dirs'].set_dir('undirected',source)
            self.add_grouped_set_eattr(edge, 'refs_by_dir', 'undirected', refs)
        # setting signs:
        if stim:
            g.es[edge]['dirs'].set_sign((nameA,nameB),'positive',source)
        if inh:
            g.es[edge]['dirs'].set_sign((nameA,nameB),'negative',source)
        # updating sources-by-type dict:
        self.add_grouped_set_eattr(edge, 'sources_by_type', typ, source)
        # adding type:
        self.add_list_eattr(edge, 'type', typ)
        # adding extra attributes:
        for key, value in iteritems(extraAttrs):
            if key not in g.es.attributes():
                g.es[key] = [[] for _ in xrange(self.graph.ecount())] \
                    if type(value) is list else [None]
            g.es[edge][key] = self.combine_attr([g.es[edge][key], value])
    
    def add_list_eattr(self, edge, attr, value):
        value = value if type(value) is list else [value]
        e = self.graph.es[edge]
        if attr not in self.graph.es.attributes():
            self.graph.es[attr] = [[] for _ in xrange(0, self.graph.ecount())]
        if e[attr] is None:
            e[attr] = []
        elif type(e[attr]) is not list:
            e[attr] = [e[attr]]
        e[attr] = common.uniqList(e[attr] + value)
    
    def add_set_eattr(self, edge, attr, value):
        value = value if type(value) is set \
            else set(value) if type(value) is list \
            else set([value])
        e = self.graph.es[edge]
        if attr not in self.graph.es.attributes():
            self.graph.es[attr] = [set([]) for _ in xrange(0, self.graph.ecount())]
        if e[attr] is None:
            e[attr] = set([])
        elif type(e[attr]) is not set:
            e[attr] = set(e[attr]) if type(e[attr]) is list else set([e[attr]])
        e[attr].update(value)
    
    def add_grouped_eattr(self, edge, attr, group, value, ):
        value = value if type(value) is list else [value]
        e = self.graph.es[edge]
        if attr not in self.graph.es.attributes():
            self.graph.es[attr] = [{} for _ in xrange(0, self.graph.ecount())]
        if type(e[attr]) is not dict:
            e[attr] = {}
        if  group not in e[attr] or type(e[attr][group]) is None:
            e[attr][group] = []
        elif type(e[attr][group]) is not list:
            e[attr][group] = [e[attr][group]]
        e[attr][group] = common.uniqList(e[attr][group] + value)
    
    def add_grouped_set_eattr(self, edge, attr, group, value):
        value = value if type(value) is set \
            else set(value) if type(value) is list \
            else set([value])
        e = self.graph.es[edge]
        if attr not in self.graph.es.attributes():
            self.graph.es[attr] = [{} for _ in xrange(0, self.graph.ecount())]
        if type(e[attr]) is not dict:
            e[attr] = {}
        if group not in e[attr] or type(e[attr][group]) is None:
            e[attr][group] = set([])
        elif type(e[attr][group]) is not set:
            e[attr][group] = set(e[attr][group]) \
                if type(e[attr][group]) is list else set([e[attr][group]])
        e[attr][group].update(value)
    
    def get_directed(self, graph = False, conv_edges = False, mutual = False, ret = False):
        """
        Converts ``graph`` undirected ``igraph.Graph`` object to a directed one.
        By default it converts the graph in ``PyPath.graph`` and places the directed
        instance in ``PyPath.dgraph``.
        
        @graph : igraph.Graph
            Undirected graph object.
        
        @conv_edges : bool
            Whether to convert undirected edges (those without explicit
            direction information) to an arbitrary direction edge or
            a pair of opposite edges.
            Otherwise those will be deleted. Default is ``False``.
        
        @mutual : bool
            If ``conv_edges`` is ``True``, whether to convert the
            undirected edges to a single, arbitrary directed edge,
            or a pair of opposite directed edges. Default is ``False``.
        
        @ret : bool
            Return the directed graph instance, or return ``None``.
            Default is ``False`` (returns ``None``).
        """
        toDel = []
        g = self.graph if not graph else graph
        d = g.as_directed(mutual = True)
        self.update_vname()
        d.es['directed_sources'] = [[] for _ in xrange(g.ecount())]
        d.es['undirected_sources'] = [[] for _ in xrange(g.ecount())]
        d.es['directed'] = [False for _ in xrange(g.ecount())]
        prg = Progress(total = g.ecount(),
                       name = "Setting directions", interval = 17)
        for e in g.es:
            '''
            This works because in directed graphs get_eid() defaults to
            directed = True, so the source -> target edge is returned.
            '''
            dir_one = (g.vs['name'][e.source], g.vs['name'][e.target])
            dir_two = (g.vs['name'][e.target], g.vs['name'][e.source])
            dir_edge_one = d.get_eid(d.vs['name'].index(g.vs['name'][e.source]),
                                 d.vs['name'].index(g.vs['name'][e.target]))
            dir_edge_two = d.get_eid(d.vs['name'].index(g.vs['name'][e.target]),
                                 d.vs['name'].index(g.vs['name'][e.source]))
            if not e['dirs'].get_dir(dir_one):
                if not conv_edges or e['dirs'].get_dir(dir_two):
                    toDel.append(dir_edge_one)
            else:
                d.es[dir_edge_one]['directed'] = True
                d.es[dir_edge_one]['directed_sources'] += \
                    e['dirs'].get_dir(dir_one, sources = True)
                d.es[dir_edge_one]['undirected_sources'] += \
                    e['dirs'].get_dir('undirected', sources = True)
            if not e['dirs'].get_dir(dir_two):
                if not conv_edges or e['dirs'].get_dir(dir_one):
                    toDel.append(dir_edge_two)
            else:
                d.es[dir_edge_two]['directed'] = True
                d.es[dir_edge_two]['directed_sources'] += \
                    e['dirs'].get_dir(dir_two, sources = True)
                d.es[dir_edge_two]['undirected_sources'] += \
                    e['dirs'].get_dir('undirected', sources = True)
            if e['dirs'].get_dir('undirected') and \
                not e['dirs'].get_dir(dir_one) and \
                not e['dirs'].get_dir(dir_two):
                if conv_edges:
                    d.es[dir_edge_one]['undirected_sources'] += \
                        e['dirs'].get_dir('undirected', sources = True)
                    if mutual:
                        d.es[dir_edge_two]['undirected_sources'] += \
                            e['dirs'].get_dir('undirected', sources = True)
                    else:
                        toDel.append(dir_edge_two)
                else:
                    toDel += [dir_edge_one, dir_edge_two]
            prg.step()
        d.delete_edges(list(set(toDel)))
        prg.terminate()
        deg = d.vs.degree()
        toDel = []
        for v in d.vs:
            if deg[v.index] == 0:
                toDel.append(v.index)
        del self.nodInd
        if len(toDel) > 0:
            d.delete_vertices(list(set(toDel)))
        if not graph:
            self.dgraph = d
            self._directed = self.dgraph
        self._get_directed()
        self._get_undirected()
        self.update_vname()
        if graph or ret:
            return d
    
    def new_edges(self, edges):
        self.graph.add_edges(list(edges))
    
    def new_nodes(self, nodes):
        self.graph.add_vertices(list(nodes))
    
    def edge_exists(self, nameA, nameB):
        '''
        Returns a tuple of vertice indices if edge doesn't exists, 
        otherwise edge id. Not sensitive to direction.
        '''
        if not hasattr(self, 'nodDct'):
            self.update_vname()
        nodes = [self.nodDct[nameA], 
            self.nodDct[nameB]]
        edge = self.graph.get_eid(nodes[0], nodes[1], error = False)
        if edge != -1:
            return edge
        else:
            nodes.sort()
            return nodes
    
    def edge_names(self, e):
        if type(e) is int:
            e = self.graph.es[e]
        return (self.graph.vs[e.source]['name'], 
                self.graph.vs[e.target]['name'])
    
    def node_exists(self, name):
        if not hasattr(self, 'nodInd'):
            self.update_vname()
        return name in self.nodInd
    
    def names2vids(self, names):
        vids = []
        if not hasattr(self, 'nodInd'):
            self.update_vname()
        for n in names:
            if n in self.nodInd:
                vids.append(self.nodDct[n])
        return vids
    
    def get_edge(self, nodes):
        '''
        Returns the edge id only if there is an edge from nodes[0] to nodes[1],
        returns False if edge exists in opposite direction, or no edge exists 
        between the two vertices, or any of the vertice ids doesn't exist.
        To find edges without regarding their direction, see edge_exists().
        '''
        g = self.graph
        try:
            e = g.get_eid(nodes[0],nodes[1])
            return e
        except:
            return False
    
    def straight_between(self,nameA,nameB):
        '''
        This does actually the same as get_edge(), but by names
        instead of vertex ids.
        '''
        nodNm = [nameA,nameB]
        nodNm.sort()
        nodes = [self.graph.vs['name'].index(nodNm[0]),
            self.graph.vs['name'].index(nodNm[1])]
        edge = self.get_edge(nodes)
        if type(edge) is int:
            return edge
        else:
            return nodes
    
    def all_between(self, nameA, nameB):
        '''
        Returns all edges between two given vertex names. Similar to 
        straight_between(), but checks both directions, and returns 
        list of edge ids in [undirected, straight, reveresed] format,
        for both nameA -> nameB and nameB -> nameA edges.
        '''
        g = self.graph
        edges = {'ab': [None, None, None], 'ba': [None, None, None]}
        eid = self.edge_exists(self, nameA, nameB)
        if type(eid) is int:
            if g.es[eid]['dirs'].get_dir('undirected'):
                edges['ab'][0] = eid
                edges['ba'][0] = eid
            if g.es[eid]['dirs'].get_dir((nameA,nameB)):
                edges['ab'][1] = eid
                edges['ba'][2] = eid
            if g.es[eid]['dirs'].get_dir((nameB,nameA)):
                edges['ab'][2] = eid
                edges['ba'][1] = eid
        return edges
     
    def get_node_pair(self, nameA, nameB):
        if not hasattr(self, 'nodDct'):
            self.update_vname()
        g = self.graph
        nodes = [nameA, nameB]
        nodes.sort()
        try:
            nodeA = self.nodDct[nodes[0]]
            nodeB = self.nodDct[nodes[1]]
            return (nodeA, nodeB)
        except:
            return False
    
    def update_attrs(self):
        for attr in self.graph.vs.attributes():
            types = list(set([type(x) for x in self.graph.vs[attr] if x is not None]))
            if len(types) > 1:
                self.ownlog.msg(2,'Vertex attribute `%s` has multiple types of'\
                    ' values: %s' % (attr,', '.join([x.__name__ for x in types])),
                    'WARNING')
            elif len(types) == 0:
                self.ownlog.msg(2,'Vertex attribute `%s` has only None values'\
                % (attr), 'WARNING')
            if len(types) > 0:
                if list in types:
                    self.vertexAttrs[attr] = list
                else:
                    self.vertexAttrs[attr] = types[0]
                self.init_vertex_attr(attr)
        for attr in list(set(self.graph.es.attributes()) - set(['dirs'])):
            types = list(set([type(x) for x in self.graph.es[attr] if x is not None]))
            if len(types) > 1:
                self.ownlog.msg(2,'Edge attribute `%s` has multiple types of'\
                    ' values: %s' % (attr,', '.join([x.__name__ for x in types])),
                    'WARNING')
            elif len(types) == 0:
                self.ownlog.msg(2,'Edge attribute `%s` has only None values'\
                % (attr), 'WARNING')
            if len(types) > 0:
                if list in types:
                    self.edgeAttrs[attr] = list
                else:
                    self.edgeAttrs[attr] = types[0]
                self.init_edge_attr(attr)
    
    def init_vertex_attr(self,attr):
        for v in self.graph.vs:
            if v[attr] is None:
                v[attr] = self.vertexAttrs[attr]()
            if self.vertexAttrs[attr] is list and type(v[attr]) in common.simpleTypes:
                v[attr] = [v[attr]] if len(v[attr]) > 0 else []
    
    def init_edge_attr(self, attr):
        for e in self.graph.es:
            if e[attr] is None:
                e[attr] = self.edgeAttrs[attr]()
            if self.edgeAttrs[attr] is list and type(e[attr]) in common.simpleTypes:
                e[attr] = [e[attr]] if len(e[attr]) > 0 else []
    
    def attach_network(self, edgeList = False, regulator = False):
        g = self.graph
        if not edgeList:
            if self.raw_data is not None:
                edgeList = self.raw_data
            else:
                self.ownlog.msg(2,"attach_network(): No data, nothing to do.",'INFO')
                return True
        if type(edgeList) == str:
            if edgeList in self.data:
                edgeList = self.data[edgeList]
            else:
                self.ownlog.msg(2,
                    "`%s' looks like a source name, but no data"\
                    "available under this name." % (edgeList),'ERROR')
                return False
        nodes = []
        edges = []
        # adding nodes and edges first in bunch, 
        # to avoid multiple reindexing by igraph
        self.update_vname()
        prg = Progress(
            total=len(edgeList),name="Processing nodes",interval=50)
        for e in edgeList:
            aexists = self.node_exists(e["defaultNameA"])
            bexists = self.node_exists(e["defaultNameB"])
            if not aexists and (not regulator or bexists):
                nodes.append(e["defaultNameA"])
            if not bexists and not regulator:
                nodes.append(e["defaultNameB"])
            prg.step()
        prg.terminate()
        self.new_nodes(set(nodes))
        self.ownlog.msg(2,'New nodes have been created','INFO')
        self.update_vname()
        prg = Progress(
            total=len(edgeList), name='Processing edges', interval=50)
        for e in edgeList:
            aexists = self.node_exists(e["defaultNameA"])
            bexists = self.node_exists(e["defaultNameB"])
            if aexists and bexists:
                edge = self.edge_exists(e["defaultNameA"], e["defaultNameB"])
                if type(edge) is list:
                    edges.append(tuple(edge))
                prg.step()
        prg.terminate()
        self.new_edges(set(edges))
        self.ownlog.msg(2,"New edges have been created",'INFO')
        self.ownlog.msg(2,("""Introducing new node and edge attributes..."""), 'INFO')
        prg = Progress(
            total=len(edgeList),name="Processing attributes",interval=30)
        nodes_updated = []
        self.update_vname()
        for e in edgeList:
            # adding new node attributes
            if e["defaultNameA"] not in nodes_updated:
                defAttrs = {
                    "name": e["defaultNameA"], 
                    "label": e["defaultNameA"], 
                    "nameType": e["defaultNameTypeA"], 
                    "type": e["typeA"],
                    "ncbi_tax_id": e["taxA"]}
                self.add_update_vertex(
                    defAttrs, e["nameA"], 
                    e["nameTypeA"], e["attrsNodeA"])
                nodes_updated.append(e["defaultNameA"])
            if e["defaultNameB"] not in nodes_updated:
                defAttrs = {
                    "name": e["defaultNameB"], 
                    "label": e["defaultNameB"], 
                    "nameType": e["defaultNameTypeB"], 
                    "type": e["typeB"],
                    "ncbi_tax_id": e["taxB"]}
                self.add_update_vertex(
                    defAttrs, e["nameB"], 
                    e["nameTypeB"], e["attrsNodeB"])
                nodes_updated.append(e["defaultNameB"])
            # adding new edge attributes
            self.add_update_edge(
                e["defaultNameA"], e["defaultNameB"], 
                e["source"], e["isDirected"], 
                e["references"], e["stim"], e["inh"], 
                e["taxA"], e["taxB"], e["type"], e["attrsEdge"])
            prg.step()
        prg.terminate()
        self.raw_data = None
        self.update_attrs()
    
    def apply_list(self,name,node_or_edge="node"):
        if name not in self.lists:
            self.ownlog.msg(1,("""No such list: %s""" % name), 'ERROR')
            return None
        g = self.graph
        if node_or_edge == "edge":
            g.es[name] = [None]
        else:
            g.vs[name] = [None]
        if type(self.lists[name]) is dict:
            if node_or_edge == "edge":
                for e in g.es:
                    if (v[e.source]["name"],v[e.target]["name"]) in self.lists[name]:
                        e[name] = self.lists[name][(v[e.source]["name"],v[e.target]["name"])]
                    if (v[e.target]["name"],v[e.source]["name"]) in self.lists[name]:
                        e[name] = self.lists[name][(v[e.target]["name"],v[e.source]["name"])]
            else:
                for v in g.vs:
                    if v["name"] in self.lists[name]:
                        v[name] = self.lists[name][v["name"]]
        if type(self.lists[name]) is list:
            if node_or_edge == "edge":
                for e in g.es:
                    if (v[e.source]["name"],v[e.target]["name"]) in self.lists[name]:
                        e[name] = True
                    else:
                        e[name] = False
            else:
                for v in g.vs:
                    if v["name"] in self.lists[name]:
                        v[name] = True
                    else:
                        v[name] = False
    
    def merge_lists(self,nameA,nameB,name=None,and_or="and",delete=False,func="max"):
        if nameA not in self.lists:
            self.ownlog.msg(1,("""No such list: %s""" % nameA), 'ERROR')
            return None
        if nameB not in self.lists:
            self.ownlog.msg(1,("""No such list: %s""" % nameB), 'ERROR')
            return None
        name = '_'.join([nameA,nameB]) if name is None else name
        if type(self.lists[nameA]) is list and type(self.lists[nameB]) is list:
            if and_or == "and":
                self.lists[name] = list(set(self.lists[nameA]) | set(self.lists[nameB]))
            if and_or == "or":
                self.lists[name] = list(set(self.lists[nameA]) & set(self.lists[nameB]))
        if type(self.lists[nameA]) is dict and type(self.lists[nameB]) is dict:
            self.lists[name] = {}
            if and_or == "and":
                keys = list(set(self.lists[nameA].keys) | set(self.lists[nameB].keys()))
                for k in keys:
                    if k in self.lists[nameA]:
                        self.lists[name][k] = self.lists[nameA][k]
                    if k in self.lists[nameB]:
                        self.lists[name][k] = self.lists[nameB][k]
                    if k in self.lists[nameA] and k in self.lists[nameB]:
                        self.lists[name][k] = self.combine_attr([self.lists[nameA][k],
                                                             self.lists[nameB][k]])
            if and_or == "or":
                keys = list(set(self.lists[nameA].keys) & set(self.lists[nameB].keys()))
                for k in keys:
                    self.lists[name][k] = self.combine_attr([self.lists[nameA][k],
                                                             self.lists[nameB][k]])
        if delete:
            del self.lists[nameA]
            del self.lists[nameB]
    
    def save_session(self):
        pickleFile = "pwnet-"+self.session+".pickle"
        self.ownlog.msg(1,("""Saving session to %s... """ % pickleFile), 'INFO')
        with open( pickleFile, "wb" ) as f:
            pickle.dump(self, f)
    
    ###
    ### functions for plotting // with custom typeface ;)
    ###
    
    #
    # functions to compare networks and pathways
    #
    
    def databases_similarity(self, index = 'simpson'):
        g = self.graph
        edges = {}
        nodes = {}
        self.update_sources()
        nodes = dict([(s, [v.index for v in g.vs if s in v['sources']]) \
            for s in self.sources])
        edges = dict([(s, [e.index for e in g.es if s in e['sources']]) \
            for s in self.sources])
        sNodes = self.similarity_groups(nodes, index = index)
        sEdges = self.similarity_groups(edges, index = index)
        return {'nodes': sNodes, 'edges': sEdges}
    
    def similarity_groups(self, groups, index = 'simpson'):
        index_func = '%s_index'%index
        # these are imported into globals() from common:
        if hasattr(sys.modules['%s.common'%self.__module__.split('.')[0]], index_func):
            to_call = getattr(sys.modules['%s.common'%self.__module__.split('.')[0]],
                index_func)
            grs = sorted(groups.keys())
            sor = dict([(g, {}) for g in grs])
            for g1 in xrange(0,len(grs)):
                for g2 in xrange(g1,len(grs)):
                    sor[grs[g1]][grs[g2]] = to_call(groups[grs[g1]],
                        groups[grs[g2]])
                    sor[grs[g2]][grs[g1]] = sor[grs[g1]][grs[g2]]
            return sor
        else:
            self.ownlog.msg(2, 'No such function: %s()'%index_func, 'ERROR')
    
    def sorensen_pathways(self,pwlist=None):
        g = self.graph
        if pwlist is None:
            pwlist = self.pathway_types
        for p in pwlist:
            if p not in g.vs.attributes():
                self.ownlog.msg(2,("No such vertex attribute: %s" % p),'ERROR')
        edges = {}
        nodes = {}
        for e in g.es:
            indA = e.source
            indB = e.target
            pwsA = []
            pwsB = []
            for p in pwlist:
                if g.vs[indA][p] is not None:
                    for pw in g.vs[indA][p]:
                        thisPw = p.replace("_pathways","__") + pw
                        if thisPw not in nodes:
                            nodes[thisPw] = []
                        nodes[thisPw].append(indA)
                        pwsA.append(thisPw)
                if g.vs[indB][p] is not None:
                    for pw in g.vs[indB][p]:
                        thisPw = p.replace("_pathways","__") + pw
                        if thisPw not in nodes:
                            nodes[thisPw] = []
                        nodes[thisPw].append(indB)
                        pwsB.append(thisPw)
            pwsE = set(pwsA).intersection(set(pwsB))
            for pw in pwsE:
                if pw not in edges:
                    edges[pw] = []
                edges[pw].append(e.index)
        sNodes = self.sorensen_groups(nodes)
        sEdges = self.sorensen_groups(edges)
        return {"nodes": sNodes, "edges": sEdges}
    
    def write_table(self,tbl,outfile,sep="\t",cut=None,colnames=True,rownames=True):
        out = ''
        rn = tbl.keys()
        if "header" in rn:
            cn = tbl["header"]
            del tbl["header"]
            rn.remove("header")
        else:
            cn = [str(i) for i in xrange(0,len(tbl[rn[0]]))]
        if colnames:
            if rownames:
                out += sep
            out += sep.join(cn) + "\n"
        for r in rn:
            if rownames:
                out += str(r)[0:cut] + sep
            thisRow = [str(i) for i in tbl[r]]
            out += sep.join(thisRow) + "\n"
        f = codecs.open(self.outdir+outfile, encoding='utf-8', mode='w')
        f.write(out)
        f.close()
    
    def search_attr_or(self,obj,lst):
        if len(lst) == 0:
            return True
        for a,v in iteritems(lst):
            if (type(v) is list and len(set(obj[a]).intersection(v)) > 0
                ) or (type(v) is not list and obj[a] == v):
                return True
        return False
    
    def search_attr_and(self,obj,lst):
        for a,v in iteritems(lst):
            if (type(v) is list and len(set(obj[a]).intersection(v)) == 0
                ) or (type(v) is not list and obj[a] != v):
                return False
        return True
    
    def get_sub(self, crit, andor="or", graph = None):
        g = self.graph if graph is None else graph
        keepV = []
        delE = []
        if andor == "and":
            for e in g.es:
                keepThis = self.search_attr_and(e,crit["edge"])
                if keepThis:
                    keepA = self.search_attr_and(g.vs[e.source],crit["node"])
                    if keepA:
                        keepV += [e.source]
                    keepB = self.search_attr_and(g.vs[e.target],crit["node"])
                    if keepB:
                        keepV += [e.target]
                    if not keepA or not keepB:
                        delE += [e.index]
                else:
                    delE += [e.index]
        else:
            for e in g.es:
                keepThis = self.search_attr_or(e,crit["edge"])
                if keepThis:
                    keepV += [e.source,e.target]
                    continue
                else:
                    delE += [e.index]
                if len(crit["node"]) > 0:
                    keepA = self.search_attr_or(g.vs[e.source],crit["node"])
                    if keepA:
                        keep += [e.source]
                    keepB = self.search_attr_or(g.vs[e.target],crit["node"])
                    if keepB:
                        keep += [e.target]
        return {"nodes": list(set(keepV)), "edges": list(set(delE))}
    
    def edgeseq_inverse(self,edges):
        g = self.graph
        inv = []
        for e in g.es:
            if e.index not in set(edges):
                inv.append(e.index)
        return inv
    
    def get_network(self, crit, andor="or", graph = None):
        g = self.graph if graph is None else graph
        sub = self.get_sub(crit, andor = andor, graph = g)
        new = g.copy()
        new.delete_edges(sub["edges"])
        return new.induced_subgraph(sub["nodes"])
    
    def separate(self):
        return dict([(s, self.get_network({'edge': {'sources': [s]}, 'node': {}})) \
            for s in self.sources])
    
    def separate_by_category(self):
        cats = dict(map(lambda c: (c, []), set(data_formats.categories.values())))
        for s, c in iteritems(data_formats.categories):
            cats[c].append(s)
        return dict([(c, self.get_network({'edge': {'sources': s}, 'node': {}})) \
            for c, s in iteritems(cats)])
    
    def update_pathway_types(self):
        g = self.graph
        pwTyp = []
        for i in g.vs.attributes():
            if i.find("_pathways") > -1:
                pwTyp.append(i)
        self.pathway_types = pwTyp
    
    def source_similarity(self,outfile=None):
        if outfile is None:
            outfile = ''.join(["pwnet-", self.session,"-sim-src"])
        res = self.sorensen_databases()
        self.write_table(res["nodes"],outfile+"-nodes")
        self.write_table(res["edges"],outfile+"-edges")
    
    def pathway_similarity(self,outfile=None):
        if outfile is None:
            outfile = ''.join(["pwnet-", self.session,"-sim-pw"])
        self.update_pathway_types()
        res = self.sorensen_pathways()
        self.write_table(res["nodes"],outfile+"-nodes",cut=20)
        self.write_table(res["edges"],outfile+"-edges",cut=20)
    
    def update_sources(self):
        g = self.graph
        src = []
        for e in g.es:
            src += e["sources"]
        self.sources = list(set(src))
    
    def update_pathways(self):
        g = self.graph
        pws = {}
        for v in g.vs:
            for k in g.vs.attributes():
                if k.find('_pathways') > -1:
                    if k not in pws:
                        pws[k] = []
                    if v[k] is not None:
                        for p in v[k]:
                            if p not in set(pws[k]):
                                pws[k].append(p)
        self.pathways = pws
    
    def delete_unmapped(self):
        if "unmapped" in self.graph.vs["name"]:
            self.graph.delete_vertices(self.graph.vs.find(name="unmapped").index)
            self.update_db_dict()
            self.update_vname()
    
    def genesymbol_labels(self, graph = None, remap_all = False):
        '''
        Creats vertex attribute ``label`` and fills up with Gene Symbols
        of all proteins where the Gene Symbol can be looked up based on
        the default name of the protein vertex.
        If the attribute ``label`` had been already initialized, 
        updates this attribute or recreates if ``remap_all`` 
        is ``True``.
        '''
        self._already_has_directed()
        if graph is None and self.dgraph is not None:
            self.genesymbol_labels(graph = self.dgraph, remap_all = remap_all)
        g = self.graph if graph is None else graph
        defaultNameType = self.default_name_type["protein"]
        geneSymbol = "genesymbol"
        if 'label' not in g.vs.attributes():
            remap_all = True
        labels = [None if remap_all or v['label'] == v['name'] else v['label'] for v in g.vs]
        for v, l, i in zip(g.vs, labels, xrange(g.vcount())):
            if l is None and v['type'] == 'protein':
                label = self.mapper.map_name(v['name'], defaultNameType, geneSymbol)
                if len(label) == 0:
                    labels[i] = v['name']
                else:
                    labels[i] = label[0]
        g.vs['label'] = labels
    
    def network_stats(self, outfile = None):
        '''
        Calculates basic statistics for the whole network 
        and each of sources. Writes the results in a tab file.
        '''
        if outfile is None:
            outfile = '-'.join(["pwnet",self.session,"stats"])
        stats = {}
        stats['header'] = ["vnum", "enum", "deg_avg", "diam", 
                           "trans", "adh", "coh"]
        for k in xrange(0,len(self.sources)+1):
            s = "All" if k == len(self.sources) else self.sources[k]
            g = self.graph if k == len(self.sources) else self.get_network({
                "edge": {"sources": [s]}, "node": {}})
            if g.vcount() > 0:
                stats[s] = [g.vcount(), g.ecount(),
                    sum(g.vs.degree())/float(len(g.vs)),
                    g.diameter(), g.transitivity_undirected(), g.adhesion(),
                    g.cohesion()]
        self.write_table(stats, outfile)
    
    def degree_dists(self):
        dds = {}
        for s in self.sources:
            g = self.get_network({"edge": {"sources": [s]}, "node": {}})
            if g.vcount() > 0:
                dds[s] = g.degree_distribution()
        for k,v in iteritems(dds):
            filename = ''.join([self.outdir,"pwnet-",self.session,"-degdist-",k])
            bins = []
            vals = []
            for i in v.bins():
                bins.append(int(i[0]))
                vals.append(int(i[2]))
            out = ''.join([';'.join(str(x) for x in bins),"\n",
                           ';'.join(str(x) for x in vals),"\n"])
            f = codecs.open(filename, encoding='utf-8', mode='w')
            f.write(out)
            f.close()
    
    def intergroup_shortest_paths(self,groupA,groupB,random=False):
        self.update_sources()
        if groupA not in self.graph.vs.attributes():
            self.ownlog.msg(2,("No such attribute: %s" % groupA),'ERROR')
            return False
        if groupB not in self.graph.vs.attributes():
            self.ownlog.msg(2,("No such attribute: %s" % groupB),'ERROR')
            return False
        deg_pathlen = {}
        rat_pathlen = {}
        rand_pathlen = {}
        diam_pathlen = {}
        for k in xrange(0,len(self.sources)+1):
            s = "All" if k == len(self.sources) else self.sources[k]
            outfile = '-'.join([s,groupA,groupB,"paths"])
            f = self.graph if k == len(self.sources) else self.get_network({
                "edge": {"sources": [s]}, "node": {}})
            paths = []
            grA = []
            grB = []
            for v in f.vs:
                if v[groupA]:
                    grA.append(v.index)
                if v[groupB]:
                    grB.append(v.index)
            for v in f.vs:
                if v[groupB]:
                    pt = f.get_shortest_paths(v.index,grA,output="epath")
                    for p in pt:
                        l = len(p) 
                        if l > 0:
                            paths.append(l)
                    if(v.index in grA):
                        paths.append(0)
            self.write_table({"paths": paths}, outfile,sep=";",colnames=False,rownames=False)
            deg = f.vs.degree()
            mean_pathlen = sum(paths)/float(len(paths))
            deg_pathlen[s] = [mean_pathlen, sum(deg)/float(len(deg))]
            rat_pathlen[s] = [mean_pathlen,
                                f.vcount()/float(len(list(set(grA+grB))))]
            diam_pathlen[s] = [mean_pathlen, f.diameter()]
            if random:
                groupA_random = groupA+"_random"
                groupB_random = groupB+"_random"
                random_pathlen = []
                for i in xrange(0,100):
                    f.vs[groupA_random] = copy.copy(f.vs[groupA])
                    f.vs[groupB_random] = copy.copy(f.vs[groupB])
                    random.shuffle(f.vs[groupA_random])
                    random.shuffle(f.vs[groupB_random])
                    paths = []
                    grA = []
                    grB = []
                    for v in f.vs:
                        if v[groupA_random]:
                            grA.append(v.index)
                        if v[groupB_random]:
                            grB.append(v.index)
                    for v in f.vs:
                        if v[groupB_random]:
                            pt = f.get_shortest_paths(v.index,grA,output="epath")
                            for p in pt:
                                l = len(p) 
                                if l > 0:
                                    paths.append(l)
                            if(v.index in grA):
                                paths.append(0)
                    if len(paths) > 0:
                        random_pathlen.append(sum(paths)/float(len(paths)))
                if len(random_pathlen) > 0:
                    rand_pathlen[s] = [mean_pathlen,
                                        sum(random_pathlen)/float(len(random_pathlen))]
                else:
                    rand_pathlen[s] = [mean_pathlen, 0.0]
        deg_pathlen["header"] = ["path_len","degree"]
        self.write_table(deg_pathlen,"deg_pathlen",sep=";")
        diam_pathlen["header"] = ["path_len","diam"]
        self.write_table(diam_pathlen,"diam_pathlen",sep=";")
        rat_pathlen["header"] = ["path_len","ratio"]
        self.write_table(rat_pathlen,"rat_pathlen",sep=";")
        if random:
            rand_pathlen["header"] = ["path_len","random"]
            self.write_table(rand_pathlen,"rand_pathlen",sep=";")
    
    def update_vertex_sources(self):
        g = self.graph
        for attr in ['sources', 'references']:
            g.vs[attr] = [set([]) for _ in g.vs]
            for e in g.es:
                g.vs[e.source][attr].update(e[attr])
                g.vs[e.target][attr].update(e[attr])
    
    def set_categories(self):
        self.graph.vs['cat'] = [set([]) for _ in self.graph.vs]
        self.graph.es['cat'] = [set([]) for _ in self.graph.es]
        self.graph.es['refs_by_cat'] = [{} for _ in self.graph.es]
        for v in self.graph.vs:
            for s in v['sources']:
                if s in data_formats.categories:
                    v['cat'].add(data_formats.categories[s])
        for e in self.graph.es:
            for s in e['sources']:
                if s in data_formats.categories:
                    cat = data_formats.categories[s]
                    e['cat'].add(cat)
                    if cat not in e['refs_by_cat']:
                        e['refs_by_cat'][cat] = set([])
                    if s in e['refs_by_source']:
                        e['refs_by_cat'][cat].update(e['refs_by_source'][s])
    
    def basic_stats_intergroup(self,groupA,groupB,header=None):
        result = {}
        g = self.graph
        for k in xrange(0,len(self.sources)+1):
            s = "All" if k == len(self.sources) else self.sources[k]
            f = self.graph if k == len(self.sources) else self.get_network(
                {"edge": {"sources": set([s])}, "node": {}})
            deg = f.vs.degree()
            bw = f.vs.betweenness()
            vnum = f.vcount()
            enum = f.ecount()
            cancerg = 0
            drugt = 0
            cdeg = []
            tdeg = []
            ddeg = []
            cbw = []
            tbw = []
            dbw = []
            cg = []
            dt = []
            for v in f.vs:
                tdeg.append(deg[v.index])
                tbw.append(bw[v.index])
                if v['name'] in self.lists[groupA]:
                    cg.append(v['name'])
                    cancerg += 1
                    cdeg.append(deg[v.index])
                    cbw.append(bw[v.index])
                if v['name'] in self.lists[groupB]:
                    dt.append(v['name'])
                    drugt += 1
                    ddeg.append(deg[v.index])
                    dbw.append(bw[v.index])
            cpct = cancerg*100/float(len(self.lists[groupA]))
            dpct = drugt*100/float(len(self.lists[groupB]))
            tdgr = sum(tdeg)/float(len(tdeg))
            cdgr = sum(cdeg)/float(len(cdeg))
            ddgr = sum(ddeg)/float(len(ddeg))
            tbwn = sum(tbw)/float(len(tbw))
            cbwn = sum(cbw)/float(len(cbw))
            dbwn = sum(dbw)/float(len(dbw))
            src = []
            csrc = []
            dsrc = []
            for e in f.es:
                src.append(len(e["sources"]))
                if f.vs[e.source][groupA] or f.vs[e.target][groupA]:
                    csrc.append(len(e["sources"]))
                if f.vs[e.source][groupB] or f.vs[e.target][groupB]:
                    dsrc.append(len(e["sources"]))
            snum = sum(src)/float(len(src))
            csnum = sum(csrc)/float(len(csrc))
            dsnum = sum(dsrc)/float(len(dsrc))
            result[s] = [s,str(vnum),str(enum),str(cancerg),str(drugt),
                            str(cpct),str(dpct),
                            str(tdgr),str(cdgr),str(ddgr),str(tbwn),str(cbwn),str(dbwn),
                            str(snum),str(csnum),str(dsnum)]
        outfile = '-'.join([groupA,groupB,"stats"])
        if header is None:
            self.write_table(result,outfile,colnames=False)
        else:
            result["header"] = header
            self.write_table(result,outfile,colnames=True)
    
    def sources_venn_data(self):
        result = {}
        self.update_sources()
        g = self.graph
        for i in self.sources:
            for j in self.sources:
                ini = []
                inj = []
                for e in g.es:
                    if i in e["sources"]:
                        ini.append(e.index)
                    if j in e["sources"]:
                        inj.append(e.index)
                onlyi = str(len(list(set(ini) - set(inj))))
                onlyj = str(len(list(set(inj) - set(ini))))
                inter = str(len(list(set(ini) & set(inj))))
                result[i+"-"+j] = [i,j,onlyi,onlyj,inter]
        self.write_table(result,"sources-venn-data.csv")
    
    def sources_hist(self):
        srcnum = []
        for e in self.graph.es:
            srcnum.append(len(e["sources"]))
        self.write_table(
            {"srcnum": srcnum},"source_num",sep=";",rownames=False,colnames=False)
    
    def degree_dist(self,prefix,g,group=None):
        deg = g.vs.degree()
        self.write_table({"deg": deg}, prefix+"-whole-degdist",sep=";",
                         rownames=False,colnames=False)
        if group != None:
            if len(set(group) - set(self.graph.vs.attributes())) > 0:
                self.ownlog.msg(2,("Missing vertex attribute!"),'ERROR')
                return False
            if type(group) is not list:
                group = [group]
            for gr in group:
                dgr = []
                i = 0
                for v in g.vs:
                    if v[gr]:
                        dgr.append(deg[i])
                    i += 1
                self.write_table({"deg": dgr}, prefix+"-"+gr+"-degdist",sep=";",
                                 rownames=False,colnames=False)
    
    def delete_by_source(self,source,vertexAttrsToDel=None,edgeAttrsToDel=None):
        self.update_vertex_sources()
        g = self.graph
        verticesToDel = []
        for v in g.vs:
            if len(v['sources'] - set([source])) == 0:
                verticesToDel.append(v.index)
        g.delete_vertices(verticesToDel)
        edgesToDel = []
        for e in g.es:
            if len(e['sources'] - set([source])) == 0:
                edgesToDel.append(e.index)
            else:
                e['sources'] = set(e['sources']) - set([source])
        g.delete_edges(edgesToDel)
        if vertexAttrsToDel is not None:
            for vAttr in vertexAttrsToDel:
                if vAttr in g.vs.attributes():
                    del g.vs[vAttr]
        if edgeAttrsToDel is not None:
            for eAttr in edgeAttrsToDel:
                if eAttr in g.vs.attributes():
                    del g.vs[eAttr]
        self.update_vertex_sources()
    
    def reference_hist(self,filename=None):
        g = self.graph
        tbl = []
        for e in g.es:
            tbl.append((
                g.vs[e.source]['name'],
                g.vs[e.target]['name'],
                str(len(e['references'])),
                str(len(e['sources']))
            ))
        if filename is None:
            filename = self.outdir+"/"+self.session+"-refs-hist"
        out = ''
        for i in tbl:
            out += "\t".join(list(i)) + "\n"
        outf = codecs.open(filename, encoding='utf-8', mode='w')
        outf.write(out[:-1])
        outf.close()
    
    def load_resources(self, lst = omnipath, exclude = [], cache_files = {},
        reread = False, redownload = False):
        '''
        Loads multiple resources, and cleans up after. 
        Looks up ID types, and loads all ID conversion 
        tables from UniProt if necessary. This is much
        faster than loading the ID conversion and the 
        resources one by one.
        '''
        self.load_reflists()
        huge = dict((k, v) for k, v in iteritems(lst) \
            if v.huge and k not in exclude and v.name not in cache_files)
        nothuge = dict((k, v) for k, v in iteritems(lst) \
            if (not v.huge or v.name in cache_files) and k not in exclude)
        for lst in [huge, nothuge]:
            ac_types = set([])
            for k, v in iteritems(lst):
                if type(v.nameTypeA) is list:
                    ac_types = ac_types | set(v.nameTypeA)
                else:
                    ac_types.add(v.nameTypeA)
                if type(v.nameTypeB) is list:
                    ac_types = ac_types | set(v.nameTypeB)
                else:
                    ac_types.add(v.nameTypeB)
            table_loaded = set([])
            for ids in self.mapper.tables.keys():
                if ids[1] == 'uniprot':
                    table_loaded.add(ids[0])
            self.mapper.load_uniprot_mappings(list(ac_types - table_loaded & \
                set(self.mapper.name_types.keys())))
            for k, v in iteritems(lst):
                self.load_resource(v, clean = False,
                        cache_files = cache_files,
                        reread = reread,
                        redownload = redownload)
                #try:
                #    self.load_resource(v, clean = False,
                #        cache_files = cache_files,
                #        reread = reread,
                #        redownload = redownload)
                #except:
                #    sys.stdout.write('\t:: Could not load %s, unexpected error '\
                #        'occurred, see %s for error.\n'%(k, self.ownlog.logfile))
                #    self.ownlog.msg(1, 'Error at loading %s: \n%s\n, \t%s, %s\n' % \
                #            (k, sys.exc_info()[1],
                #            sys.exc_info()[2],
                #            sys.exc_info()[0]),
                #        'ERROR')
                #    sys.stdout.flush()
        sys.stdout.write('\n')
        self.clean_graph()
        self.update_sources()
        self.update_vertex_sources()
        sys.stdout.write(
            '''\n » %u interactions between %u nodes\n from %u'''\
            ''' resources have been loaded,\n for details see the log: ./%s\n''' %
            (self.graph.ecount(), self.graph.vcount(), 
            len(self.sources), self.ownlog.logfile))
    
    def load_mappings(self):
        self.mapper.load_mappings(maps=data_formats.mapList)
    
    def load_resource(self, settings, clean = True, cache_files = {},
        reread = False, redownload = False):
        sys.stdout.write(' » '+settings.name+'\n')
        self.read_data_file(settings, cache_files = cache_files,
            reread = reread, redownload = redownload)
        self.attach_network()
        if clean:
            self.clean_graph()
        self.update_sources()
        self.update_vertex_sources()
    
    def load_reflists(self, reflst = None):
        if reflst is None:
            reflst = reflists.get_reflists()
        for rl in reflst:
            self.load_reflist(rl)
    
    def load_reflist(self, reflist):
        reflist.load()
        idx = (reflist.nameType,reflist.typ,reflist.tax)
        self.reflists[idx] = reflist
    
    def load_negatives(self):
        for k,v in iteritems(negative):
            sys.stdout.write(' » '+v.name+'\n')
            self.apply_negative(v)
    
    def list_resources(self):
        sys.stdout.write(' » omnipath\n')
        for k,v in iteritems(omnipath):
            sys.stdout.write('\t:: %s (%s)\n' % (v.name,k))
        sys.stdout.write(' » good\n')
        for k,v in iteritems(good):
            sys.stdout.write('\t:: %s (%s)\n' % (v.name,k))
    
    def info(self,name):
        d = descriptions.descriptions
        if name not in d:
            sys.stdout.write(' :: Sorry, no description available about %s\n' % name)
            return None
        dd = d[name]
        out = '\n\t::: %s :::\n\n' % name
        if 'urls' in dd:
            if 'webpages' in dd['urls']:
                out += '\t:: Webpages:\n'
                for w in dd['urls']['webpages']:
                    out += '\t    » %s\n' % w
            if 'articles' in dd['urls']:
                out += '\t:: Articles:\n'
                for w in dd['urls']['articles']:
                    out += '\t    » %s\n' % w
        if 'taxons' in dd:
            out += '\t:: Taxons: %s\n' % ', '.join(dd['taxons'])
        if 'descriptions' in dd and len(dd['descriptions']) > 0:
            out += '\n\t:: From the authors:\n'
            txt = dd['descriptions'][0].split('\n')
            txt = '\n\t'.join(['\n\t'.join(textwrap.wrap(t,50)) for t in txt])
            out += '\t\t %s\n' % txt.replace('\t\t','\t    ')
        if 'notes' in dd and len(dd['notes']) > 0:
            out += '\n\t:: Notes:\n'
            txt = dd['notes'][0].split('\n')
            txt = '\n\t'.join(['\n\t'.join(textwrap.wrap(t,50)) for t in txt])
            out += '\t\t %s\n\n' % txt.replace('\t\t','\t    ')
        sys.stdout.write(out)
    
    #
    # functions to make life easier
    #
    
    def having_attr(self, attr, graph = None, index = True, edges = True):
        graph = graph or self.graph
        es_or_vs = getattr(graph, 'es' if edges else 'vs')
        if attr in es_or_vs.attributes():
            for i in es_or_vs:
                if something(i[attr]):
                    yield i.index if index else i
    
    def having_eattr(self, attr, graph = None, index = True):
        return self.having_attr(attr, graph, index)
    
    def having_vattr(self, attr, graph = None, index = True):
        return self.having_attr(attr, graph, index, False)
    
    def having_ptm(self, index = True, graph = None):
        return self.having_eattr('ptm', graph, index)
    
    def loop_edges(self, index = True, graph = None):
        graph = graph or self.graph
        for e in graph.es:
            if e.source == e.target:
                yield e.index if index else e
    
    #
    # functions to make topological analysis on the graph
    #
    
    def first_neighbours(self, node, indices=False):
        g = self.graph
        lst = []
        if type(node) is not int:
            node = g.vs.select(name=node)
            if len(node) > 0:
                node = node[0].index
            else:
                return lst
        lst = list(set(g.neighborhood(node))-set([node]))
        if indices:
            return lst
        else:
            nlst = []
            for v in lst:
                nlst.append(g.vs[v]['name'])
            return nlst
    
    def second_neighbours(self, node, indices = False, with_first = False):
        g = self.graph
        lst = []
        if type(node) is int:
            node_i = node 
            node_n = g.vs[node_i]['name']
        else:
            node_i = g.vs.select(name=node)
            if len(node_i) > 0:
                node_i = node_i[0].index
                node_n = node
            else:
                return lst
        first = self.first_neighbours(node_i, indices = indices)
        for n in first:
            lst += self.first_neighbours(n, indices = indices)
        if with_first:
            lst += first
        else:
            lst = list(set(lst)-set(first))
        if indices:
            return list(set(lst)-set([node_i]))
        else:
            return list(set(lst)-set([node_n]))
    
    def all_neighbours(self, indices=False):
        g = self.graph
        g.vs['neighbours'] = [[] for _ in xrange(g.vcount())]
        prg = Progress(
            total=g.vcount(),name="Searching neighbours",interval=30)
        for v in g.vs:
            v['neighbours'] = self.first_neighbours(v.index,indices=indices)
            prg.step()
        prg.terminate()
    
    def jaccard_edges(self):
        g = self.graph
        self.all_neighbours(indices=True)
        metaEdges = []
        prg = Progress(
            total=g.vcount(),name="Calculating Jaccard-indices",interval=11)
        for v in xrange(0,g.vcount()-1):
            for w in xrange(v+1,g.vcount()):
                vv = g.vs[v]
                vw = g.vs[w]
                ja = (len(set(vv['neighbours']) & set(vw['neighbours']))
                / float(len(vv['neighbours'])+len(vw['neighbours'])))
                metaEdges.append((vv['name'],vw['name'],ja))
            prg.step()
        prg.terminate()
        return metaEdges
    
    def jaccard_meta(self,jedges,critical):
        edges = []
        for e in jedges:
            if e[2] > critical:
                edges.append((e[0],e[1]))
        return igraph.Graph.TupleList(edges)
    
    def apply_negative(self,settings):
        g = self.graph
        if settings.name not in self.negatives:
            self.raw_data = None
            self.read_data_file(settings)
            self.negatives[settings.name] = self.raw_data
        neg = self.negatives[settings.name]
        prg = Progress(
        total=len(neg),name="Matching interactions",interval=11)
        matches = 0
        g.es['negative'] = [set([]) if e['negative'] is None else e['negative'] for e in g.es]
        g.es['negative_refs'] = [set([]) if e['negative_refs'] is None else e['negative_refs'] for e in g.es]
        for n in neg:
            aexists = n["defaultNameA"] in g.vs['name']
            bexists = n["defaultNameB"] in g.vs['name']
            if aexists and bexists:
                edge = self.edge_exists(n["defaultNameA"],n["defaultNameB"])
                if type(edge) is int:
                    g.es[edge]['negative'].add(settings.name)
                    refs = set(list(map(lambda r: _refs.Reference(int(r)), n['attrsEdge']['references'])))
                    g.es[edge]['negative_refs'].add(refs)
                    matches += 1
            prg.step()
        prg.terminate()
        sys.stdout.write('\t%u matches found with negative set\n' % matches)
    
    def negative_report(self,lst=True,outFile=None):
        if outFile is None:
            outFile = self.outdir + self.session + '-negatives'
        self.genesymbol_labels()
        out = ''
        neg = []
        g = self.graph
        for e in g.es:
            if len(e['negative']) > 0:
                if outFile:
                    out += '\t'.join([
                        g.vs[e.source]['name'],
                        g.vs[e.target]['name'],
                        g.vs[e.source]['label'],
                        g.vs[e.target]['label'],
                        ';'.join(list(e['sources'])),
                        ';'.join(map(lambda r: r.pmid, e['references'])),
                        ';'.join(e['negative']),
                        ';'.join(e['negative_refs'])]) + '\n'
                if lst:
                    neg.append(e)
        if outFile:
            outf = codecs.open(outFile,encoding='utf-8',mode='w')
            outf.write(out)
            outf.close()
        if lst:
            return neg
    
    def export_ptms_tab(self, outfile = None):
        if outfile is None:
            outfile = os.path.join(self.outdir,'network-'+self.session+'.tab')
        self.genesymbol_labels()
        self.update_vname()
        g = self.graph
        if 'ddi' not in g.es.attributes():
            g.es['ddi'] = [[] for _ in g.es]
        if 'ptm' not in g.es.attributes():
            g.es['ptm'] = [[] for _ in g.es]
        header = ['UniProt_A', 'UniProt_B', 'GeneSymbol_B', 'GeneSymbol_A', 'Databases',
                  'PubMed_IDs', 'Stimulation', 'Inhibition', 'Substrate-isoform', 
                  'Residue_number', 'Residue_letter', 'PTM_type']
        stripJson = re.compile(r'[\[\]{}\"]')
        # first row is header
        outl = [header]
        with codecs.open(outfile,encoding='utf-8',mode='w') as f:
            f.write('\t'.join(header) + '\n')
            prg = Progress(total=self.graph.ecount(),
                        name='Writing table',interval=31)
            uniqedges = []
            for e in g.es:
                prg.step()
                # only directed
                for di in e['dirs'].which_dirs():
                    src = self.nodDct[di[0]]
                    tgt = self.nodDct[di[1]]
                    # uniprot names
                    row = list(di)
                    # genesymbols
                    row += [g.vs[src]['label'], g.vs[tgt]['label']]
                    # sources
                    dbs = e['dirs'].get_dir(di, sources = True)
                    row.append(';'.join(dbs))
                    # references
                    row.append(';'.join([r for rs in \
                        [refs for db, refs in iteritems(e['refs_by_source']) \
                            if db in dbs] \
                        for r in rs]))
                    # signs
                    row += [str(int(x)) for x in e['dirs'].get_sign(di)]
                    # domain-motif
                    # row.append('#'.join([x.print_residues() for x in e['ptm'] \
                    #    if x.__class__.__name__ == 'DomainMotif']))
                    for dmi in e['ptm']:
                        if dmi.__class__.__name__ == 'DomainMotif':
                            if dmi.ptm.residue is not None:
                                if dmi.ptm.residue.protein == di[1]:
                                    uniqedges.append(e.index)
                                    r = row + [
                                        '%s-%u' % (dmi.ptm.protein, 
                                            dmi.ptm.isoform),
                                        str(dmi.ptm.residue.number),
                                        dmi.ptm.residue.name, 
                                        dmi.ptm.typ]
                                    # here each ptm in separate row:
                                    outl.append(r)
                    # row complete, appending to main list
                    # outl.append(row)
            # tabular text from list of lists; writing to file
            out = '\n'.join(['\t'.join(row) for row in outl])
            with codecs.open(outfile, encoding = 'utf-8', mode = 'w') as f:
                f.write(out)
            prg.terminate()
            console(':: Data has been written to %s'%outfile)
            return list(set(uniqedges))
    
    def export_struct_tab(self, outfile = None):
        if outfile is None:
            outfile = os.path.join(self.outdir,'network-'+self.session+'.tab')
        self.genesymbol_labels()
        self.update_vname()
        g = self.graph
        if 'ddi' not in g.es.attributes():
            g.es['ddi'] = [[] for _ in g.es]
        if 'ptm' not in g.es.attributes():
            g.es['ptm'] = [[] for _ in g.es]
        header = ['UniProt_A', 'UniProt_B', 'GeneSymbol_B', 'GeneSymbol_A', 'Databases',
                  'PubMed_IDs', 'Stimulation', 'Inhibition', 'Domain-domain', 
                  'Domain-motif-PTM', 'PTM-regulation']
        stripJson = re.compile(r'[\[\]{}\"]')
        # first row is header
        outl = [header]
        with codecs.open(outfile,encoding='utf-8',mode='w') as f:
            f.write('\t'.join(header) + '\n')
            prg = Progress(total=self.graph.ecount(),
                        name='Writing table',interval=31)
            for e in g.es:
                prg.step()
                # only directed
                for di in e['dirs'].which_dirs():
                    src = self.nodDct[di[0]]
                    tgt = self.nodDct[di[1]]
                    # uniprot names
                    row = list(di)
                    # genesymbols
                    row += [g.vs[src]['label'], g.vs[tgt]['label']]
                    # sources
                    dbs = e['dirs'].get_dir(di, sources = True)
                    row.append(';'.join(dbs))
                    # references
                    row.append(';'.join([r for rs in \
                        [refs for db, refs in iteritems(e['refs_by_source']) \
                            if db in dbs] \
                        for r in rs]))
                    # signs
                    row += [str(int(x)) for x in e['dirs'].get_sign(di)]
                    # domain-domain
                    row.append('#'.join([x.serialize() for x in e['ddi']]))
                    # domain-motif
                    row.append('#'.join([x.serialize() for x in e['ptm'] \
                        if x.__class__.__name__ == 'Ptm']))
                    # domain-motif
                    row.append('#'.join([x.serialize() for x in e['ptm'] \
                        if x.__class__.__name__ == 'Regulation']))
                    # row complete, appending to main list
                    outl.append(row)
            # tabular text from list of lists; writing to file
            out = '\n'.join(['\t'.join(row) for row in outl])
            with codecs.open(outfile, encoding = 'utf-8', mode = 'w') as f:
                f.write(out)
            prg.terminate()
            console(':: Data has been written to %s'%outfile)
    
    def export_tab(self,extraNodeAttrs={},extraEdgeAttrs={},outfile=None):
        if outfile is None:
            outfile = os.path.join(self.outdir,'network-'+self.session+'.tab')
        self.genesymbol_labels()
        header = ['UniProt_A','GeneSymbol_A','UniProt_B','GeneSymbol_B','Databases',
                  'PubMed_IDs','Undirected','Direction_A-B',
                  'Direction_B-A', 'Stimulatory_A-B','Inhibitory_A-B',
                  'Stimulatory_B-A','Inhibitory_B-A','Category']
        header += extraEdgeAttrs.keys()
        header += [x + '_A' for x in extraNodeAttrs.keys()]
        header += [x + '_B' for x in extraNodeAttrs.keys()]
        stripJson = re.compile(r'[\[\]{}\"]')
        with codecs.open(outfile,encoding='utf-8',mode='w') as f:
            f.write('\t'.join(header) + '\n')
            prg = Progress(total=self.graph.ecount(),
                        name='Writing table',interval=31)
            for e in self.graph.es:
                nameA = self.graph.vs[e.source]['name']
                nameB = self.graph.vs[e.target]['name']
                thisEdge = []
                thisEdge += [nameA.replace(' ',''),
                            self.graph.vs[e.source]['label'].replace(' ','')]
                thisEdge += [nameB.replace(' ',''),
                            self.graph.vs[e.target]['label']]
                thisEdge += [';'.join(list(e['sources'])),
                             ';'.join(map(lambda r: r.pmid, e['references']))]
                thisEdge += [';'.join(e['dirs'].get_dir('undirected',sources=True)),
                             ';'.join(e['dirs'].get_dir((nameA,nameB),sources=True)),
                             ';'.join(e['dirs'].get_dir((nameB,nameA),sources=True))]
                thisEdge += [';'.join(a) for a in \
                            e['dirs'].get_sign((nameA,nameB),sources=True) + \
                            e['dirs'].get_sign((nameB,nameA),sources=True)]
                thisEdge.append(e['type'])
                for k,v in iteritems(extraEdgeAttrs):
                    thisEdge.append(
                        ';'.join([x.strip() for x in 
                            stripJson.sub('',json.dumps(e[v])).split(',')])
                    )
                for k,v in iteritems(extraNodeAttrs):
                    thisEdge.append(
                        ';'.join([x.strip() for x in 
                            stripJson.sub('',json.dumps(
                                self.graph.vs[e.source][v])
                            ).split(',')])
                    )
                for k,v in iteritems(extraNodeAttrs):
                    thisEdge.append(
                        ';'.join([x.strip() for x in 
                            stripJson.sub('',json.dumps(
                                self.graph.vs[e.target][v])
                            ).split(',')])
                    )
                f.write('\t'.join(thisEdge) + '\n')
                prg.step()
        prg.terminate()
    
    def export_sif(self, outfile = None):
        outfile = outfile if outfile is not None \
            else 'network-%s.sif'%self.session
        with open(outfile, 'w') as f:
            for e in self.graph.es:
                for d in [d for d, b in iteritems(e['dirs'].dirs) if b]:
                    if e['dirs'].is_directed() and d == 'undirected':
                        continue
                    sign = '' if d == 'undirected' \
                        else ''.join([['+', '-'][i] \
                        for i, v in enumerate(e['dirs'].get_sign(d)) if v])
                    dirn = '=' if d == 'undirected' else '>'
                    source = self.graph.vs[e.source]['name'] \
                        if d == 'undirected' else d[0]
                    target = self.graph.vs[e.target]['name'] \
                        if d == 'undirected' else d[1]
                    f.write('\t'.join([source, sign + dirn, target]) + '\n')
    
    def export_graphml(self,outfile=None,graph=None,name='main'):
        self.genesymbol_labels()
        g = self.graph if graph is None else graph
        if outfile is None:
            outfile = os.path.join(self.outdir,'network-'+self.session+'.graphml')
        isDir = 'directed' if g.is_directed() else 'undirected'
        isDirB = 'true' if g.is_directed() else 'false'
        nodeAttrs = [('UniProt','string'),
                     ('GeneSymbol','string'),
                     ('Type','string')]
        edgeAttrs = [('Databases','string'),
                     ('PubMedIDs','string'),
                     ('Undirected','string'),
                     ('DirectionAB','string'),
                     ('DirectionBA','string'),
                     ('StimulatoryAB','string'),
                     ('InhibitoryAB','string'),
                     ('StimulatoryBA','string'),
                     ('InhibitoryBA','string'),
                     ('Category','string')]
        header = '''<?xml version="1.0" encoding="UTF-8"?>
                    <graphml xmlns="http://graphml.graphdrawing.org/xmlns" 
                    xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                    xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns 
                    http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">\n\n
                '''
        with codecs.open(outfile,encoding='utf-8',mode='w') as f:
            f.write(header)
            for attr in nodeAttrs:
                f.write('\t<key id="%s" for="node" attr.name="%s" attr.type="%s" />\n' %
                    (attr[0],attr[0],attr[1]))
            for attr in edgeAttrs:
                f.write('\t<key id="%s" for="edge" attr.name="%s" attr.type="%s" />\n' %
                    (attr[0],attr[0],attr[1]))
            f.write('''\n<graph id="%s" edgedefault="%s" 
                        parse.nodeids="free" parse.edgeids="canonical" 
                        parse.order="nodesfirst">\n\n''' %
                    (name,isDir))
            prg = Progress(total=g.vcount(),
                        name='Writing nodes',interval=31)
            f.write('\n\t<!-- graph properties -->\n\n')
            f.write('\n\t<!-- vertices -->\n\n')
            for v in g.vs:
                f.write('<node id="%s">\n' % (v['name']))
                f.write('\t<data key="UniProt">%s</data>\n' % (v['name']))
                f.write('\t<data key="GeneSymbol">%s</data>\n' % (
                    v['label'].replace(' ','')))
                f.write('\t<data key="Type">%s</data>\n' % (v['type']))
                f.write('</node>\n')
            prg.terminate()
            prg = Progress(total=g.ecount(),
                        name='Writing edges',interval=31)
            f.write('\n\t<!-- edges -->\n\n')
            for e in g.es:
                f.write('<edge id="%s_%s" source="%s" target="%s" directed="%s">\n' \
                    % (g.vs[e.source]['name'], g.vs[e.target]['name'],
                       g.vs[e.source]['name'], g.vs[e.target]['name'],
                       isDirB))
                f.write('\t<data key="Databases">%s</data>\n' % (
                        ';'.join(list(e['sources']))))
                f.write('\t<data key="PubMedIDs">%s</data>\n' % (
                        ';'.join(list(map(lambda r: r.pmid, e['references'])))))
                f.write('\t<data key="Undirected">%s</data>\n' % (
                        ';'.join(common.uniqList(e['dirs_by_source'][0]))))
                f.write('\t<data key="DirectionAB">%s</data>\n' % (
                        ';'.join(common.uniqList(e['dirs_by_source'][1]))))
                f.write('\t<data key="DirectionBA">%s</data>\n' % (
                        ';'.join(common.uniqList(e['dirs_by_source'][2]))))
                f.write('\t<data key="StimulatoryAB">%s</data>\n' % (
                        ';'.join(common.uniqList(e['signs'][0][0]))))
                f.write('\t<data key="InhibitoryAB">%s</data>\n' % (
                        ';'.join(common.uniqList(e['signs'][0][1]))))
                f.write('\t<data key="StimulatoryBA">%s</data>\n' % (
                        ';'.join(common.uniqList(e['signs'][1][0]))))
                f.write('\t<data key="InhibitoryBA">%s</data>\n' % (
                        ';'.join(common.uniqList(e['signs'][1][1]))))
                f.write('\t<data key="InhibitoryBA">%s</data>\n' % (
                        e['type']))
                f.write('</edge>\n')
                prg.step()
            f.write('\n\t</graph>\n</graphml>')
        prg.terminate()
    
    def compounds_from_chembl(self, chembl_mysql = None, nodes=None, crit=None, andor="or",
                              assay_types=['B','F'], relationship_types=['D','H'],
                              multi_query=False, **kwargs):
        chembl_mysql = chembl_mysql or self.chembl_mysql
        self.chembl = chembl.Chembl(chembl_mysql, self.ncbi_tax_id,mapper=self.mapper)
        if nodes is None:
            if crit is None:
                nodes = xrange(0,self.graph.vcount())
            else:
                sub = self.get_sub(crit=crit,andor=andor)
                nodes = sub['nodes']
        uniprots = []
        for v in self.graph.vs:
            if v.index in nodes and v['nameType'] == 'uniprot':
                uniprots.append(v['name'])
        self.chembl.compounds_targets(uniprots,assay_types=assay_types,
                            relationship_types=relationship_types, **kwargs)
        self.chembl.compounds_by_target()
        self.update_vname()
        self.graph.vs['compounds_chembl'] = [[] for _ in xrange(self.graph.vcount())]
        self.graph.vs['compounds_names'] = [[] for _ in xrange(self.graph.vcount())]
        self.graph.vs['compounds_data'] = [[] for _ in xrange(self.graph.vcount())]
        num = len(self.chembl.compounds)
        prg = Progress(total=num,name='Adding compounds',interval=11)
        hascomp = 0
        for target,data in iteritems(self.chembl.compounds):
            prg.step()
            if self.node_exists(target):
                hascomp += 1
                node = self.graph.vs[self.graph.vs['name'].index(target)]
                node['compounds_data'] = data
                for comp in data:
                    node['compounds_chembl'].append(comp['chembl'])
                    node['compounds_names'] += comp['compound_names']
                node['compounds_chembl'] = common.uniqList(node['compounds_chembl'])
                node['compounds_names'] = common.uniqList(node['compounds_names'])
        prg.terminate()
        percent = hascomp/float(self.graph.vcount())
        sys.stdout.write('\n\tCompounds found for %u targets, (%.2f%% of all proteins).\n\n'\
            % (hascomp,percent*100.0))
    
    def network_filter(self, p=2.0):
        '''
        This function aims to cut the number of edges in the network, 
        without loosing nodes, to make the network less connected, 
        less hairball-like, more usable for analysis.
        '''
        ref_freq = {}
        for s in self.sources:
            ref_freq[s] = {}
            for e in self.graph.es:
                if s in e['sources']:
                    for r in e['refs_by_source'][s]:
                        if r not in ref_freq[s]:
                            ref_freq[s][r] = 1
                        else:
                            ref_freq[s][r] += 1
        self.graph.es['score'] = [0.0]
        deg = self.graph.vs.degree()
        avdeg = sum(deg)/len(deg)
        prg = Progress(self.graph.ecount(),'Calculating scores',11)
        for e in self.graph.es:
            score = 0.0
            for s,rs in iteritems(e['refs_by_source']):
                for r in rs:
                    score += 1.0 / ref_freq[s][r]
            mindeg = min(self.graph.vs[e.source].degree(),self.graph.vs[e.target].degree())
            if mindeg < avdeg:
                score *= pow((mindeg - avdeg),p)
            e['score'] = score
            prg.step()
        prg.terminate()
    
    def shortest_path_dist(self, graph = None, subset = None, outfile = None, **kwargs):
        '''
        subset is a tuple of two lists if you wish to look for
        paths between elements of two groups, or a list if you 
        wish to look for shortest paths within this group
        '''
        graph = graph if graph is not None else self.graph
        shortest_paths = []
        subset = subset if type(subset) is tuple or subset is None else (subset,subset)
        prg = Progress(graph.vcount(),'Calculating paths',1)
        for i in xrange(0,graph.vcount()-1):
            if subset is None or i in subset[0] or i in subset[1]:
                paths = graph.get_shortest_paths(i, xrange(i+1,graph.vcount()), **kwargs)
                for j in xrange(0,len(paths)):
                    if subset is None or (i in subset[0] and i+j+1 in subset[1]) or \
                                            (i in subset[1] and i+j+1 in subset[0]):
                        shortest_paths.append(len(paths[j]))
            prg.step()
        prg.terminate()
        if outfile is not None:
            out = '\n'.join([str(i) for i in shortest_paths])
            with codecs.open(outfile, encoding='utf-8', mode='w') as f:
                f.write(out)
        return shortest_paths
    
    def load_pdb(self,graph=None):
        graph = graph if graph is not None else self.graph
        u_pdb,pdb_u = dataio.get_pdb()
        if u_pdb is None:
            self.ownlog.msg(2,'Failed to download UniProt-PDB dictionary','ERROR')
        else:
            graph.vs['pdb'] = [None]
            for v in graph.vs:
                v['pdb'] = {}
                if v['name'] in u_pdb:
                    for pdb in u_pdb[v['name']]:
                        v['pdb'][pdb[0]] = (pdb[1],pdb[2])
            self.ownlog.msg(2,'PDB IDs for proteins has been retrieved.','INFO')
    
    def load_pfam(self, graph = None):
        graph = graph if graph is not None else self.graph
        u_pfam, pfam_u = dataio.get_pfam(graph.vs['name'])
        if u_pfam is None:
            self.ownlog.msg(2,'Failed to download Pfam data from UniProt','ERROR')
        else:
            graph.vs['pfam'] = [None]
            for v in graph.vs:
                v['pfam'] = []
                if v['name'] in u_pfam:
                    v['pfam'] += u_pfam[v['name']]
            self.ownlog.msg(2,'Pfam domains has been retrieved.','INFO')
    
    def load_pfam2(self):
        self.pfam_regions()
        if self.u_pfam is None:
            self.ownlog.msg(2,'Failed to download data from Pfam','ERROR')
        else:
            self.graph.vs['pfam'] = [{} for _ in self.graph.vs]
            for v in self.graph.vs:
                if v['name'] in self.u_pfam:
                    v['pfam'] = self.u_pfam[v['name']]
            self.ownlog.msg(2,'Pfam domains has been retrieved.','INFO')
    
    def load_pfam3(self):
        self.pfam_regions()
        if self.u_pfam is None:
            self.ownlog.msg(2,'Failed to download data from Pfam','ERROR')
        else:
            self.graph.vs['doms'] = [[] for _ in self.graph.vs]
            for v in self.graph.vs:
                if v['name'] in self.u_pfam:
                    for pfam, regions in iteritems(self.u_pfam[v['name']]):
                        for region in regions:
                            v['doms'].append(intera.Domain(protein = v['name'], 
                                domain = pfam, start = region['start'], 
                                end = region['end'], isoform = region['isoform']))
            self.ownlog.msg(2,'Pfam domains has been retrieved.','INFO')
    
    def load_corum(self,graph=None):
        graph = graph if graph is not None else self.graph
        complexes,members = dataio.get_corum()
        if complexes is None:
            self.ownlog.msg(2,'Failed to download data from CORUM','ERROR')
        else:
            self.init_complex_attr(graph,'corum')
            for u,cs in iteritems(members):
                sw = self.mapper.map_name(u,'uniprot','uniprot')
                for s in sw:
                    if s in graph.vs['name']:
                        for c in cs:
                            others = []
                            for memb in complexes[c[0]][0]:
                                others += self.mapper.map_name(memb,'uniprot','uniprot')
                            graph.vs.select(name=s)[0]['complexes']['corum'][c[1]] = {
                                'full_name': c[0],
                                'all_members': others,
                                'all_members_original': complexes[c[0]][0],
                                'references': c[2],
                                'functions': c[4],
                                'diseases': c[5],
                            }
            self.ownlog.msg(2,'Complexes from CORUM have been retrieved.','INFO')
    
    def init_complex_attr(self,graph,name):
        if 'complexes' not in graph.vs.attributes():
            graph.vs['complexes'] = [None]
        for v in graph.vs:
            if v['complexes'] is None:
                v['complexes'] = {}
            if name not in v['complexes']:
                v['complexes'][name] = {}
    
    def load_havugimana(self,graph=None):
        graph = graph if graph is not None else self.graph
        complexes = dataio.read_complexes_havugimana()
        if complexes is None:
            self.ownlog.msg(2,'Failed to read data from Havugimana','ERROR')
        else:
            self.init_complex_attr(graph,'havugimana')
            for c in complexes:
                membs = []
                names = []
                for memb in c:
                    membs += self.mapper.map_name(memb,'uniprot','uniprot')
                for u in membs:
                    names += self.mapper.map_name(u,'uniprot','genesymbol')
                names = list(set(names))
                names.sort()
                name = ':'.join(names)
                for u in membs:
                    if u in graph.vs['name']:
                        graph.vs.select(name=u)[0]['complexes']['havugimana'][name] = {
                            'full_name': '-'.join(names) + ' complex',
                            'all_members': membs,
                            'all_members_original': c
                        }
                self.ownlog.msg(2,'Complexes from Havugimana have been retrieved.','INFO')
    
    def load_compleat(self,graph=None):
        graph = graph if graph is not None else self.graph
        complexes = dataio.get_compleat()
        if complexes is None:
            self.ownlog.msg(2,'Failed to load data from COMPLEAT','ERROR')
        else:
            self.init_complex_attr(graph,'compleat')
            for c in complexes:
                c['uniprots'] = []
                c['gsymbols'] = []
                for e in c['entrez']:
                    c['uniprots'] += self.mapper.map_name(e,'entrez','uniprot')
                for u in c['uniprots']:
                    c['gsymbols'] += self.mapper.map_name(u,'uniprot','genesymbol')
                c['gsymbols'] = list(set([gs.replace('; ','') for gs in c['gsymbols']]))
                if len(c['uniprots']) > 0:
                    for u in c['uniprots']:
                        if u in graph.vs['name']:
                            name = '-'.join(c['gsymbols'])
                            graph.vs.select(name=u)[0]['complexes']['compleat'][name] = {
                            'full_name': name + ' complex',
                            'all_members': c['uniprots'],
                            'all_members_original': c['entrez'],
                            'source': c['source'],
                            'references': c['pubmeds']
                        }
            self.ownlog.msg(2,'Complexes from COMPLEAT have been retrieved.','INFO')
    
    def load_complexportal(self,graph=None):
        graph = graph if graph is not None else self.graph
        ## TODO: handling species
        complexes = dataio.get_complexportal()
        if complexes is None:
            self.ownlog.msg(2,'Failed to read data from Havugimana','ERROR')
        else:
            if 'complexes' not in graph.vs.attributes():
                graph.vs['complexes'] = [None]
            for v in graph.vs:
                if v['complexes'] is None:
                    v['complexes'] = {}
                if 'complexportal' not in v['complexes']:
                    v['complexes']['complexportal'] = {}
            for c in complexes:
                swprots = []
                if 'complex recommended name' in c['names']:
                    name = c['names']['complex recommended name']
                else:
                    name = c['fullname']
                for u in c['uniprots']:
                    swprots += self.mapper.map_name(u,'uniprot','uniprot')
                swprots = list(set(swprots))
                for sw in swprots:
                    if sw in graph.vs['name']:
                        v = graph.vs.select(name=sw)[0]
                        v['complexes']['complexportal'][name] = {
                            'full_name': c['fullname'],
                            'all_members': swprots,
                            'all_members_original': c['uniprots'],
                            'pdbs': c['pdbs'],
                            'references': c['pubmeds'],
                            'synonyms': c['names'],
                            'description': c['description']
                        }
            self.ownlog.msg(2,'Complexes from Complex Portal have been retrieved.','INFO')
    
    def load_3dcomplexes(self,graph=None):
        graph = graph if graph is not None else self.graph
        c3d = dataio.get_3dcomplexes()
        if c3d is None:
            self.ownlog.msg(2,'Failed to download data from 3DComplexes and PDB','ERROR')
        else:
            if 'complexes' not in graph.vs.attributes():
                graph.vs['complexes'] = [None]
            for v in graph.vs:
                if v['complexes'] is None:
                    v['complexes'] = {}
                if '3dcomplexes' not in v['complexes']:
                    v['complexes']['3dcomplexes'] = {}
            if '3dstructure' not in graph.es.attributes():
                graph.es['3dstructure'] = [None]
            for e in graph.es:
                if e['3dstructure'] is None:
                    e['3dstructure'] = {}
                if '3dcomplexes' not in e['3dstructure']:
                    e['3dstructure']['3dcomplexes'] = []
            compl_names = {}
            compl_membs = {}
            compl_links = []
            prg = Progress(len(c3d),'Processing complexes',7)
            for cname,v in iteritems(c3d):
                swprots = []
                uprots = []
                for ups,contact in iteritems(v):
                    uprots += list(ups)
                    up1s = self.mapper.map_name(ups[0],'uniprot','uniprot')
                    for up1 in up1s:
                        inRefLists = False
                        for tax,lst in iteritems(self.reflists):
                            if up1 in lst.lst:
                                up2s = self.mapper.map_name(ups[1],'uniprot','uniprot')
                                for up2 in up2s:
                                    for tax,lst in iteritems(self.reflists):
                                        if up2 in lst.lst:
                                            inRefLists = True
                                            thisPair = [up1,up2]
                                            thisPair.sort()
                                            swprots += thisPair
                                            compl_links.append((
                                                thisPair,
                                                contact,
                                                cname
                                                ))
                                            break
                swprots = list(set(swprots))
                uprots = list(set(uprots))
                if len(swprots) > 0:
                    name = []
                    for sp in swprots:
                        name += self.mapper.map_name(sp,'uniprot','genesymbol')
                    compl_names[cname] = '-'.join(name) + ' complex'
                    compl_membs[cname] = (swprots,uprots)
                prg.step()
            prg.terminate()
            prg = Progress(len(compl_membs),'Processing nodes',3)
            for cname,uniprots in iteritems(compl_membs):
                for sp in uniprots[0]:
                    if sp in graph.vs['name']:
                        graph.vs.select(name=sp)[0]['complexes']['3dcomplexes'][cname] = {
                            'full_name': compl_names[cname],
                            'all_members': uniprots[0],
                            'all_members_original': uniprots[1]
                        }
                prg.step()
            prg.terminate()
            prg = Progress(len(compl_links),'Processing edges',3)
            for links in compl_links:
                one = links[0][0]
                two = links[0][1]
                if one in graph.vs['name'] and two in graph.vs['name']:
                    nodeOne = graph.vs.select(name=one)[0].index
                    nodeTwo = graph.vs.select(name=two)[0].index
                    try:
                        edge = graph.es.select(_between=((nodeOne,),(nodeTwo,)))[0]
                        edge['3dstructure']['3dcomplexes'].append({
                            'pdb': links[2].split('_')[0],
                            'numof_residues': links[1]
                            })
                    except:
                        pass
                prg.step()
            prg.terminate()
    
    def load_pisa(self, graph = None):
        graph = graph if graph is not None else self.graph
        if 'complexes' not in graph.vs.attributes() \
            or '3dcomplexes' not in graph.vs[0]['complexes']:
            self.load_3dcomplexes(graph=graph)
        if 'complexportal' not in graph.vs[0]['complexes']:
            self.load_complexportal(graph=graph)
        pdblist = []
        for v in graph.vs:
            for n, d in iteritems(v['complexes']['3dcomplexes']):
                pdblist.append(n.split('_')[0])
            for n, d in iteritems(v['complexes']['complexportal']):
                pdblist += d['pdbs']
        pdblist = list(set(pdblist))
        pisa, unmapped = dataio.get_pisa(pdblist)
        if 'interfaces' not in graph.es.attributes():
            graph.es['interfaces'] = [None]
        for e in graph.es:
            if e['interfaces'] is None:
                e['interfaces'] = {}
            if 'pisa' not in e['interfaces']:
                e['interfaces']['pisa'] = {}
        for pdb,iflist in iteritems(pisa):
            for uniprots,intf in iteritems(iflist):
                if uniprots[0] in graph.vs['name'] and uniprots[1] in graph.vs['name']:
                    e = self.edge_exists(uniprots[0], uniprots[1])
                    if type(e) is int:
                        if pdb not in graph.es[e]['interfaces']['pisa']:
                            graph.es[e]['interfaces']['pisa'][pdb] = []
                        graph.es[e]['interfaces']['pisa'][pdb].append(intf)
        return unmapped
    
    #
    # methods with biological meaning
    #
    
    def genesymbol(self, genesymbol):
        '''
        Returns ``igraph.Vertex()`` object if the GeneSymbol
        can be found in the default undirected network, 
        otherwise ``None``.
        
        @genesymbol : str
            GeneSymbol.
        '''
        graph = self._get_undirected()
        return graph.vs[self.labDct[genesymbol]] \
            if genesymbol in self.labDct else None
    
    gs = genesymbol
    
    def dgenesymbol(self, genesymbol):
        '''
        Returns ``igraph.Vertex()`` object if the GeneSymbol
        can be found in the default directed network, 
        otherwise ``None``.
        
        @genesymbol : str
            GeneSymbol.
        '''
        dgraph = self._get_directed()
        return dgraph.vs[self.dlabDct[genesymbol]] \
            if genesymbol in self.dlabDct else None
    
    dgs = dgenesymbol
    
    def genesymbols(self, genesymbols):
        return filter(lambda v: v is not None,
            map(self.genesymbol, genesymbols))
    
    gss = genesymbols
    
    def dgenesymbols(self, genesymbols):
        return filter(lambda v: v is not None,
            map(self.dgenesymbol, genesymbols))
    
    dgss = dgenesymbols
    
    def uniprot(self, uniprot):
        '''
        Returns ``igraph.Vertex()`` object if the UniProt
        can be found in the default undirected network, 
        otherwise ``None``.
        
        @uniprot : str
            UniProt ID.
        '''
        graph = self._get_undirected()
        return graph.vs[self.nodDct[uniprot]] \
            if uniprot in self.nodDct else None
    
    up = uniprot
    
    def duniprot(self, uniprot):
        '''
        Same as ``PyPath.uniprot(), just for directed graph.
        Returns ``igraph.Vertex()`` object if the UniProt
        can be found in the default directed network, 
        otherwise ``None``.
        
        @uniprot : str
            UniProt ID.
        '''
        dgraph = self._get_directed()
        return dgraph.vs[self.dnodDct[uniprot]] \
            if uniprot in self.dnodDct else None
    
    dup = duniprot
    
    def uniprots(self, uniprots):
        '''
        Returns list of ``igraph.Vertex()`` object
        for a list of UniProt IDs omitting those
        could not be found in the default
        undirected graph.
        '''
        return filter(lambda v: v is not None, 
            map(self.uniprot, uniprots))
    
    ups = uniprots
    
    def duniprots(self, uniprots):
        '''
        Returns list of ``igraph.Vertex()`` object
        for a list of UniProt IDs omitting those
        could not be found in the default
        directed graph.
        '''
        return filter(lambda v: v is not None, 
            map(self.duniprot, uniprots))
    
    dups = duniprots
    
    def protein(self, identifier):
        '''
        Returns ``igraph.Vertex()`` object if the identifier
        is a valid vertex index in the default undirected graph,
        or a UniProt ID or GeneSymbol which can be found in the
        default undirected network, otherwise ``None``.
        
        @identifier : int, str
            Vertex index (int) or GeneSymbol (str) or UniProt ID (str).
        '''
        graph = self._get_undirected()
        return graph.vs[identifier] \
            if type(identifier) is int and identifier < graph.vcount() \
            else graph.vs[self.nodDct[identifier]] \
            if identifier in self.nodDct else \
            graph.vs[self.labDct[identifier]] \
            if identifier in self.labDct else None
    
    p = protein
    
    def dprotein(self, identifier):
        '''
        Same as ``PyPath.protein``, just for the directed graph.
        Returns ``igraph.Vertex()`` object if the identifier
        is a valid vertex index in the default directed graph,
        or a UniProt ID or GeneSymbol which can be found in the
        default directed network, otherwise ``None``.
        
        @identifier : int, str
            Vertex index (int) or GeneSymbol (str) or UniProt ID (str).
        '''
        dgraph = self._get_directed()
        return dgraph.vs[identifier] \
            if type(identifier) is int and identifier < dgraph.vcount() \
            else dgraph.vs[self.dnodDct[identifier]] \
            if identifier in self.dnodDct else \
            dgraph.vs[self.dlabDct[identifier]] \
            if identifier in self.dlabDct else None
    
    dp = dprotein
    
    def proteins(self, proteins):
        return filter(lambda v: v is not None, 
            map(self.protein, proteins))
    
    ps = proteins
    
    def dproteins(self, proteins):
        return filter(lambda v: v is not None, 
            map(self.dprotein, proteins))
    
    dps = dproteins
    
    def up_edge(self, source, target, directed = True):
        '''
        Returns ``igraph.Edge`` object if an edge exist between
        the 2 proteins, otherwise ``None``.
        
        @source : str
            UniProt ID
        @target : str
            UniProt ID
        @directed : bool
            To be passed to igraph.Graph.get_eid()
        '''
        v_source = self.uniprot(source)
        v_target = self.uniprot(target)
        if v_source is not None and v_target is not None:
            eid = self.graph.get_eid(v_source.index, v_target.index, 
                directed = directed, error = False)
            if eid != -1:
                return self.graph.es[eid]
        return None
    
    def gs_edge(self, source, target, directed = True):
        '''
        Returns ``igraph.Edge`` object if an edge exist between
        the 2 proteins, otherwise ``None``.
        
        @source : str
            GeneSymbol
        @target : str
            GeneSymbol
        @directed : bool
            To be passed to igraph.Graph.get_eid()
        '''
        v_source = self.genesymbol(source)
        v_target = self.genesymbol(target)
        if v_source is not None and v_target is not None:
            eid = self.graph.get_eid(v_source.index, v_target.index, 
                directed = directed, error = False)
            if eid != -1:
                return self.graph.es[eid]
        return None
    
    def protein_edge(self, source, target, directed = True):
        '''
        Returns ``igraph.Edge`` object if an edge exist between
        the 2 proteins, otherwise ``None``.
        
        @source : int, str
            Vertex index or UniProt ID or GeneSymbol
        @target : int, str
            Vertex index or UniProt ID or GeneSymbol
        @directed : bool
            To be passed to igraph.Graph.get_eid()
        '''
        v_source = self.protein(source)
        v_target = self.protein(target)
        if v_source is not None and v_target is not None:
            eid = self.graph.get_eid(v_source.index, v_target.index, 
                directed = directed, error = False)
            if eid != -1:
                return self.graph.es[eid]
        return None
    
    def _has_directed(self):
        if self._directed is None:
            if self.graph.is_directed():
                self._directed = self.graph
            else:
                self.get_directed()
    
    def _already_has_directed(self):
        if self._directed is None:
            if self.graph.is_directed():
                self._directed = self.graph
            elif self.dgraph is not None and self.dgraph.is_directed():
                self._directed = self.dgraph
    
    def _get_directed(self):
        '''
        Returns the directed instance of the graph.
        If not available, creates one at ``PyPath.dgraph``.
        '''
        self._has_directed()
        return self._directed
    
    # conversion between directed and undirected vertices
    
    def _get_undirected(self):
        if self._undirected != self.graph and not self.graph.is_directed():
            self._undirected = self.graph
        if self.graph.is_directed():
            self._undirected = None
        return self._undirected
    
    def up_in_directed(self, uniprot):
        self._has_directed()
        return self.dnodDct[uniprot] if uniprot in self.dnodDct else None
    
    def up_in_undirected(self, uniprot):
        self._has_undirected()
        return self.nodDct[uniprot] if uniprot in self.nodDct else None
    
    def gs_in_directed(self, genesymbol):
        self._has_directed()
        return self.dlabDct[genesymbol] if genesymbol in self.dlabDct else None
    
    def gs_in_undirected(self, genesymbol):
        self._has_undirected()
        return self.labDct[genesymbol] if genesymbol in self.labDct else None
    
    def in_directed(self, vertex):
        return self.up_in_directed(vertex['name'])
    
    def in_undirected(self, vertex):
        return self.up_in_undirected(vertex['name'])
    
    # affects and affected_by
    
    def _affected_by(self, vertex):
        dgraph = self._get_directed()
        if dgraph != vertex.graph:
            vertex = self.in_directed(vertex['name'])
        vs = vertex.neighbors(mode = 'IN') \
            if vertex is not None else []
        return _NamedVertexSeq(vs, self.dnodNam, self.dnodLab)
    
    def _affects(self, vertex):
        dgraph = self._get_directed()
        if dgraph != vertex.graph:
            vertex = self.in_directed(vertex['name'])
        vs = vertex.neighbors(mode = 'OUT') \
            if vertex is not None else []
        return _NamedVertexSeq(vs, self.dnodNam, self.dnodLab)
    
    def affected_by(self, identifier):
        vrtx = self.dprotein(identifier)
        if vrtx is not None:
            return self._affected_by(vrtx)
        return []
    
    def affects(self, identifier):
        vrtx = self.dprotein(identifier)
        if vrtx is not None:
            return self._affects(vrtx)
        return []
    
    def up_affects(self, uniprot):
        vrtx = self.duniprot(uniprot)
        if vrtx is not None:
            return self._affects(vrtx)
        return []
    
    def up_affected_by(self, uniprot):
        vrtx = self.duniprot(uniprot)
        if vrtx is not None:
            return self._affected_by(vrtx)
        return []
    
    def gs_affects(self, genesymbol):
        vrtx = self.dgenesymbol(genesymbol)
        if vrtx is not None:
            return self._affects(vrtx)
        return []
    
    def gs_affected_by(self, genesymbol):
        vrtx = self.dgenesymbol(genesymbol)
        if vrtx is not None:
            return self._affected_by(vrtx)
        return []
    
    def up_stimulated_by(self, uniprot):
        dgraph = self._get_directed()
        if uniprot in self.dnodDct:
            vid = self.dnodDct[uniprot]
            vs = self.up_affected_by(uniprot)
            return _NamedVertexSeq(filter(lambda v: \
                dgraph.es[dgraph.get_eid(v.index, vid)]\
                    ['dirs'].positive[v['name'], uniprot], 
                vs), self.dnodNam, self.dnodLab)
        else:
            return _NamedVertexSeq([], self.dnodNam, self.dnodLab)
    
    def up_inhibited_by(self, uniprot):
        dgraph = self._get_directed()
        if uniprot in self.dnodDct:
            vid = self.dnodDct[uniprot]
            vs = self.up_affected_by(uniprot)
            return _NamedVertexSeq(filter(lambda v: \
                dgraph.es[dgraph.get_eid(v.index, vid)]\
                    ['dirs'].negative[v['name'], uniprot], 
                vs), self.dnodNam, self.dnodLab)
        else:
            return _NamedVertexSeq([], self.dnodNam, self.dnodLab)
    
    def up_stimulates(self, uniprot):
        dgraph = self._get_directed()
        if uniprot in self.dnodDct:
            vid = self.dnodDct[uniprot]
            vs = self.up_affects(uniprot)
            return _NamedVertexSeq(filter(lambda v: \
                dgraph.es[dgraph.get_eid(vid, v.index)]\
                    ['dirs'].positive[uniprot, v['name']], 
                vs), self.dnodNam, self.dnodLab)
        else:
            return _NamedVertexSeq([], self.dnodNam, self.dnodLab)
    
    def up_inhibits(self, uniprot):
        dgraph = self._get_directed()
        if uniprot in self.dnodDct:
            vid = self.dnodDct[uniprot]
            vs = self.up_affects(uniprot)
            return _NamedVertexSeq(filter(lambda v: \
                dgraph.es[dgraph.get_eid(vid, v.index)]\
                    ['dirs'].negative[uniprot, v['name']], 
                vs), self.dnodNam, self.dnodLab)
        else:
            return _NamedVertexSeq([], self.dnodNam, self.dnodLab)
    
    def gs_stimulated_by(self, genesymbol):
        dgraph = self._get_directed()
        uniprot = self.dnodNam[self.dlabDct[genesymbol]] \
            if genesymbol in self.dlabDct else None
        return self.up_stimulated_by(uniprot)
    
    def gs_stimulates(self, genesymbol):
        dgraph = self._get_directed()
        uniprot = self.dnodNam[self.dlabDct[genesymbol]] \
            if genesymbol in self.dlabDct else None
        return self.up_stimulates(uniprot)
    
    def gs_inhibited_by(self, genesymbol):
        dgraph = self._get_directed()
        uniprot = self.dnodNam[self.dlabDct[genesymbol]] \
            if genesymbol in self.dlabDct else None
        return self.up_inhibited_by(uniprot)
    
    def gs_inhibits(self, genesymbol):
        dgraph = self._get_directed()
        uniprot = self.dnodNam[self.dlabDct[genesymbol]] \
            if genesymbol in self.dlabDct else None
        return self.up_inhibits(uniprot)
    
    # meighbors variations
    
    def up_neighbors(self, uniprot, mode = 'ALL'):
        vrtx = self.uniprot(uniprot)
        if vrtx is not None:
            return _NamedVertexSeq(vrtx.neighbors(mode = mode), 
                self.nodNam, self.nodLab)
        return _NamedVertexSeq([], self.nodNam, self.nodLab)
    
    def gs_neighbors(self, genesymbol, mode = 'ALL'):
        vrtx = self.genesymbol(genesymbol)
        if vrtx is not None:
            return _NamedVertexSeq(vrtx.neighbors(mode = mode), 
                self.nodNam, self.nodLab)
        return _NamedVertexSeq([], self.nodNam, self.nodLab)
    
    def neighbors(self, identifier, mode = 'ALL'):
        vrtx = self.protein(identifier)
        if vrtx is not None:
            return _NamedVertexSeq(vrtx.neighbors(mode = mode), 
                self.nodNam, self.nodLab)
        return _NamedVertexSeq([], self.nodNam, self.nodLab)
    
    # neighborhood variations:
    
    def _neighborhood(self, vs, order = 1, mode = 'ALL'):
        return _NamedVertexSeq(
            map(lambda vi: self.graph.vs[vi],
                reduce(lambda a, b:
                    a.extend(b),
                    self.graph.neighborhood(vs,
                        order = order, mode = mode)
                ),
            ),
            self.nodNam, self.nodLab)
    
    def up_neighborhood(self, uniprot, order = 1, mode = 'ALL'):
        if type(uniprots) in common.simpleTypes:
            uniprots = [uniprots]
        vs = self.uniprots(uniprots)
        return self._neighborhood(vs, order = order, mode = mode)
    
    def gs_neighborhood(self, genesymbols, order = 1, mode = 'ALL'):
        if type(genesymbols) in common.simpleTypes:
            genesymbols = [genesymbols]
        vs = self.genesymbols(genesymbols)
        return self._neighborhood(vs, order = order, mode = mode)
    
    def neighborhood(self, identifiers, order = 1, mode = 'ALL'):
        if type(identifiers) in common.simpleTypes:
            identifiers = [identifiers]
        vs = self.proteins(identifiers)
        return self._neighborhood(vs, order = order, mode = mode)
    
    # compexes
    
    def complex_comembership_network(self,graph=None,resources=None):
        graph = graph if graph is not None else self.graph
        if resources is None:
            resources = graph.vs[0]['complexes'].keys()
        cnet = igraph.Graph()
        cdict = {}
        for v in graph.vs:
            for src in resources:
                if src not in cdict:
                    cdict[src] = {}
                if src in c['complexes']:
                    for cname,cannot in iteritems(c['complexes'][src]):
                        if cname not in cdict[src]:
                            cdict[src][cname] = []
                        cdict[src][cname].append(v['name'])
        pass
    
    def edges_in_comlexes(self, csources = ['corum'], graph = None):
        '''
        Creates edge attributes ``complexes`` and ``in_complex``.
        These are both dicts where the keys are complex resources.
        The values in ``complexes`` are the list of complex names
        both the source and the target vertices belong to.
        The values ``in_complex`` are boolean values whether there
        is at least one complex in the given resources both the
        source and the target vertex of the edge belong to.
        
        @csources : list
            List of complex resources. Should be already loaded.
        @graph : igraph.Graph()
            The graph object to do the calculations on.
        '''
        graph = graph if graph is not None else self.graph
        if 'complexes' not in graph.es.attributes():
            graph.es['complexes'] = [{} for _ in graph.es]
        if 'in_complex' not in graph.es.attributes():
            graph.es['in_complex'] = [{} for _ in graph.es]
        def _common_complexes(e, cs):
            return set(graph.vs[e.source]['complexes'][cs].keys()) & \
                set(graph.vs[e.source]['complexes'][cs].keys())
        nul = map(lambda cs: \
            map(lambda e: \
                e['complexes'].__setitem__(cs, _common_complexes(e, cs)),
                graph.es),
            csources)
        nul = map(lambda cs: \
            map(lambda e: \
                e['in_complex'].__setitem__(cs, bool(len(e['complexes'][cs]))),
                graph.es),
            csources)
    
    def sum_in_complex(self, csources = ['corum'], graph = None):
        '''
        Returns the total number of edges in the network falling
        between two members of the same complex.
        Returns as a dict by complex resources.
        Calls :py:func:pypath.pypath.Pypath.edges_in_comlexes()
        to do the calculations.
        
        @csources : list
            List of complex resources. Should be already loaded.
        @graph : igraph.Graph()
            The graph object to do the calculations on.
        '''
        graph = graph if graph is not None else self.graph
        self.edges_in_comlexes(csources = csources, graph = graph)
        return dict(map(lambda cs: 
            (cs, sum(map(lambda e: 
                e['in_complex'][cs], graph.es)
            )), 
            csources)
        )
    
    #
    #
    #
    
    def get_function(self, fun):
        if hasattr(fun, '__call__'):
            return fun
        fun = fun.split('.')
        fun0 = fun.pop(0)
        toCall = None
        if fun0 in globals():
            toCall = globals()[fun0]
        elif fun0 in locals():
            toCall = locals()[fun0]
        elif fun0 == __name__.split('.')[0]:
            toCall = __main__
        elif fun0 == 'self' or fun0 == __name__.split('.')[-1]:
            toCall = self
        elif fun0 in dir(self):
            toCall = getattr(self, fun0)
        else:
            for subm in globals().keys():
                if hasattr(globals()[subm], '__name__') and \
                    globals()[subm].__name__.split('.')[0] == __name__.split('.')[-1]:
                    if hasattr(globals()[subm], fun0):
                        toCall = getattr(globals()[subm], fun0)
        if toCall is None:
            return None
        for fun0 in fun:
            if hasattr(toCall, fun0):
                toCall = getattr(toCall, fun0)
        if hasattr(toCall, '__call__'):
            return toCall
        else:
            return None
    
    def edges_3d(self,methods=['dataio.get_instruct', 'dataio.get_i3d']):
        all_3d = []
        self.update_vname()
        for m in methods:
            fun = self.get_function(m)
            if fun is not None:
                all_3d += fun()
        # initializing edge attributes:
        if 'ddi' not in self.graph.es.attributes():
            self.graph.es['ddi'] = [None]
        for e in self.graph.es:
            if e['ddi'] is None:
                e['ddi'] = []
        # assigning annotations:
        for i in all_3d:
            u1 = i['uniprots'][0]
            u2 = i['uniprots'][1]
            if u1 != u2 and self.node_exists(u1) and self.node_exists(u2):
                    edge = self.edge_exists(u1, u2)
                    if type(edge) is int:
                        for seq1 in i[u1]['seq']:
                            for seq2 in i[u2]['seq']:
                                dom1 = intera.Domain(protein = u1, 
                                    domain = i[u1]['pfam'], 
                                    start = seq1[0], 
                                    end = seq1[1], 
                                    chains = {i['pdb'][0]: i[u1]['chain']})
                                dom2 = intera.Domain(protein = u2, 
                                    domain = i[u2]['pfam'], 
                                    start = seq2[0],
                                    end = seq2[1],
                                    chains = {i['pdb'][0]: i[u2]['chain']})
                                domdom = intera.DomainDomain(dom1, dom2, 
                                    refs = i['references'], 
                                    sources = i['source'], pdbs = i['pdb'])
                                self.graph.es[edge]['ddi'].append(domdom)
    
    def edges_ptms(self):
        self.pfam_regions()
        self.load_pepcyber()
        self.load_psite_reg()
        self.load_ielm()
        self.load_phosphoelm()
        self.load_elm()
        self.load_3did_dmi()
    
    def pfam_regions(self):
        if self.u_pfam is None:
            self.u_pfam = dataio.get_pfam_regions(
                uniprots = self.graph.vs['name'], 
                dicts = 'uniprot',
                keepfile = True)
    
    def complexes(self,methods=['3dcomplexes', 'havugimana', 'corum',
                                'complexportal','compleat']):
        for m in methods:
            m = 'load_' + m
            if hasattr(self,m):
                toCall = getattr(self, m)
                if hasattr(toCall, '__call__'):
                    toCall()
    
    def load_domino_dmi(self, organism = None):
        organism = organism if organism is not None else self.ncbi_tax_id
        #all_unip = dataio.uniprot_input.all_uniprots(organism)
        domi = dataio.get_domino_ptms()
        if domi is None:
            self.ownlog.msg(2,
                'Failed to load domain-motif interaction data from DOMINO','ERROR')
            return None
        self.update_vname()
        if 'ptm' not in self.graph.es.attributes():
            self.graph.es['ptm'] = [[] for _ in self.graph.es]
        prg = Progress(len(domi['dmi']), 'Loading domain-motif interactions', 11)
        for dm in domi['dmi']:
            prg.step()
            uniprot1 = dm.domain.protein
            uniprot2 = dm.ptm.protein
            if self.node_exists(uniprot1) and self.node_exists(uniprot2):
                e = self.edge_exists(uniprot1, uniprot2)
                if type(e) is int:
                    if type(e) is int:
                        if type(self.graph.es[e]['ptm']) is not list:
                            self.graph.es[e]['ptm'] = []
                        self.graph.es[e]['ptm'].append(dm)
        prg.terminate()
    
    def load_3did_dmi(self):
        dmi = dataio.process_3did_dmi()
        if dmi is None:
            self.ownlog.msg(2,
                'Failed to load domain-motif interaction data from 3DID','ERROR')
            return None
        self.update_vname()
        if 'ptm' not in self.graph.es.attributes():
            self.graph.es['ptm'] = [[] for _ in self.graph.es]
        prg = Progress(len(dmi), 'Loading domain-motif interactions', 11)
        for uniprots, dmi_list in iteritems(dmi):
            prg.step()
            if self.node_exists(uniprots[0]) and self.node_exists(uniprots[1]):
                e = self.edge_exists(uniprots[0], uniprots[1])
                if type(e) is int:
                    if type(self.graph.es[e]['ptm']) is not list:
                        self.graph.es[e]['ptm'] = []
                    self.graph.es[e]['ptm'] += dmi_list
        prg.terminate()
    
    def load_ddi(self, ddi):
        '''
        ddi is either a list of intera.DomainDomain objects, 
        or a function resulting this list
        '''
        data = ddi if not hasattr(ddi, '__call__') else ddi()
        if data is None:
            if ddi.__module__.split('.')[1] == 'dataio':
                self.ownlog.msg(2,
                    'Function %s() failed'%ddi,'ERROR')
            return None
        if 'ddi' not in self.graph.es.attributes():
            self.graph.es['ddi'] = [[] for _ in self.graph.es]
        prg = Progress(len(data),'Loading domain-domain interactions',99)
        in_network = 0
        for dd in data:
            prg.step()
            uniprot1 = dd.domains[0].protein
            uniprot2 = dd.domains[1].protein
            if self.node_exists(uniprot1) and self.node_exists(uniprot2):
                e = self.edge_exists(uniprot1, uniprot2)
                if type(e) is int:
                    if type(self.graph.es[e]['ddi']) is not list:
                        self.graph.es[e]['ddi'] = []
                    in_network += 1
                    self.graph.es[e]['ddi'].append(dd)
        prg.terminate()
    
    def load_dmi(self, dmi):
        '''
        dmi is either a list of intera.DomainMotif objects, 
        or a function resulting this list
        '''
        data = dmi if not hasattr(dmi, '__call__') else dmi()
        if data is None:
            if dmi.__module__.split('.')[1] == 'dataio':
                self.ownlog.msg(2,
                    'Function %s() failed'%dmi,'ERROR')
            return None
        if 'ptm' not in self.graph.es.attributes():
            self.graph.es['ptm'] = [[] for _ in self.graph.es]
    
    def run_batch(self, methods, toCall = None):
        if toCall is not None:
            toCall = self.get_function(toCall)
        for m in methods:
            fun = self.get_function(m)
            if fun is not None:
                if hasattr(toCall, '__call__'):
                    toCall(fun)
                else:
                    fun()
    
    def load_ddis(self, methods = ['dataio.get_3dc_ddi', 'dataio.get_domino_ddi',
            'self.load_3did_ddi2']):
        self.run_batch(methods, toCall = self.load_ddi)
    
    def load_dmis(self, 
        methods = ['self.pfam_regions',
        'self.load_depod_dmi',
        'self.load_dbptm',
        'self.load_mimp_dmi',
        'self.load_pnetworks_dmi',
        'self.load_domino_dmi',
        'self.load_pepcyber',
        'self.load_psite_reg',
        'self.load_psite_phos',
        'self.load_ielm',
        'self.load_phosphoelm',
        'self.load_elm',
        'self.load_3did_dmi']):
        self.run_batch(methods)
        self.uniq_ptms()
        self.phosphorylation_directions()
    
    def load_interfaces(self):
        self.load_3did_ddi2(ddi = False, interfaces = True)
        unm = self.load_pisa()
    
    def load_3did_ddi(self):
        g = self.graph
        ddi, interfaces = dataio.get_3did_ddi(residues = True)
        if ddi is None or interfaces is None:
            self.ownlog.msg(2,
                'Failed to load domain-domain interaction data from 3DID','ERROR')
            return None
        if 'ddi' not in g.es.attributes():
            g.es['ddi'] = [None]
        for e in g.es:
            if e['ddi'] is None:
                e['ddi'] = {}
            if '3did' not in e['ddi']:
                e['ddi']['3did'] = []
        prg = Progress(len(ddi),'Loading domain-domain interactions',99)
        for k,v in iteritems(ddi):
            uniprot1 = k[0]
            uniprot2 = k[1]
            swprots = self.mapper.swissprots([uniprot1,uniprot2])
            for swprot1 in swprots[uniprot1]:
                for swprot2 in swprots[uniprot2]:
                    if swprot1 in g.vs['name'] and swprot2 in g.vs['name']:
                        e = self.edge_exists(swprot1,swprot2)
                        if type(e) is int:
                            for domains,structures in iteritems(v):
                                for pdb,pdb_uniprot_pairs in \
                                        iteritems(structures['pdbs']):
                                    for pdbuniprots in pdb_uniprot_pairs:
                                        pdbswprots = self.mapper.swissprots(pdbuniprots)
                                        for pdbswprot1 in pdbswprots[pdbuniprots[0]]:
                                            for pdbswprot2 in pdbswprots[pdbuniprots[1]]:
                                                this_ddi = {}
                                                this_ddi[swprot1] = {
                                                    'pfam': domains[0]
                                                }
                                                this_ddi[swprot2] = {
                                                    'pfam': domains[1]
                                                }
                                                this_ddi['uniprots'] = [swprot1,swprot2]
                                                this_ddi['uniprots_original'] = k
                                                this_ddi['pdb'] = {
                                                    swprot1: pdbswprot1,
                                                    swprot2: pdbswprot2,
                                                    'pdb': pdb
                                                }
                                                g.es[e]['ddi']['3did'].append(this_ddi)
            prg.step()
        prg.terminate()
    
    def load_3did_interfaces(self):
        self.load_3did_ddi2(ddi = False, interfaces = True)
    
    def load_3did_ddi2(self, ddi = True, interfaces = False):
        self.update_vname()
        ddi, intfs = dataio.get_3did()
        if ddi is None or interfaces is None:
            self.ownlog.msg(2,
                'Failed to load domain-domain interaction data from 3DID','ERROR')
            return None
        #### ERROR
        if interfaces:
            if 'interfaces' not in self.graph.es.attributes():
                self.graph.es['interfaces'] = [[] for _ in self.graph.es]
            for intf in intfs:
                uniprot1 = intf.domains[0].protein
                uniprot2 = intf.domains[1].protein
                if self.node_exists(uniprot1) and self.node_exists(uniprot2):
                    e = self.edge_exists(uniprot1, uniprot2)
                    if type(e) is int:
                        if type(self.graph.es[e]['interfaces']) is not list:
                            self.graph.es[e]['interfaces'] = []
                        self.graph.es[e]['interfaces'].append(intf)
        if ddi:
            return ddi
    
    def load_ielm(self):
        self.update_vname()
        if 'ptm' not in self.graph.es.attributes():
            self.graph.es['ptm'] = [[] for _ in self.graph.es]
        ppi = []
        for e in self.graph.es:
            ppi.append((self.graph.vs[e.source]['name'], 
                self.graph.vs[e.target]['name']))
        ielm = dataio.get_ielm(ppi)
        elm = dataio.get_elm_classes()
        prg = Progress(len(ielm), 'Processing domain-motif interactions', 13)
        noelm = []
        for l in ielm:
            prg.step()
            nodes = self.get_node_pair(l[1], l[9])
            if nodes:
                e = self.graph.get_eid(nodes[0], nodes[1], error = False)
                if e != -1:
                    if self.graph.es[e]['ptm'] is None:
                        self.graph.es[e]['ptm'] = []
                    if l[2] not in elm:
                        noelm.append(l[2])
                    motif = [None] * 5 if l[2] not in elm else elm[l[2]]
                    mot = intera.Motif(l[1], int(l[3]), int(l[4]), regex = motif[3], 
                        prob = None if motif[4] is None else float(motif[4]), 
                        description = motif[2], elm = motif[0], motif_name = l[2])
                    dom = intera.Domain(protein = l[9], start = int(l[11]), 
                        end = int(l[12]), domain = l[10], domain_id_type = 'ielm_hmm')
                    if self.u_pfam is not None and l[9] in self.u_pfam:
                        for pfam, regions in iteritems(self.u_pfam[l[9]]):
                            for region in regions:
                                if int(l[11]) == region['start'] and \
                                    int(l[12]) == region['end']:
                                    dom.pfam = pfam
                                    dom.isoform = region['isoform']
                    ptm = intera.Ptm(protein = l[1], motif = mot, 
                        typ = l[2].split('_')[0])
                    domMot = intera.DomainMotif(dom, ptm, 'iELM')
                    self.graph.es[e]['ptm'].append(domMot)
        prg.terminate()
        # find deprecated elm classes:
        # list(set(noelm))
    
    def load_elm(self):
        self.update_vname()
        if 'ptm' not in self.graph.es.attributes():
            self.graph.es['ptm'] = [[] for _ in self.graph.es]
        elm = dataio.get_elm_interactions()
        prg = Progress(len(elm), 'Processing domain-motif interactions', 11)
        for l in elm:
            prg.step()
            if len(l) > 7:
                uniprot_elm = l[2]
                uniprot_dom = l[3]
                if self.node_exists(uniprot_elm) and self.node_exists(uniprot_dom):
                    nodes = self.get_node_pair(l[1], l[9])
                    if nodes:
                        e = self.graph.get_eid(nodes[0], nodes[1], error = False)
                        if e != -1:
                            if self.graph.es[e]['ptm'] is None:
                                self.graph.es[e]['ptm'] = []
                            mot = intera.Motif(protein = uniprot_elm, motif_name = l[0], 
                                start = int(l[4]), end = int(l[5]))
                            ptm = intera.Ptm(protein = uniprot_elm, motif = mot)
                            dstart = start = None if l[6] == 'None' else int(l[6])
                            dend = None if l[6] == 'None' else int(l[7])
                            if self.u_pfam is not None and uniprot_dom in self.u_pfam:
                                if l[1] in self.u_pfam[uniprot_dom]:
                                    for region in self.u_pfam[uniprot_dom][l[1]]:
                                        if dstart is None or dend is None or \
                                            (dstart == region['start'] and \
                                            dend == region['end']):
                                            doms.append(
                                                intera.Domain(
                                                    protein = uniprot_dom, 
                                                    domain = l[1], 
                                                    start = region['start'], 
                                                    end = region['end'],
                                                    isoform = region['isoform']
                                                )
                                            )
                            for dom in doms:
                                self.graph.es[e]['ptm'].append(
                                    intera.DomainMotif(dom, ptm, 'ELM'))
        prg.terminate()
    
    def load_lmpid(self, method):
        pass
    
    def process_dmi(self, source, **kwargs):
        '''
        This is an universal function 
        for loading domain-motif objects
        like load_phospho_dmi() for PTMs.
        TODO this will replace load_elm, load_ielm, etc
        '''
        functions = {
            'LMPID': 'lmpid_dmi'
        }
        motif_plus = {
            'LMPID': []
        }
        self.update_vname()
        toCall = getattr(dataio, functions[source])
        data = toCall(**kwargs)
        if self.seq is None:
            self.sequences(self.ncbi_tax_id)
        if self.seq is None:
            self.sequences(isoforms = True)
        if 'ptm' not in self.graph.es.attributes():
            self.graph.es['ptm'] = [[] for _ in self.graph.es]
        prg = Progress(len(data), 'Processing domain-motif interactions from %s'%source, 7)
        for d in data:
            prg.step()
            domain_ups = []
            motif_upd = []
            if source == 'LMPID':
                domain_ups = self.mapper.map_name(d['domain_protein'], 'uniprot', 'uniprot')
                motif_ups = self.mapper.map_name(d['motif_protein'], 'uniprot', 'uniprot')
            for du in domain_ups:
                dom = intera.Domain(du, 
                    domain = None if 'domain_name' not in d else d['domain_name'], 
                    domain_id_type = None if 'domain_name_type' not in d else d['domain_name_type'])
                for mu in motif_ups:
                    if mu in self.seq and mu in self.nodInd and du in self.nodInd:
                        edge = self.get_edge((self.nodDct[du], self.nodDct[mu]))
                        if edge:
                            mse = self.seq[mu]
                            isos = []
                            if d['instance'] is None:
                                start, end, inst = mse.get_region(start = d['motif_start'], 
                                    end = d['motif_end'], isoform = 1)
                                isos.append((start, end, 1, inst))
                            for iso in mse.isoforms():
                                start, end, inst = mse.get_region(start = d['motif_start'], 
                                    end = d['motif_end'], isoform = iso)
                                if inst == d['instance']:
                                    isos.append((start, end, iso, inst))
                            for iso in isos:
                                motargs = dict([(k, d[k]) for k in motif_plus[source]])
                                mot = intera.Motif(mu, iso[0], iso[1], isoform = iso[2], 
                                    instance = iso[3], **motargs)
                                ptm = intera.Ptm(mu, motif = mot, isoform = iso[2], source = [source])
                                dommot = intera.DomainMotif(domain = dom, ptm = ptm, 
                                    sources = [source], refs = d['refs'])
                                self.graph.es[edge]['ptm'].append(dommot)
        prg.terminate()
    
    def load_pepcyber(self):
        self.update_vname()
        if 'ptm' not in self.graph.es.attributes():
            self.graph.es['ptm'] = [[] for _ in self.graph.es]
        pepc = dataio.get_pepcyber()
        prg = Progress(len(pepc), 'Processing domain-motif interactions', 13)
        for l in pepc:
            prg.step()
            uniprot1 = [l[9]] if len(l[9]) > 0 else []
            if len(l[9]) == 0 and len(l[10]) > 0:
                uniprot1 = self.mapper.map_name(l[10], 'refseq', 'uniprot')
            uniprot2 = [l[11]] if len(l[11]) > 0 else []
            # ptm on u2, 
            # u1 interacts with u2 depending on ptm
            for u1 in uniprot1:
                for u2 in uniprot2:
                    nodes = self.get_node_pair(u1, u2)
                    if nodes:
                        e = self.graph.get_eid(nodes[0], nodes[1], error = False)
                        if e != -1:
                            res = intera.Residue(int(l[4]), l[8], u2)
                            ptm = intera.Ptm(protein = u2, residue = res, 
                                typ = 'phosphorylation')
                            reg = intera.Regulation(
                                source = u2, target = u1, 
                                sources = ['PepCyber'],
                                effect = 'induces', ptm = ptm)
                            self.graph.es[e]['ptm'].append(reg)
        prg.terminate()
    
    def load_psite_reg(self):
        modtyp = {
            'p': 'phosphorylation',
            'ac': 'acetylation',
            'ub': 'ubiquitination',
            'me': 'methylation',
            'sm': 'sumoylation',
            'ga': 'o-galnac',
            'gl': 'o-glcnac',
            'sc': 'succinylation',
            'm3': 'tri-methylation',
            'm1': 'mono-methylation',
            'm2': 'di-methylation',
            'pa': 'palmitoylation'
        }
        self.update_vname()
        if 'ptm' not in self.graph.es.attributes():
            self.graph.es['ptm'] = [[] for _ in self.graph.es]
        preg = dataio.get_psite_reg()
        prg = Progress(len(preg), 'Processing regulatory effects', 11)
        for src, tgts in iteritems(preg):
            prg.step()
            # ptm on src
            # tgt: interactor of src, depending on ptm
            if self.node_exists(src):
                for tgt in tgts:
                    for effect in ['induces', 'disrupts']:
                        for ind in tgt[effect]:
                            uniprots = self.mapper.map_name(ind, 'genesymbol', 'uniprot')
                            for u in uniprots:
                                if self.node_exists(u):
                                    nodes = self.get_node_pair(src, u)
                                    if nodes:
                                        e = self.graph.get_eid(nodes[0], nodes[1], 
                                            error = False)
                                        if e != -1:
                                            if self.graph.es[e]['ptm'] is None:
                                                self.graph.es[e]['ptm'] = []
                                            res = intera.Residue(int(tgt['res']), 
                                                tgt['aa'], src)
                                            ptm = intera.Ptm(protein = src, residue = res, 
                                                typ = modtyp[tgt['modt']])
                                            reg = intera.Regulation(
                                                source = src, target = u, 
                                                sources = ['PhosphoSite'], 
                                                refs = tgt['pmids'],
                                                effect = effect, ptm = ptm)
                                            self.graph.es[e]['ptm'].append(reg)
        prg.terminate()
    
    def load_comppi(self, graph = None):
        graph = graph if graph is not None else self.graph
        self.update_vname()
        if 'comppi' not in graph.es.attributes():
            graph.es['comppi'] = [None for _ in graph.es]
        if 'comppi' not in graph.vs.attributes():
            graph.vs['comppi'] = [{} for _ in graph.vs]
        comppi = dataio.get_comppi()
        prg = Progress(len(comppi), 'Processing localizations', 33)
        for c in comppi:
            prg.step()
            uniprots1 = self.mapper.map_name(c['uniprot1'], 'uniprot', 'uniprot')
            uniprots2 = self.mapper.map_name(c['uniprot2'], 'uniprot', 'uniprot')
            for u1 in uniprots1:
                if self.node_exists(u1):
                    for loc in [x.split(':') for x in c['loc1'].split('|')]:
                        graph.vs[self.nodDct[u1]]\
                            ['comppi'][loc[0]] = float(loc[1])
            for u2 in uniprots1:
                if self.node_exists(u2):
                    for loc in [x.split(':') for x in c['loc2'].split('|')]:
                        graph.vs[self.nodDct[u2]]\
                            ['comppi'][loc[0]] = float(loc[1])
            for u1 in uniprots1:
                for u2 in uniprots2:
                    if self.node_exists(u1) and self.node_exists(u2):
                        nodes = self.get_node_pair(u1, u2)
                        if nodes:
                            e = graph.get_eid(nodes[0], nodes[1], error = False)
                            if e != -1:
                                graph.es[e]['comppi'] = float(c['loc_score'])
        prg.terminate()
    
    def edge_loc(self, graph = None, topn = 2):
        graph = graph if graph is not None else self.graph
        if 'comppi' not in graph.vs.attributes():
            self.load_comppi()
        graph.es['loc'] = [[] for _ in graph.es]
        for e in graph.es:
            e['loc'] = list(set([i[0] for i in \
                heapq.nlargest(2 , iteritems(graph.vs[e.source]['comppi']), 
                operator.itemgetter(1))
            ]) & set([i[0] for i in \
                heapq.nlargest(2 , iteritems(graph.vs[e.target]['comppi']), 
                operator.itemgetter(1))
            ]))
    
    def sequences(self, isoforms = True):
        self.seq = uniprot_input.swissprot_seq(self.ncbi_tax_id, isoforms)
    
    def load_ptms(self):
        self.load_depod_dmi()
        self.load_signor_ptms()
        self.load_li2012_ptms()
        self.load_hprd_ptms()
        self.load_mimp_dmi()
        self.load_pnetworks_dmi()
        self.load_phosphoelm()
        self.load_dbptm()
        self.load_psite_phos()
        self.uniq_ptms()
        self.phosphorylation_directions()
    
    def load_mimp_dmi(self, non_matching = False, trace = False, **kwargs):
        trace = self.load_phospho_dmi(source = 'MIMP', trace = trace, **kwargs)
        if trace:
            return trace
    
    def load_pnetworks_dmi(self, trace = False, **kwargs):
        trace = self.load_phospho_dmi(source = 'PhosphoNetworks', 
            trace = trace, **kwargs)
        if trace:
            return trace
    
    def load_phosphoelm(self, trace = False, ltp_only = True, **kwargs):
        trace = self.load_phospho_dmi(source = 'phosphoELM', trace = trace, 
            ltp_only = ltp_only, **kwargs)
        if trace:
            return trace
    
    def load_dbptm(self, non_matching = False, trace = False, **kwargs):
        trace = self.load_phospho_dmi(source = 'dbPTM', trace = trace, **kwargs)
        if trace:
            return trace
    
    def load_hprd_ptms(self, non_matching = False, trace = False, **kwargs):
        trace = self.load_phospho_dmi(source = 'HPRD', trace = trace, **kwargs)
        if trace:
            return trace
    
    def load_li2012_ptms(self, non_matching = False, trace = False, **kwargs):
        trace = self.load_phospho_dmi(source = 'Li2012', trace = trace, **kwargs)
        if trace:
            return trace
    
    def load_signor_ptms(self, non_matching = False, trace = False, **kwargs):
        trace = self.load_phospho_dmi(source = 'Signor', trace = trace, **kwargs)
        if trace:
            return trace
    
    def load_psite_phos(self, trace = False, **kwargs):
        trace = self.load_phospho_dmi(source = 'PhosphoSite', trace = trace, **kwargs)
        if trace:
            return trace
    
    def load_phospho_dmi(self, source, trace = False, return_raw = False, **kwargs):
        functions = {
            'Signor': 'load_signor_ptms',
            'MIMP': 'get_mimp',
            'PhosphoNetworks': 'get_phosphonetworks',
            'phosphoELM': 'get_phosphoelm',
            'dbPTM': 'get_dbptm',
            'PhosphoSite': 'get_psite_phos',
            'HPRD': 'get_hprd_ptms',
            'Li2012': 'li2012_phospho'
        }
        self.update_vname()
        toCall = getattr(dataio, functions[source])
        data = toCall(**kwargs)
        if self.seq is None:
            self.sequences(isoforms = True)
        if 'ptm' not in self.graph.es.attributes():
            self.graph.es['ptm'] = [[] for _ in self.graph.es]
        nomatch = []
        kin_ambig = {}
        sub_ambig = {}
        prg = Progress(len(data), 'Processing PTMs from %s'%source, 23)
        raw = []
        for p in data:
            prg.step()
            if p['kinase'] is not None and len(p['kinase']) > 0:
                # database specific id conversions
                if source in ['PhosphoSite', 'phosphoELM', 'Signor']:
                    kinase_ups = self.mapper.map_name(p['kinase'], 'uniprot', 'uniprot')
                else:
                    if type(p['kinase']) is not list:
                        p['kinase'] = [p['kinase']]
                    kinase_ups = [i for ii in \
                        [self.mapper.map_name(k, 'genesymbol', 'uniprot') \
                        for k in p['kinase']] for i in ii]
                    kinase_ups = list(set(kinase_ups))
                if type(p['kinase']) is not list:
                        p['kinase'] = [p['kinase']]
                if p['substrate'].startswith('HLA'):
                    continue
                if source in ['MIMP', 'PhosphoNetworks', 'Li2012']:
                    substrate_ups_all = self.mapper.map_name(p['substrate'], 
                        'genesymbol', 'uniprot')
                if source == 'MIMP':
                    substrate_ups_all += self.mapper.map_name(p['substrate_refseq'], 
                        'refseq', 'uniprot')
                    substrate_ups_all = list(set(substrate_ups_all))
                if source in ['phosphoELM', 'dbPTM', 'PhosphoSite', 'Signor']:
                    substrate_ups_all = self.mapper.map_name(p['substrate'], 
                        'uniprot', 'uniprot')
                if source == 'HPRD':
                    substrate_ups_all = self.mapper.map_name(p['substrate_refseqp'], 
                        'refseqp', 'uniprot')
                    substrate_ups_all = common.uniqList(substrate_ups_all)
                for k in p['kinase']:
                    if k not in kin_ambig:
                        kin_ambig[k] = kinase_ups
                # looking up sequences in all isoforms:
                substrate_ups = []
                for s in substrate_ups_all:
                    if s in self.seq:
                        for isof in self.seq[s].isoforms():
                            if p['instance'] is not None:
                                if self.seq[s].match(p['instance'], p['start'], 
                                    p['end'], isoform = isof):
                                    substrate_ups.append((s, isof))
                            else:
                                if self.seq[s].match(p['resaa'], p['resnum'], 
                                    isoform = isof):
                                    substrate_ups.append((s, isof))
                if p['substrate'] not in sub_ambig:
                    sub_ambig[p['substrate']] = substrate_ups
                # generating report on non matching substrates
                if len(substrate_ups) == 0:
                    for s in substrate_ups_all:
                        if s[0] in self.seq:
                            nomatch.append((s[0], s[1], 
                                p['substrate_refseq'], s, p['instance'],
                                self.seq[s].get(p['start'], p['end'])))
                # adding kinase-substrate interactions
                for k in kinase_ups:
                    for s in substrate_ups:
                        nodes = self.get_node_pair(k, s[0])
                        if nodes or return_raw:
                            e = None
                            if nodes:
                                e = self.graph.get_eid(nodes[0], nodes[1], 
                                    error = False)
                            if (type(e) is int and e > 0) or return_raw:
                                res = intera.Residue(p['resnum'], p['resaa'], s[0], 
                                    isoform = s[1])
                                if p['instance'] is None:
                                    reg = self.seq[s[0]].get_region(p['resnum'], 
                                        p['start'], p['end'], isoform = s[1])
                                    if reg is not None:
                                        p['instance'] = reg[2]
                                        p['start'] = reg[0]
                                        p['end'] = reg[1]
                                if 'typ' not in p:
                                    p['typ'] = 'phosphorylation'
                                mot = intera.Motif(s[0], p['start'], p['end'], 
                                    instance = p['instance'], isoform = s[1])
                                ptm = intera.Ptm(s[0], motif = mot, residue = res, 
                                    typ = p['typ'], source = [source], 
                                    isoform = s[1])
                                dom = intera.Domain(protein = k)
                                if 'references' not in p:
                                    p['references'] = []
                                dommot = intera.DomainMotif(domain = dom, ptm = ptm, 
                                    sources = [source], refs = p['references'])
                                if source == 'MIMP':
                                    dommot.mimp_sources = ';'.split(p['databases'])
                                    dommot.npmid = p['npmid']
                                elif source == 'PhosphoNetworks':
                                    dommot.pnetw_score = p['score']
                                elif source == 'dbPTM':
                                    dommot.dbptm_sources = [p['source']]
                                if type(e) is int and e > 0:
                                    if self.graph.es[e]['ptm'] is None:
                                        self.graph.es[e]['ptm'] = []
                                    self.graph.es[e]['ptm'].append(dommot)
                                if return_raw:
                                    raw.append(dommot)
        prg.terminate()
        if trace:
            return {'non_matching': nomatch, 'kinase_ambiguousity': kin_ambig,
                'substrate_ambiguousity': sub_ambig}
        if return_raw:
            return raw
    
    def load_depod_dmi(self):
        reres = re.compile(r'([A-Z][a-z]+)-([0-9]+)')
        non_digit = re.compile(r'[^\d.-]+')
        data = dataio.get_depod()
        aadict = dict(zip([a.lower().capitalize() for a in common.aaletters.keys()],
            common.aaletters.values()))
        if self.seq is None:
            self.sequences()
        if 'ptm' not in self.graph.es.attributes():
            self.graph.es['ptm'] = [[] for _ in self.graph.es]
        prg = Progress(len(data), 'Loading dephosphorylation data from DEPOD', 11)
        mapp = []
        for l in data:
            prg.step()
            reslist = [(aadict[r[0]], int(non_digit.sub('', r[1]))) \
                for r in reres.findall(l[2]) \
                if r[0] in aadict]
            if len(l[4]) != 0 and len(l[5]) != 0:
                enzymes = self.mapper.map_name(l[4][0], 'uniprot', 'uniprot')
                substrates = self.mapper.map_name(l[5][0], 'uniprot', 'uniprot')
                substrates = [s for s in substrates if s in self.seq]
                mapp.append([l[0], l[1], enzymes, substrates, reslist])
                for r in reslist:
                    substrates = [s for s in substrates \
                        if self.seq[s].match(r[0], r[1])]
                mapp[-1].append(substrates)
                for d in enzymes:
                    for s in substrates:
                        nodes = self.get_node_pair(d, s)
                        if nodes:
                            e = self.graph.get_eid(nodes[0], nodes[1], 
                                error = False)
                            if type(e) is int and e > 0:
                                for r in reslist:
                                    res = intera.Residue(r[1], r[0], s)
                                    ptm = intera.Ptm(s, residue = res, 
                                        typ = 'dephosphorylation', 
                                        source = ['DEPOD'])
                                    dom = intera.Domain(protein = d)
                                    dommot = intera.DomainMotif(domain = dom, ptm = ptm, 
                                        sources = ['DEPOD'], 
                                        refs = [x.strip() for x in l[3].split(',')])
                                    if self.graph.es[e]['ptm'] is None:
                                        self.graph.es[e]['ptm'] = []
                                    self.graph.es[e]['ptm'].append(dommot)
        prg.terminate()
        # return mapp
    
    def uniq_ptms(self):
        if 'ptm' in self.graph.es.attributes():
            self.graph.es['ptm'] = [self.uniq_ptm(e['ptm']) for e in self.graph.es]
    
    def uniq_ptm(self, ptms):
        ptms_uniq = []
        for ptm in ptms:
            merged = False
            for i, ptmu in enumerate(ptms_uniq):
                if ptm == ptmu:
                    ptms_uniq[i].merge(ptm)
                    merged = True
            if not merged:
                ptms_uniq.append(ptm)
        return ptms_uniq
    
    def phosphorylation_directions(self):
        self.uniq_ptms()
        isdir = 0
        for e in self.graph.es:
            if e['dirs'].is_directed():
                isdir += 1
        for e in self.graph.es:
            for ptm in e['ptm']:
                if ptm.__class__.__name__ == 'DomainMotif' and \
                    ptm.ptm.typ in ['phosphorylation', 'dephosphorylation']:
                    e['dirs'].set_dir((ptm.domain.protein, ptm.ptm.protein), 
                        ptm.ptm.sources)
        isdir2 = 0
        for e in self.graph.es:
            if e['dirs'].is_directed():
                isdir2 += 1
        sys.stdout.write('\t:: Directionality set for %u interactions\n'\
            '\t   based on known (de)phosphorylation events.\n'%(isdir2 - isdir))
        sys.stdout.flush()
    
    def phosphorylation_signs(self):
        self.update_vname()
        new_signs = 0
        dephos = {}
        # looking up effects of dephosphorylations:
        for e in self.graph.es:
            for ptm in e['ptm']:
                sign = None
                if ptm.ptm.typ == 'dephosphorylation':
                    direction = (ptm.domain.protein, ptm.ptm.protein)
                    signs = e['dirs'].get_sign(direction)
                    if signs[0] and not signs[1]:
                        sign = 'positive'
                    elif signs[1] and not signs[0]:
                        sign = 'negative'
                    if sign:
                        if ptm.ptm.protein not in dephos:
                            dephos[ptm.ptm.protein] = []
                        dephos[ptm.ptm.protein].append({
                            'protein': ptm.ptm.protein,
                            'resaa': ptm.ptm.residue.name,
                            'resnum': ptm.ptm.residue.number,
                            'sign': sign})
        # set the opposite sign for posphorylations as it is 
        # at corresponding dephosphorylations:
        for e in self.graph.es:
            for ptm in e['ptm']:
                if ptm.ptm.typ == 'phosphorylation':
                    if ptm.ptm.protein in dephos:
                        for de in dephos[protein]:
                            if ptm.ptm.residue.number == de['resnum'] and \
                                ptm.ptm.residue.name == de['resaa']:
                                direction = (ptm.domain.protein, ptm.ptm.protein)
                                signs = e['dirs'].get_sign(direction)
                                sign = 'positive' if de['sign'] == 'negative' \
                                    else 'negative'
                                if not bool(sum(signs)):
                                    e['dirs'].get_sign(direction, sign, ptm.sources)
                                    new_signs += 1
        sys.stdout.write('\t:: Signes set based on phosphorylation-'\
            'dephosphorylation pairs: %u\n'%new_signs)
        sys.stdout.flush()
    
    def kinase_stats(self):
        counts = {}
        pcounts = {}
        ks_pairs = 0
        psite_num = 0
        for e in self.graph.es:
            ks_srcs = []
            for p in e['ptm']:
                if p.__class__.__name__ == 'DomainMotif' and p.ptm.typ == 'phosphorylation':
                    ks_srcs += p.ptm.sources + p.sources
                    p_srcs = p.ptm.sources + p.sources
                    p_srcs = list(set(p_srcs) - set(['Swiss-Prot']))
                    p_srcs.sort()
                    p_srcs = tuple(p_srcs)
                    if p_srcs not in pcounts:
                        pcounts[p_srcs] = 0
                    pcounts[p_srcs] += 1
                    psite_num += 1
            if len(ks_srcs) > 0:
                ks_srcs = list(set(ks_srcs) - set(['Swiss-Prot']))
                ks_srcs.sort()
                ks_srcs = tuple(ks_srcs)
                if ks_srcs not in counts:
                    counts[ks_srcs] = 0
                counts[ks_srcs] += 1
                ks_pairs += 1
        return {'phosphorylations': pcounts, 'kinase_substrate': counts}
    
    def update_db_dict(self):
        self.db_dict = {
            'nodes': {},
            'edges': {}
        }
        self.update_vertex_sources()
        self.update_sources()
        for e in self.graph.es:
            for s in e['sources']:
                if s not in self.db_dict['edges']:
                    self.db_dict['edges'][s] = set()
                self.db_dict['edges'][s].add(e.index)
        for v in self.graph.vs:
            for s in v['sources']:
                if s not in self.db_dict['nodes']:
                    self.db_dict['nodes'][s] = set()
                self.db_dict['nodes'][s].add(v.index)
    
    def sources_overlap(self, diagonal = False):
        self.update_db_dict()
        result = {
            'single': {
                'nodes': {},
                'edges': {}
            },
            'overlap': {
                'nodes': {},
                'edges': {}
            }
        }
        for s in self.sources:
            result['single']['nodes'][s] = len(self.db_dict['nodes'][s])
            result['single']['edges'][s] = len(self.db_dict['edges'][s])
        for s1 in self.sources:
            for s2 in self.sources:
                if diagonal or s1 != s2:
                    result['overlap']['nodes'][(s1, s2)] = \
                        len(self.db_dict['nodes'][s1] & self.db_dict['nodes'][s2])
                    result['overlap']['edges'][(s1, s2)] = \
                        len(self.db_dict['edges'][s1] & self.db_dict['edges'][s2])
        return result
    
    def source_stats(self):
        stats = self.sources_overlap()
        degrees = self.graph.vs.degree()
        bwness = self.graph.vs.betweenness()
        ebwness = self.graph.es.edge_betweenness()
        for s in stats['single']['nodes'].keys():
            pass
    
    def source_diagram(self, outf = None, **kwargs):
        outf = outf if outf is not None else os.path.join('pdf', 'databases.pdf')
        stats = self.sources_overlap(diagonal = True)
        sources = []
        overlaps = {}
        for s, n in iteritems(stats['single']['nodes']):
            sources.append((s, (n, None), (stats['single']['edges'][s], None)))
        for s, n in iteritems(stats['overlap']['nodes']):
            overlaps[s] = {'size': (n, stats['overlap']['edges'][s])}
        diagram = bdrawing.InterSet(sources, overlaps, outf = outf, **kwargs)
        diagram.draw()
    
    def get_dirs_signs(self):
        result = {}
        for dbs in [data_formats.ptm.values(), data_formats.interaction_htp.values(),
            data_formats.pathway.values(), data_formats.transcription.values()]:
            for db in dbs:
                result[db.name] = [bool(db.isDirected), bool(db.sign)]
        return result
    
    def basic_stats(self, latex = False, caption = '', latex_hdr = True,
                    fontsize = 8, font = 'HelveticaNeueLTStd-LtCn',
                    header_format = '%s', row_order = None, by_category = True,
                    use_cats = ['p', 'm', 'i', 'r']):
        '''
        Returns basic numbers about the network resources, e.g. edge and 
        node counts. 
        
        latex
            Return table in a LaTeX document. This can be compiled by
            PDFLaTeX: 
            latex stats.tex
        '''
        outf = os.path.join('results', 'databases-%s.tex'%self.session) \
            if latex else os.path.join('results', 'databases-%s.tsv'%self.session)
        stats = self.sources_overlap()
        dirs = self.get_dirs_signs()
        header = ['Database', 'Node count', 'Edge count', 'Directions', 'Signs', 'Annotations', 'Notes']
        out = [header]
        
        desc = descriptions.descriptions
        for s in sorted(stats['single']['nodes'].keys()):
            annot = ', '.join(desc[s]['annot']) if s in desc and 'annot' in desc[s] else ''
            recom = desc[s]['recommend'] if s in desc and 'recommend' in desc[s] else ''
            out.append([x for x in [
                s,
                stats['single']['nodes'][s],
                stats['single']['edges'][s],
                int(dirs[s][0]) if s in dirs else '',
                int(dirs[s][1]) if s in dirs else '',
                annot,
                recom,
            ]])
        if not latex:
            out = '\n'.join(['\t'.join(x) for x in out])
            with open(outf, 'w') as f:
                f.write(out)
            sys.stdout.write('\t:: Output written to file `%s`\n'%outf)
            sys.stdout.flush()
        else:
            
            cats = list(reduce(lambda e1, e2: e1 | e2['cat'], self.graph.es, set([]))) \
                if by_category else []
            
            cats = set(cats) & set(use_cats)
            use_cats = list(filter(lambda c: c in cats, use_cats))
            
            out = dict(map(lambda l: (l[0], l[1:]), out[1:]))
            
            if not by_category:
                row_order = sorted(self.sources, key = lambda s: s.lower())
            else:
                row_order = []
                for cat in use_cats:
                    row_order.append((data_formats.catnames[cat], 'subtitle'))
                    row_order.extend(
                        sorted(
                            filter(
                                lambda s:
                                    data_formats.categories[s] == cat,
                                self.sources
                            ),
                            key = lambda s: s.lower()
                        )
                    )
            
            texnewline = r'\\' + '\n'
            
            _latex_tab = r'''%s
                    \begin{tabularx}{\textwidth}{%s}
                    \toprule
                        %s
                    \midrule
                        %s
                    \bottomrule
                    \end{tabularx}
                    %s
                '''
            _latex_hdr = r'''\documentclass[a4paper,%upt]{extarticle}
                    \usepackage{fontspec}
                    \usepackage{xunicode}
                    \usepackage{polyglossia}
                    \setdefaultlanguage{english}
                    \usepackage{xltxtra}
                    \usepackage{microtype}
                    \usepackage[margin=5pt,portrait,paperwidth=24cm,paperheight=30cm]{geometry}
                    \usepackage{amsmath}
                    \usepackage{amssymb}
                    \usepackage[usenames,dvipsnames,svgnames,table]{xcolor}
                    \usepackage{color}
                    \usepackage{booktabs}
                    \usepackage{tabularx}
                    \setmainfont{%s}
                    \definecolor{grey875}{gray}{0.125}
                    \begin{document}
                    \color{grey875}
                    \thispagestyle{empty}
                    \vfill
                    \begin{table}[h]
                ''' % (fontsize, font) if latex_hdr else ''
            _latex_end = r'''
                    \caption{%s}
                    \end{table}
                    \end{document}
                ''' % caption if latex_hdr else ''
            
            _hdr_row = ' & '.join([header_format%h.replace(r'%', r'\%') \
                for h in header]) + '\\\\'
            formatter = lambda x: locale.format('%.2f', x, grouping = True) \
                if type(x) is float \
                else locale.format('%d', x, grouping = True) \
                if type(x) is int \
                else x
            intfloat = lambda x: float(x) if '.' in x else int(x)
            _rows = ''
            for i, k in enumerate(row_order):
                
                
                
                if type(k) is tuple and k[1] == 'subtitle':
                    row = '\n'.join([
                        r'\midrule' if i > 0 else '',
                        r'\multicolumn{6}{l}{%s}\\' % k[0],
                        r'\midrule',
                        ''
                    ])
                else:
                    out[k][2] = r'$\bigstar$' if bool(out[k][2]) else ''
                    out[k][3] = r'$\bigstar$' if bool(out[k][3]) else ''
                    row = ' & '.join([k] + [
                        xx.replace('_', r'\_') \
                            if type(xx) is not int \
                            else '{:,}'.format(xx) \
                        for xx in out[k]]
                    ) + '\\\\\n'
                
                _rows += row
            
            _latex_tab = _latex_tab % (_latex_hdr, 'r'*(len(header) - 2) + r'p{2.7cm}<{\raggedright}X<{\flushleft}', _hdr_row, _rows, _latex_end)
            
            with open(outf, 'w') as f:
                f.write(_latex_tab)
            sys.stdout.write('\t:: Output written to file `%s`\n'%outf)
            sys.stdout.flush()
    
    def source_network(self, font = 'HelveticaNeueLTStd'):
        '''
        For EMBL branding, use Helvetica Neue Linotype Standard light
        '''
        stats = self.sources_overlap()
        tupleListNodes = []
        tupleListEdges = []
        for dbs, overlap in iteritems(stats['overlap']['nodes']):
            if overlap > 0:
                tupleListNodes.append(tuple(sorted(list(dbs)) + [overlap]))
        for dbs, overlap in iteritems(stats['overlap']['edges']):
            if overlap > 0:
                tupleListEdges.append(tuple(sorted(list(dbs)) + [overlap]))
        tupleListNodes = list(set(tupleListNodes))
        tupleListEdges = list(set(tupleListEdges))
        self.sourceNetNodes = igraph.Graph.TupleList(tupleListNodes, weights = True)
        self.sourceNetEdges = igraph.Graph.TupleList(tupleListEdges, weights = True)
        # edge widths proportional to overlaps in unique nodes/edges
        self.sourceNetNodes.es['edge_width'] = [math.log(
            stats['overlap']['nodes'][(
                self.sourceNetNodes.vs[x.source]['name'],
                self.sourceNetNodes.vs[x.target]['name'])], 10)
            for x in self.sourceNetNodes.es]
        self.sourceNetEdges.es['edge_width'] = [math.log(
            stats['overlap']['edges'][(
                self.sourceNetEdges.vs[x.source]['name'],
                self.sourceNetEdges.vs[x.target]['name'])], 10)
            for x in self.sourceNetEdges.es]
        # node sizes proportional to number of nodes/edges
        self.sourceNetNodes.vs['vertex_size'] = [math.log(len(
            self.db_dict['nodes'][x['name']]), 10) * 5 
            for x in self.sourceNetNodes.vs]
        self.sourceNetEdges.vs['vertex_size'] = [math.log(len(
            self.db_dict['edges'][x['name']]), 10) * 5 
            for x in self.sourceNetEdges.vs]
        # numbers in vertex labels:
        v['label'] = [v['name'] + ' (%u)'%len(self.db_dict['nodes'][v['name']]) \
            for v in self.sourceNetNodes.vs]
        v['label'] = [v['name'] + ' (%u)'%len(self.db_dict['edges'][v['name']]) \
            for v in self.sourceNetEdges.vs]
        plotParamNodes = PlotParam(graph = self.sourceNetNodes,
            filename = 'db_net_nodes.pdf', 
            layout = 'circular', vertex_label_color = '#4d4d4d', 
            vertex_color = '#73b360', edge_color = '#006666', 
            vertex_fill_alpha = 'ff',
            vertex_label_font = font, 
            vertex_size = self.sourceNetNodes.vs['vertex_size'],
            bbox = igraph.drawing.utils.BoundingBox(20, 20, 994, 994), 
            dimensions = (1024, 1024))
        plotParamEdges = PlotParam(graph = self.sourceNetEdges,
            filename = 'db_net_nodes.pdf', 
            layout = 'circular', vertex_label_color = '#4d4d4d', 
            vertex_color = '#73b360', edge_color = '#006666', 
            vertex_fill_alpha = 'ff',
            vertex_label_font = font, 
            vertex_size = self.sourceNetEdges.vs['vertex_size'],
            bbox = igraph.drawing.utils.BoundingBox(20, 20, 994, 994), 
            dimensions = (1024, 1024))
        return plotParamNodes, plotParamEdges
    
    #
    # Load data from GDSC
    #
    
    def load_mutations(self, attributes = None, gdsc_datadir = None, 
            mutation_file = None):
        '''
        Mutations are listed in vertex attributes. Mutation() objects 
        offers methods to identify residues and look up in Ptm(), Motif() 
        and Domain() objects, to check if those residues are 
        modified, or are in some short motif or domain.
        '''
        self.mutation_samples = []
        attributes = attributes if attributes is not None else \
            ['Consequence', 'COSMIC_ID', 'SAMPLE_NAME', 'Tissue_TCGA', 'ZYGOSITY']
        self.update_vname()
        g = gdsc.GDSC(datadir = gdsc_datadir)
        data = g.read_mutations(attributes = attributes, infile = mutation_file)
        if 'mut' not in self.graph.vs.attributes():
            self.graph.vs['mut'] = [{} for _ in self.graph.vs]
        prg = Progress(len(data), 'Processing mutations', 33)
        for uniprot, muts in iteritems(data):
            prg.step()
            if uniprot in self.nodDct:
                for mu in muts:
                    if self.graph.vs[self.nodDct[uniprot]]['mut'] is None:
                        self.graph.vs[self.nodDct[uniprot]]['mut'] = {}
                    if mu.sample not in \
                        self.graph.vs[self.nodDct[uniprot]]['mut']:
                        self.graph.vs[self.nodDct[uniprot]]['mut']\
                            [mu.sample] = []
                    self.graph.vs[self.nodDct[uniprot]]['mut']\
                        [int(mu.sample)].append(mu)
                    if mu.sample not in self.mutation_samples:
                        self.mutation_samples.append(int(mu.sample))
        prg.terminate()
        data = None
    
    def load_expression(self, array = False):
        '''
        Expression data can be loaded into vertex attributes, 
        or into a pandas DataFrame – the latter offers faster 
        ways to process and use these huge matrices.
        '''
        self.update_vname()
        data = gdsc.read_transcriptomics()
        if 'exp' not in self.graph.vs.attributes():
            self.graph.vs['exp'] = [{} for _ in self.graph.vs]
        prg = Progress(len(data), 'Processing transcriptomics', 33)
        if array:
            for gsymb in data.keys():
                prg.step()
                for up in self.mapper.map_name(gsymb, 'genesymbol', 'uniprot'):
                    if up in self.nodDct:
                        data[up] = data[gsymb]
                del data[gsymb]
            self.exp = pandas.DataFrame(data)
        else:
            for gsymb, expr in iteritems(data):
                prg.step()
                uniprots = self.mapper.map_name(gsymb, 'genesymbol', 'uniprot')
                for up in uniprots:
                    if up in self.nodDct:
                        self.graph.vs[self.nodDct[up]]['exp'] = \
                            dict(expr.items() + \
                                self.graph.vs[self.nodDct[up]]['exp'].items())
        prg.terminate()
    
    def edges_expression(self, func = lambda x, y: x * y):
        '''
        Executes function `func` for each pairs of connected proteins in the 
        network, for every expression dataset. By default, `func` simply
        gives the product the (normalized) expression values.
        
        func : callable
            Function to handle 2 vectors (pandas.Series() objects), should
            return one vector of the same length.
        '''
        self.update_vindex()
        self.exp_prod = pandas.DataFrame(index = self.exp.index, 
            columns = [])
        prg = Progress(self.graph.ecount(), 
            'Weigh edges based on protein expression', 37)
        for e in self.graph.es:
            prg.step()
            nodes = self.edge_names(e)
            if nodes[0] in self.exp.columns and nodes[1] in self.exp.columns:
                self.exp_prod[e.index] = func(self.exp[nodes[0]], 
                    self.exp[nodes[1]])
            else:
                self.exp_prod[e.index] = pandas.Series([None] * \
                    self.exp_prod.shape[0])
        prg.terminate()
    
    #
    # Find and remove edges where mutations disrupt PTMs
    #
    
    def mutated_edges(self, sample):
        '''
        Compares the mutated residues and the modified residues in PTMs.
        Interactions are marked as mutated if the target residue in the 
        underlying PTM is mutated.
        '''
        toDel = []
        disrupted = {}
        for e in self.graph.es:
            for v in [e.source, e.target]:
                for smpl, mut in iteritems(self.graph.vs[v]['mut']):
                    if smpl == sample:
                        for ptm in e['ptm']:
                            if mut.original == ptm.ptm.residue:
                                toDel.append(e.index)
                                if e.index not in disrupted:
                                    disrupted[e.index] = \
                                        {'ptms': len(e['ptm']), 'disr': 0}
                                disrupted[e.index]['disr'] += 1
        return toDel, disrupted
    
    def load_go(self, aspect = ['C', 'F', 'P']):
        go.load_go(self.graph, aspect = aspect)
    
    def go_dict(self, organism = 9606):
        if not hasattr(self, 'go'):
            self.go = {}
        self.go[organism] = go.GOAnnotation(organism)
    
    def go_enrichment(self, proteins = None, aspect = 'P', alpha = 0.05, 
        correction_method = 'hommel', all_proteins = None):
        if not hasattr(self, 'go') or self.ncbi_tax_id not in self.go:
            self.go_dict()
        all_proteins = set(all_proteins) \
            if type(all_proteins) is list else all_proteins \
            if type(all_proteins) is set else set(self.graph.vs['name'])
        annotation = dict([(up, g) for up, g in \
            getattr(self.go[self.ncbi_tax_id], iteritems(aspect.lower())) \
            if up in all_proteins])
        enr = go.GOEnrichmentSet(aspect = aspect, organism = self.ncbi_tax_id, 
            basic_set = annotation, alpha = alpha, 
            correction_method = correction_method)
        if proteins is not None: enr.new_set(set_names = proteins)
        return enr
    
    def init_gsea(self, user):
        self.gsea = gsea.GSEA(user = user, mapper = self.mapper)
        sys.stdout.write('\n :: GSEA object initialized, use '\
            'load_genesets() to load some of the collections.\n')
        sys.stdout.write('      e.g. load_genesets([\'H\'])\n\n')
        sys.stdout.flush()
        self.gsea.show_collections()
    
    def add_genesets(self, genesets):
        for gsetid in genesets:
            if gsetid in self.gsea.collections:
                self.gsea.load_collection(gsetid)
    
    def geneset_enrichment(self, proteins, all_proteins = None,
        geneset_ids = None, alpha = 0.05, correction_method = 'hommel'):
        all_proteins = self.graph.vs['name'] \
            if all_proteins is None else all_proteins
        enr = gsea.GSEABinaryEnrichmentSet(basic_set = all_proteins,
            gsea = self.gsea, geneset_ids = geneset_ids,
            alpha = alpha, correction_method = correction_method)
        enr.new_set(proteins)
        return enr
    
    def find_all_paths(self, start, end, mode = 'OUT', 
        maxlen = 2, graph = None):
        '''
        Finds all paths up to length `maxlen` between groups of
        vertices. This function is needed only becaues igraph`s
        get_all_shortest_paths() finds only the shortest, not any
        path up to a defined length.
        
        @start : int or list
            Indices of the starting node(s) of the paths.
        @end : int or list
            Indices of the target node(s) of the paths.
        @mode : 'IN', 'OUT', 'ALL'
            Passed to igraph.Graph.neighbors()
        @maxlen : int
            Maximum length of paths in steps, i.e. if maxlen = 3, then 
            the longest path may consist of 3 edges and 4 nodes.
        @graph : igraph.Graph object
            The graph you want to find paths in. self.graph by default.
        '''
        def find_all_paths_aux(adjlist, start, end, path, maxlen = None):
            path = path + [start]
            if start == end:
                return [path]
            paths = []
            if len(path) < maxlen + 1:
                for node in adjlist[start] - set(path):
                    paths.extend(find_all_paths_aux(adjlist, node, end, path, maxlen))
            return paths
        graph = self.graph if graph is None else graph
        adjlist = [set(graph.neighbors(node, mode = mode)) \
            for node in xrange(graph.vcount())]
        all_paths = []
        start = start if type(start) is list else [start]
        end = end if type(end) is list else [end]
        prg = Progress(len(start) * len(end), 
            'Looking up all paths up to length %u'%maxlen, 1)
        for s in start:
            for e in end:
                prg.step()
                all_paths.extend(find_all_paths_aux(adjlist, s, e, [], maxlen))
        prg.terminate()
        return all_paths
    
    def find_all_paths2(self, graph, start, end, mode = 'OUT', maxlen = 2, psize = 100):
        def one_step(paths, adjlist):
            # extends all paths by one step using all neighbors in adjacency list
            return [i for ii in [[s + [a] for a in adjlist[s[-1]] if a not in s] \
                for s in paths] for i in ii]
        def parts(paths, targets, adjlist, maxlen = 2, psize = 100, depth = 1):
            complete_paths = [p for p in paths if p[-1] in targets]
            if len(paths) > 0 and len(paths[0]) <= maxlen:
                for i in xrange(0, len(paths), psize):
                    new_paths = one_step(paths[i:i+psize], adjlist)
                    complete_paths += parts(new_paths, targets, adjlist, maxlen, psize, 
                        depth = depth + 1)
                    sys.stdout.write("\r"+" "*90)
                    sys.stdout.write('\r\tDepth: %u :: Paths found: %u' % \
                        (depth, len(complete_paths)))
                    sys.stdout.flush()
            return complete_paths
        graph = self.graph if graph is None else graph
        all_paths = []
        start = start if type(start) is list else [start]
        end = end if type(end) is list else [end]
        send = set(end)
        sys.stdout.write('\n')
        adjlist = [set(graph.neighbors(node, mode = mode)) \
            for node in xrange(graph.vcount())]
        paths = [[s] for s in start]
        all_paths = parts(paths, end, adjlist, maxlen, psize)
        sys.stdout.write('\n')
        return all_paths
    
    def transcription_factors(self):
        return common.uniqList([j for ssl in \
            [i for sl in \
                [[e['dirs'].src_by_source(s) for s in e['sources_by_type']['TF']]\
                    for e in self.graph.es if 'TF' in e['type']] \
            for i in sl] \
            for j in ssl])
    
    def neighbourhood_network(self, center, second = False):
        center = center if type(center) is int else self.graph.vs['name'].index(center)
        if second:
            nodes = self.second_neighbours(center, indices = True, with_first = True)
        else:
            nodes = self.first_neighbours(center, indices = True)
        nodes.append(center)
        return self.graph.induced_subgraph(nodes, implementation = 'create_from_scratch')
    
    def get_proteomicsdb(self, user, passwd, tissues = None, pickle = None):
        self.proteomicsdb = proteomicsdb.ProteomicsDB(user, passwd)
        self.proteomicsdb.load(pfile = pickle)
        self.proteomicsdb.get_tissues()
        self.proteomicsdb.tissues_x_proteins(tissues = tissues)
        self.exp_samples = self.proteomicsdb.tissues_loaded
    
    def prdb_tissue_expr(self, tissue, prdb = None, graph = None, occurrence = 1, 
        group_function = lambda x: sum(x) / float(len(x))):
        graph = self.graph if graph is None else graph
        prdb = self.proteomicsdb if prdb is None else prdb
        nsamples = len(prdb.samples[tissue])
        occurrence = min(nsamples, occurrence) \
            if type(occurrence) is int \
            else nsamples * occurrence
        proteins_present = set([uniprot for uniprot, cnt in \
            Counter([uniprot for uniprots in \
                [expr.keys() for expr in \
                    [prdb.expression[sample] for sample in prdb.samples[tissue]] \
                ] for uniprot in iteritems(uniprots)]) \
            if cnt >= occurrence]) & set(graph.vs['name'])
        expressions = dict([(uniprot, group_function(
            [prdb.expression[sample][uniprot] \
                for sample in prdb.samples[tissue] \
                if uniprot in prdb.expression[sample]])) \
            for uniprot in proteins_present])
        graph.vs[tissue] = [0.0 if v['name'] not in expressions \
            else expressions[v['name']] for v in graph.vs]
    
    def prdb_tissue_network(self, tissue, graph = None):
        graph = self.graph if graph is None else graph
        if tissue not in graph.vs.attributes():
            self.prdb_tissue_expr(tissue, graph = graph)
        return graph.induced_subgraph([v.index for v in graph.vs if v[tissue] > 0.0])
    
    def small_plot(self, graph, **kwargs):
        '''
        This method is deprecated, do not use it.
        '''
        arrow_size = []
        arrow_width = []
        edge_color = []
        dgraph = graph if graph.is_directed() else self.get_directed(graph, 
            True, False, True)
        toDel = []
        for e in dgraph.es:
            if not e['dirs'].is_directed and e.index not in toDel:
                opp = dgraph.get_eid(e.target, e.soure, error = False)
                if opp != -1 and not dgraph.es[opp]['dirs'].is_directed():
                    toDel.append(opp)
        dgraph.delete_edges(list(set(toDel)))
        for e in dgraph.es:
            src = dgraph.vs[e.source]['name']
            tgt = dgraph.vs[e.target]['name']
            if not e['dirs'].is_directed():
                edge_color.append('#646567')
                arrow_size.append(0.0001)
                arrow_width.append(0.0001)
            else:
                if e['dirs'].is_stimulation((src, tgt)):
                    edge_color.append('#6EA945')
                    arrow_size.append(0.5)
                    arrow_width.append(0.7)
                elif e['dirs'].is_inhibition((src, tgt)):
                    edge_color.append('#DA0025')
                    arrow_size.append(0.5)
                    arrow_width.append(0.7)
                else:
                    edge_color.append('#007B7F')
                    arrow_size.append(0.5)
                    arrow_width.append(0.7)
        p = bdrawing.Plot(graph = dgraph, edge_color = edge_color, 
            edge_arrow_size = arrow_size, edge_arrow_width = arrow_width,
            vertex_label = dgraph.vs['label'], vertex_color = 'ltp', 
            vertex_alpha = 'FF', edge_alpha = 'FF', 
            edge_label = [', '.join(l) for l in dgraph.es['loc']],
            vertex_label_family = 'HelveticaNeueLT Std Lt', 
            edge_label_family = 'HelveticaNeueLT Std Lt', **kwargs)
        return p.draw()
    
    def communities(self, method, **kwargs):
        graph = self.graph
        if method == 'spinglass':
            giant = self.get_giant()
            graph = giant
            if 'spins' not in kwargs:
                kwargs['spins'] = 255
        elif method == 'fastgreedy':
            undgr = self.as_undirected(combine_edges = 'ignore')
            graph = undgr
        if hasattr(graph, '%s_community'%method):
            to_call = getattr(graph, '%s_community'%method)
            if hasattr(to_call, '__call__'):
                comm = to_call(**kwargs)
            if comm.__class__.__name__ == 'VertexDendrogram':
                comm = comm.as_clustering()
        return comm
    
    def set_receptors(self):
        '''
        Creates a vertex attribute `rec` with value *True* if
        the protein is a receptor, otherwise *False*.
        '''
        self.update_vname()
        self.graph.vs['rec'] = [False for _ in self.graph.vs]
        if 'rec' not in self.lists:
            self.receptors_list()
        for rec in self.lists['rec']:
            if rec in self.nodDct:
                self.graph.vs[self.nodDct[rec]]['rec'] = True
    
    def set_kinases(self):
        '''
        Creates a vertex attribute `kin` with value *True* if
        the protein is a kinase, otherwise *False*.
        '''
        self.update_vname()
        self.graph.vs['kin'] = [False for _ in self.graph.vs]
        if 'kin' not in self.lists:
            self.kinases_list()
        for kin in self.lists['kin']:
            self.graph.vs[self.nodDct[kin]]['kin'] = True
    
    def set_druggability(self):
        '''
        Creates a vertex attribute `dgb` with value *True* if
        the protein is druggable, otherwise *False*.
        '''
        self.update_vname()
        self.graph.vs['dgb'] = [False for _ in self.graph.vs]
        if 'dgb' not in self.lists:
            self.druggability_list()
        for dgb in self.lists['dgb']:
            self.graph.vs[self.nodDct[dgb]]['dgb'] = True
    
    def set_drugtargets(self, pchembl = 5.0):
        '''
        Creates a vertex attribute `dtg` with value *True* if
        the protein has at least one compound binding with 
        affinity higher than `pchembl`, otherwise *False*.
        '''
        self.update_vname()
        self.graph.vs['dtg'] = [False for _ in self.graph.vs]
        if 'compounds_data' not in self.graph.vs.attributes():
            self.compounds_from_chembl(assay_types = ['B'], pchembl = True)
        for v in self.graph.vs:
            for d in v['compounds_data']:
                pc = [float(p) for p in d['pchembl'] if len(p) > 0]
                if len(pc) > 0:
                    if max(pc) > pchembl:
                        v['dtg'] = True
    
    def set_transcription_factors(self, classes = ['a', 'b', 'other']):
        '''
        Creates a vertex attribute `tf` with value *True* if
        the protein is a transcription factor, otherwise *False*.
        '''
        self.update_vname()
        self.graph.vs['tf'] = [False for _ in self.graph.vs]
        if 'tfs' not in self.lists:
            self.tfs_list()
        for tf in self.lists['tfs']:
            if tf in self.nodDct:
                self.graph.vs[self.nodDct[tf]]['tf'] = True
    
    def get_pathways(self, source):
        attrname = '%s_pathways'%source
        proteins_pws = None
        interactions_pws = None
        if hasattr(dataio, attrname):
            fun = getattr(dataio, attrname)
            proteins_pws, interactions_pws = fun(mapper = self.mapper)
        return proteins_pws, interactions_pws
    
    def pathway_members(self, pathway, source):
        attr = '%s_pathways'%source
        if attr in self.graph.vs.attribute_names():
            return _NamedVertexSeq(
                filter(lambda v:
                    pathway in v[attr],
                    self.graph.vs
                ),
                self.nodNam,
                self.nodLab
            )
        else:
            return _NamedVertexSeq([], self.nodNam, self.nodLab)
    
    def load_all_pathways(self, graph = None):
        self.kegg_pathways(graph = graph)
        self.signor_pathways(graph = graph)
        self.pathway_attributes(graph = graph)
    
    def load_pathways(self, source, graph = None):
        attrname = '%s_pathways'%source
        g = self.graph if graph is None else graph
        nodDct = dict(zip(g.vs['name'], xrange(g.vcount())))
        proteins_pws, interactions_pws = self.get_pathways(source)
        g.vs[attrname] = [set([]) for _ in g.vs]
        g.es[attrname] = [set([]) for _ in g.es]
        if type(proteins_pws) is dict:
            for pw, proteins in iteritems(proteins_pws):
                for protein in proteins:
                    if protein in proteins:
                        uniprots = self.mapper.map_name(protein, 
                            'uniprot', 'uniprot')
                        for u in uniprots:
                            if u in nodDct:
                                g.vs[nodDct[u]][attrname].add(pw)
        if type(interactions_pws) is dict:
            for pw, ia in iteritems(interactions_pws):
                for pair in ia:
                    usrcs = self.mapper.map_name(pair[0], 'uniprot', 'uniprot')
                    utgts = self.mapper.map_name(pair[1], 'uniprot', 'uniprot')
                    for usrc in usrcs:
                        for utgt in utgts:
                            if usrc in nodDct and utgt in nodDct:
                                eid = g.get_eid(nodDct[usrc], 
                                    nodDct[utgt], error = False)
                                if eid != -1:
                                    g.es[eid][attrname].add(pw)
    
    def signor_pathways(self, graph = None):
        self.load_pathways('signor', graph = graph)
    
    def kegg_pathways(self, graph = None):
        self.load_pathways('kegg', graph = graph)
    
    def pathway_attributes(self, graph = None):
        g = self.graph if graph is None else graph
        g.vs['netpath_pathways'] = [set([]) for _ in xrange(g.vcount())]
        for e in g.es:
            g.vs[e.source]['netpath_pathways'] = \
                g.vs[e.source]['netpath_pathways'] | set(e['netpath_pathways'])
            g.vs[e.target]['netpath_pathways'] = \
                g.vs[e.target]['netpath_pathways'] | set(e['netpath_pathways'])
        g.vs['signalink_pathways'] = [set(v['slk_pathways']) for v in g.vs]
        for v in g.vs:
            if v['atg']:
                v['signalink_pathways'].add('autophagy')
    
    def pathways_table(self, filename = 'genes_pathways.list', 
        pw_sources = ['signalink', 'signor', 'netpath', 'kegg'], graph = None):
        result = []
        hdr = ['UniProt', 'GeneSymbol', 'Database', 'Pathway']
        g = self.graph if graph is None else graph
        self.genesymbol_labels(graph = g)
        for v in g.vs:
            for src in pw_sources:
                pw_attr = '%s_pathways'%src
                for pw in v[pw_attr]:
                    result.append([v['name'], v['label'], src, pw])
        with open(filename, 'w') as f:
            f.write('\t'.join(hdr))
            f.write('\n'.join(map(lambda l: '\t'.join(l), result)))
    
    def guide2pharma(self):
        result = []
        data = dataio.get_guide2pharma()
        for d in data:
            ulig = []
            urec = self.mapper.map_name(d['receptor_uniprot'], 'uniprot', 'uniprot')
            if len(d['ligand_uniprot']) > 0:
                ulig = self.mapper.map_name(d['ligand_uniprot'], 'uniprot', 'uniprot')
            if len(d['ligand_genesymbol']) > 0:
                ulig += self.mapper.map_name(d['ligand_genesymbol'], 
                    'genesymbol', 'uniprot')
            if len(ulig) > 0 and len(urec) > 0:
                for ur in urec:
                    for ul in ulig:
                        result.append([ul, ur, d['effect'], d['pubmed'], True])
        return result
    
    def set_tfs(self, classes = ['a', 'b', 'other']):
        self.set_transcription_factors(classes)
    
    def load_disgenet(self, dataset = 'curated', score = 0.0):
        self.update_vname()
        data = dataio.get_disgenet(dataset = dataset)
        self.graph.vs['dis'] = [[] for _ in self.graph.vs]
        for d in data:
            if d['score'] >= score:
                uniprots = self.mapper.map_name(d['entrez'], 'entrez', 'uniprot')
                for up in uniprots:
                    if up in self.nodInd:
                        self.graph.vs[self.nodDct[up]]['dis'].append(d['disease'])
    
    def curation_stats(self, by_category = True):
        result = {}
        all_refs = len(set(common.flatList([[r.pmid for r in e['references']] \
            for e in self.graph.es])))
        
        cats = list(reduce(lambda e1, e2: e1 | e2['cat'], self.graph.es, set([]))) \
            if by_category else []
        
        for s in list(self.sources) + cats:
            
            sattr = 'cat' if s in data_formats.catnames else 'sources'
            rattr = 'refs_by_cat' if s in data_formats.catnames else 'refs_by_source'
            
            cat = None if s in data_formats.catnames \
                or s not in data_formats.categories \
                else data_formats.categories[s]
            catmembers = set(data_formats.catnames.keys()) \
                if s in data_formats.catnames \
                else set(self.sources) if not hasattr(data_formats, cat) \
                else getattr(data_formats, cat)
            
            src_nodes = len([_ for v in self.graph.vs if s in v[sattr]])
            cat_nodes = self.graph.vcount() if cat is None \
                else len([v for v in self.graph.vs if len(v[sattr] & catmembers)])
            src_nodes_pct = src_nodes / float(cat_nodes) * 100.0
            only_src_nodes = len([_ for v in self.graph.vs \
                if s in v[sattr] and len(v[sattr] & catmembers) == 1])
            only_src_nodes_pct = only_src_nodes / float(cat_nodes) * 100.0
            shared_nodes = len([_ for v in self.graph.vs \
                if s in v[sattr] and len(v[sattr] & catmembers) > 1])
            
            src_edges = len([e for e in self.graph.es if s in e[sattr]])
            cat_edges = self.graph.ecount() if cat is None \
                else len([e for e in self.graph.es if len(e[sattr] & catmembers)])
            src_edges_pct = src_edges / \
                    float(cat_edges) * 100.0
            only_src_edges = len([e for e in self.graph.es \
                if s in e[sattr] and len(e[sattr] & catmembers) == 1])
            only_src_edges_pct = only_src_edges / float(cat_edges) * 100.0
            shared_edges = len([e.index for e in self.graph.es \
                if s in e[sattr] and len(e[sattr] & catmembers) > 1])
            
            src_refs = set(common.uniqList([r.pmid for r in common.flatList([e[rattr][s] \
                for e in self.graph.es if s in e[rattr]])]))
            other_refs = set(common.flatList([[r.pmid for r in \
                    common.flatList([rr for sr, rr in iteritems(e[rattr]) \
                        if sr != s and sr in catmembers])] \
                for e in self.graph.es]))
            only_src_refs = len(src_refs - other_refs)
            only_src_refs_pct = len(src_refs - other_refs) / float(all_refs) * 100.0
            src_refs_pct = len(src_refs) / float(all_refs) * 100.0
            shared_refs = len(src_refs & other_refs)
            
            shared_curation_effort = sum([len(x) for x in \
                [set(common.flatList([[(r.pmid, e.index) for r in rr] \
                    for sr, rr in iteritems(e[rattr]) \
                        if sr != s and sr in catmembers])) \
                & \
                set([(rl.pmid, e.index) for rl in e[rattr][s]]) \
                for e in self.graph.es if s in e[rattr]]])
            
            src_only_curation_effort = sum([len(x) for x in \
                [set([(rl.pmid, e.index) for rl in e[rattr][s]]) - \
                set(common.flatList([[(r.pmid, e.index) for r in rr] \
                    for sr, rr in iteritems(e[rattr]) \
                        if sr != s if sr in catmembers])) \
                for e in self.graph.es if s in e[rattr]]])
            
            src_curation_effort = sum([len(x) for x in \
                [set([(rl.pmid, e.index) for rl in e[rattr][s]]) \
                    for e in self.graph.es if s in e[rattr]]])
            ratio = len(src_refs) / float(src_edges)
            
            if s in data_formats.catnames:
                s = data_formats.catnames[s]
            
            result[s] = {
                'source_nodes': src_nodes,
                'source_nodes_percentage': src_nodes_pct,
                'specific_nodes': only_src_nodes,
                'specific_nodes_percentage': only_src_nodes_pct,
                'shared_nodes': shared_nodes,
                'source_edges': src_edges,
                'source_edges_percentage': src_edges_pct,
                'specific_edges': only_src_edges,
                'specific_edges_percentage': only_src_edges_pct,
                'shared_edges': shared_edges,
                'specific_refs': only_src_refs,
                'specific_refs_percentage': only_src_refs_pct,
                'source_refs': len(src_refs),
                'source_refs_percentage': src_refs_pct,
                'shared_refs': shared_refs,
                'source_curation_effort': src_curation_effort,
                'source_specific_curation_effort': src_only_curation_effort,
                'shared_curation_effort': shared_curation_effort,
                'refs_edges_ratio': ratio,
                'corrected_curation_effort': src_curation_effort * ratio
            }
        
        return result
    
    def table_latex(self, fname, header, data, sum_row = True, row_order = None,
        latex_hdr = True, caption = '', font = 'HelveticaNeueLTStd-LtCn', fontsize = 8,
        sum_label = 'Total', sum_cols = None, header_format = '%s', by_category = True):
        non_digit = re.compile(r'[^\d.-]+')
        row_order = sorted(data.keys(), key = lambda x: x.upper()) \
            if row_order is None else row_order
        _latex_tab = r'''%s
                \begin{tabularx}{\textwidth}{%s}
                \toprule
                    %s
                \midrule
                    %s
                %s\bottomrule
                \end{tabularx}
                %s
            '''
        _latex_hdr = r'''\documentclass[a4wide,%upt]{extarticle}
                \usepackage{fontspec}
                \usepackage{xunicode}
                \usepackage{polyglossia}
                \setdefaultlanguage{english}
                \usepackage{xltxtra}
                \usepackage{microtype}
                \usepackage[margin=5pt,landscape]{geometry}
                \usepackage{amsmath}
                \usepackage{amssymb}
                \usepackage[usenames,dvipsnames,svgnames,table]{xcolor}
                \usepackage{color}
                \usepackage{booktabs}
                \usepackage{tabularx}
                \setmainfont{%s}
                \definecolor{grey875}{gray}{0.125}
                \begin{document}
                \color{grey875}
                \thispagestyle{empty}
                \vfill
                \begin{table}[h]
            ''' % (fontsize, font) if latex_hdr else ''
        _latex_end = r'''
                \caption{%s}
                \end{table}
                \end{document}
            ''' % caption if latex_hdr else ''
        _hdr_row = ' & '.join([''] + [header_format%h[1].replace(r'%', r'\%') \
            for h in header]) + '\\\\'
        formatter = lambda x: locale.format('%.2f', x, grouping = True) \
            if type(x) is float \
            else locale.format('%d', x, grouping = True) \
            if type(x) is int \
            else x
        intfloat = lambda x: float(x) if '.' in x else int(x)
        _rows = ''
        for i, k in enumerate(row_order):
            
            row = ' & '.join([k[0] if type(k) is tuple else k] + \
                [formatter(data[k][h[0]]) for h in header]) + '\\\\'
            
            if type(k) is tuple and k[1] == 'subtitle':
                row = '\n'.join([
                    r'\midrule' if i > 0 else '',
                    row,
                    r'\midrule',
                    ''
                ])
            else:
                row = row + '\n'
            
            _rows += row
        
        sum_cols = xrange(len(header)) if sum_cols is None \
            else sum_cols
        _sum_row = ' & '.join([sum_label] + ['' if i not in sum_cols else formatter(sum([ \
            intfloat(list(filter(lambda x: len(x) > 0, [non_digit.sub('', str(v[h[0]])), '0']))[0]) \
            for v in data.values()])) \
            for i, h in enumerate(header)]) + '\\\\\n'
        _latex_tab = _latex_tab % (_latex_hdr, 'X' + 'r'*len(header), _hdr_row, _rows, 
            r'\midrule' + '\n%s'%_sum_row if sum_row else '', _latex_end)
        with open(fname, 'w') as f:
            f.write(_latex_tab)
    
    def curation_tab(self, fname = 'curation_stats.tex', by_category = True, 
                     use_cats = ['p', 'm', 'i', 'r'],
                     header_size = 'normalsize', **kwargs):
        
        if by_category and 'cat' not in self.graph.es.attributes():
            self.set_categories()
        
        cats = list(reduce(lambda e1, e2: e1 | e2['cat'], self.graph.es, set([]))) \
            if by_category else []
        
        cats = set(cats) & set(use_cats)
        use_cats = list(filter(lambda c: c in cats, use_cats))
        
        header = [
            ('source_nodes', 'Proteins'),
            ('source_nodes_percentage', r'Proteins [%]'),
            ('shared_nodes', 'Shared proteins'),
            ('specific_nodes', 'Specific proteins'),
            ('specific_nodes_percentage', r'Specific proteins [%]'),
            ('source_edges', 'Edges'),
            ('source_edges_percentage', r'Edges [%]'),
            ('shared_edges', 'Shared edges'),
            ('specific_edges', 'Specific edges'),
            ('specific_edges_percentage', r'Specific edges [%]'),
            ('source_refs', 'References'),
            ('source_refs_percentage', r'References [%]'),
            ('shared_refs', 'Shared references'),
            ('specific_refs', 'Specific references'),
            ('specific_refs_percentage', r'Specific references [%]'),
            ('source_curation_effort', 'Curation effort'),
            ('shared_curation_effort', 'Shared curation effort'),
            ('source_specific_curation_effort', 'Specific curation effort'),
            ('refs_edges_ratio', 'References-edges ratio'),
            ('corrected_curation_effort', 'Corrected curation effort')
        ]
        header_format = (r'\rotatebox{90}{\%s ' % header_size) + '%s}'
        
        cs = self.curation_stats(by_category = by_category)
        
        for name, data in iteritems(cs):
            if data['specific_refs'] == 0 and data['shared_refs'] == 0:
                data['source_refs'] = 'N/A'
                data['specific_refs'] = 'N/A'
                data['shared_refs'] = 'N/A'
                data['source_refs_percentage'] = 'N/A'
                data['specific_refs_percentage'] = 'N/A'
                data['source_curation_effort'] = 'N/A'
                data['shared_curation_effort'] = 'N/A'
                data['source_specific_curation_effort'] = 'N/A'
                data['refs_edges_ratio'] = 'N/A'
                data['corrected_curation_effort'] = 'N/A'
        
        for key in use_cats:
            if key in data_formats.catnames:
                name = data_formats.catnames[key]
                if by_category:
                    cs[(name, 'subtitle')] = cs[name]
                else:
                    if name in cs:
                        del cs[name]
        
        row_order = []
        
        if by_category:
            for cat in use_cats:
                row_order.append((data_formats.catnames[cat], 'subtitle'))
                row_order.extend(
                    sorted(
                        filter(
                            lambda name:
                                name in data_formats.categories and \
                                    data_formats.categories[name] == cat,
                            cs.keys()
                        )
                    )
                )
        
        self.table_latex(fname, header, cs, header_format = header_format,
            row_order = row_order if by_category else None, by_category = by_category,
            sum_row = False, **kwargs)
    
    def load_omnipath(self, threshold = 1):
        self.load_resources(data_formats.omnipath)
        self.third_source_directions()
        self.remove_htp(threshold = threshold, keep_directed = True)
    
    def remove_htp(self, threshold = 50, keep_directed = False):
        self.htp_stats()
        vcount_before = self.graph.vcount()
        ecount_before = self.graph.ecount()
        htedgs = [e.index for e in self.graph.es if \
            len(set([r.pmid for r in e['references']]) - self.htp[threshold]['htrefs']) == 0 \
                and (not keep_directed or not e['dirs'].is_directed())]
        self.graph.delete_edges(htedgs)
        zerodeg = [v.index for v in self.graph.vs if v.degree() == 0]
        self.graph.delete_vertices(zerodeg)
        self.update_vname()
        sys.stdout.write('\t:: Interactions with only high-throughput references '\
            'have been removed.\n\t   %u interactions removed.\n\t   Number of edges '\
            'decreased from %u to %u, number of vertices from %u to %u.\n' % \
            (len(htedgs), ecount_before, self.graph.ecount(), 
             vcount_before, self.graph.vcount()))
        sys.stdout.flush()
    
    def remove_undirected(self, min_refs = None):
        vcount_before = self.graph.vcount()
        ecount_before = self.graph.ecount()
        udedgs = [e.index for e in self.graph.es if \
                not e['dirs'].is_directed() and (
                    min_refs is None or \
                    len(set([r.pmid for r in e['references']])) < min_refs
                )]
        self.graph.delete_edges(udedgs)
        zerodeg = [v.index for v in self.graph.vs if v.degree() == 0]
        self.graph.delete_vertices(zerodeg)
        self.update_vname()
        sys.stdout.write('\t:: Undirected interactions %s '\
            'have been removed.\n\t   %u interactions removed.\n\t   Number of edges '\
            'decreased from %u to %u, number of vertices from %u to %u.\n' % \
            ('' if min_refs is None else 'with less than %u references' % min_refs,
            len(udedgs), ecount_before, self.graph.ecount(),
             vcount_before, self.graph.vcount()))
        sys.stdout.flush()
    
    def numof_directed_edges(self):
        return len(list(filter(lambda e: e['dirs'].is_directed(), self.graph.es)))
    
    def numof_undirected_edges(self):
        return len(list(filter(lambda e: not e['dirs'].is_directed(), self.graph.es)))
    
    def htp_stats(self):
        htdata = {}
        refc = Counter(common.flatList((r.pmid for r in e['references']) for e in self.graph.es))
        for htlim in reversed(xrange(1, 201)):
            htrefs = set([i[0] for i in refc.most_common() if i[1] > htlim])
            htedgs = [e.index for e in self.graph.es if \
                len(set([r.pmid for r in e['references']]) - htrefs) == 0]
            htsrcs = common.uniqList(common.flatList([self.graph.es[e]['sources'] for e in htedgs]))
            htdata[htlim] = {
                'rnum': len(htrefs),
                'enum': len(htedgs),
                'snum': len(htsrcs),
                'htrefs': htrefs
            }
        self.htp = htdata
    
    def third_source_directions(self, graph = None):
        '''
        This method calls a series of methods to get
        additional direction & effect information
        from sources having no literature curated references,
        but giving sufficient evidence about the directionality
        for interactions already supported by literature 
        evidences from other sources.
        '''
        self.string_effects(graph = graph)
        self.kegg_directions(graph = graph)
        self.laudanna_effects(graph = graph)
        self.laudanna_directions(graph = graph)
        self.wang_effects(graph = graph)
        self.acsn_effects(graph = graph)
        self.phosphosite_directions(graph = graph)
        self.phosphopoint_directions(graph = graph)
        self.phosphonetworks_directions(graph = graph)
        self.mimp_directions(graph = graph)
    
    def kegg_directions(self, graph = None):
        keggd = dataio.get_kegg()
        self.process_directions(keggd, 'KEGG', stimulation = 'activation', 
            inhibition = 'inhibition', graph = graph)
    
    def phosphosite_directions(self, graph = None):
        psite = dataio.phosphosite_directions()
        self.process_directions(psite, 'PhosphoSite_dir', dirs_only = True, 
            id_type = 'uniprot', graph = graph)
    
    def phosphopoint_directions(self, graph = None):
        ppoint = dataio.phosphopoint_directions()
        self.process_directions(ppoint, 'PhosphoPoint', dirs_only = True, 
            id_type = 'genesymbol', graph = graph)
    
    def phosphonetworks_directions(self, graph = None):
        pnet = dataio.pnetworks_interactions()
        self.process_directions(pnet, 'PhosphoNetworks', dirs_only = True, 
            id_type = 'genesymbol', graph = graph)
    
    def mimp_directions(self, graph = None):
        mimp = dataio.mimp_interactions()
        self.process_directions(mimp, 'MIMP', dirs_only = True, 
            id_type = 'genesymbol', graph = graph)
    
    def laudanna_directions(self, graph = None):
        laud = dataio.get_laudanna_directions()
        self.process_directions(laud, 'Laudanna_sigflow', dirs_only = True, 
            id_type = 'genesymbol', graph = graph)
    
    def laudanna_effects(self, graph = None):
        laud = dataio.get_laudanna_effects()
        self.process_directions(laud, 'Laudanna_effects', stimulation = 'activation', 
            inhibition = 'inhibition', directed = 'docking', 
            id_type = 'genesymbol', graph = graph)
    
    def string_effects(self, graph = None):
        string = dataio.get_string_effects()
        self.process_directions(string, 'STRING', stimulation = '+',
            inhibition = '-', directed = '*',
            id_type = 'ensp', graph = graph)
    
    def acsn_effects(self, graph = None):
        acsnd = dataio.get_acsn_effects()
        self.process_directions(acsnd, 'ACSN', stimulation = '+',
            inhibition = '-', directed = '*',
            id_type = 'genesymbol', graph = graph)
    
    def wang_effects(self, graph = None):
        wangd = dataio.get_wang_effects()
        self.process_directions(wangd, 'Wang', stimulation = '+', 
            inhibition = '-', directed = '0', 
            id_type = 'genesymbol', graph = graph)
    
    def process_directions(self, dirs, name, directed = None,
        stimulation = None, inhibition = None, graph = None,
        id_type = None, dirs_only = False):
        g = graph if graph is not None else self.graph
        nodes = set(g.vs['name'])
        sourcedirs = 0
        newdirs = 0
        newsigns = 0
        for k in dirs:
            if dirs_only or k[2] == stimulation or k[2] == inhibition or k[2] == directed:
                src = [k[0]] if id_type is None \
                    else self.mapper.map_name(k[0], id_type, 'uniprot')
                tgt = [k[1]] if id_type is None \
                    else self.mapper.map_name(k[1], id_type, 'uniprot')
                for s in src:
                    for t in tgt:
                        if s in nodes and t in nodes:
                            v1 = g.vs.find(name = s)
                            v2 = g.vs.find(name = t)
                            e = g.get_eid(v1, v2, error = False)
                            if e != -1:
                                sourcedirs +=1
                                if not g.es[e]['dirs'].get_dir((s, t)):
                                    newdirs += 1
                                if dirs_only or k[2] == directed:
                                    g.es[e]['dirs'].set_dir((s, t), name)
                                elif k[2] == stimulation:
                                    if not g.es[e]['dirs'].get_sign((s, t), 'positive'):
                                        newsigns += 1
                                    g.es[e]['dirs'].set_sign((s, t), 'positive', name)
                                elif k[2] == inhibition:
                                    if not g.es[e]['dirs'].get_sign((s, t), 'negative'):
                                        newsigns += 1
                                    g.es[e]['dirs'].set_sign((s, t), 'negative', name)
        sys.stdout.write('\t:: Directions and signs set for %u edges based on %s,'\
            ' %u new directions, %u new signs.\n' % (sourcedirs, name, newdirs, newsigns))
    
    def curation_effort(self, sum_by_source = False):
        '''
        Returns the total number of reference-interactions pairs.
        
        @sum_by_source : bool
            If True, counts the refrence-interaction pairs by
            sources, and returns the sum of these values.
        '''
        if sum_by_source:
            return sum(
                map(
                    sum,
                        map(
                            lambda rs:
                                map(
                                    len,
                                    rs.values()
                                ),
                            self.graph.es['refs_by_source']
                        )
                    )
                )
        else:
            return sum(
                map(
                    len,
                    self.graph.es['references']
                )
            )
    
    def export_dot(self, nodes = None, edges = None, directed = True, 
        labels = 'genesymbol', edges_filter = lambda e: True, nodes_filter = lambda v: True,
        edge_sources = None, dir_sources = None, graph = None,
        return_object = False, save_dot = None, save_graphics = None, 
        prog = 'neato', format = None, hide = False, 
        font = None, auto_edges = False, hide_nodes = [], 
        defaults = {}, **kwargs):
        '''
        Builds a pygraphviz.AGraph() object with filtering the edges 
        and vertices along arbitrary criteria.
        Returns the Agraph object if requesred, or exports the dot
        file, or saves the graphics.
        
        @nodes : list
        List of vertex ids to be included.
        @edges : list
        List of edge ids to be included.
        @directed : bool
        Create a directed or undirected graph.
        @labels : str
        Name type to be used as id/label in the dot format.
        @edges_filter : function
        Function to filter edges, accepting igraph.Edge as argument.
        @nodes_filter : function
        Function to filter vertices, accepting igraph.Vertex as argument.
        @edge_sources : list
        Sources to be included.
        @dir_sources : list
        Direction and effect sources to be included.
        @graph : igraph.Graph
        The graph object to export.
        @return_object : bool
        Whether to return the pygraphviz.AGraph object.
        @save_dot : str
        Filename to export the dot file to.
        @save_graphics : str
        Filename to export the graphics, the extension defines the format.
        @prog : str
        The graphviz layout algorithm to use.
        @format : str
        The graphics format passed to pygraphviz.AGrapg().draw().
        @hide : bool
        Hide filtered edges instead of omit them.
        @hide nodes : list
        Nodes to hide. List of vertex ids.
        @auto_edges : str
        Automatic, built-in style for edges. 
        'DIRECTIONS' or 'RESOURCE_CATEGORIES' are supported.
        @font : str
        Font to use for labels. 
        For using more than one fonts refer to graphviz attributes with constant values 
        or define callbacks or mapping dictionaries.
        @defaults : dict
        Default values for graphviz attributes, labeled with the entity, e.g.
        `{'edge_penwidth': 0.2}`.
        @**kwargs : constant, callable or dict
        Graphviz attributes, labeled by the target entity. E.g. `edge_penwidth`,
        'vertex_shape` or `graph_label`. 
        If the value is constant, this value will be used.
        If the value is dict, and has `_name` as key, for every instance of the
        given entity, the value of the attribute defined by `_name` will be looked
        up in the dict, and the corresponding value will be given to the graphviz
        attribute. If the key `_name` is missing from the dict, igraph vertex and
        edge indices will be looked up among the keys.
        If the value is callable, it will be called with the current instance of
        the entity and the returned value will be used for the graphviz attribute.
        E.g. `edge_arrowhead(edge)` or `vertex_fillcolor(vertex)`
        Example:
            import pypath
            from pypath import data_formats
            net = pypath.PyPath()
            net.init_network(pfile = 'cache/default.pickle')
            #net.init_network({'arn': data_formats.omnipath['arn']})
            tgf = [v.index for v in net.graph.vs if 'TGF' in v['slk_pathways']]
            dot = net.export_dot(nodes = tgf, save_graphics = 'tgf_slk.pdf', prog = 'dot',
                main_title = 'TGF-beta pathway', return_object = True,
                label_font = 'HelveticaNeueLTStd Med Cn', 
                edge_sources = ['SignaLink3'], 
                dir_sources = ['SignaLink3'], hide = True)
        '''
        _attrs = {}
        _custom_attrs = kwargs
        graph_attrs, vertex_attrs, edge_attrs = dataio.get_graphviz_attrs()
        _defaults = {
            'edge_color': {
                'undirected': {
                    'unknown': '#CCCCCC'
                },
                'directed': {
                    'stimulation': '#00CC00',
                    'inhibition': '#CC0000',
                    'unknown': '#0000CC'
                },
                'pathway': '#7AA0A177',
                'ptm': '#C6909C77',
                'reaction': '#C5B26E77',
                'interaction': '#9D8BB777'
            },
            'edge_arrowhead': {
                'undirected': {
                    'unknown': 'none'
                },
                'directed': {
                    'stimulation': 'normal',
                    'inhibition': 'tee',
                    'unknown': 'diamond'
                }
            },
            'vertex_fillcolor': '#AAAAAA',
            'vertex_fontcolor': '#000000'
        }
        #
        for k, v in iteritems(defaults):
            _defaults[k] = v
        #
        g = self.graph if graph is None else graph
        labels = 'name' if labels == 'uniprot' else 'label'
        edge_sources = edge_sources if edge_sources is None else set(edge_sources)
        dir_sources = dir_sources if dir_sources is None else set(dir_sources)
        labels = 'name' if labels == 'uniprot' else labels
        labels = 'label' if labels == 'genesymbol' else labels
        if labels == 'label' and g.vs['label'] == g.vs['name']:
            self.genesymbol_labels()
        if nodes is None and edges is not None:
            nodes = [n for e in g.es for n in (e.source, e.target) if e.index in edges]
        elif nodes is not None and edges is None:
            edges = [e.index for e in g.es if e.source in nodes and e.target in nodes]
        else:
            edges = xrange(g.ecount())
            nodes = xrange(g.vcount())
        dNodes = dict((v.index, v[labels]) for v in g.vs \
            if nodes is None or v.index in nodes)
        hide_nodes = set(hide_nodes)
        if font is not None:
            _custom_attrs['graph_fontname'] = font
            _custom_attrs['vertex_fontname'] = font
            _custom_attrs['edge_fontname'] = font
        # attribute callbacks
        for entity in ['graph', 'vertex', 'edge']:
            callbacks_dict = '%s_callbacks' % entity
            _attrs[callbacks_dict] = {}
            callbacks = _attrs[callbacks_dict]
            if entity == 'edge':
                if (auto_edges == 'RESOURCE_CATEGORIES' or \
                    auto_edges == 'DIRECTIONS') \
                    and 'edge_color' not in _custom_attrs \
                    and 'edge_arrowhead' not in _custom_attrs:
                    callbacks['color'] = \
                        AttrHelper(auto_edges, 'edge_color', _defaults)
                    if auto_edges == 'DIRECTIONS':
                        callbacks['arrowhead'] = \
                            AttrHelper(auto_edges, 'edge_arrowhead', _defaults)
                    else:
                        callbacks['arrowhead'] = \
                            AttrHelper('none', 'edge_arrowhead', _defaults)
            for attr in locals()['%s_attrs'%entity].keys():
                callback_name = '%s_%s' % (entity, attr)
                if callback_name in _custom_attrs:
                    callback_value = _custom_attrs[callback_name]
                    if type(callback_value) is dict:
                        if '_name' not in callback_value:
                            callback_value['_name'] = 'index'
                    callbacks[attr] = AttrHelper(value = callback_value, 
                        name = attr, defaults = _defaults)
        # graph
        dot = graphviz.AGraph(directed = directed)
        attrs = {}
        for gattr, fun in iteritems(_attrs['graph_callbacks']):
            attrs[gattr] = fun(g)
        attrs = common.cleanDict(attrs)
        for gattr, value in iteritems(attrs):
            dot.graph_attr[gattr] = value
        # vertices
        for vid, node in iteritems(dNodes):
            attrs = {}
            for vattr, fun in iteritems(_attrs['vertex_callbacks']):
                attrs[vattr] = fun(g.vs[vid])
            if vid in hide_nodes:
                attrs['style'] = 'invis'
            attrs = common.cleanDict(attrs)
            dot.add_node(node, **attrs)
        # edges
        edge_callbacks = _attrs['edge_callbacks']
        for eid in edges:
            s = g.es[eid].source
            t = g.es[eid].target
            sn = g.vs[s]['name']
            tn = g.vs[t]['name']
            sl = g.vs[s][labels]
            tl = g.vs[t][labels]
            d = g.es[eid]['dirs']
            # this edge should be visible at all?
            evis = edges_filter(g.es[eid]) and \
                nodes_filter(g.vs[s]) and nodes_filter(g.vs[t]) and \
                (edge_sources is None or \
                    len(g.es[eid]['sources'] & edge_sources) > 0) and \
                g.es[eid].source not in hide_nodes and g.es[eid].target not in hide_nodes
            if evis or hide:
                drawn_directed = False
                thisSign = 'unknown'
                thisDir = 'undirected'
                thisSources = set([])
                if directed:
                    if d.get_dir((sn, tn)):
                        sdir = d.get_dir((sn, tn), sources = True)
                        thisDir = (sn, tn)
                        vis = (dir_sources is None or len(sdir & dir_sources) > 0) and evis
                        if vis or hide:
                            attrs = {}
                            sign = d.get_sign((sn, tn))
                            ssign = d.get_sign((sn, tn), sources = True)
                            drawn_directed = True
                            if vis and (sign[0] and dir_sources is None or \
                                dir_sources is not None and \
                                len(ssign[0] & dir_sources) > 0):
                                thisSign = 'stimulation'
                                thisSources = ssign[0] if dir_sources is None else \
                                    ssign[0] & dir_sources
                                for eattr, fun in iteritems(edge_callbacks):
                                    attrs[eattr] = fun(g.es[eid], 
                                        thisDir, thisSign, thisDirSources, g.es[eid]['sources'])
                            elif vis and (sign[1] and dir_sources is None or \
                                dir_sources is not None and \
                                len(ssign[1] & dir_sources) > 0):
                                thisSign = 'inhibition'
                                thisSoures = ssign[1] if dir_sources is None else \
                                    ssign[1] & dir_sources
                                for eattr, fun in iteritems(edge_callbacks):
                                    attrs[eattr] = fun(g.es[eid], 
                                        thisDir, thisSign, thisSources, g.es[eid]['sources'])
                            elif vis:
                                thisSign = 'unknown'
                                thisSources = sdir
                                for eattr, fun in iteritems(edge_callbacks):
                                    attrs[eattr] = fun(g.es[eid], 
                                        thisDir, thisSign, thisSources, g.es[eid]['sources'])
                            else:
                                attrs['style'] = 'invis'
                                drawn_directed = False
                            attrs = common.cleanDict(attrs)
                            dot.add_edge(sl, tl, **attrs)
                    if d.get_dir((tn, sn)):
                        sdir = d.get_dir((tn, sn), sources = True)
                        thisDir = (tn, sn)
                        vis = (dir_sources is None or len(sdir & dir_sources) > 0) and evis
                        if vis or hide:
                            attrs = {}
                            sign = d.get_sign((tn, sn))
                            ssign = d.get_sign((tn, sn), sources = True)
                            drawn_directed = True
                            if vis and (sign[0] and dir_sources is None or \
                                dir_sources is not None and \
                                len(ssign[0] & dir_sources) > 0):
                                thisSign = 'stimulation'
                                thisSources = ssign[0] if dir_sources is None else \
                                    ssign[0] & dir_sources
                                for eattr, fun in iteritems(edge_callbacks):
                                    attrs[eattr] = fun(g.es[eid],
                                        thisDir, thisSign, thisSources, (g.es[eid]['sources']))
                            elif vis and (sign[1] and dir_sources is None or \
                                dir_sources is not None and \
                                len(ssign[1] & dir_sources) > 0):
                                thisSign = 'inhibition'
                                thisSources = ssign[1] if dir_sources is None else \
                                    ssign[1] & dir_sources
                                for eattr, fun in iteritems(edge_callbacks):
                                    attrs[eattr] = fun(g.es[eid],
                                        thisDir, thisSign, thisSources, g.es[eid]['sources'])
                            elif vis:
                                thisSign = 'unknown'
                                thisSources = sdir
                                for eattr, fun in iteritems(edge_callbacks):
                                    attrs[eattr] = fun(g.es[eid],
                                        thisDir, thisSign, thisSources, g.es[eid]['sources'])
                            else:
                                attrs['style'] = 'invis'
                                drawn_directed = False
                            attrs = common.cleanDict(attrs)
                            dot.add_edge(tl, sl, **attrs)
                if not directed or d.get_dir('undirected'):
                    attrs = {}
                    thisDir = 'undirected'
                    thisSign = 'unknown'
                    thisSources = d.get_dir('undirected', sources = True)
                    for eattr, fun in iteritems(edge_callbacks):
                        attrs[eattr] = fun(g.es[eid], thisDir, thisSign, 
                            thisSources, g.es[eid]['sources'])
                    if (not evis and hide) or drawn_directed:
                        attrs['style'] = 'invis'
                    if dot.has_neighbor(sl, tl):
                        if dot.get_edge(sl, tl).attr['style'] is not None and \
                            'invis' in dot.get_edge(sl, tl).attr['style']:
                            dot.delete_edge(sl, tl)
                    if not dot.has_neighbor(sl, tl):
                        attrs = common.cleanDict(attrs)
                        dot.add_edge((sl, tl), **attrs)
        if type(save_dot) in set([str, unicode]):
            with open(save_dot, 'w') as f:
                f.write(dot.to_string())
        if type(save_graphics) in set([str, unicode]):
            dot.draw(save_graphics, format = format, prog = prog)
        if return_object:
            return dot
    
    def consistency(self):
        con = dict(map(lambda c: (c, dict(
                map(lambda t: (t, dict(
                    ((s1, s2), dict(
                        map(lambda a: (a, set([]) if t.endswith('edges') else 0), \
                            ['total', 'minor', 'major']))) \
                        for s1 in net.sources for s2 in net.sources)), \
                ['directions', 'directions_edges', 'signs', 'signs_edges']))), \
            ['consistency', 'inconsistency']))
        # inconsistency #
        prg = progress.Progress(len(self.sources)**2, 'Counting inconsistency', 1)
        for s1 in self.sources:
            for s2 in self.sources:
                prg.step()
                s12 = set([s1, s2])
                for e in self.graph.es:
                    d = e['dirs']
                    if s1 in d.sources_straight() and \
                        s1 not in d.sources_reverse() and \
                        s2 in d.sources_reverse() and \
                        s2 not in d.sources_straight() or \
                        s2 in d.sources_straight() and \
                        s2 not in d.sources_reverse() and \
                        s1 in d.sources_reverse() and \
                        s1 not in d.sources_straight():
                        con['inconsistency']['directions'][(s1, s2)]['total'] += 1
                        con['inconsistency']['directions_edges'][(s1, s2)]['total'].add(e.index)
                        if s1 in d.sources_straight() and s1 != s2:
                            if len(d.sources_straight()) > len(d.sources_reverse()):
                                con['inconsistency']['directions'][(s1, s2)]['major'] += 1
                                con['inconsistency']['directions'][(s2, s1)]['minor'] += 1
                                con['inconsistency']['directions_edges'][(s1, s2)]['major'].add(e.index)
                                con['inconsistency']['directions_edges'][(s2, s1)]['minor'].add(e.index)
                            elif len(d.sources_straight()) < len(d.sources_reverse()):
                                con['inconsistency']['directions'][(s1, s2)]['minor'] += 1
                                con['inconsistency']['directions'][(s2, s1)]['major'] += 1
                                con['inconsistency']['directions_edges'][(s1, s2)]['minor'].add(e.index)
                                con['inconsistency']['directions_edges'][(s2, s1)]['major'].add(e.index)
                            elif len(d.sources_straight()) == 1 and \
                                len(d.sources_reverse()) == 1:
                                con['inconsistency']['directions'][(s1, s2)]['minor'] += 1
                                con['inconsistency']['directions'][(s2, s1)]['minor'] += 1
                                con['inconsistency']['directions_edges'][(s1, s2)]['minor'].add(e.index)
                                con['inconsistency']['directions_edges'][(s2, s1)]['minor'].add(e.index)
                    if s1 in d.positive_sources_straight() and \
                        s2 in d.negative_sources_straight() or \
                        s1 in d.negative_sources_straight() and \
                        s2 in d.positive_sources_straight():
                        con['inconsistency']['signs'][(s1, s2)]['total'] += 1
                        con['inconsistency']['signs_edges'][(s1, s2)]['total'].add(e.index)
                        if s1 in d.positive_sources_straight():
                            if len(d.positive_sources_straight()) > \
                                len(d.negative_sources_straight()):
                                con['inconsistency']['signs'][(s1, s2)]['major'] += 1
                                con['inconsistency']['signs'][(s2, s1)]['minor'] += 1
                                con['inconsistency']['signs_edges'][(s1, s2)]['major'].add(e.index)
                                con['inconsistency']['signs_edges'][(s2, s1)]['minor'].add(e.index)
                            elif len(d.positive_sources_straight()) < \
                                len(d.negative_sources_straight()):
                                con['inconsistency']['signs'][(s1, s2)]['minor'] += 1
                                con['inconsistency']['signs'][(s2, s1)]['major'] += 1
                                con['inconsistency']['signs_edges'][(s1, s2)]['minor'].add(e.index)
                                con['inconsistency']['signs_edges'][(s2, s1)]['major'].add(e.index)
                            elif len(d.positive_sources_straight()) == 1 and \
                                len(d.negative_sources_straight()) == 1:
                                con['inconsistency']['signs'][(s1, s2)]['minor'] += 1
                                con['inconsistency']['signs'][(s2, s1)]['minor'] += 1
                                con['inconsistency']['signs_edges'][(s1, s2)]['minor'].add(e.index)
                                con['inconsistency']['signs_edges'][(s2, s1)]['minor'].add(e.index)
                    if s1 in d.positive_sources_reverse() and \
                        s2 in d.negative_sources_reverse() or \
                        s1 in d.negative_sources_reverse() and \
                        s2 in d.positive_sources_reverse():
                        con['inconsistency']['signs'][(s1, s2)]['total'] += 1
                        con['inconsistency']['signs_edges'][(s1, s2)]['total'].add(e.index)
                        if s1 in d.positive_sources_reverse():
                            if len(d.positive_sources_reverse()) > \
                                len(d.negative_sources_reverse()):
                                con['inconsistency']['signs'][(s1, s2)]['major'] += 1
                                con['inconsistency']['signs'][(s2, s1)]['minor'] += 1
                                con['inconsistency']['signs_edges'][(s1, s2)]['major'].add(e.index)
                                con['inconsistency']['signs_edges'][(s2, s1)]['minor'].add(e.index)
                            elif len(d.positive_sources_reverse()) < \
                                len(d.negative_sources_reverse()):
                                con['inconsistency']['signs'][(s1, s2)]['minor'] += 1
                                con['inconsistency']['signs'][(s2, s1)]['major'] += 1
                                con['inconsistency']['signs_edges'][(s1, s2)]['minor'].add(e.index)
                                con['inconsistency']['signs_edges'][(s2, s1)]['major'].add(e.index)
                            elif len(d.positive_sources_reverse()) == 1 and \
                                len(d.negative_sources_reverse()) == 1:
                                con['inconsistency']['signs'][(s1, s2)]['minor'] += 1
                                con['inconsistency']['signs'][(s2, s1)]['minor'] += 1
                                con['inconsistency']['signs_edges'][(s1, s2)]['minor'].add(e.index)
                                con['inconsistency']['signs_edges'][(s2, s1)]['minor'].add(e.index)
        prg.terminate()
        # consistency #
        prg = progress.Progress(len(self.sources)**2, 'Counting consistency', 1)
        for s1 in self.sources:
            for s2 in self.sources:
                prg.step()
                s12 = set([s1, s2])
                for e in self.graph.es:
                    d = e['dirs']
                    if s12 <= d.sources_straight():
                        con['consistency']['signs']['directions'][(s1, s2)]['total'] += 1
                        con['consistency']['signs']['directions_edges'][(s1, s2)]['total'].add(e.index)
                        if len(d.sources_straight()) > len(d.sources_reverse()) and \
                            len(s12 & d.sources_reverse()) == 0:
                            con['consistency']['signs']['directions'][(s1, s2)]['major'] += 1
                            con['consistency']['signs']['directions_edges'][(s1, s2)]['major'].add(e.index)
                        elif len(d.sources_straight()) < len(d.sources_reverse()) and \
                            len(s12 & d.sources_reverse()) == 0:
                            con['consistency']['signs']['directions'][(s1, s2)]['minor'] += 1
                            con['consistency']['signs']['directions_edges'][(s1, s2)]['minor'].add(e.index)
                    if s12 <= d.sources_reverse():
                        con['consistency']['signs']['directions'][(s1, s2)]['total'] += 1
                        con['consistency']['signs']['directions_edges'][(s1, s2)]['total'].add(e.index)
                        if len(d.sources_reverse()) > len(d.sources_straight()) and \
                            len(s12 & d.sources_straight()) == 0:
                            con['consistency']['signs']['directions'][(s1, s2)]['major'] += 1
                            con['consistency']['signs']['directions_edges'][(s1, s2)]['major'].add(e.index)
                        elif len(d.sources_reverse()) < len(d.sources_straight()) and \
                            len(s12 & d.sources_straight()) == 0:
                            con['consistency']['signs']['directions'][(s1, s2)]['minor'] += 1
                            con['consistency']['signs']['directions_edges'][(s1, s2)]['minor'].add(e.index)
                    if s12 <= d.positive_sources_straight():
                        con['consistency']['signs'][(s1, s2)]['total'] += 1
                        con['consistency']['signs']['signs_edges'][(s1, s2)]['total'].add(e.index)
                        if len(d.positive_sources_straight()) > len(d.positive_sources_reverse()) and \
                            len(s12 & d.positive_sources_reverse()) == 0:
                            con['consistency']['signs'][(s1, s2)]['major'] += 1
                            con['consistency']['signs']['signs_edges'][(s1, s2)]['major'].add(e.index)
                        elif len(d.positive_sources_straight()) < len(d.positive_sources_reverse()) and \
                            len(s12 & d.positive_sources_reverse()) == 0:
                            con['consistency']['signs'][(s1, s2)]['minor'] += 1
                            con['consistency']['signs']['signs_edges'][(s1, s2)]['minor'].add(e.index)
                    if s12 <= d.negative_sources_straight():
                        con['consistency']['signs'][(s1, s2)]['total'] += 1
                        con['consistency']['signs']['signs_edges'][(s1, s2)]['total'].add(e.index)
                        if len(d.negative_sources_straight()) > len(d.negative_sources_reverse()) and \
                            len(s12 & d.negative_sources_reverse()) == 0:
                            con['consistency']['signs'][(s1, s2)]['major'] += 1
                            con['consistency']['signs']['signs_edges'][(s1, s2)]['major'].add(e.index)
                        elif len(d.negative_sources_straight()) < len(d.negative_sources_reverse()) and \
                            len(s12 & d.negative_sources_reverse()) == 0:
                            con['consistency']['signs'][(s1, s2)]['minor'] += 1
                            con['consistency']['signs']['signs_edges'][(s1, s2)]['minor'].add(e.index)
                    if s12 <= d.positive_sources_reverse():
                        con['consistency']['signs'][(s1, s2)]['total'] += 1
                        con['consistency']['signs']['signs_edges'][(s1, s2)]['total'].add(e.index)
                        if len(d.positive_sources_reverse()) > len(d.positive_sources_straight()) and \
                            len(s12 & d.positive_sources_straight()) == 0:
                            con['consistency']['signs'][(s1, s2)]['major'] += 1
                            con['consistency']['signs']['signs_edges'][(s1, s2)]['major'].add(e.index)
                        elif len(d.positive_sources_reverse()) < len(d.positive_sources_straight()) and \
                            len(s12 & d.positive_sources_straight()) == 0:
                            con['consistency']['signs'][(s1, s2)]['minor'] += 1
                            con['consistency']['signs']['signs_edges'][(s1, s2)]['minor'].add(e.index)
                    if s12 <= d.negative_sources_reverse():
                        con['consistency']['signs'][(s1, s2)]['total'] += 1
                        con['consistency']['signs']['signs_edges'][(s1, s2)]['total'].add(e.index)
                        if len(d.negative_sources_reverse()) > len(d.negative_sources_straight()) and \
                            len(s12 & d.negative_sources_straight()) == 0:
                            con['consistency']['signs'][(s1, s2)]['major'] += 1
                            con['consistency']['signs']['signs_edges'][(s1, s2)]['major'].add(e.index)
                        elif len(d.negative_sources_reverse()) < len(d.negative_sources_straight()) and \
                            len(s12 & d.negative_sources_straight()) == 0:
                            con['consistency']['signs'][(s1, s2)]['minor'] += 1
                            con['consistency']['signs']['signs_edges'][(s1, s2)]['minor'].add(e.index)
        prg.terminate()
        return con
    
    def export_edgelist(self, fname, graph = None, names = ['name'],
        edge_attributes = [], sep = '\t'):
        """
            Write edge list to text file with attributes
            
            @param fname: the name of the file or a stream to read from.
            @param graph: the igraph object containing the network
            @param names: list with the vertex attribute names to be printed
                for source and target vertices
            @param edge_attributes: list with the edge attribute names
                to be printed
            @param sep: string used to separate columns
            """
        # from Luis Tobalina
        graph = self.graph if graph is None else graph
        # check that input 'names' and 'edge_attributes' exist
        names = \
            filter(
                lambda name:
                    name in graph.vs.attribute_names(),
                names
            )
        edge_attributes = \
            filter(
                lambda attr:
                    attr in graph.es.attribute_names(),
                edge_attributes
            )
        # write file
        with open(fname, 'wt') as fid:
            # write header
            for iname in names:
                fid.write('%s%s' % (sep.join(['{}_{}'.format(st, iname)
                    for st in ('source', 'target')]), sep))
            fid.write('%s\n' % sep.join(eattr for eattr in edge_attributes))
            # write data
            for edge in graph.es:
                for iname in names:
                    fid.write('%s%s' % (sep.join([graph.vs[v][iname] \
                        for v in edge.tuple]), sep))
                fid.write('%s\n' % sep.join(['{}'.format(edge[eattr])
                    for eattr in edge_attributes]))
    
    def in_complex(self, csources = ['corum']):
        self.graph.es['in_complex'] = \
            [sum([len(set(self.graph.vs[e.source]['complexes'][cs].keys()) & \
                set(self.graph.vs[e.target]['complexes'][cs].keys())) for cs in csources]) > 0 \
                for e in self.graph.es]
    
    def reload(self):
        modname = self.__class__.__module__
        mod = __import__(modname, fromlist = [modname.split('.')[0]])
        imp.reload(mod)
        new = getattr(mod, self.__class__.__name__)
        setattr(self, '__class__', new)
    
    def _disclaimer(self):
        sys.stdout.write(self.disclaimer)
    
    def licence(self):
        self._disclaimer()
