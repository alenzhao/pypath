#!/usr/bin/env python2
# -*- coding: utf-8 -*-

#
#  This file is part of the `bioigraph` python module
#
#  Copyright (c) 2014-2015 - EMBL-EBI
#
#  File author(s): Dénes Türei (denes@ebi.ac.uk)
#
#  This module (bioigraph.gdsc) is not available for public,
#  please use only within EBI.
#
#  Website: http://www.ebi.ac.uk/~denes
#

# external modules:
import os
import sys
import re

# from this package:
import intera
import seq
import progress
from dataio import curl

def read_mutations(infile = None, sample_col = 'COSMIC_ID', attributes = []):
    # the file processed by Luz
    # original data:
    # /nfs/research2/saezrodriguez/jsr-gdsc/RAW/Genomic/
    # All_variants_cell-lines_22102014.xlsx
    # original location: 
    # /nfs/research2/saezrodriguez/jsr-gdsc/PROCESSED/Genomic/
    # All_variants_cell-lines_22102014_indelMod_ANNOVfun.txt
    result = {}
    infile = '/home/denes/Dokumentumok/pw/data/All_variants_cell-'\
        'lines_22102014_indelMod_ANNOVfun.txt' if infile is None else infile
    size = os.path.getsize(infile)
    remut = re.compile(r'([A-Z])([0-9]*)([A-Z])')
    prg = progress.Progress(size, 'Reading mutations', 7)
    with open(infile, 'r') as f:
        hdr = f.readline().split('\t')
        cols = {}
        for i, col in enumerate(hdr):
            cols[col] = i
        for l in f:
            prg.step(len(l))
            l = l.split('\t')
            if not l[5].startswith('syn'):
                uniprot = l[11]
                mutation = remut.findall(l[12])
                if len(mutation) != 0:
                    mutation = mutation[0]
                    this_attrs = {}
                    for attr in attributes:
                        if attr in cols:
                            this_attrs[attr] = l[cols[attr]].strip()
                    smpl = 0 if sample_col not in cols else \
                        int(l[cols[sample_col]].strip())
                    ori = intera.Residue(mutation[1], mutation[0], uniprot)
                    mtd = intera.Residue(mutation[1], mutation[2], uniprot)
                    mut = intera.Mutation(ori, mtd, smpl, this_attrs)
                    if uniprot not in result:
                        result[uniprot] = []
                    result[uniprot].append(mut)
    prg.terminate()
    return result

def read_transcriptomics(infile = 'normalized', datadir = None):
    # this fun reads the raw transcriptomics data
    # original data:
    # /nfs/research2/saezrodriguez/jsr-gdsc/RAW/Transcriptomic/01_RMAproc_basal_exp.csv
    # returns a ?
    datadir = datadir if datadir is not None else '/home/denes/Dokumentumok/pw/data'
    files = {
        'raw': '01_RMAproc_basal_exp.csv',
        'normalized': '02_d_norm_basal_exp.csv',
        'tissue': '03_d_norm_tissue_centered_basal_exp.csv'
    }
    infile = '01_RMAproc_basal_exp.csv' \
        if infile is None else infile
    infile = infile if infile not in files else files[infile]
    infile = os.path.join(datadir, infile)
    result = {}
    cols = {}
    size = os.path.getsize(infile)
    sys.stdout.write('\t:: Reading transcriptomics data from\n'\
        '\t\t%s\n'%infile)
    sys.stdout.flush()
    prg = progress.Progress(size, 'Reading transcriptomics data', 7)
    with open(infile, 'r') as f:
        # cosmic ids as integers:
        try:
            hdr = [int(x) for x in f.readline().strip().split(',')[1:]]
        except:
            f.seek(0)
            print f.readline().split(',')
        for l in f:
            prg.step(len(l))
            l = l.split(',')
            result[l[0]] = dict(zip(hdr, [float(x) for x in l[1:]]))
    prg.terminate()
    return result