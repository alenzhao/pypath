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

from future.utils import iteritems
from past.builtins import xrange, range, reduce

import os
import sys
import math
import random
import textwrap
import hashlib

__all__ = [
    'ROOT', 'aacodes', 'aaletters', 'simpleTypes', 'numTypes', 'uniqList',
    'addToList', 'addToSet', 'gen_session_id', 'sorensen_index',
    'simpson_index', 'simpson_index_counts', 'jaccard_index', 'console', 'wcl',
    'flatList', 'charTypes', 'delEmpty', '__version__', 'get_args',
    'something', 'rotate', 'cleanDict', 'igraph_graphics_attrs', 'md5',
    'mod_keywords', 'Namespace', 'fun', 'taxids', 'taxa', 'phosphoelm_taxids',
    'dbptm_taxids'
]

# get the location
ROOT = os.path.abspath(os.path.dirname(__file__))


def _get_version():
    with open(os.path.join(ROOT, '__version__'), 'r') as v:
        return tuple([int(i) for i in v.read().strip().split('.')])


_MAJOR, _MINOR, _MICRO = _get_version()
__version__ = '%d.%d.%d' % (_MAJOR, _MINOR, _MICRO)
__release__ = '%d.%d' % (_MAJOR, _MINOR)

default_name_type = {
    "protein": "uniprot",
    "mirna": "mirbase",
    "lncrna": "lncrnaname",
    "drug": "pubchem"
}

aacodes = {
    'A': 'ALA',
    'G': 'GLY',
    'M': 'MET',
    'W': 'TRP',
    'Y': 'TYR',
    'R': 'ARG',
    'C': 'CYS',
    'S': 'SER',
    'V': 'VAL',
    'I': 'ILE',
    'L': 'LEU',
    'P': 'PRO',
    'H': 'HIS',
    'T': 'THR',
    'E': 'GLU',
    'Q': 'GLN',
    'Z': 'GLX',
    'D': 'ASP',
    'N': 'ASN',
    'B': 'ASX',
    'K': 'LYS',
    'F': 'PHE',
    'J': 'XLE',
    'X': 'XAA'
}

aanames = {
    'alanine': 'A',
    'arginine': 'R',
    'asparagine': 'N',
    'aspartic acid': 'D',
    'cysteine': 'C',
    'glutamine': 'Q',
    'glutamic acid': 'E',
    'glycine': 'G',
    'histidine': 'H',
    'isoleucine': 'I',
    'leucine': 'L',
    'lysine': 'K',
    'methionine': 'M',
    'phenylalanine': 'F',
    'proline': 'P',
    'serine': 'S',
    'threonine': 'T',
    'tryptophan': 'W',
    'tyrosine': 'Y',
    'valine': 'V'
}

mod_keywords = {
    'Reactome':
    [('phosphopantetheinylation', ['phosphopantet']),
     ('phosphorylation', ['phospho']),
     ('acetylneuraminylation', ['acetylneuraminyl']),
     ('acetylation', ['acetyl']), ('farnesylation', ['farnesyl']),
     ('palmitoylation', ['palmito']), ('methylation', ['methyl']),
     ('tetradecanoylation', ['tetradecanoyl']),
     ('decanoylation', ['decanoyl']), ('palmitoleylation', ['palmytoleil']),
     ('formylation', ['formyl']), ('ubiquitination', ['ubiquitin']),
     ('galactosylation', ['galactos']), ('glutamylation', ['glutamyl']),
     ('fucosylation', ['fucosyl']), ('myristoylation', ['myristoyl']),
     ('carboxylation', ['carboxyl']), ('biotinylation', ['biotinyl']),
     ('glycosylation', ['glycosyl']), ('octanoylation', ['octanoyl']),
     ('glycylation', ['glycyl']), ('hydroxylation', ['hydroxy']),
     ('sulfhydration', ['persulfid']), ('thiolation', ['thio']),
     ('amidation', ['amide']), ('selenation', ['seleno']),
     ('glucosylation', ['glucosyl']), ('neddylation', ['neddyl']),
     ('sumoylation', ['sumoyl']), ('prenylation', ['prenyl'])],
    'ACSN': [('phosphorylation', ['phospho']), ('glycylation', ['glycyl']),
             ('ubiquitination', ['ubiquitin']), ('acetylation', ['acetyl']),
             ('myristoylation', ['myristoyl']), ('prenylation', ['prenyl']),
             ('hydroxylation', ['hydroxy'])],
    'WikiPathways': [],
    'NetPath': [('phosphorylation', ['phospho']), ('glycylation', ['glycyl']),
                ('ubiquitination', ['ubiquitin']),
                ('acetylation', ['acetyl'])],
    'PANTHER': [('phosphorylation', ['phospho']), ('acetylation', ['acetyl'])],
    'NCI-PID':
    [('phosphorylation', ['phospho']), ('methylation', ['methyl']),
     ('farnesylation', ['farnesyl']), ('palmitoylation', ['palmito']),
     ('myristoylation', ['myristoyl']), ('glycylation', ['glycyl']),
     ('ubiquitination', ['ubiquitin']), ('acetylation', ['acetyl']),
     ('glycosylation', ['glycosyl']), ('geranylation', ['geranyl']),
     ('hydroxylation', ['hydroxy'])],
    'KEGG':
    [('phosphorylation', ['hospho']), ('methylation', ['methyl']),
     ('ubiquitination', ['ubiquitin']), ('acetylation', ['acetyl']),
     ('hydroxylation', ['hydroxy']), ('carboxyethylation', ['carboxyethyl']),
     ('ribosylation', ['ribosyl']), ('nitrosylation', ['nitrosyl']),
     ('sulfoylation', ['ulfo']), ('biotinylation', ['biotinyl']),
     ('malonylation', ['malonyl']), ('glutarylation', ['lutaryl'])]
}

