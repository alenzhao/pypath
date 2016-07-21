#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#
#  This file is part of the `pypath` python module
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

# external modules:
from future.utils import iteritems

import os
import copy

# from pypath:
import pypath.input_formats as input_formats
from pypath import common

__all__ = ['urls', 'mapList', 'otherMappings', 'refLists',
           'reaction', 'interaction', 'interaction_misc', 'pathway',
           'interaction_htp',
           'ptm', 'ptm_misc', 'obsolate', 'transcription_deprecated',
           'omnipath', 'transcription', 'negative', 'gdsc_comp_target', 'cgc',
           'mapListUniprot', 'mapListBasic', 'reactome_modifications',
           'reaction_misc']

ROOT = common.ROOT

# this is all what is needed to load the resources 
# included in the pypath package

'''
Old input definitions, should not be used.
'''
obsolate = {
    'signalink2': input_formats.ReadSettings(name = "SignaLink2", separator = ",", 
                nameColA = 0, nameColB = 1,
                nameTypeA = "uniprot", nameTypeB = "uniprot",
                typeA="protein", typeB="protein", isDirected=(7,['1','2']), 
                sign=(6,'1','-1'),
                inFile=os.path.join(ROOT, 'data', 'slk01human.csv'),references=(9,':'),ncbiTaxId=9606,
                extraEdgeAttrs={
                    "netbiol_effect": 8, 
                    "is_direct": 6,
                    "is_directed": 7},
                extraNodeAttrsA={
                    "slk_pathways": (4, ":"),
                    "gene_name": 2},
                extraNodeAttrsB={
                    "slk_pathways": (5, ":"),
                    "gene_name": 3}),
    'nci_pid': input_formats.ReadSettings(name="NCI-PID", 
                separator="\t", nameColA=0, nameColB=1,
                nameTypeA="uniprot", nameTypeB="uniprot",
                typeA="protein", typeB="protein", isDirected=(2,['1','-1']), 
                inFile=os.path.join(ROOT, 'data', 'nci-pid-strict.csv'),
                references=(4, ";"),ncbiTaxId=9606,
                extraEdgeAttrs={
                    "pid_effect": 2,
                    "pid_evidence": (5, ";"),
                    "pid_pathways": (6, ";")},
                extraNodeAttrsA={},
                extraNodeAttrsB={})
}

'''
Reaction databases.
These are not included in OmniPath, because only a minor
part of their content can be used when processing along
strict conditions to have only binary interactions with
references.
'''
reaction = {
    'Reaction resources': input_formats.ReadSettings(
        name = "reaction resources",
        separator = None, nameColA = 0, nameColB = 1,
        nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB = "protein", isDirected = (3, '1'),
        sign = None,
        resource = 4,
        inFile = 'get_reactions',
        references = (5, ';'), ncbiTaxId = 9606,
        extraEdgeAttrs = {
            "sif_rule": (2, ";")
            },
        extraNodeAttrsA={},
        extraNodeAttrsB={},
        must_have_references = False
    )
}

reaction_misc = {
    'nci_pid': input_formats.ReadSettings(name = "NCI-PID", 
        separator = None, nameColA = 0,
        nameColB = 1, nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB = "protein", 
        isDirected = (4, 'directed'), sign = False,
        ncbiTaxId = 9606,
        inFile = 'pid_interactions', references = (3, ';'), header = False,
        extraEdgeAttrs={},
        extraNodeAttrsA={},
        extraNodeAttrsB={}),
    'acsn': input_formats.ReadSettings(name = "ACSN", 
        separator = None, nameColA = 0,
        nameColB = 1, nameTypeA = "genesymbol", nameTypeB = "genesymbol",
        typeA = "protein", typeB = "protein", 
        isDirected = (4, 'directed'), sign = False,
        ncbiTaxId = 9606,
        inFile = 'acsn_interactions', references = (3, ';'), header = False,
        extraEdgeAttrs={},
        extraNodeAttrsA={},
        extraNodeAttrsB={}),
    'reactome': input_formats.ReadSettings(name = "Reactome", 
        separator = None, nameColA = 0,
        nameColB = 1, nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB = "protein", 
        isDirected = (4, 'directed'), sign = False,
        ncbiTaxId = 9606, huge = True, 
        inFile = 'reactome_interactions', references = (3, ';'), header = False,
        extraEdgeAttrs={},
        extraNodeAttrsA={},
        extraNodeAttrsB={})
}

reaction_pc = {
    'acsn': input_formats.ReadSettings(name="ACSN", 
        separator = None, nameColA=0,
        nameColB=1, nameTypeA="genesymbol", nameTypeB="genesymbol",
        typeA = "protein", typeB = "protein", 
        isDirected = (2, [
            'UNKNOWN_TRANSITION', 'INTERACTION_TYPE', 'KNOWN_TRANSITION_OMITTED', 
            'INHIBITION', 'UNKNOWN_POSITIVE_INFLUENCE', 'PROTEIN_INTERACTION',
            'UNKNOWN_CATALYSIS', 'POSITIVE_INFLUENCE', 'STATE_TRANSITION', 
            'TRANSLATION', 'UNKNOWN_NEGATIVE_INFLUENCE', 'NEGATIVE_INFLUENCE', 
            'MODULATION', 'TRANSCRIPTION', 'COMPLEX_EXPANSION', 'TRIGGER', 'CATALYSIS',
            'PHYSICAL_STIMULATION', 'UNKNOWN_INHIBITION', 'TRANSPORT'], ';'), 
        sign = (2, ['TRIGGER',
            'UNKNOWN_POSITIVE_INFLUENCE', 'POSITIVE_INFLUENCE'], 
            ['UNKNOWN_NEGATIVE_INFLUENCE', 'NEGATIVE_INFLUENCE'], ';'),
        ncbiTaxId = 9606,
        negativeFilters = [
            (2, ['COMPLEX_EXPANSION', 'TRANSCRIPTION'], ';'), (3, 'N/A')],
        positiveFilters = [],
        references = False,
        inFile = 'acsn_ppi', header = False,
        extraEdgeAttrs={
            'acsn_effect': (2, ';'),
            'acsn_refs': (3, ';')
        },
        extraNodeAttrsA={},
        extraNodeAttrsB={}),
}

