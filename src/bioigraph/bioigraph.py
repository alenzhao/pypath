#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#
#  This file is part of the `bioigraph` python module
#
#  Copyright (c) 2014-2015 - EMBL-EBI
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

# external modules:
import os
import sys
import re
import math
import igraph
import cairo
import codecs
import random
import textwrap
import copy
import json
import pandas
from itertools import chain
import cPickle as pickle

# from this module:
import logn
import data_formats
import mapping
import descriptions
import chembl
import gdsc
import mysql
import dataio
import intera
import drawing as bdrawing
from ig_drawing import *
from common import *
from colorgen import *
from gr_plot import *
from progress import *
from data_formats import *

__all__ = ['PlotParam', 'BioGraph', 'Direction']

class PlotParam(object):
    
    def __init__(
        self, graph = None, filename = None, graphix_dir = "pdf",
        graphix_format = "pdf", name = None,
        layout = "fruchterman_reingold", vertex_label = None, vertex_size = 2,
        vertex_color = "#87AADEAA", vertex_label_color = "#000033CC",
        vertex_label_size = "degree_label_size", edge_width = 0.02, 
        edge_color = "#CCCCCCAA", vertex_frame_color = "#FFFFFF00", 
        vertex_frame_width = 0, vertex_fill_alpha = "AA", 
        vertex_label_font = "sans-serif", palette = "rainbow", 
        bbox=igraph.drawing.utils.BoundingBox(10, 10, 1260, 1260),
        dimensions = (1280, 1280), grouping = None, **kwargs):
        for key, val in locals().iteritems():
            setattr(self, key, val)