if 'long' not in __builtins__:
    long = int

if 'unicode' not in __builtins__:
    unicode = str

aaletters = dict(zip(aacodes.values(), aacodes.keys()))

simpleTypes = set([int, long, float, str, unicode, bytes])

numTypes = set([int, long, float])

charTypes = set([str, unicode, bytes])


def uniqList(seq):
    """
    Not order preserving
    From http://www.peterbe.com/plog/uniqifiers-benchmark
    """
    return list({}.fromkeys(seq).keys())


def uniqList1(seq):
    """
    Not order preserving
    From http://www.peterbe.com/plog/uniqifiers-benchmark
    """
    return list(set(seq))


def uniqList2(seq):
    """
    Not order preserving
    From http://www.peterbe.com/plog/uniqifiers-benchmark
    """
    keys = {}
    for e in seq:
        keys[e] = 1
    return list(keys.keys())


def flatList(lst):
    return [it for sl in lst for it in sl]


def delEmpty(lst):
    return [i for i in lst if len(i) > 0]


def uniqOrdList(seq, idfun=None):
    """
    Order preserving
    From http://www.peterbe.com/plog/uniqifiers-benchmark
    """
    if idfun is None:

        def idfun(x):
            return x

    seen = {}
    result = []
    for item in seq:
        marker = idfun(item)
        if marker in seen:
            continue
        seen[marker] = 1
        result.append(item)
    return result


def addToList(lst, toadd):
    if type(lst) is not list:
        if type(lst) in simpleTypes:
            lst = [lst]
        else:
            lst = list(lst)
    if toadd is None:
        return lst
    if type(toadd) in simpleTypes:
        lst.append(toadd)
    else:
        if type(toadd) is not list:
            toadd = list(toadd)
        lst.extend(toadd)
    if None in lst:
        lst.remove(None)
    return uniqList(lst)


def addToSet(st, toadd):
    if type(toadd) in simpleTypes:
        st.add(toadd)
    if type(toadd) is list:
        toadd = set(toadd)
    if type(toadd) is set:
        st.update(toadd)
    return st


def something(anything):
    return not (anything is None or
                (type(anything) in [list, set, dict, str, unicode] and
                 len(anything) == 0))


def gen_session_id(length=5):
    abc = '0123456789abcdefghijklmnopqrstuvwxyz'
    return ''.join(random.choice(abc) for i in range(length))


def simpson_index(a, b):
    a = set(a)
    b = set(b)
    ab = a & b
    return float(len(ab)) / float(min(len(a), len(b)))


def simpson_index_counts(a, b, c):
    return float(c) / float(min(a, b)) if min(a, b) > 0 else 0.0


def sorensen_index(a, b):
    a = set(a)
    b = set(b)
    ab = a & b
    return float(len(ab)) / float(len(a) + len(b))


def jaccard_index(a, b):
    a = set(a)
    b = set(b)
    ab = a & b
    return float(len(ab)) / float(len(a | b))


def console(message):
    message = '\n\t'.join(textwrap.wrap(message, 80))
    sys.stdout.write(('\n\t' + message).ljust(80))
    sys.stdout.write('\n')
    sys.stdout.flush()


def wcl(f):
    toClose = type(f) is file
    f = f if type(f) is file else open(f, 'r')
    for i, l in enumerate(f):
        pass
    if toClose:
        f.seek(0)
    else:
        f.close()
    return i + 1


def get_args(loc_dict, remove=set([])):
    if type(remove) not in [set, list]:
        remove = set([remove])
    if type(remove) is list:
        remove = set(remove)
    remove.add('self')
    remove.add('kwargs')
    args = dict((k, v) for k, v in iteritems(loc_dict) if k not in remove)
    if 'kwargs' in loc_dict:
        args = dict(args.items() + loc_dict['kwargs'].items())
    return args