'''
Pathway databases included in OmniPath.
These are manually curated, directed, and in most
of the cases signed interactions, with literature references.
'''
pathway = {
    'trip': input_formats.ReadSettings(name="TRIP", 
        separator = None, nameColA = 1,
        nameColB = 0, nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB = "protein", 
        isDirected = (4, ['stimulation', 'inhibition']), 
        sign = (4, 'stimulation', 'inhibition'),
        ncbiTaxId = 9606,
        inFile = 'trip_interactions', references = (2, ';'), header = False,
        extraEdgeAttrs = {'trip_methods': (3, ';')},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'spike': input_formats.ReadSettings(name = "SPIKE", 
        separator = "\t", nameColA = 1, nameColB = 3,
        nameTypeA = "genesymbol", nameTypeB = "genesymbol",
        typeA = "protein", typeB = "protein", isDirected = (4,['1']), 
        sign  =  (7, '1', '2'),
        inFile = 'spike_interactions',
        references = (5, ";"), ncbiTaxId = 9606,
        extraEdgeAttrs = {
            'spike_effect': 7, 
            'spike_mechanism': 11},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'signalink3': input_formats.ReadSettings(name = "SignaLink3", 
        separator = None, nameColA = 0, nameColB = 1,
        nameTypeA="uniprot", nameTypeB="uniprot",
        typeA="protein", typeB="protein", isDirected = (6, 'directed'), 
        sign=(4, 'stimulation', 'inhibition'),
        inFile = 'signalink_interactions', 
        references = (2, ';'), ncbiTaxId = 9606,
        extraEdgeAttrs={
            "netbiol_effect": 4, 
            "netbiol_is_direct": 5,
            "netbiol_is_directed": 6,
            "netbiol_mechanism": 7},
        extraNodeAttrsA={
            "slk_pathways": (8, ";")
            },
        extraNodeAttrsB={
            "slk_pathways": (9, ";")
            }),
    'guide2pharma': input_formats.ReadSettings(name = "Guide2Pharma", 
        separator = None, nameColA = 0, nameColB = 1,
        nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB = "protein", isDirected = True, 
        sign = (2, 1, -1), inFile = 'guide2pharma', 
        references=(3, "|"), ncbiTaxId = 9606,
        extraEdgeAttrs = {},
        extraNodeAttrsA = {'g2p_ligand': 4},
        extraNodeAttrsB = {'g2p_receptor': 4}),
    'ca1': input_formats.ReadSettings(name = "CA1", 
        nameColA = 1, nameColB = 6,
        nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB = "protein", 
        isDirected = (10, ['_', '+']), sign = (10, '+', '_'),
        header = False, 
        inFile = 'get_ca1',
        references = (12, ";"), ncbiTaxId = 9606,
        extraEdgeAttrs = {
            "ca1_effect": 10,
            "ca1_type": 11},
        extraNodeAttrsA = {
            "ca1_location": 4,
            "ca1_function": 3},
        extraNodeAttrsB = {
            "ca1_location": 9,
            "ca1_function": 8}),
    'arn': input_formats.ReadSettings(name="ARN", 
        separator=",", nameColA=0, nameColB=1,
        nameTypeA="uniprot", nameTypeB="uniprot",
        typeA="protein", typeB="protein", 
        isDirected=(3,['1','2']), sign=(4,'1','-1'),
        inFile=os.path.join(ROOT, 'data', 'arn_curated.csv'),
        references=(7, ":"),ncbiTaxId=9606,
        extraEdgeAttrs={
            "netbiol_effect": 4,
            "is_direct": 2,
            "is_directed": 3
            },
        extraNodeAttrsA={
            "atg": 5
            },
        extraNodeAttrsB={
            "atg": 6
            }),
    'nrf2': input_formats.ReadSettings(name = "NRF2ome", 
        separator = ",", nameColA = 0, nameColB = 1,
        nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB = "protein", 
        isDirected = (3,['1','2']), sign = (4,'1','-1'),
        inFile = os.path.join(ROOT, 'data', 'nrf2ome.csv'),
        references = (5, ":"),ncbiTaxId = 9606,
        extraEdgeAttrs = {
            "netbiol_effect": 4,
            "is_direct": 2,
            "is_directed": 3
            },
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'macrophage': input_formats.ReadSettings(name = "Macrophage", 
        separator = ";", nameColA = 0, nameColB = 1,
        nameTypeA = "genesymbol", nameTypeB = "genesymbol",
        typeA = "protein", typeB = "protein", isDirected = (3,['1']),
        sign = (2,'Activation','Inhibition'),
        inFile  =  'macrophage_interactions',
        references = (5, ","),ncbiTaxId = 9606,
        extraEdgeAttrs = {
            "macrophage_type": (2, ","),
            "macrophage_location": (4, ",")},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'death': input_formats.ReadSettings(name = "DeathDomain", 
        separator = "\t", nameColA = 0, nameColB = 1,
        nameTypeA = "genesymbol", nameTypeB = "genesymbol",
        typeA = "protein", typeB = "protein", isDirected = False, sign = False,
        inFile = 'deathdomain_interactions',
        references = (3, ";"), ncbiTaxId  =  9606,
        extraEdgeAttrs = {
            "dd_methods": (2, ';')
            },
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'pdz': input_formats.ReadSettings(name = "PDZBase", 
        separator  =  None, nameColA = 1,
        nameColB = 4, nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA  =  "protein", typeB  =  "protein", isDirected  =  1, sign  =  False,
        ncbiTaxId  =  {'col': 5, 'dict': {'human': 9606}}, 
        inFile  =  'get_pdzbase', references  =  6, header  =  False,
        extraEdgeAttrs = {},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'signor': input_formats.ReadSettings(name="Signor", 
        separator="\t", nameColA = 2, nameColB = 6,
        nameTypeA="uniprot", nameTypeB="uniprot",
        # only direct interactions
        positiveFilters = [(22, 'YES')], 
        # exclude TF-target interactions
        negativeFilters = [(9, 'transcriptional regulation')], 
        typeA="protein", typeB="protein", 
        ncbiTaxId = {'col': 12, 'dict': {'9606;9606': 9606}},
        isDirected = (8, ['up-regulates', 'up-regulates activity', 
            'up-regulates quantity by stabilization',
            'down-regulates', 'down-regulates activity', 
            'down-regulates quantity by destabilization']), 
        sign = (8, ['up-regulates', 'up-regulates activity', 
            'up-regulates quantity by stabilization'],
            ['down-regulates', 'down-regulates activity', 
            'down-regulates quantity by destabilization']), 
        inFile = 'signor_interactions', references=(21, ";"), header=True,
        extraEdgeAttrs={
            "signor_mechanism": (9, ';')
            },
        extraNodeAttrsA={},
        extraNodeAttrsB={})
}

'''
Interaction databases included in OmniPath.
These are subsets of the named databases, having
only low throughput, manually curated, undirected
interactions with literature references.
'''
interaction = {
    'biogrid': input_formats.ReadSettings(name="BioGRID", 
        separator = None, nameColA = 0,
        nameColB = 1, nameTypeA = "genesymbol", nameTypeB = "genesymbol",
        typeA = "protein", typeB = "protein", isDirected = False, sign = False,
        ncbiTaxId = 9606,
        inFile = 'biogrid_interactions', references = (2, '|'), header = False,
        extraEdgeAttrs={},
        extraNodeAttrsA={},
        extraNodeAttrsB={}),
    'ccmap': input_formats.ReadSettings(name="CancerCellMap", 
        nameColA = 0, nameColB = 1,
        nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB = "protein",
        isDirected = (2, 'directed'), sign = False, ncbiTaxId = 9606,
        inFile = 'get_ccmap',
        references = (3, ";"),
        extraEdgeAttrs={},
        extraNodeAttrsA={},
        extraNodeAttrsB={}),
    'mppi': input_formats.ReadSettings(name = "MPPI", 
        separator = "|", nameColA = 2, nameColB = 6,
        nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB = "protein", isDirected = False, sign = False,
        inFile = 'mppi_interactions',
        references = (0, ";"), ncbiTaxId = 9606,
        extraEdgeAttrs = {
            "mppi_evidences": (1, ";")},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'dip': input_formats.ReadSettings(name="DIP",
        nameColA=0, nameColB=1,
        nameTypeA="uniprot", nameTypeB="uniprot",
        typeA="protein", typeB="protein",isDirected=False,sign=False,
        inFile = 'get_dip',
        references=(2, ";"),ncbiTaxId=9606,
        extraEdgeAttrs={
            "dip_methods": (4, ";"),
            "dip_type": (3, ";"),
            'dip_id': 5
        },
        extraNodeAttrsA={},
        extraNodeAttrsB={}),
    'netpath': input_formats.ReadSettings(name = "NetPath", separator = None,
        nameColA = 1, nameColB = 3,
        nameTypeA="entrez", nameTypeB="entrez",
        typeA="protein", typeB="protein", isDirected=False, sign=False,
        inFile='netpath_interactions', references=(4, ";"), ncbiTaxId=9606,
        extraEdgeAttrs={
            "netpath_methods": (5, ";"),
            "netpath_type": (6, ";"),
            "netpath_pathways": (7, ';')},
        extraNodeAttrsA={},
        extraNodeAttrsB={}),
    'innatedb': input_formats.ReadSettings(name = "InnateDB", 
        nameColA = 0, nameColB = 2,
        nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB = "protein", isDirected = False, sign = False,
        inFile = 'get_innatedb',
        references = (4, ":"),ncbiTaxId = 9606,
        extraEdgeAttrs = {},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'alz': input_formats.ReadSettings(name="AlzPathway",
        separator="\t", nameColA=0, nameColB=1,
        nameTypeA="uniprot", nameTypeB="uniprot",
        typeA="protein", typeB="protein", isDirected=False, sign=False,
        inFile=os.path.join(ROOT, 'data', 'alzpw-ppi.csv'),
        references=(8, ";"),ncbiTaxId=9606,
        extraEdgeAttrs={},
        extraNodeAttrsA={},
        extraNodeAttrsB={}),
    'matrixdb': input_formats.ReadSettings(name = "MatrixDB", 
        nameColA = 0, nameColB = 1,
        nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB = "protein", isDirected = False, sign = False,
        inFile = 'get_matrixdb',
        references = (2, "|"),ncbiTaxId = 9606,
        extraEdgeAttrs = {
            "matrixdb_methods": (3, '|')
            },
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
}

'''
PTM databases included in OmniPath.
These supply large sets of directed interactions.
'''
ptm = {
    'psite': input_formats.ReadSettings(name="PhosphoSite", 
        separator = None, nameColA = 0, nameColB = 1,
        nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB="protein", isDirected = True, sign = False,
        inFile = 'get_phosphosite_curated',
        references = (5, ";"), ncbiTaxId = 9606,
        extraEdgeAttrs = {
            "psite_evidences": (4, ";")},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'depod': input_formats.ReadSettings(name = "DEPOD", 
        separator = ";", nameColA = 0, nameColB = 1,
        nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB = "protein", isDirected = True, sign = False,
        inFile = 'depod_interactions',
        references = (2, "|"),ncbiTaxId = 9606,
        extraEdgeAttrs = {},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'lmpid': input_formats.ReadSettings(name = "LMPID", 
        separator  =  None, nameColA  =  0,
        nameColB  =  1, nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA  =  "protein", typeB  =  "protein", isDirected  =  0, sign  =  False,
        ncbiTaxId  =  9606, 
        inFile  =  'lmpid_interactions', references  =  (2, ';'), header  =  False,
        extraEdgeAttrs = {},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'phelm': input_formats.ReadSettings(name = "phosphoELM", 
        separator  =  None, nameColA = 0,
        nameColB = 1, nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA  =  "protein", typeB  =  "protein", isDirected  =  1, sign  =  False,
        ncbiTaxId  =  {'col': 3, 'dict': {'Homo sapiens': 9606}}, 
        inFile  =  'phelm_interactions', references  =  (2, ';'), header  =  False,
        extraEdgeAttrs = {},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'elm': input_formats.ReadSettings(name = "ELM", 
        separator  =  None, nameColA = 2,
        nameColB = 3, nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA  =  "protein", typeB  =  "protein", isDirected  =  0, sign  =  False,
        ncbiTaxId  =  {'A': {'col': 11, 'dict': {'"9606"(Homo sapiens)': 9606}}, 
                        'B': {'col': 12, 'dict': {'"9606"(Homo sapiens)': 9606}}},
        inFile  =  'get_elm_interactions', references  =  (10, ','), header  =  False,
        extraEdgeAttrs = {},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'domino': input_formats.ReadSettings(name = "DOMINO", 
        separator  =  None, nameColA = 0,
        nameColB = 1, nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA  =  "protein", typeB  =  "protein", isDirected  =  0, sign  =  False,
        ncbiTaxId  =  {'A': {'col': 6, 'dict': {'9606': 9606}},
                        'B': {'col': 7, 'dict': {'9606': 9606}}},
        inFile  =  'get_domino_interactions', references  =  (5, ';'),
        header  =  False,
        extraEdgeAttrs = {'domino_methods': (4, ';')},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'dbptm': input_formats.ReadSettings(name="dbPTM", 
        separator = None, nameColA=0,
        nameColB=1, nameTypeA = ['genesymbol', 'uniprot'], 
        nameTypeB="uniprot",
        typeA = "protein", typeB = "protein", isDirected = 1, sign = False,
        ncbiTaxId = 9606,
        inFile = 'dbptm_interactions', 
        references = (2, ';'), header = False,
        extraEdgeAttrs={},
        extraNodeAttrsA={},
        extraNodeAttrsB={},
        must_have_references = True),
    'hprd_p': input_formats.ReadSettings(name="HPRD-phos",
        separator = None, nameColA = 6,
        nameColB = 3, nameTypeA = "genesymbol", nameTypeB = "refseqp",
        typeA = "protein", typeB = "protein", isDirected = 1, sign = False,
        ncbiTaxId = 9606,
        inFile = 'hprd_interactions', references = (10, ','), header = False,
        extraEdgeAttrs={'hprd_mechanism': 8},
        extraNodeAttrsA={},
        extraNodeAttrsB={})
}

'''
The default set of resources in OmniPath.
'''
omnipath = {}
omnipath.update(pathway)
omnipath.update(ptm)
omnipath.update(interaction)

del omnipath['netpath']
#del omnipath['innatedb']
del omnipath['alz']
#del omnipath['biogrid']
omnipath['intact'] = interaction_htp['intact']
omnipath['biogrid'] = interaction_htp['biogrid']
omnipath['hprd'] = interaction_htp['hprd']

'''
Other PTM datasets which are not used because the lack of
references.
'''
ptm_misc = {
    'psite_noref': input_formats.ReadSettings(name="PhosphoSite_noref", 
        separator = None, 
        nameColA=0, nameColB=1, nameTypeA="uniprot", nameTypeB="uniprot",
        typeA="protein", typeB="protein", isDirected=True, 
        sign=False, ncbiTaxId=9606,
        inFile = 'get_phosphosite_noref',
        references = False,
        extraEdgeAttrs = {
            "psite_evidences": (4, ";")},
        extraNodeAttrsA={},
        extraNodeAttrsB={}),
    'ppoint': input_formats.ReadSettings(name="PhosphoPoint", separator=";", 
        nameColA=1, nameColB=3,
        nameTypeA="entrez", nameTypeB="entrez",
        typeA="protein", typeB="protein", isDirected=0, header=True, ncbiTaxId=9606, 
        inFile=os.path.join(ROOT, 'data', 'phosphopoint.csv'), 
        references = False, sign=False,
        extraEdgeAttrs={
            "phosphopoint_category": 4
            },
        extraNodeAttrsA={},
        extraNodeAttrsB={}),
    'pnetworks': input_formats.ReadSettings(name="PhosphoNetworks", 
        separator = None, nameColA=0,
        nameColB=1, nameTypeA="genesymbol", nameTypeB="genesymbol",
        typeA = "protein", typeB = "protein", isDirected = 1, sign = False,
        ncbiTaxId = 9606,
        inFile = 'pnetworks_interactions', references = False, header = False,
        extraEdgeAttrs={},
        extraNodeAttrsA={},
        extraNodeAttrsB={}),
    'mimp': input_formats.ReadSettings(name = "MIMP", 
        separator = None, nameColA = 0,
        nameColB = 1, nameTypeA = "genesymbol", nameTypeB = "genesymbol",
        typeA = "protein", typeB = "protein", isDirected = 1, sign = False,
        ncbiTaxId = 9606,
        inFile = 'mimp_interactions', references = False, header = False,
        extraEdgeAttrs = {},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'li2012': input_formats.ReadSettings(name = "Li2012", separator = False, 
        nameColA = 0, nameColB = 1,
        nameTypeA="genesymbol", nameTypeB="genesymbol",
        typeA="protein", typeB="protein", isDirected = 1, 
        sign = False,
        inFile = 'li2012_interactions', references = False, ncbiTaxId = 9606,
        extraEdgeAttrs = {
            'li2012_mechanism': 3,
            'li2012_route': 2
        },
        extraNodeAttrsA = {},
        extraNodeAttrsB = {})
}

ptm_all = copy.deepcopy(ptm_misc)
ptm_all.update(ptm)

'''
Interaction databases not included in OmniPath.
These were omitted because lack of references,
or because we could not separate the low throughput,
manually curated interactions.
'''
interaction_misc = {
    'intact': input_formats.ReadSettings(name = "IntAct", 
        separator = ",", nameColA = 0, nameColB = 1,
        nameTypeA  =  "uniprot", nameTypeB  =  "uniprot",
        typeA  =  "protein", typeB  =  "protein", isDirected  =  False, sign  =  False,
        inFile = 'intact_interactions',
        references = (2, ";"), ncbiTaxId  =  9606,
        extraEdgeAttrs = {
            "intact_methods": (3, ';')
            },
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'biogrid': input_formats.ReadSettings(name="BioGRID", separator = None, nameColA = 0,
        nameColB = 1, nameTypeA = "genesymbol", nameTypeB = "genesymbol",
        typeA = "protein", typeB = "protein", isDirected = False, sign = False,
        ncbiTaxId = 9606,
        inFile = 'biogrid_interactions', references = (2, '|'), header = False,
        extraEdgeAttrs={},
        extraNodeAttrsA={},
        extraNodeAttrsB={}),
    'hsn': input_formats.ReadSettings(name="Wang", separator=",", 
        nameColA = 0, nameColB = 2,
        nameTypeA="entrez", nameTypeB="entrez",
        typeA="protein", typeB="protein", isDirected = (4, ['Pos', 'Neg']), 
        sign = (4, 'Pos', 'Neg'),
        inFile = 'get_hsn',references = False, ncbiTaxId = 9606,
        extraEdgeAttrs={},
        extraNodeAttrsA={},
        extraNodeAttrsB={}),
    'acsn': input_formats.ReadSettings(name="ACSN", 
        separator = None, nameColA=0,
        nameColB=2, nameTypeA="genesymbol", nameTypeB="genesymbol",
        typeA = "protein", typeB = "protein", 
        isDirected = (1, ['CATALYSIS', 'UNKNOWN_CATALYSIS', 'INHIBITION',
            'PHYSICAL_STIMULATION', 'TRIGGER', 'activates', 
            'UNKNOWN_POSITIVE_INFLUENCE', 'inhibits', 'MODULATION']), 
        sign = (1, ['PHYSICAL_STIMULATION', 'TRIGGER', 'activates',
            'UNKNOWN_POSITIVE_INFLUENCE'], ['INHIBITION', 'inhibits']),
        ncbiTaxId = 9606,
        inFile = 'get_acsn', references = False, header = False,
        extraEdgeAttrs={
            'acsn_effect': 1
        },
        extraNodeAttrsA={},
        extraNodeAttrsB={}),
    'hi2': input_formats.ReadSettings(name="HI-II", 
        separator = None, nameColA = 2,
        nameColB = 3, nameTypeA = "genesymbol", nameTypeB = "genesymbol",
        typeA = "protein", typeB = "protein", 
        isDirected = False, 
        sign = False,
        ncbiTaxId = 9606,
        inFile = 'rolland_hi_ii_14', 
        references = False, header = False,
        extraEdgeAttrs = {'hi2_numof_screens': 4},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'hi3': input_formats.ReadSettings(name = "HI-III", 
        separator = None, nameColA = 1,
        nameColB = 3, nameTypeA = "genesymbol", nameTypeB = "genesymbol",
        typeA = "protein", typeB = "protein", 
        isDirected = False, 
        sign = False,
        ncbiTaxId = 9606,
        inFile = '/home/denes/Dokumentumok/pw/data/hi3.tsv', 
        references = False, header = True,
        extraEdgeAttrs = {},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'lit13': input_formats.ReadSettings(name = "Lit-BM-13", 
        separator = None, nameColA = 1,
        nameColB = 3, nameTypeA = "genesymbol", nameTypeB = "genesymbol",
        typeA = "protein", typeB = "protein",
        isDirected = False,
        sign = False,
        ncbiTaxId = 9606,
        inFile = 'get_lit_bm_13',
        references = False, header = False,
        extraEdgeAttrs = {},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'cpdb': input_formats.ReadSettings(name="CPDB",
        separator = None, nameColA = 0,
        nameColB = 1, nameTypeA="uniprot-entry", nameTypeB="uniprot-entry",
        typeA = "protein", typeB = "protein", 
        isDirected = False,
        sign = False,
        ncbiTaxId = 9606,
        inFile = 'get_cpdb',
        references = (3, ','), header = False,
        extraEdgeAttrs = {},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {})
}

interaction_htp = {
    'intact': input_formats.ReadSettings(name = "IntAct",
        separator = ",", nameColA = 0, nameColB = 1,
        nameTypeA  =  "uniprot", nameTypeB  =  "uniprot",
        typeA  =  "protein", typeB  =  "protein", isDirected  =  False, sign  =  False,
        inFile = 'intact_interactions',
        references = (2, ";"), ncbiTaxId  =  9606,
        extraEdgeAttrs = {
            "intact_methods": (3, ';')
            },
        extraNodeAttrsA = {},
        extraNodeAttrsB = {},
        inputArgs = {'miscore': 0.0}),
    'biogrid': input_formats.ReadSettings(name="BioGRID",
        separator = None, nameColA = 0,
        nameColB = 1, nameTypeA = "genesymbol", nameTypeB = "genesymbol",
        typeA = "protein", typeB = "protein", isDirected = False, sign = False,
        ncbiTaxId = 9606,
        inFile = 'biogrid_interactions', references = (2, '|'), header = False,
        extraEdgeAttrs={},
        extraNodeAttrsA={},
        extraNodeAttrsB={},
        inputArgs = {'htp_limit': None, 'ltp': False}),
    'dip': input_formats.ReadSettings(name="DIP",
        nameColA=0, nameColB=1,
        nameTypeA="uniprot", nameTypeB="uniprot",
        typeA="protein", typeB="protein",isDirected=False,sign=False,
        inFile = 'get_dip',
        references=(2, ";"),ncbiTaxId=9606,
        extraEdgeAttrs={
            "dip_methods": (4, ";"),
            "dip_type": (3, ";"),
            'dip_id': 5
        },
        extraNodeAttrsA={},
        extraNodeAttrsB={},
        inputArgs = {'core_only': False, 'small_scale_only': False}),
    'ccmap': input_formats.ReadSettings(name="CancerCellMap", 
        nameColA = 0, nameColB = 1,
        nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB = "protein",
        isDirected = (2, 'directed'), sign = False, ncbiTaxId = 9606,
        inFile = 'get_ccmap',
        references = (3, ";"),
        extraEdgeAttrs={},
        extraNodeAttrsA={},
        extraNodeAttrsB={}),
    'innatedb': input_formats.ReadSettings(name = "InnateDB",
        nameColA = 0, nameColB = 2,
        nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB = "protein", isDirected = False, sign = False,
        inFile = 'get_innatedb',
        references = (4, ":"),ncbiTaxId = 9606,
        extraEdgeAttrs = {},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'matrixdb': input_formats.ReadSettings(name = "MatrixDB",
        nameColA = 0, nameColB = 1,
        nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB = "protein", isDirected = False, sign = False,
        inFile = 'get_matrixdb',
        references = (2, "|"),ncbiTaxId = 9606,
        extraEdgeAttrs = {
            "matrixdb_methods": (3, '|')
            },
        extraNodeAttrsA = {},
        extraNodeAttrsB = {}),
    'hprd': input_formats.ReadSettings(name="HPRD",
        separator = None, nameColA = 0,
        nameColB = 3, nameTypeA = "genesymbol", nameTypeB = "genesymbol",
        typeA = "protein", typeB = "protein", isDirected = 0, sign = False,
        ncbiTaxId = 9606,
        inFile = 'hprd_htp', references = (7, ','), header = False,
        extraEdgeAttrs={'hprd_methods': (6, ';')},
        extraNodeAttrsA={},
        extraNodeAttrsB={}),
    'hi3': input_formats.ReadSettings(
        name = "Vidal HI-III",
        separator = None,
        nameColA = 1,
        nameColB = 3,
        nameTypeA = "genesymbol",
        nameTypeB = "genesymbol",
        typeA = "protein",
        typeB = "protein",
        isDirected = False,
        sign = False,
        ncbiTaxId = 9606,
        inFile = 'vidal_hi_iii',
        references = False,
        extraEdgeAttrs = {},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {},
        must_have_references = False,
        inputArgs = {'fname': '/home/denes/Documents/pw/data/hi3-2.3.tsv'}),
    'mppi': input_formats.ReadSettings(name = "MPPI", 
        separator = "|", nameColA = 2, nameColB = 6,
        nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB = "protein", isDirected = False, sign = False,
        inFile = 'mppi_interactions',
        references = (0, ";"), ncbiTaxId = 9606,
        extraEdgeAttrs = {
            "mppi_evidences": (1, ";")},
        extraNodeAttrsA = {},
        extraNodeAttrsB = {})
}

'''
Transcriptional regulatory interactions.
'''
transcription = {
    'abs': input_formats.ReadSettings(name="ABS", 
                separator = None, nameColA = 0,
                nameColB = 1, nameTypeA = "genesymbol", nameTypeB="embl_id",
                typeA = "protein", typeB = "protein", 
                isDirected = True, 
                sign = False,
                ncbiTaxId = 9606,
                inFile = 'get_abs', 
                interactionType = 'TF',
                references = False, header = False,
                extraEdgeAttrs = {},
                extraNodeAttrsA = {},
                extraNodeAttrsB = {}),
    'encode_dist': input_formats.ReadSettings(name = "ENCODE_distal", 
                separator = None, nameColA = 0,
                nameColB = 2, nameTypeA = "genesymbol", nameTypeB = "genesymbol",
                typeA = "protein", typeB = "protein", 
                isDirected = True, 
                sign = False,
                ncbiTaxId = 9606,
                inFile = 'http://encodenets.gersteinlab.org/enets3.Distal.txt', 
                interactionType = 'TF',
                references = False, header = False,
                extraEdgeAttrs = {},
                extraNodeAttrsA = {},
                extraNodeAttrsB = {}),
    'encode_prox': input_formats.ReadSettings(name = "ENCODE_proximal", 
                separator = None, nameColA = 0,
                nameColB = 2, nameTypeA = "genesymbol", nameTypeB = "genesymbol",
                typeA = "protein", typeB = "protein", 
                isDirected = True, 
                sign = False,
                ncbiTaxId = 9606,
                inFile = \
                    'http://encodenets.gersteinlab.org/enets2.Proximal_filtered.txt', 
                interactionType = 'TF',
                references = False, header = False,
                extraEdgeAttrs = {},
                extraNodeAttrsA = {},
                extraNodeAttrsB = {}),
    'pazar': input_formats.ReadSettings(name = "PAZAR", 
                separator = None, nameColA = 0,
                nameColB = 1, nameTypeA = "enst", nameTypeB = "ensg",
                typeA = "protein", typeB = "protein", 
                isDirected = True, 
                sign = False,
                ncbiTaxId = 9606,
                inFile = 'get_pazar', 
                interactionType = 'TF',
                references = 2, header = False,
                extraEdgeAttrs = {},
                extraNodeAttrsA = {},
                extraNodeAttrsB = {}),
    'htri': input_formats.ReadSettings(name = "HTRI", 
                separator = None, nameColA = 0,
                nameColB = 1, nameTypeA = "entrez", nameTypeB = "entrez",
                typeA = "protein", typeB = "protein", 
                isDirected = True, 
                sign = False,
                ncbiTaxId = 9606,
                inFile = 'get_htri', 
                interactionType = 'TF',
                references = 2, header = False,
                extraEdgeAttrs = {},
                extraNodeAttrsA = {},
                extraNodeAttrsB = {}),
    'oreganno': input_formats.ReadSettings(name = "ORegAnno", 
                separator = None, nameColA = 0, 
                nameColB = 1, nameTypeA = "genesymbol", nameTypeB = "genesymbol",
                typeA = "protein", typeB = "protein", 
                isDirected = True, 
                sign = False,
                ncbiTaxId = 9606,
                inFile = 'get_oreganno', 
                interactionType = 'TF',
                references = 2, header = False,
                extraEdgeAttrs = {},
                extraNodeAttrsA = {},
                extraNodeAttrsB = {})
}

'''
Old transctiptional regulation input formats.
Should not be used.
'''
transcription_deprecated = {
    'oreganno_old': input_formats.ReadSettings(name = "ORegAnno", 
                separator = None, nameColA = 0, 
                nameColB = 1, nameTypeA = "genesymbol", nameTypeB = "genesymbol",
                typeA = "protein", typeB = "protein", 
                isDirected = True, 
                sign = False,
                ncbiTaxId = 9606,
                inFile = 'get_oreganno_old', 
                interactionType = 'TF',
                references = 2, header = False,
                extraEdgeAttrs = {},
                extraNodeAttrsA = {},
                extraNodeAttrsB = {})
}

'''
Manually curated negative interactions, i.e. pairs of
proteins prooved in experiments to not interact with
each other.
'''
negative = {
    'negatome': input_formats.ReadSettings(name = "Negatome", 
        separator = "\t", nameColA = 0, nameColB = 1,
        nameTypeA = "uniprot", nameTypeB = "uniprot",
        typeA = "protein", typeB = "protein", isDirected = 0, 
        inFile = 'negatome_pairs', ncbiTaxId = 9606,
        extraEdgeAttrs = {
            "references": (2, ';'),
            "negatome_methods": (3, ';')
            },
        extraNodeAttrsA = {},
        extraNodeAttrsB = {})
}

biocarta = input_formats.ReadSettings(name="BioCarta", separator=";", nameColA=0, nameColB=2,
                nameTypeA="entrez", nameTypeB="entrez",
                typeA="protein", typeB="protein", isDirected=1, 
                inFile=os.path.join(ROOT, 'data', 'biocarta-pid.csv'),
                extraEdgeAttrs={},
                extraNodeAttrsA={
                    "biocarta_pathways": (4, ",")},
                extraNodeAttrsB={
                    "biocarta_pathways": (4, ",")})

nci_pid = input_formats.ReadSettings(name="NCI-PID", separator=";", nameColA=0, nameColB=1,
                nameTypeA="uniprot", nameTypeB="uniprot",
                typeA="protein", typeB="protein", isDirected=1, 
                inFile=os.path.join(ROOT, 'data', 'nci-pid.csv'),
                extraEdgeAttrs={},
                extraNodeAttrsA={
                    "nci_pid_pathways": (2, ",")},
                extraNodeAttrsB={
                    "nci_pid_pathways": (2, ",")})

reactome = input_formats.ReadSettings(name="Reactome", separator=";", nameColA=0, nameColB=1,
                nameTypeA="uniprot", nameTypeB="uniprot",
                typeA="protein", typeB="protein", isDirected=1, 
                inFile=os.path.join(ROOT, 'data', 'reactome-pid.csv'),
                extraEdgeAttrs={},
                extraNodeAttrsA={
                    "reactome_pathways": (2, ",")},
                extraNodeAttrsB={
                    "reactome_pathways": (2, ",")})

gdsc_comp_target = input_formats.ReadSettings(name="GDSC", 
                separator=";", nameColA=1, nameColB=0,
                nameTypeA="pubchem", nameTypeB="genesymbol",
                typeA="drug", typeB="protein", isDirected=1, 
                inFile="gdsc.sif",
                extraEdgeAttrs={},
                extraNodeAttrsA={
                    "gene_name": 2},
                extraNodeAttrsB={})

gdsc_lst = input_formats.ReadList(name="GDSC", separator=";", nameCol=0,
                nameType="genesymbol", typ="protein",
                inFile=os.path.join(ROOT, 'data', 'gdsc.sif'),
                extraAttrs={'drugs': 2})

gdsc_lst = input_formats.ReadList(name="atg", separator=";", nameCol=0,
                nameType="genesymbol", typ="protein",
                inFile=os.path.join(ROOT, 'data', 'autophagy.list'),
                extraAttrs={'drugs': 2})

cgc = input_formats.ReadList(name = "CancerGeneCensus", nameCol = 2,
                nameType = "entrez", typ = "protein",
                inFile = 'get_cgc',
                extraAttrs = {})

intogen_cancer = input_formats.ReadList(name = "IntOGen", separator = "\t", nameCol=1,
                nameType = "genesymbol", typ = "protein",
                inFile = 'intogen_cancerdrivers.tsv',
                extraAttrs={})

reactome_modifications = {
    'phosphorylated': ('phosphorylation', 'X'),
    'glycosylated': ('glycosylation', 'X'),
    'acetylated': ('acetylated', 'X'),
    'prenylated': ('prenylation', 'X'),
    'ubiquitinated': ('ubiquitination', 'X'),
    'myristoylated': ('myristoylation', 'X'),
    'hydroxylated': ('hydroxylation', 'X'),
    'acetylated residue': ('acetylation', 'X'),
    'palmitoylated residue': ('palmitoylation', 'X'),
    'sumoylated lysine': ('sumoylation', 'K'),
    'O-palmitoyl-L-threonine': ('palmitoylation', 'T'),
    'acetylated L-serine': ('acetylation', 'S'),
    'glycosylated residue': ('glycosylation', 'X'),
    'methylated L-arginine': ('methylation', 'R'),
    'ubiquitination': ('ubiquitination', 'X'),
    'phosphorylated residue': ('phosphorylation', 'X'),
    'O-phospho-L-threonine': ('phosphorylation', 'T'),
    'O-glycosyl-L-threonine': ('glycosylation', 'T'),
    'methylated L-lysine': ('methylation', 'K'),
    'myristoylated residue': ('myristoylation', 'X'),
    'N-myristoyl-glycine': ('myristoylation', 'G'),
    'O-palmitoyl-L-serine': ('palmitoylation', 'S'),
    'palmitoylated residue [residue=N]': ('palmitoylation', 'X'),
    'N-acetylated L-lysine': ('acetylation', 'K'),
    'O-glycosyl-L-serine': ('glycosylation', 'S'),
    'N-acetyl-L-methionine': ('acetylation', 'M'),
    'ubiquitinylated lysine': ('ubiquitination', 'K'),
    'S-farnesyl-L-cysteine': ('farnesylation', 'C'),
    'S-phospho-L-cysteine': ('phosphorylation', 'C'),
    'hydroxylated proline': ('hydroxylation', 'P'),
    'palmitoylated residue [residue=Y]': ('palmitoylation', 'Y'),
    'O4\'-phospho-L-tyrosine': ('phosphorylation', 'Y'),
    'O-phospho-L-serine': ('phosphorylation', 'S'),
    'O-phospho-L-threonine': ('phosphorylation', 'T'),
    '(2S,4R)-4-hydroxyproline': ('hydroxylation', 'P'),
    '(2S,3S)-3-hydroxyproline': ('hydroxylation', 'P'),
    'O5-galactosyl-L-hydroxylysine': ('galactosytlation', 'K'),
    '(2S,5R)-5-hydroxylysine': ('hydroxylation', 'K'),
    'O5-glucosylgalactosyl-L-hydroxylysine': ('glucosylgalactosylation', 'K'),
    'N4-glycosyl-L-asparagine': ('glycosylation', 'N'),
    'S-palmitoyl-L-cysteine': ('palmitoylation', 'C'),
    'N-myristoylglycine': ('myristoylation', 'G'),
    'half cystine': ('half cystine', 'C'),
    'S-geranylgeranyl-L-cysteine': ('geranylation', 'C'),
    'N6-acetyl-L-lysine': ('acetylation', 'K'),
    'N\'-formyl-L-kynurenine': ('formylation', 'W'),
    'Oxohistidine (from histidine)': ('oxo', 'H'),
    'dihydroxyphenylalanine (Phe)': ('dihydroxylation', 'F'),
    'glutamyl semialdehyde (Pro)': ('glutamylation', 'P'),
    'monohydroxylated asparagine': ('hydroxylation', 'N'),
    'monohydroxylated proline': ('hydroxylation', 'P'),
    'ubiquitinylated lysine': ('ubiquitination', 'K'),
    'N6,N6,N6-trimethyl-L-lysine': ('trimethylation', 'K'),
    'N6,N6-dimethyl-L-lysine': ('dimethylation', 'K'),
    'N6-myristoyl-L-lysine': ('myristoylation', 'K'),
    'sumoylated lysine': ('sumoylation', 'K'),
    'N6-methyl-L-lysine': ('methylation', 'K'),
    'omega-N-methyl-L-arginine': ('methylation', 'R'),
    'asymmetric dimethyl-L-arginine': ('dimethylation', 'R'),
    'symmetric dimethyl-L-arginine': ('dimethylation', 'R'),
    'O4\'-glucosyl-L-tyrosine': ('glycosylation', 'Y'),
    'N6-biotinyl-L-lysine': ('biotinylation', 'K'),
    'O-acetyl-L-serine': ('acetylation', 'S'),
    '1-thioglycine': ('thiolation', 'G'),
    'S-acetyl-L-cysteine': ('acetylation', 'C'),
    'N-acetyl-L-alanine': ('acetylation', 'A'),
    'S-methyl-L-cysteine': ('methylation', 'C'),
    'L-gamma-carboxyglutamic acid': ('carboxylation', 'Z'),
    '(2S,3R)-3-hydroxyaspartic acid': ('hydroxylation', 'D'),
    'O-fucosyl-L-threonine': ('fucosylation', 'T'),
    'O-fucosyl-L-serine': ('fucosylation', 'S'),
    'O-palmitoleyl-L-serine': ('palmitoylation', 'S'),
    '1-thioglycine (C-terminal)': ('thiolation', 'G'),
    'neddylated lysine': ('neddylation', 'K'),
    'N-palmitoyl-L-cysteine': ('palmitoylation', 'C'),
    'S-farnesyl-L-cysteine': ('farnesylation', 'C')
}

categories = {
    'Vidal HI-III': 'i',
    'CancerCellMap': 'p',
    'InnateDB': 'i',
    'SPIKE': 'p',
    'LMPID': 'm',
    'DIP': 'i',
    'HPRD': 'i',
    'HPRD-phos': 'm',
    'PDZBase': 'p',
    'dbPTM': 'm',
    'MatrixDB': 'i',
    'DOMINO': 'm',
    'Signor': 'p',
    'Macrophage': 'p',
    'NetPath': 'r',
    'ELM': 'm',
    'SignaLink2': 'p',
    'SignaLink3': 'p',
    'NRF2ome': 'p',
    'DEPOD': 'm',
    'phosphoELM': 'm',
    'MPPI': 'i',
    'Guide2Pharma': 'p',
    'TRIP': 'p',
    'AlzPathway': 'r',
    'PhosphoSite': 'm',
    'CA1': 'p',
    'NCI-PID': 'r',
    'DeathDomain': 'p',
    'ARN': 'p',
    'BioGRID': 'i',
    'IntAct': 'i',
    'Reactome': 'r',
    'ACSN': 'r',
    'WikiPathways': 'r',
    'PANTHER': 'r',
    'ABS': 't',
    'ENCODE_distal': 't',
    'PAZAR': 't',
    'ENCODE_proximal': 't',
    'ORegAnno': 't',
    'HTRI': 't'
}

p = set([])
i = set([])
r = set([])
m = set([])
t = set([])

for db, c in iteritems(categories):
    locals()[c].add(db)

catnames = {
    'm': 'Enzyme-substrate',
    'p': 'Activity flow',
    'i': 'Interaction',
    'r': 'Process description',
    't': 'Transcription'
}

pathway_resources = p
interaction_resources = i
ptm_resources = m
reaction_resources = r
transctiption_resources = t