class Direction(object):
    
    def __init__(self,nameA,nameB):
        self.nodes = [nameA,nameB]
        self.nodes.sort()
        self.straight = (self.nodes[0],self.nodes[1])
        self.reverse = (self.nodes[1],self.nodes[0])
        self.dirs = {
            self.straight: False,
            self.reverse: False,
            'undirected': False
            }
        self.sources = {
            self.straight: [],
            self.reverse: [],
            'undirected': []
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
            self.straight: [],
            self.reverse: []
        }
        self.negative_sources = {
            self.straight: [],
            self.reverse: []
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
            if type(source) is not list:
                source = [source]
            self.sources[direction] = uniqList(self.sources[direction] + source)
    
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
        return [d for d, s in self.dirs.iteritems() if s and d != 'undirected']
    
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
        return bool(sum([v for k,v in self.dirs.iteritems() if k != 'undirected']))
    
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
            if sign == 'positive':
                self.positive[direction] = True
                if source not in self.positive_sources[direction]:
                    self.positive_sources[direction].append(source)
            else:
                self.negative[direction] = True
                if source not in self.negative_sources[direction]:
                    self.negative_sources[direction].append(source)
    
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
    
    def merge(self,other):
        if other.__class__.__name__ == 'Direction' and self.check_nodes(other.nodes):
            self.dirs[self.straight] = self.dirs[self.straight] or \
                other.dirs[self.straight]
            self.dirs[self.reverse] = self.dirs[self.reverse] or \
                other.dirs[self.reverse]
            self.dirs['undirected'] = self.dirs['undirected'] or \
                other.dirs['undirected']
            self.sources[self.straight] = uniqList(self.sources[self.straight] + \
                other.sources[self.straight])
            self.sources[self.reverse] = uniqList(self.sources[self.reverse] + \
                other.sources[self.reverse])
            self.sources['undirected'] = uniqList(self.sources['undirected'] + \
                other.sources['undirected'])
            self.positive[self.straight] = self.positive[self.straight] or \
                other.positive[self.straight]
            self.negative[self.reverse] = self.negative[self.reverse] or \
                other.negative[self.reverse]
            self.positive_sources[self.straight] = \
                uniqList(self.positive_sources[self.straight] or \
                other.positive_sources[self.straight])
            self.negative_sources[self.reverse] = \
                uniqList(self.negative_sources[self.reverse] + \
                other.negative_sources[self.reverse])

class BioGraph(object):
    
    ###
    ### main network object
    ###
    
    default_name_type = {
        "protein": "uniprot", 
        "mirna": "mirbase", 
        "drug": "chembl"
    }
    
    def __init__(self, ncbi_tax_id, default_name_type=default_name_type,
                 copy=None,mysql=(None,'mapping'), name='unnamed', outdir='results',
                 loglevel='INFO'):
        # mysql gives the parameters of mysql server, if available
        # it is a dict like this: 
            #{
              #"host": 127.0.0.1, 
              #"user": "somebody", 
              #"passwd": "xxxx", 
              #"db": "mydb"
            #}
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
            g.es['sources'] = [[] for _ in xrange(self.graph.vcount())]
            g.es['references'] = [[] for _ in xrange(self.graph.vcount())]
            g.es['refs_by_source'] = [{} for _ in xrange(self.graph.vcount())]
            g.es['negative_refs'] = [[] for _ in xrange(self.graph.vcount())]
            g.es['negative'] = [[] for _ in xrange(self.graph.vcount())]
            g.es['dirs'] = [None]
            g['layout_type'] = None
            g['layout_data'] = None
            g['only_directed'] = False
            self.failed_edges = []
            self.edges_depod = None
            self.uniprot_mapped = []
            self.mysql_conf = mysql
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
            self.sources = []
            self.db_dict = {}
            self.pathway_types = []
            self.pathways = {}
            self.vertexAttrs = {}
            self.edgeAttrs = {}
            self.u_pfam = None
            self.seq = None
            self.session = gen_session_id()
            self.session_name = ''.join([self.name,'-',self.session])
            self.loglevel = loglevel
            self.ownlog = logn.logw(self.session,self.loglevel)
            self.mapper = mapping.Mapper(self.ncbi_tax_id, 
                                         mysql_conf = self.mysql_conf, log = self.ownlog)
            self.ownlog.msg(1, "bioIgraph has been initialized")
            self.ownlog.msg(1, "Beginning session '%s'" % self.session)
            sys.stdout.write(
                """\t» New session started,\n\tsession ID: '%s'\n\tlogfile: './%s'.\n""" % \
                (self.session,self.ownlog.logfile))
        else:
            self.copy(copy)
    
    def copy(self,other):
        self.__dict__ = other.__dict__
        self.ownlog.msg(1,"Reinitialized",'INFO')
    
    def init_network(self):
        self.load_mappings()
        self.load_reflists()
        self.load_resources()
    
    ###
    ### functions to read networks from text files or mysql
    ###
    
    def get_max(self,attrList):
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
    
    def get_giant(self, replace = False, graph = None):
        '''
        Returns the giant component of the graph, or 
        replaces the igraph object with only the giant 
        component.
        '''
        g = graph if graph is not None else self.graph
        gg = g if replace else copy.deepcopy(g)
        cl = gg.components()
        cl_sizes = cl.sizes()
        giant_component_index = cl_sizes.index(max(cl_sizes))
        in_giant = [x == giant_component_index for x in cl.membership]
        console(':: Nodes in giant component: %u' % in_giant.count(True))
        toDel = [i for i in range(0,gg.vcount()) if not in_giant[i]]
        gg.delete_vertices(toDel)
        console(':: Giant component size: %u edges, %u nodes' % \
            (gg.ecount(), gg.vcount()))
        if not replace:
            return gg
    
    def update_vname(self):
        self.nodInd = set(self.graph.vs['name'])
        self.nodDct = dict(zip(self.graph.vs['name'], range(0,self.graph.vcount())))
    
    def read_data_file(self, settings, keep_raw=False):
        edgeList = []
        nodeList = []
        if settings.__class__.__name__ != "ReadSettings":
            self.ownlog.msg(2,("""No proper input file definition!\n\'settings\'
                should be a \'ReadSettings\' instance\n"""), 'ERROR')
            return None
        elif not os.path.isfile(settings.inFile) and \
            not hasattr(dataio, settings.inFile):
            self.ownlog.msg(2,"%s: No such file or dataio function! :(\n" % \
                (filename), 'ERROR')
            return None
        else:
            fromA = settings.nameTypeA
            toA = self.default_name_type[settings.typeA]
            fromB = settings.nameTypeB
            toB = self.default_name_type[settings.typeB]
            mapOne = ''.join([fromA,"_",toA])
            mapTwo = ''.join([fromB,"_",toB])
            if mapOne not in self.mapper.tables and fromA != toA:
                self.mapper.map_table_error(fromA, toA)
                return None
            if mapTwo not in self.mapper.tables and fromB != toB:
                self.mapper.map_table_error(fromB, toB)
                return None
            if ((toA == "uniprot" or toB == "uniprot") 
                and "uniprot-sec_uniprot-pri" not in self.mapper.tables):
                self.mapper.map_table_error("uniprot-sec", "uniprot-pri")
                return None
            # reading from local file, or executing import function:
            if hasattr(dataio, settings.inFile):
                toCall = dataio.__dict__[settings.inFile]
                infile = toCall(**settings.inputArgs)
                self.ownlog.msg(2, "Retrieving data by dataio.%s() ..." % \
                    toCall.__name__)
            else:
                infile = codecs.open(settings.inFile, encoding='utf-8', mode='r')
                self.ownlog.msg(2, "%s opened..." % settings.inFile)
            # finding the largest referred column number, 
            # to avoid references out of range
            isDir = settings.isDirected
            sign = settings.sign
            refCol = None if type(settings.refs) is not tuple else settings.refs[0]
            sigCol = None if type(sign) is not tuple else sign[0]
            dirCol = None if type(isDir) is not tuple else isDir[0]
            dirVal = None if type(isDir) is not tuple else isDir[1]
            refs = []
            maxCol = max(
                [ 
                    settings.nameColA, 
                    settings.nameColB, 
                    self.get_max(settings.extraEdgeAttrs), 
                    self.get_max(settings.extraNodeAttrsA), 
                    self.get_max(settings.extraNodeAttrsB),
                    refCol,dirCol,sigCol
                ])
            # iterating lines from input file
            lnum = 1
            readError = 0
            for line in infile:
                if len(line) <= 1 or (lnum == 1 and settings.header):
                    # empty lines
                    # or header row
                    lnum += 1
                    continue
                if type(line) is not list:
                    line = line.replace('\n','').replace('\r','').split(settings.separator)
                else:
                    line = [x.replace('\n','').replace('\r','') for x in line]
                # in case line has less fields than needed
                if len(line) < maxCol:
                    self.ownlog.msg(2,(
                        "Line #%u has less than %u fields! :(\n" % (lnum, maxCol)),
                        'ERROR')
                    readError = 1
                    break
                else:
                    # reading names and attributes
                    # try:
                    if isDir != True:
                        isDir = (False if type(isDir) is not tuple else 
                            True if line[isDir[0]] in isDir[1] else False)
                    if refCol is not None:
                        refs = list(set(line[refCol].split(settings.refs[1])))
                    # to give an easy way:
                    if type(settings.ncbiTaxId) is int:
                        taxA = settings.ncbiTaxId
                        taxB = settings.ncbiTaxId
                    # to enable more sophisticated inputs:
                    if type(settings.ncbiTaxId) is dict:
                        taxx = self.get_taxon(settings.ncbiTaxId, line)
                        if type(taxx) is tuple:
                            taxA = taxx[0]
                            taxB = taxx[1]
                        else:
                            taxA = taxB = taxx
                    if taxA is None or taxB is None:
                        continue
                    stim = False
                    inh = False
                    if type(sign) is tuple:
                        if line[sign[0]] == sign[1] or (type(sign[1]) is list \
                            and line[sign[0]]):
                            stim = True
                        elif line[sign[0]] == sign[2] or (type(sign[2]) is list \
                            and line[sign[2]]):
                            inh = True
                    newEdge = {
                        "nameA": line[settings.nameColA], 
                        "nameB": line[settings.nameColB], 
                        "nameTypeA": settings.nameTypeA, 
                        "nameTypeB": settings.nameTypeB, 
                        "typeA": settings.typeA, 
                        "typeB": settings.typeB, 
                        "source": settings.name, 
                        "isDirected": isDir,
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
                    newEdge = dict(chain(newEdge.iteritems(), nodeAttrs.iteritems() ))
                if readError != 0:
                    break
                edgeList.append(newEdge)
                lnum += 1
            if type(infile) is file:
                infile.close()
            ### !!!! ##
            edgeListMapped = self.map_list(edgeList)
            self.ownlog.msg(2, "%u lines have been read from %s, %u links after mapping" %
                            (lnum-1, settings.inFile, len(edgeListMapped)))
        if keep_raw:
            self.data[settings.name] = edgeListMapped
        self.raw_data = edgeListMapped
    
    def read_list_file(self, settings):
        if settings.__class__.__name__ != "ReadList":
            self.ownlog.msg(2,("""No proper input file definition!\n\'settings\'
                should be a \'readList\' instance\n"""), 'ERROR')
            return None
        elif not os.path.isfile(settings.inFile):
            self.ownlog.msg(2,"%s: No such file! :(\n" % (settings.inFile), 'ERROR')
            return None
        else:
            originalNameType = settings.nameType
            defaultNameType = self.default_name_type[settings.typ]
            mapTbl = ''.join([originalNameType,"_",defaultNameType])
            if mapTbl not in self.mapper.tables and originalNameType != defaultNameType:
                self.mapper.map_table_error(originalNameType, defaultNameType)
                return None
            if (defaultNameType == "uniprot" and 
                "uniprot-sec_uniprot-pri" not in self.mapper.tables):
                self.mapper.map_table_error("uniprot-sec", "uniprot-pri")
                return None
            infile = codecs.open(settings.inFile, encoding='utf-8', mode='r')
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
            for line in infile:
                if len(line) == 0 or (lnum == 1 and settings.header):
                    # empty lines
                    # or header row
                    lnum += 1
                    continue
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
                    newItem = dict(chain(newItem.iteritems(), attrsItem.iteritems() ))
                if readError != 0:
                    break
                itemList.append(newItem)
                lnum += 1
            infile.close()
            itemListMapped = self.map_list(itemList,singleList=True)
            itemListMapped = list(set(itemListMapped) - set(["unmapped"]))
            self.ownlog.msg(2, "%u lines have been read from %s, %u items after mapping" %
                            (lnum, settings.inFile, len(itemListMapped)))
        self.lists[settings.name] = itemListMapped
    
    def map_list(self,lst,singleList=False):
        # only a wrapper for map_edge()
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
        if defaultNames[0] == 'unmapped':
            self.unmapped.append(item['name'])
        return defaultNames
    
    def map_edge(self,edge):
        edgeStack = []
        defaultNameA = self.mapper.map_name(
            edge['nameA'], 
            edge['nameTypeA'], 
            self.default_name_type[edge['typeA']])
        defaultNameB = self.mapper.map_name(
            edge['nameB'], 
            edge['nameTypeB'], 
            self.default_name_type[edge['typeB']])
        if self.default_name_type[edge['typeA']] == 'uniprot':
            defaultNameA = self.mapper.get_primary_uniprot(defaultNameA)
            defaultNameA = self.mapper.trembl_swissprot(defaultNameA)
        if self.default_name_type[edge['typeB']] == 'uniprot':
            defaultNameB = self.mapper.get_primary_uniprot(defaultNameB)
            defaultNameB = self.mapper.trembl_swissprot(defaultNameB)
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
        return edgeStack
    
    def merge_attrs(self,a,b,exc=["name"]):
        sys.stdout.write('.')
        for key, val in b.attributes().iteritems():
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
                sigA[out][inn] = uniqList(sigA[out][inn]+sigB[out][inn])
        return sigA
    
    def combine_dirs(self,dirA,dirB):
        newDir = [False,False,False]
        for i in [0,1,2]:
            newDir[i] = dirA[i] or dirB[i]
        return tuple(newDir)
    
    def combine_dirsrc(self,dirsA,dirsB):
        for i in [0,1,2]:
            dirsA[i] = uniqList(dirsA[i]+dirsB[i])
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
        if (isinstance(lst[0], (int, long, float)) and 
            isinstance(lst[1], (int, long, float))):
            return max(lst)
        if isinstance(lst[0], list) and isinstance(lst[1], list):
            try:
                return list(set(lst[0] + lst[1]))
            except:
                return lst[0] + lst[1]
        if isinstance(lst[0], dict) and isinstance(lst[1], dict):
            return dict(lst[0].items() + lst[1].items())
        if (isinstance(lst[0], str) or isinstance(lst[0], unicode) 
            and isinstance(lst[1], str) or isinstance(lst[1], unicode)):
            if len(lst[0]) == 0:
                return lst[1]
            if len(lst[1]) == 0:
                return lst[0]
            return [lst[0],lst[1]]
        if (type(lst[0]) is list and type(lst[1]) in simpleTypes):
            if len(lst[1]) > 0:
                return addToList(lst[0],lst[1])
            else:
                return lst[0]
        if (type(lst[1]) is list and type(lst[0]) in simpleTypes):
            if len(lst[0]) > 0:
                return addToList(lst[1],lst[0])
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
    
    def map_network(self,mapping="trembl_swissprot"):
        # in the whole network changes every uniprot id to primary
        if not self.mapper.has_mapping_table("uniprot-sec", "uniprot-pri"):
            return None
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
        for k,v in primNodes.iteritems():
            prim = g.vs.find(name=k)
            for s in v:
                sec = g.vs.find(name=s)
                self.merge_attrs(prim,sec,exc=["name"])
            prg.step()
        prg.terminate()
        # copying edge attributes
        prg = Progress(
            total=len(primEdges),name="Processing edge attributes",interval=10)
        for a,bdict in primEdges.iteritems():
            primA = g.vs.find(name=a).index
            for b,originals in bdict.iteritems():
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
    
    def delete_by_taxon(self,tax):
        g = self.graph
        toDel = []
        for v in g.vs:
            if v['ncbi_tax_id'] not in tax:
                toDel.append(v.index)
        g.delete_vertices(toDel)
    
    def delete_unknown(self,tax,typ='protein',defaultNameType=None):
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
            g.simplify(loops=True, multiple=True, combine_edges=self.combine_attr)
        self.delete_unmapped()
        ## TODO: multispec ##
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
        s = 0
        for i in self.graph.vs.degree():
            if i == 0:
                s += 1
        return s
    
    def add_update_vertex(
            self, defAttrs, originalName, 
            originalNameType, extraAttrs={}, add=False):
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
        for key, value in defAttrs.iteritems():
            thisNode[key] = value
        for key, value in extraAttrs.iteritems():
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
        if not g.es[edge]["sources"]:
            g.es[edge]["sources"] = []
        if source not in g.es[edge]["sources"]:
            g.es[edge]["sources"].append(source)
        # adding references:
        if not g.es[edge]["references"]:
            g.es[edge]["references"] = []
        g.es[edge]["references"] += refs
        # setting directions:
        if not g.es[edge]['dirs']:
            g.es[edge]['dirs'] = Direction(nameA,nameB)
        if isDir:
            g.es[edge]['dirs'].set_dir((nameA,nameB),source)
        else:
            g.es[edge]['dirs'].set_dir('undirected',source)
        # setting signs:
        if stim:
            g.es[edge]['dirs'].set_sign((nameA,nameB),'positive',source)
        if inh:
            g.es[edge]['dirs'].set_sign((nameA,nameB),'negative',source)
        # updating references-by-source dict:
        if not g.es[edge]['refs_by_source']:
            g.es[edge]['refs_by_source'] = {}
        if source not in g.es[edge]['refs_by_source']:
            g.es[edge]['refs_by_source'][source] = []
        g.es[edge]['refs_by_source'][source] += refs
        # adding type:
        g.es[edge]['type'] = typ
        # adding extra attributes:
        for key, value in extraAttrs.iteritems():
            if key not in g.es.attributes():
                g.es[key] = [[] for _ in xrange(self.graph.ecount())] \
                    if type(value) is list else [None]
            g.es[edge][key] = self.combine_attr([g.es[edge][key], value])
    
    def get_directed(self,graph=False,conv_edges=False,ret=False):
        toDel = []
        if not graph:
            g = self.graph
        else:
            g = graph
        d = g.as_directed(mutual=True)
        self.update_vname()
        d.es['directed_sources'] = [[] for _ in xrange(g.ecount())]
        d.es['undirected_sources'] = [[] for _ in xrange(g.ecount())]
        d.es['directed'] = [False for _ in xrange(g.ecount())]
        prg = Progress(total=g.ecount(),name="Setting directions",interval=17)
        for e in g.es:
            '''
            This works because in directed graphs get_eid() defaults to 
            directed = True, so the source -> target edge is returned.
            '''
            dir_one = (g.vs['name'][e.source],g.vs['name'][e.target])
            dir_two = (g.vs['name'][e.target],g.vs['name'][e.source])
            dir_edge_one = d.get_eid(d.vs['name'].index(g.vs['name'][e.source]),
                                 d.vs['name'].index(g.vs['name'][e.target]))
            dir_edge_two = d.get_eid(d.vs['name'].index(g.vs['name'][e.target]),
                                 d.vs['name'].index(g.vs['name'][e.source]))
            if not e['dirs'].get_dir(dir_one):
                toDel.append(dir_edge_one)
            else:
                d.es[dir_edge_one]['directed'] = True
                d.es[dir_edge_one]['directed_sources'] += \
                    e['dirs'].get_dir(dir_one, sources = True)
                d.es[dir_edge_one]['undirected_sources'] += \
                    e['dirs'].get_dir('undirected', sources = True)
            if not e['dirs'].get_dir(dir_two):
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
                    d.es[dir_edge_two]['undirected_sources'] += \
                        e['dirs'].get_dir('undirected', sources = True)
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
    
    def node_exists(self, name):
        if not hasattr(self, 'nodInd'):
            self.update_vname()
        return name in self.nodInd
    
    def get_edge(self,nodes):
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
            if self.vertexAttrs[attr] is list and type(v[attr]) in simpleTypes:
                v[attr] = [v[attr]] if len(v[attr]) > 0 else []
    
    def init_edge_attr(self, attr):
        for e in self.graph.es:
            if e[attr] is None:
                e[attr] = self.edgeAttrs[attr]()
            if self.edgeAttrs[attr] is list and type(e[attr]) in simpleTypes:
                e[attr] = [e[attr]] if len(e[attr]) > 0 else []
    
    def attach_network(self, edgeList=False, regulator=False):
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
        # add nodes and edges first in bunch, 
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
            total=len(edgeList),name='Processing edges',interval=50)
        for e in edgeList:
            aexists = self.node_exists(e["defaultNameA"])
            bexists = self.node_exists(e["defaultNameB"])
            if aexists and bexists:
                edge = self.edge_exists(e["defaultNameA"],e["defaultNameB"])
                if type(edge) is list:
                    edges.append(tuple(edge))
                prg.step()
        prg.terminate()
        if e['source'] == 'DEPOD':
            self.edges_depod = edges
        self.new_edges(set(edges))
        self.ownlog.msg(2,"New edges have been created",'INFO')
        self.ownlog.msg(2,("""Introducing new node and edge attributes..."""), 'INFO')
        prg = Progress(
            total=len(edgeList),name="Processing attributes",interval=50)
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
    
    def make_layout(self,layout_type,graph=None, **kwargs):
        if graph is None:
            g = self.graph
        else:
            g = graph
        if (not hasattr(g,"layout_type") or g.layout_type != layout_type or not
                hasattr(g,"layout_data") or len(g.layout_data) != len(g.vs)):
            self.ownlog.msg(2,("""Calculating %s layout... (numof nodes/edges: %u/%u)""" % 
                (layout_type, g.vcount(), g.ecount())), 'INFO')
            g['layout_data'] = g.layout(layout_type, **kwargs)
            g['layout_type'] = layout_type
    
    def basic_plot(self, param, **kwargs):
        if param.__class__.__name__ != "PlotParam":
            self.ownlog.msg(2,("""No proper graphical parameters definition!\n\'param\'
                should be a \'PlotParam\' instance\n"""), 'ERROR')
            return None
        if param.graph is None:
            g = self.graph
            gl = None
        else:
            g = param.graph
            gl = g
        if type(param.vertex_label) is str:
            param.vertex_label = g.vs[param.vertex_label]
        g.font = param.vertex_label_font
        if param.name is None:
            param.name = 'plot'+str(len(self.plots)+1)
        if param.filename is None:
            param.filename = ''.join([
                'network-',self.session,'-',param.name,'.',param.graphix_format
                ])
        filename = os.path.join(param.graphix_dir, param.filename)
        print filename
        # ## layout ## #
        if param.grouping is not None:
            self.ownlog.msg(2,("""Calculating %s layout... (numof nodes/edges: %u/%u)""" % 
                (layout_type+' grouped', g.vcount(), g.ecount())), 'INFO')
            if param.layout in set(["intergroup","modular_fr","modular_circle"]):
                f = getattr(gr_plot,"layout_"+param.layout)
                f(g,param.grouping,**kwargs)
            else:
                if param.layout not in set(["fruchterman_reingold","fr","circle"]):
                    param.layout = "fr"
                g['layout_data'] = layout_intergroup(g,param.grouping, **kwargs)
                g['layout_type'] = "layout_intergroup"
            if param.vertex_color == "groups":
                g.vs["color"] = group_colors(g,param.grouping)
        else:
            self.make_layout(param.layout, graph = gl, **kwargs)
        # ## layout ready ## #
        self.ownlog.msg(2,("""Plotting %s to file %s...""" % 
            (param.graphix_format,filename)), 'INFO')
        if param.graphix_format == "pdf":
            sf = cairo.PDFSurface(filename, param.dimensions[0], param.dimensions[1])
        else:
            # currently doing only pdf
            sf = cairo.PDFSurface(filename, param.dimensions[0], param.dimensions[1])
        if type(param.vertex_label_color) is list:
            vColAlpha = []
            for col in param.vertex_label_color:
                vColAlpha.append(''.join([col[0:7],param.vertex_fill_alpha]))
            param.vertex_label_color = vColAlpha
        elif type(param.vertex_label_color) is str:
            vertex_label_color = ''.join([
                param.vertex_label_color[0:7],
                param.vertex_fill_alpha])
        if param.vertex_label_size == "degree_label_size":
            # TODO
            dgr = g.vs.degree()
            maxDgr = float(max(dgr))
            g.vs["label_size"] = [None]
            for v in g.vs:
                v["label_size"] = math.log(float(v.degree()) / maxDgr + 1.0)*9.0 + 1.7
            param.vertex_label_size = g.vs["label_size"]
        elif type(param.vertex_label_size) is not int:
            param.vertex_label_size = 6
        plot = igraph.plot(g, layout = g['layout_data'],
                    target = sf,
                    bbox = param.bbox,
                    drawer_factory = DefaultGraphDrawerFFsupport,
                    vertex_size = param.vertex_size,
                    vertex_color = param.vertex_color,
                    vertex_frame_color = param.vertex_frame_color,
                    vertex_frame_width = param.vertex_frame_width,
                    vertex_label = param.vertex_label,
                    vertex_label_color = param.vertex_label_color,
                    vertex_label_size = param.vertex_label_size,
                    edge_color = param.edge_color,
                    edge_width = param.edge_width,
                    **param.kwargs)
        plot.redraw()
        plot.save()
        self.ownlog.msg(2,("""Plot saved to %s""" % filename), 'INFO')
        self.plots[param.name] = plot
        return self.plots[param.name]
    
    #
    # functions to compare networks and pathways
    #
    
    def sorensen_databases(self):
        g = self.graph
        edges = {}
        nodes = {}
        for e in g.es:
            for s in e["sources"]:
                if s not in edges:
                    edges[s] = []
                if s not in nodes:
                    nodes[s] = []
                edges[s].append(e.index)
                nodes[s].append(e.source)
                nodes[s].append(e.target)
        sNodes = self.sorensen_groups(nodes)
        sEdges = self.sorensen_groups(edges)
        return {"nodes": sNodes, "edges": sEdges}
    
    def sorensen_groups(self,groups):
        grs = groups.keys()
        sor = {}
        for g in grs:
            sor[g] = {}
        for g1 in xrange(0,len(grs)):
            for g2 in xrange(g1,len(grs)):
                sor[grs[g1]][grs[g2]] = sorensen_index(grs[g1],grs[g2])
                sor[grs[g2]][grs[g1]] = sor[grs[g1]][grs[g2]]
        return sor
    
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
        for a,v in lst.iteritems():
            if (type(v) is list and len(set(obj[a]).intersection(v)) > 0
                ) or (type(v) is not list and obj[a] == v):
                return True
        return False
    
    def search_attr_and(self,obj,lst):
        for a,v in lst.iteritems():
            if (type(v) is list and len(set(obj[a]).intersection(v)) == 0
                ) or (type(v) is not list and obj[a] != v):
                return False
        return True
    
    def get_sub(self,crit,andor="or"):
        g = self.graph
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
    
    def get_network(self,crit,andor="or"):
        sub = self.get_sub(crit,andor=andor)
        new = self.graph.copy()
        new.delete_edges(sub["edges"])
        return new.induced_subgraph(sub["nodes"])
    
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
    
    def genesymbol_labels(self):
        g = self.graph
        defaultNameType = self.default_name_type["protein"]
        geneSymbol = "genesymbol"
        mapTbl = ''.join([defaultNameType,'_',geneSymbol])
        mapTblRev = ''.join([geneSymbol,'_',defaultNameType])
        if not((mapTbl in self.mapper.tables and 
                len(self.mapper.tables[mapTbl].mapping['to']) > 0) or 
               (mapTblRev in self.mapper.tables and 
                len(self.mapper.tables[mapTblRev].mapping['from']) > 0)):
                    self.ownlog.msg(2,("Missing mapping table: %s or %s" % 
                        (mapTbl,mapTblRev)),'ERROR')
                    return False
        g.vs["label"] = [None]
        for v in g.vs:
            if v["type"] == "protein":
                label = self.mapper.map_name(v["name"],defaultNameType,geneSymbol)
                if label[0] == "unmapped":
                    v["label"] = v["name"]
                else:
                    v["label"] = label[0]
    
    def network_stats(self,outfile=None):
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
                stats[s] = [g.vcount(), g.ecount(), sum(g.vs.degree())/len(g.vs),
                    g.diameter(), g.transitivity_undirected(), g.adhesion(),
                    g.cohesion()]
        self.write_table(stats,outfile)
    
    def degree_dists(self):
        dds = {}
        for s in self.sources:
            g = self.get_network({"edge": {"sources": [s]}, "node": {}})
            if g.vcount() > 0:
                dds[s] = g.degree_distribution()
        for k,v in dds.iteritems():
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
        g.vs['sources'] = [None]
        for e in g.es:
            if g.vs[e.source]['sources'] is None:
                g.vs[e.source]['sources'] = []
            g.vs[e.source]['sources'] += e['sources']
            if g.vs[e.target]['sources'] is None:
                g.vs[e.target]['sources'] = []
            g.vs[e.target]['sources'] += e['sources']
        for v in g.vs:
            if v['sources'] is None:
                v['sources'] = []
            v['sources'] = list(set(v['sources']))
    
    def basic_stats_intergroup(self,groupA,groupB,header=None):
        result = {}
        g = self.graph
        for k in xrange(0,len(self.sources)+1):
            s = "All" if k == len(self.sources) else self.sources[k]
            f = self.graph if k == len(self.sources) else self.get_network(
                {"edge": {"sources": [s]}, "node": {}})
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
            if len(set(v['sources']) - set([source])) == 0:
                verticesToDel.append(v.index)
        g.delete_vertices(verticesToDel)
        edgesToDel = []
        for e in g.es:
            if len(set(e['sources']) - set([source])) == 0:
                edgesToDel.append(e.index)
            else:
                e['sources'] = list(set(e['sources']) - set([source]))
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
    
    def load_resources(self,lst=best):
        for k,v in lst.iteritems():
            self.load_resource(v, clean = False)
        sys.stdout.write('\n')
        self.clean_graph()
        self.update_sources()
        self.update_vertex_sources()
        sys.stdout.write(
            '''\n » %u interactions between %u nodes\n from %u resources have been loaded,\n for details see the log: ./%s\n''' %
            (self.graph.ecount(),self.graph.vcount(),len(self.sources),self.ownlog.logfile))
    
    def load_mappings(self):
        self.mapper.load_mappings(maps=data_formats.mapList)
    
    def load_resource(self, settings, clean = True):
        sys.stdout.write(' » '+settings.name+'\n')
        self.read_data_file(settings)
        self.attach_network()
        if clean:
            self.clean_graph()
        self.update_sources()
        self.update_vertex_sources()
    
    def load_reflists(self, reflists = refLists):
        for rl in reflists:
            self.load_reflist(rl)
    
    def load_reflist(self,reflist):
        reflist.load()
        idx = (reflist.nameType,reflist.typ,reflist.tax)
        self.reflists[idx] = reflist
    
    def load_negatives(self):
        for k,v in negative.iteritems():
            sys.stdout.write(' » '+v.name+'\n')
            self.apply_negative(v)
    
    def list_resources(self):
        sys.stdout.write(' » best\n')
        for k,v in best.iteritems():
            sys.stdout.write('\t:: %s (%s)\n' % (v.name,k))
        sys.stdout.write(' » good\n')
        for k,v in good.iteritems():
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
    # functions to make topological analysis on the graph
    #
    
    def first_neighbours(self,node,indices=False):
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
    
    def second_neighbours(self,node,indices=False,with_first=False):
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
        first = self.first_neighbours(node_i,indices=indices)
        for n in first:
            lst += self.first_neighbours(n,indices=indices)
        if with_first:
            lst += first
        else:
            lst = list(set(lst)-set(first))
        if indices:
            return list(set(lst)-set([node_i]))
        else:
            return list(set(lst)-set([node_n]))
    
    def all_neighbours(self,indices=False):
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
        for e in g.es:
            e['negative'] = [] if e['negative'] is None else e['negative']
            e['negative_refs'] = [] if e['negative_refs'] is None else e['negative_refs']
        for n in neg:
            aexists = n["defaultNameA"] in g.vs['name']
            bexists = n["defaultNameB"] in g.vs['name']
            if aexists and bexists:
                edge = self.edge_exists(n["defaultNameA"],n["defaultNameB"])
                if type(edge) is int:
                    if settings.name not in g.es[edge]['negative']:
                        g.es[edge]['negative'].append(settings.name)
                    g.es[edge]['negative_refs'] += n['attrsEdge']['references']
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
                        ';'.join(e['sources']),
                        ';'.join(e['references']),
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
                  'PubMed_IDs', 'Stimulation', 'Inhibition', 'PTM']
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
                        [refs for db, refs in e['refs_by_source'].iteritems() \
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
                                if dmi.ptm.residue.identifier == di[1]:
                                    uniqedges.append(e.index)
                                    r = row + [
                                        '%s-%u' % (dmi.ptm.protein, 
                                            dmi.ptm.isoform),
                                        str(dmi.ptm.residue.number), dmi.ptm.typ]
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
                        [refs for db, refs in e['refs_by_source'].iteritems() \
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
                thisEdge += [';'.join(uniqList(e['sources'])),
                             ';'.join(uniqList(e['references']))]
                thisEdge += [';'.join(e['dirs'].get_dir('undirected',sources=True)),
                             ';'.join(e['dirs'].get_dir((nameA,nameB),sources=True)),
                             ';'.join(e['dirs'].get_dir((nameB,nameA),sources=True))]
                thisEdge += [';'.join(a) for a in \
                            e['dirs'].get_sign((nameA,nameB),sources=True) + \
                            e['dirs'].get_sign((nameB,nameA),sources=True)]
                thisEdge.append(e['type'])
                for k,v in extraEdgeAttrs.iteritems():
                    thisEdge.append(
                        ';'.join([x.strip() for x in 
                            stripJson.sub('',json.dumps(e[v])).split(',')])
                    )
                for k,v in extraNodeAttrs.iteritems():
                    thisEdge.append(
                        ';'.join([x.strip() for x in 
                            stripJson.sub('',json.dumps(
                                self.graph.vs[e.source][v])
                            ).split(',')])
                    )
                for k,v in extraNodeAttrs.iteritems():
                    thisEdge.append(
                        ';'.join([x.strip() for x in 
                            stripJson.sub('',json.dumps(
                                self.graph.vs[e.target][v])
                            ).split(',')])
                    )
                f.write('\t'.join(thisEdge) + '\n')
                prg.step()
        prg.terminate()
    
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
                        ';'.join(uniqList(e['sources']))))
                f.write('\t<data key="PubMedIDs">%s</data>\n' % (
                        ';'.join(uniqList(e['references']))))
                f.write('\t<data key="Undirected">%s</data>\n' % (
                        ';'.join(uniqList(e['dirs_by_source'][0]))))
                f.write('\t<data key="DirectionAB">%s</data>\n' % (
                        ';'.join(uniqList(e['dirs_by_source'][1]))))
                f.write('\t<data key="DirectionBA">%s</data>\n' % (
                        ';'.join(uniqList(e['dirs_by_source'][2]))))
                f.write('\t<data key="StimulatoryAB">%s</data>\n' % (
                        ';'.join(uniqList(e['signs'][0][0]))))
                f.write('\t<data key="InhibitoryAB">%s</data>\n' % (
                        ';'.join(uniqList(e['signs'][0][1]))))
                f.write('\t<data key="StimulatoryBA">%s</data>\n' % (
                        ';'.join(uniqList(e['signs'][1][0]))))
                f.write('\t<data key="InhibitoryBA">%s</data>\n' % (
                        ';'.join(uniqList(e['signs'][1][1]))))
                f.write('\t<data key="InhibitoryBA">%s</data>\n' % (
                        e['type']))
                f.write('</edge>\n')
                prg.step()
            f.write('\n\t</graph>\n</graphml>')
        prg.terminate()
    
    def compounds_from_chembl(self,chembl_mysql,nodes=None,crit=None,andor="or",
                              assay_types=['B','F'],relationship_types=['D','H'],
                              multi_query=False,**kwargs):
        self.chembl = chembl.Chembl(chembl_mysql,self.ncbi_tax_id,mapper=self.mapper)
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
        if multi_query:
            self.chembl.compounds_targets_1b1(uniprots,assay_types=assay_types,
                            relationship_types=relationship_types,**kwargs)
        else:
            self.chembl.compounds_targets(uniprots,assay_types=assay_types,
                                relationship_types=relationship_types)
        self.chembl.compounds_by_target()
        self.update_vname()
        self.graph.vs['compounds_chembl'] = [[] for _ in xrange(self.graph.vcount())]
        self.graph.vs['compounds_names'] = [[] for _ in xrange(self.graph.vcount())]
        self.graph.vs['compounds_data'] = [[] for _ in xrange(self.graph.vcount())]
        num = len(self.chembl.compounds)
        prg = Progress(total=num,name='Adding compounds',interval=11)
        hascomp = 0
        for target,data in self.chembl.compounds.iteritems():
            prg.step()
            if self.node_exists(target):
                hascomp += 1
                node = self.graph.vs[self.graph.vs['name'].index(target)]
                node['compounds_data'] = data
                for comp in data:
                    node['compounds_chembl'].append(comp['chembl'])
                    node['compounds_names'] += comp['compound_names']
                node['compounds_chembl'] = uniqList(node['compounds_chembl'])
                node['compounds_names'] = uniqList(node['compounds_names'])
        prg.terminate()
        percent = hascomp/float(self.graph.vcount())
        sys.stdout.write('\n\tCompounds found for %u targets, (%.2f%% of all proteins).\n\n'\
            % (hascomp,percent*100.0))
    
    def html_descriptions(self,filename=None):
        filename = os.path.join(self.outdir,'resources.html') \
            if filename is None else filename
        head = '''<!DOCTYPE HTML>
        <html>
            <head>
                <meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
                <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
                <meta http-equiv="Content-Language" content="en">
                <meta name="dc.language" content="en">
                <meta name="viewport" content="width=device-width, 
                initial-scale=1.0">
                <style type="text/css">
                    .quotebox {
                        border-color: #7AADBD;
                        border-style: solid;
                        border-width: 1px 1px 1px 3px;
                        margin: 0.75em 1em;
                        padding: 0px 0.75em;
                        background-color: #F6F9FC;
                        color: #444444;
                    }
                </style>
            </head>
            <body>
            <h1>PPI resources'''
        foot = '''\t</body>\n
        </html>\n'''
        doc = ''
        for k,v in descriptions.descriptions.iteritems():
            doc += '\t\t<h2>%s</h2>\n' % k
            for uk,uv in v['urls'].iteritems():
                doc += '\t\t\t<h3>%s</h3>\n' % (uk.capitalize())
                for a in uv:
                    doc += '\t\t\t\t<a href="%s" target="_blank">%s</a>\n' % (
                        a,a)
            if 'taxons' in v:
                doc += '<p><b>Taxons: </b>%s</p>' % ', '.join(v['taxons'])
            if 'size' in v:
                doc += '<p><b>Nodes: </b>%s, <b>Edges:</b>%s</p>' % (
                    v['size']['nodes'],v['size']['edges'])
            if 'descriptions' in v:
                doc += '\t\t\t\t<div class="quotebox">\n'
                pars = v['descriptions'][0].split('\n')
                for p in pars:
                    p = p.strip()
                    if len(p) > 0:
                        doc += '\t\t\t\t<p>%s</p>\n' % p
                doc += '\t\t\t\t</div>\n'
            if 'notes' in v:
                doc += '\t\t\t\t<div class="quotebox">\n'
                pars = v['notes'][0].split('\n')
                for p in pars:
                    p = p.strip()
                    if len(p) > 0:
                        doc += '\t\t\t\t<p>%s</p>\n' % p
                doc += '\t\t\t\t</div>\n'
        html = head + doc + foot
        with codecs.open(filename,encoding='utf-8',mode='w') as f:
            f.write(html)
    
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
            for s,rs in e['refs_by_source'].iteritems():
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
    
    def load_pfam(self,graph=None):
        graph = graph if graph is not None else self.graph
        u_pfam, pfam_u = dataio.get_pfam(graph.vs['name'])
        if pfams is None:
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
                    for pfam, regions in self.u_pfam[v['name']].iteritems():
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
            for u,cs in members.iteritems():
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
                    if 'unmapped' in c['uniprots']:
                        c['uniprots'].remove('unmapped')
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
            for cname,v in c3d.iteritems():
                swprots = []
                uprots = []
                for ups,contact in v.iteritems():
                    uprots += list(ups)
                    up1s = self.mapper.map_name(ups[0],'uniprot','uniprot')
                    for up1 in up1s:
                        inRefLists = False
                        for tax,lst in self.reflists.iteritems():
                            if up1 in lst.lst:
                                up2s = self.mapper.map_name(ups[1],'uniprot','uniprot')
                                for up2 in up2s:
                                    for tax,lst in self.reflists.iteritems():
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
            for cname,uniprots in compl_membs.iteritems():
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
            for n, d in v['complexes']['3dcomplexes'].iteritems():
                pdblist.append(n.split('_')[0])
            for n, d in v['complexes']['complexportal'].iteritems():
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
        for pdb,iflist in pisa.iteritems():
            for uniprots,intf in iflist.iteritems():
                if uniprots[0] in graph.vs['name'] and uniprots[1] in graph.vs['name']:
                    e = self.edge_exists(uniprots[0], uniprots[1])
                    if type(e) is int:
                        if pdb not in graph.es[e]['interfaces']['pisa']:
                            graph.es[e]['interfaces']['pisa'][pdb] = []
                        graph.es[e]['interfaces']['pisa'][pdb].append(intf)
        return unmapped
    
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
                    for cname,cannot in c['complexes'][src].iteritems():
                        if cname not in cdict[src]:
                            cdict[src][cname] = []
                        cdict[src][cname].append(v['name'])
        
        pass
    
    def in_complex(self,graph=None):
        graph = graph if graph is not None else self.graph
        pass
    
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
        #all_unip = dataio.all_uniprots(organism)
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
        for uniprots, dmi_list in dmi.iteritems():
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
        for k,v in ddi.iteritems():
            uniprot1 = k[0]
            uniprot2 = k[1]
            swprots = self.mapper.swissprots([uniprot1,uniprot2])
            for swprot1 in swprots[uniprot1]:
                for swprot2 in swprots[uniprot2]:
                    if swprot1 in g.vs['name'] and swprot2 in g.vs['name']:
                        e = self.edge_exists(swprot1,swprot2)
                        if type(e) is int:
                            for domains,structures in v.iteritems():
                                for pdb,pdb_uniprot_pairs in \
                                        structures['pdbs'].iteritems():
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
                        for pfam, regions in self.u_pfam[l[9]].iteritems():
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
        for src, tgts in preg.iteritems():
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
    
    def load_comppi(self):
        self.update_vname()
        if 'comppi' not in self.graph.es.attributes():
            self.graph.es['comppi'] = [None for _ in self.graph.es]
        if 'comppi' not in self.graph.vs.attributes():
            self.graph.vs['comppi'] = [{} for _ in self.graph.vs]
        comppi = dataio.get_comppi()
        prg = Progress(len(comppi), 'Processing localizations', 33)
        for c in comppi:
            prg.step()
            uniprots1 = self.mapper.map_name(c['uniprot1'], 'uniprot', 'uniprot')
            uniprots2 = self.mapper.map_name(c['uniprot2'], 'uniprot', 'uniprot')
            for u1 in uniprots1:
                if self.node_exists(u1):
                    for loc in [x.split(':') for x in c['loc1'].split('|')]:
                        self.graph.vs[self.nodDct[u1]]\
                            ['comppi'][loc[0]] = float(loc[1])
            for u2 in uniprots1:
                if self.node_exists(u2):
                    for loc in [x.split(':') for x in c['loc2'].split('|')]:
                        self.graph.vs[self.nodDct[u2]]\
                            ['comppi'][loc[0]] = float(loc[1])
            for u1 in uniprots1:
                for u2 in uniprots2:
                    if self.node_exists(u1) and self.node_exists(u2):
                        nodes = self.get_node_pair(u1, u2)
                        if nodes:
                            e = self.graph.get_eid(nodes[0], nodes[1], error = False)
                            if e != -1:
                                self.graph.es[e]['comppi'] = float(c['loc_score'])
        prg.terminate()
    
    def sequences(self, isoforms = False):
        self.seq = dataio.swissprot_seq(self.ncbi_tax_id, isoforms)
    
    def load_ptms(self):
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
        trace = self.load_phospho_dmi(source = 'PhosphoNetworks', trace = trace, **kwargs)
        if trace:
            return trace
    
    def load_phosphoelm(self, trace = False, ltp_only = True, **kwargs):
        trace = self.load_phospho_dmi(source = 'phosphoELM', trace = trace, 
            ltp_only = ltp_only, **kwargs)
        if trace:
            return trace
    
    def load_dbptm(self, non_matching = False, **kwargs):
        trace = self.load_phospho_dmi(source = 'dbPTM', trace = trace, **kwargs)
        if trace:
            return trace
    
    def load_psite_phos(self, trace = False, **kwargs):
        trace = self.load_phospho_dmi(source = 'PhosphoSite', trace = trace **kwargs)
        if trace:
            return trace
    
    def load_phospho_dmi(self, source, trace = False, **kwargs):
        functions = {
            'MIMP': 'get_mimp',
            'PhosphoNetworks': 'get_phosphonetworks',
            'phosphoELM': 'get_phosphoelm',
            'dbPTM': 'get_dbptm',
            'PhosphoSite': 'get_psite_phos'
        }
        self.update_vname()
        toCall = getattr(dataio, functions[source])
        data = toCall(**kwargs)
        if self.seq is None:
            self.sequences()
        if 'ptm' not in self.graph.es.attributes():
            self.graph.es['ptm'] = [[] for _ in self.graph.es]
        nomatch = []
        kin_ambig = {}
        sub_ambig = {}
        prg = Progress(len(data), 'Processing PTMs from %s'%source, 23)
        for p in data:
            prg.step()
            if p['kinase'] is not None and len(p['kinase']) > 0:
                # database specific id conversions
                if source in ['PhosphoSite', 'phosphoELM']:
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
                if source in ['MIMP', 'PhosphoNetworks']:
                    substrate_ups_all = self.mapper.map_name(p['substrate'], 
                        'genesymbol', 'uniprot')
                if source == 'MIMP':
                    substrate_ups_all += self.mapper.map_name(p['substrate_refseq'], 
                        'refseq', 'uniprot')
                    substrate_ups_all = list(set(substrate_ups_all))
                if source in ['phosphoELM', 'dbPTM', 'PhosphoSite']:
                    substrate_ups_all = self.mapper.map_name(p['substrate'], 
                        'uniprot', 'uniprot')
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
                        if nodes:
                            e = self.graph.get_eid(nodes[0], nodes[1], 
                                error = False)
                            if type(e) is int and e > 0:
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
                                ptm = intera.Ptm(s, motif = mot, residue = res, 
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
                                if self.graph.es[e]['ptm'] is None:
                                    self.graph.es[e]['ptm'] = []
                                self.graph.es[e]['ptm'].append(dommot)
        prg.terminate()
        if trace:
            return {'non_matching': nomatch, 'kinase_ambiguousity': kin_ambig,
                'substrate_ambiguousity': sub_ambig}
    
    def load_depod_dmi(self):
        reres = re.compile(r'([A-Z][a-z]+)-([0-9]+)')
        non_digit = re.compile(r'[^\d.-]+')
        data = dataio.get_depod()
        aadict = dict(zip([a.lower().capitalize() for a in aaletters.keys()],
            aaletters.values()))
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
        for s, n in stats['single']['nodes'].iteritems():
            sources.append((s, (n, None), (stats['single']['edges'][s], None)))
        for s, n in stats['overlap']['nodes'].iteritems():
            overlaps[s] = {'size': (n, stats['overlap']['edges'][s])}
        diagram = bdrawing.InterSet(sources, overlaps, outf = outf, **kwargs)
        diagram.draw()
    
    def get_dirs_signs(self):
        result = {}
        for db in data_formats.best.values() + data_formats.good.values() \
            + data_formats.ugly.values():
            result[db.name] = [bool(db.isDirected), bool(db.sign)]
        return result
    
    def basic_stats(self, latex = False):
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
        header = ['Database', 'Node count', 'Edge count', 'Directions', 'Signs']
        out = [header]
        for s in sorted(stats['single']['nodes'].keys()):
            out.append([x for x in [s, stats['single']['nodes'][s], 
            stats['single']['edges'][s], 
                int(dirs[s][0]), int(dirs[s][1])]])
        if not latex:
            out = '\n'.join(['\t'.join(x) for x in out])
            with open(outf, 'w') as f:
                f.write(out)
            sys.stdout.write('\t:: Output written to file `%s`\n'%outf)
            sys.stdout.flush()
        else:
            texnewline = r'\\' + '\n'
            tex = r'''\documentclass[12pt,a4paper]{article}
                \usepackage[T1]{fontenc}
                \usepackage[utf8]{inputenc}
                \usepackage[english]{babel}
                \usepackage[landscape]{geometry}
                \usepackage{booktabs}
                \usepackage{microtype}
                \usepackage{tabularx}
                \begin{document}
                \thispagestyle{empty}
                '''
            tex += r'\begin{table}[h]' + '\n'
            tex += r'\begin{tabularx}{\textwidth}{' \
                + 'X%s'%''.join(['r']*(len(header) - 1)) + r'}' + '\n' \
                + r'\toprule' + '\n'
            tex += r' & '.join(header) + texnewline
            tex += r'\midrule' + '\n'
            tex += texnewline.join([' & '.join([ \
                xx.replace('_', r'\_') if type(xx) is not int else \
                '{:,}'.format(xx) \
                for xx in x]) for x in out[1:]]) + texnewline
            tex += r'\bottomrule' + '\n'
            tex += r'\caption{' + 'Node and edge counts of pathway databases' \
                + r'}' + '\n'
            tex += r'\end{tabularx}' + '\n'
            tex += r'\end{table}' + '\n'
            tex += r'\end{document}' + '\n'
            with open(outf, 'w') as f:
                f.write(tex)
            sys.stdout.write('\t:: Output written to file `%s`\n'%outf)
            sys.stdout.flush()
    
    def source_network(self, font = 'HelveticaNeueLTStd'):
        '''
        For EMBL branding, use Helvetica Neue Linotype Standard light
        '''
        stats = self.sources_overlap()
        tupleListNodes = []
        tupleListEdges = []
        for dbs, overlap in stats['overlap']['nodes'].iteritems():
            if overlap > 0:
                tupleListNodes.append(tuple(sorted(list(dbs)) + [overlap]))
        for dbs, overlap in stats['overlap']['edges'].iteritems():
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
    
    def load_mutations(self, attributes = None):
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
        data = gdsc.read_mutations(attributes = attributes)
        if 'mut' not in self.graph.vs.attributes():
            self.graph.vs['mut'] = [{} for _ in self.graph.vs]
        prg = Progress(len(data), 'Processing mutations', 33)
        for uniprot, muts in data.iteritems():
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
            for gsymb, expr in data.iteritems():
                prg.step()
                uniprots = self.mapper.map_name(gsymb, 'genesymbol', 'uniprot')
                for up in uniprots:
                    if up in self.nodDct:
                        self.graph.vs[self.nodDct[up]]['exp'] = \
                            dict(expr.items() + \
                                self.graph.vs[self.nodDct[up]]['exp'].items())
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
                for smpl, mut in self.graph.vs[v]['mut'].iteritems():
                    if smpl == sample:
                        for ptm in e['ptm']:
                            if mut.original == ptm.ptm.residue:
                                toDel.append(e.index)
                                if e.index not in disrupted:
                                    disrupted[e.index] = \
                                        {'ptms': len(e['ptm']), 'disr': 0}
                                disrupted[e.index]['disr'] += 1
        return toDel, disrupted
    