def rotate(point, angle, center=(0.0, 0.0)):
    """
    from http://stackoverflow.com/a/20024348/854988
    Rotates a point around center. Angle is in degrees.
    Rotation is counter-clockwise
    """
    angle = math.radians(angle)
    temp_point = point[0] - center[0], point[1] - center[1]
    temp_point = (
        temp_point[0] * math.cos(angle) - temp_point[1] * math.sin(angle),
        temp_point[0] * math.sin(angle) + temp_point[1] * math.cos(angle))
    temp_point = temp_point[0] + center[0], temp_point[1] + center[1]
    return temp_point


def cleanDict(dct):
    """
    Removes ``None`` values from dict and casts everything else to ``str``.
    """
    toDel = []
    for k, v in iteritems(dct):
        if v is None:
            toDel.append(k)
        else:
            dct[k] = str(v)
    for k in toDel:
        del dct[k]
    return dct


def md5(value):
    """
    Returns the ms5sum of ``value`` as string.
    """
    try:
        string = str(value).encode('ascii')
    except:
        string = str(value).encode('ascii')
    return hashlib.md5(string).hexdigest()


igraph_graphics_attrs = {
    'vertex': [
        'size', ' color', 'frame_color', 'frame_width', 'shape', 'label',
        'label_dist', 'label_color', 'label_size', 'label_angle'
    ],
    'edge': ['curved', 'color', 'width', 'arrow_size', 'arrow_width']
}


def merge_dicts(d1, d2):
    """
    Merges dicts recursively
    """
    for k2, v2 in iteritems(d2):
        t = type(v2)
        if k2 not in d1:
            d1[k2] = v2
        elif t is dict:
            d1[k2] = merge_dicts(d1[k2], v2)
        elif t is list:
            d1[k2].extend(v2)
        elif t is set:
            d1[k2].update(v2)
    return d1


def dict_set_path(d, path):
    """
    In dict of dicts ``d`` looks up the keys following ``path``,
    creates new subdicts and keys if those do not exist yet,
    and sets/merges the leaf element according to simple heuristic.
    """
    val = path[-1]
    key = path[-2]
    subd = d
    for k in path[:-2]:
        if type(subd) is dict:
            if k in subd:
                subd = subd[k]
            else:
                subd[k] = {}
                subd = subd[k]
        else:
            return d
    if key not in subd:
        subd[key] = val
    elif type(val) is dict and type(subd[key]) is dict:
        subd[key].update(val)
    elif type(subd[key]) is list:
        if type(val) is list:
            subd[key].extend(val)
        else:
            subd[key].append(val)
    elif type(subd[key]) is set:
        if type(val) is set:
            subd[key].update(val)
        else:
            subd[key].add(val)
    return d


def dict_diff(d1, d2):
    ldiff = {}
    rdiff = {}
    keys = set(d1.keys()) & set(d2.keys())
    for k in keys:
        if type(d1[k]) is dict and type(d2[k]) is dict:
            ldiff[k], rdiff[k] = dict_diff(d1[k], d2[k])
        elif type(d1[k]) is set and type(d2[k]) is set:
            ldiff[k], rdiff[k] = (d1[k] - d2[k], d2[k] - d1[k])
    return ldiff, rdiff


def dict_sym_diff(d1, d2):
    diff = {}
    keys = set(d1.keys()) & set(d2.keys())
    for k in keys:
        if type(d1[k]) is dict and type(d2[k]) is dict:
            diff[k] = dict_sym_diff(d1[k], d2[k])
        elif type(d1[k]) is set and type(d2[k]) is set:
            diff[k] = d1[k] ^ d2[k]
    return diff


class Namespace(object):
    pass


def fun():
    print(__name__)
    print(__name__ in globals())
    for n in __name__.split('.'):
        print(n, n in globals())
    return __name__

taxids = {
    9606: 'human',
    10090: 'mouse',
    10116: 'rat',
    9031: 'chicken',
    9913: 'cow',
    9986: 'rabbit',
}

taxa = dict(map(lambda i: (i[1], i[0]), taxids.items()))

phosphoelm_taxids = {
    9606: 'Homo sapiens',
    10090: 'Mus musculus',
    9913: 'Bos taurus',
    9986: 'Oryctolagus cuniculus',
    9615: 'Canis familiaris',
    10029: 'Cricetulus griseus',
    9267: 'Didelphis virginiana',
    9031: 'Gallus gallus',
    10036: 'Mesocricetus auratus',
    9940: 'Ovis aries',
    10116: 'Rattus norvegicus',
    9823: 'Sus scrofa',
    8355: 'Xenopus laevis'
}

dbptm_taxids = {
    9606: 'HUMAN',
    10090: 'MOUSE',
    7227: 'DROME',
    10116: 'RAT',
    559292: 'YEAST',
    284812: 'SCHPO',
    4081: 'SOLLC',
    3702: 'ARATH',
    9940: 'SHEEP',
    9913: 'BOVIN',
    9925: 'CAPHI',
    44689: 'DICDI',
    4577: 'MAIZE',
    9823: 'PIG',
    9615: 'CANLF',
    6239: 'CAEEL',
    8455: 'XENLA',
    83333: 'ECOLI',
    1891767: 'SV40'
}
