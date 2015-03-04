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

#http://www.ijbs.com/v06p0051.htm
#http://www.nature.com/cddis/journal/v4/n8/full/cddis2013292a.html

descriptions = {
    'DeathDomain': {
        'urls': {
            'articles': [
                'http://nar.oxfordjournals.org/content/40/D1/D331'
            ],
            'webpages': [
                'http://deathdomain.org/'
            ]
        },
        'files': {
            'articles': [
                'DeathDomain_Kwon2011.pdf'
            ],
            'data': {
                'raw': [
                    'deathdomain.tsv'
                ],
                'processed': [
                    'deathdomain.sif'
                ]
            }
        },
        'taxons': [
            'human'
        ],
        'size': {
            'nodes': 99,
            'edges': 175
        },
        'identifiers': [
            'GeneSymbol'
        ],
        'descriptions': [
            """
            The PubMed database was used as the primary source for collecting information and constructing the DD database. After finding synonyms for each of the 99 DD superfamily proteins using UniProtKB and Entrez Gene, we obtained a list of articles using each name of the proteins and its synonyms on a PubMed search, and we selected the articles that contained evidence for physical binding among the proteins denoted. We also manually screened information that was in other databases, such as DIP, IntAct, MINT, STRING and Entrez Gene. All of the 295 articles used for database construction are listed on our database website.
            """
        ],
        'notes': [
            """
            Detailful dataset with many references. Sadly the data can be extracted only by parsing HTML. It doesn't mean more difficulty than parsing XML formats, just it is not intended to use for this purpose.
            """
        ]
    },
    'TRIP': {
        'urls': {
            'articles': [
                'http://www.plosone.org/article/info:doi/10.1371/journal.pone.0047165',
                'http://nar.oxfordjournals.org/content/39/suppl_1/D356.full'
            ],
            'webpages': [
                'http://www.trpchannel.org'
            ]
        },
        'files': {
            'articles': [
                'TRIP_Shin2012.pdf'
            ],
            'data': {
                'raw': [],
                'processed': [
                    'trip.sif'
                ]
            }
        },
        'taxons': [
            'mammals'
        ],
        'identifiers': [
            'GeneSymbol'
        ],
        'descriptions': [
            """
            The literature on TRP channel PPIs found in the PubMed database serve as the primary information source for constructing the TRIP Database. First, a list of synonyms for the term ‘TRP channels’ was constructed from UniprotKB, Entrez Gene, membrane protein databases (Supplementary Table S2) and published review papers for nomenclature. Second, using these synonyms, a list of articles was obtained through a PubMed search. Third, salient articles were collected through a survey of PubMed abstracts and subsequently by search of full-text papers. Finally, we selected articles that contain evidence for physical binding among the proteins denoted. To prevent omission of relevant papers, we manually screened information in other databases, such as DIP, IntAct, MINT, STRING, BioGRID, Entrez Gene, IUPHAR-DB and ISI Web of Knowledge (from Thomson Reuters). All 277 articles used for database construction are listed in our database website.
            """
        ],
        'notes': [
            """
            Good manually curated dataset focusing on TRP channel proteins, with ~800 binary interactions. The table is very detailed, and easy to use. However, we can not avoid to loose dozens of interactions in mapping, because of the non standard protein names, with greek letters and only human understandable formulas.
            """
        ]
    },
    'Cui2007': {
        'urls': {
            'articles': [
                'http://msb.embopress.org/content/3/1/152'
            ],
            'webpages': []
        },
        'files': {
            'articles': [
                'Cui2007.pdf'
            ],
            'data': {
                'raw': [
                    'cui-network.xls',
                ],
                'processed': [
                    'cui.sif'
                ]
            }
        },
        'identifiers': [
            'EntrezGene'
        ],
        'size': {
            'edges': 4249,
            'nodes': 1528
        },
        'taxons': [
            'human'
        ],
        'descriptions': [
            """
            To build up the human signaling network, we manually curated the signaling molecules (most of them are proteins) and the interactions between these molecules from the most comprehensive signaling pathway database, BioCarta (http://www.biocarta.com/). The pathways in the database are illustrated as diagrams. We manually recorded the names, functions, cellular locations, biochemical classifications and the regulatory (including activating and inhibitory) and interaction relations of the signaling molecules for each signaling pathway. To ensure the accuracy of the curation, all the data have been crosschecked four times by different researchers. After combining the curated information with another literature‐mined signaling network that contains ∼500 signaling molecules (Ma'ayan et al, 2005)[this is the CA1!!!], we obtained a signaling network containing ∼1100 proteins (Awan et al, 2007). We further extended this network by extracting and adding the signaling molecules and their relations from the Cancer Cell Map (http://cancer.cellmap.org/cellmap/), a database that contains 10 manually curated signaling pathways for cancer. As a result, the network contains 1634 nodes and 5089 links that include 2403 activation links (positive links), 741 inhibitory links (negative links), 1915 physical links (neutral links) and 30 links whose types are unknown (Supplementary Table 9). To our knowledge, this network is the biggest cellular signaling network at present.
            To construct the human cellular signalling network, we manually curated signalling pathways from literature. The signalling data source for our pathways is the BioCarta database (http://www.biocarta.com/genes/allpathways.asp), which, so far, is the most comprehensive database for human cellular signalling pathways. Our curated pathway database recorded gene names and functions, cellular locations of each gene and relationships between genes such as activation, inhibition, translocation, enzyme digestion, gene transcription and translation, signal stimulation and so on. To ensure the accuracy and the consistency of the database, each referenced pathway was cross-checked by different researchers and finally all the documented pathways were checked by one researcher.
            """
        ],
        'notes': [
            """
            Excellent signaling network with good topology for all those who doesn't mind to use data of unknown origin. Supposedly a manually curated network, but data files doesn't include article references. Merging CA1 network with CancerCellMap and BioCarta (also without references) makes the origin of the data untraceable.
            """
        ]
    },
    'BioCarta': {
        'urls': {
            'webpages': [
                'http://www.biocarta.com/'
            ],
            'articles': []
        },
        'taxons': [
            'human'
        ],
        'descriptions': [
            """
            Community built pathway database based on expert curation.
            """
        ],
        'notes': [
            """
            This resource includes a huge number of pathways, each curated by experts form a few reviews. The data is not available for download from the original webpage, only from second hand, for example from NCI-PID, in NCI-XML format. However, these files doesn't contain any references, which makes problematic the use of the BioCarta dataset. Also, some pathways are reviewed long time ago, possibly outdated.
            """
        ]
    },
    'TLR': {
        'urls': {
            'articles': [
                'http://msb.embopress.org/content/2/1/2006.0015.long'
            ]
        }
    },
    'CA1': {
        'urls': {
            'articles': [
                'http://www.sciencemag.org/content/309/5737/1078.full'
            ]
        },
        'taxons': [
            'human',
            'mouse'
        ],
        'descriptions': [
            """
            We used published research literature to identify the key components of signaling pathways and cellular machines, and their binary interactions. Most components (~80%) have been described in hippocampal neurons or related neuronal cells. Other components are from other cells, but are included because they are key components in processes known to occur in hippocampal neurons, such as translation. We then established that these interactions were both direct and functionally relevant. All of the connections were individually verified by at least one of the authors of this paper by reading the relevant primary paper(s). We developed a system made of 545 components (nodes) and 1259 links (connections). We used arbitrary but consistent rules to sort components into various groups. For instance, transcription factors are considered a as part of the transcriptional machinery, although it may also be equally valid to consider them as the most downstream component of the central signaling network. Similarly the AMPA receptor-channel (AMPAR) is considered part of the ion channels in the electrical response system since its activity is essential to defining the postsynaptic response, although it binds to and is activated by glutamate, and hence can be also considered a ligand gated receptor-channel in the plasma membrane. The links were specified by two criteria: function and biochemical mechanism. Three types of functional links were specified. This follows the rules used for representation of pathways in Science’s STKE (S1). Links may be activating, inhibitory or neutral. Neutral links do not specify directionality between components, and are mostly used to represent scaffolding and anchoring undirected or bidirectional interactions. The biochemical specification includes defining the reactions as non-covalent binding interactions or enzymatic reactions. Within the enzymatic category, reactions were further specified as phosphorylation, dephosphorylation, hydrolysis, etc. These two criteria for specification are independent and were defined for all interactions. For the analyses in this study we only used the functional criteria: activating, inhibitory or neutral specifications. We chose papers that demonstrated direct interactions that were supported by either biochemical or physiological effects of the interactions. From these papers we identified the components and interactions that make up the system we analyzed. During this specification process we did not consider whether these interactions would come together to form higher order organizational units. Each component and interaction was validated by a reference from the primary literature (1202 papers were used). A list of authors who read the papers to validate the components and interactions is provided under authors contributions.
            """
        ],
        'notes': [
            """
            One of the earliest manually curated networks, available in easily accessible tabular format, including UniProt IDs and PubMed references.
            """
        ]
    },
    'CancerCellMap': {
        'urls': {
            'articles': [],
            'webpages': [
                'http://www.pathwaycommons.org/pc-snapshot/current-release/tab_delim_network/by_source/'
            ]
        },
        'descriptions': [
            """
            Manually curated data, unpublished. A team of M.Sc. and Ph.D. biologists at the Institute of Bioinformatics in Bangalore, India read original research papers and hand-entered the pathway data into our database. The quality of the Cancer Cell Map pathways is very high. Half of the pathways were reviewed by experts at Memorial Sloan-Kettering Cancer Center and were found to contain only a few errors, which were subsequently fixed.
            """
        ],
        'notes': [
            """
            One of the first manually curated datasets, now only available from second hand, e.g. from PathwayCommons. Included in many other resources. Contains binary interactions with PubMed references.
            """
        ]
    },
    'HumanSignalingNetwork': {
        'urls':{
            'webpages': [
                'http://www.cancer-systemsbiology.org/datasoftware.htm'
            ],
            'articles': []
        },
        'taxons': [
            'human',
            'mouse',
            'rat'
        ],
        'contains': [
            'Cui2007', 
            'CancerCellMap',
            'Awan2007',
            'NetPath',
            'CA1'
        ],
        'descriptions': [
            """
            Composed from multiple manually curated datasets, and contains own manual cuartion effort. Methods are unclear, and the dataset has not been published in reviewed paper. Based on the CancerCellMap.
            Wang Lab has manually curated human signaling data from literature since 2005. The data sources include BioCarta, CST Signaling pathways, Pathway Interaction database, IHOP, and many review papers. The contents are updated every year. 
            """
        ],
        'notes': [
            """
            This network aims to merge multiple manually curated networks. It's a pity, that a precise description of the sources and methods is missing. Also, the dataset doesn't include references.
            """
        ]
    },
    'Ataxia': {
        'urls':{
            'webpages': [
                'http://franklin.imgen.bcm.tmc.edu/ppi/tables.html'
            ],
            'articles': [
                'http://hmg.oxfordjournals.org/content/20/3/510.long'
            ]
        },
        'taxons': [
            'human'
        ],
        'descriptions': [
            """
            In order to expand the interaction dataset, we added relevant direct protein–protein interactions from currently available human protein–protein interaction networks (Rual et al., 2005; Stelzl et al., 2005). We also searched public databases, including BIND (Bader et al., 2003), DIP (Xenarios et al., 2002), HPRD (Peri et al., 2003), MINT (Zanzoni et al., 2002), and MIPS (Pagel et al., 2005), to identify literature-based binary interactions involving the 54 ataxia-associated baits and the 561 interacting prey proteins. We identified 4796 binary protein–protein interactions for our Y2H baits and prey proteins (Table S4) and incorporated them in the Y2H protein–protein interaction map (Figures 4A–4C).
            """
        ],
        'notes': [
            """
            The Ataxia network doesn't contain original manual curation effort. The integrated data are very old. 
            """
        ]
    },
    'Reactome': {
        'urls': {
            'webpages': [
                'http://reactome.org/'
            ],
            'articles': [
                'http://genomebiology.com/content/8/3/R39',
                'http://nar.oxfordjournals.org/content/42/D1/D472.long'
            ]
        },
        'descriptions': [
            """
            Once the content of the module is approved by the author and curation staff, it is peer-reviewed on the development web-site, by one or more bench biologists selected by the curator in consultation with the author. The peer review is open and the reviewers are acknowledged in the database by name. Any issues raised in the review are resolved, and the new module is scheduled for release.
            """
        ],
        'notes': [
            """
            No binary interactions can be exported programmatically from any format of the Reactome dataset. Reactome's curation method doesn't cover binary interactions, the inferred lists on the webpage are based on automatic expansion of complexes and reactions, and thus are unreliable. In lack of information, references cannot be assigned to interactions.
            """
        ]
    },
    'Li2012': {
        'urls': {
            'articles': [
                'http://genome.cshlp.org/content/22/7/1222'
            ]
        },
        'descriptions': [
            """
            Human phosphotyrosine signaling network. 
            We manually collected the experimentally determined human TK–substrate interactions and substrate–SH2/PTB domain interactions from the literature (see Supplemental Materials), as well as the Phospho.ELM and PhosphoSitePlus databases. [71 references, 585 circuits]
            """
        ]
    },
    'Zaman2013': {
        'urls': {
            'articles': [
                'http://www.sciencedirect.com/science/article/pii/S2211124713004695'
            ],
            'webpages': []
        },
        'contains': [
            'HumanSignalingNetwork',
            'Cui2007',
            'CA1',
            'BioCarta',
            'Awan2007',
            'Li2012',
            'NCI-PID'
        ],
        'descriptions': [
            """
            The human signaling network (Version 4, containing more than 6,000 genes and more than 50,000 relations) includes our previous data obtained from manually curated signaling networks (Awan et al., 2007; Cui et al., 2007; Li et al., 2012) and by PID (http://pid.nci.nih.gov/) and our recent manual curations using the iHOP database (http://www.ihop-net.org/UniPub/iHOP/).
            """
        ]
    },
    'AlzPathway': {
        'urls': {
            'articles': [
                'http://www.biomedcentral.com/1752-0509/6/52'
            ],
            'webpages': [
                'http://alzpathway.org/AlzPathway.html'
            ]
        },
        'descriptions': [
            """
            We collected 123 review articles related to AD accessible from PubMed. We then manually curated these review articles, and have built an AD pathway map by using CellDesigner. Molecules are distinguished by the following types: proteins, complexes, simple molecules, genes, RNAs, ions, degraded products, and phenotypes. Gene symbols are pursuant to the HGNC symbols. Reactions are also distinguished by the following categories: state transition, transcription, translation, heterodimer association, dissociation, transport, unknown transition, and omitted transition. All the reactions have evidences to the references in PubMed ID using the MIRIAM scheme [14]. All the references used for constructing the AlzPathway are listed in the ‘References for AlzPathway’. Cellular types are distinguished by the followings: neuron, astrocyte, and microglial cells. Cellular compartments are also distinguished by the followings: brain blood barrier, presynaptic, postsynaptic, and their inner cellular localizations.
            """
        ],
        'notes': [
            """
            References can be fetched only from XML formats, not from the SIF file. Among approx. 150 protein-protein interactions, also contains interactions of many small molecules, denoted by pubchem IDs.
            """
        ]
    },
    'MPPI': {
        'urls': {
            'articles': [
                'http://bioinformatics.oxfordjournals.org/content/21/6/832'
            ],
            'webpages': [
                'http://mips.helmholtz-muenchen.de/proj/ppi/'
            ]
        },
        'descriptions': [
            """
            The first and foremost principle of our MPPI database is to favor quality over completeness. Therefore, we decided to include only published experimental evidence derived from individual experiments as opposed to large-scale surveys. High-throughput data may be integrated later, but will be marked to distinguish it from evidence derived from individual experiments.
            """
        ],
        'notes': [
            """
            This database contains hundreds of interactions curated manually from original papers. The format is perfect, with UniProt IDs, and PubMed references.
            """
        ]
    },
    'Negatome': {
        'urls': {
            'articles': [
                'http://nar.oxfordjournals.org/content/38/suppl_1/D540.long',
                'http://nar.oxfordjournals.org/content/42/D1/D396.long'
            ],
            'webpages': [
                'http://mips.helmholtz-muenchen.de/proj/ppi/negatome/'
            ]
        },
        'descriptions': [
            """
            Annotation of the manual dataset was performed analogous to the annotation of protein–protein interactions and protein complexes in previous projects published by our group. Information about NIPs was extracted from scientific literature using only data from individual experiments but not from high-throughput experiments. Only mammalian proteins were considered. Data from high-throughput experiments were omitted in order to maintain the highest possible standard of reliability.
            """
        ]
    },
    'Macrophage': {
        'urls': {
            'articles': [
                'http://www.biomedcentral.com/1752-0509/4/63'
            ],
            'webpages': []
        },
        'descriptions': [
            """
            Ongoing analysis of macrophage-related datasets and an interest in consolidating our knowledge of a number of signalling pathways directed our choice of pathways to be mapped (see Figure 1). Public and propriety databases were initially used as resources for data mining, but ultimately all molecular interaction data was sourced from published literature. Manual curation of the literature was performed to firstly evaluate the quality of the evidence supporting an interaction and secondly, to extract the necessary and additional pieces of information required to 'understand' the pathway and construct an interaction diagram. We have drawn pathways based on our desire to model pathways active in a human macrophage and therefore all components have been depicted using standard human gene nomenclature (HGNC). However, our understanding of the pathway components and the interactions between them, have been drawn largely from a consensus view of literature knowledge. As such the pathways presented here are based on data derived from a range of different cellular systems and mammalian species (human and mouse).
            """
        ]
    },
    'NetPath': {
        'urls': {
            'articles': [
                'http://genomebiology.com/content/11/1/R3',
                'http://database.oxfordjournals.org/content/2011/bar032.long'
            ],
            'webpages': [
                'http://netpath.org/'
            ]
        },
        'descriptions': [
            """
            The initial annotation process of any signaling pathway involves gathering and reading of review articles to achieve a brief overview of the pathway. This process is followed by listing all the molecules that arereported to be involved in the pathway under annotation. Information regarding potential pathway authorities are also gathered at this initial stage. Pathway experts are involved in initial screening of the molecules listed to check for any obvious omissions. In the second phase, annotators manually perform extensive literature searches using search keys, which include all the alter native names of the molecules involved, the name of the pathway, the names of reactions, and so on. In addition, the iHOP resource is also used to perform advanced PubMed-based literature searches to collect the reactions that were reported to be implicated in a given pathway. The collected reactions are manually entered using the PathBuilder annotation interface, which is subjected to an internal review process involving PhD level scientists with expertise in the areas of molecular biology, immunology and biochemistry. However, there are instances where a molecule has been implicated in a pathway in a published report but the associated experimental evidence is either weak or differs from experiments carried out by other groups. For this purpose, we recruit several investigators as pathway authorities based on their expertise in individual signaling pathways. The review by pathway authorities occasionally leads to correction of errors or, more commonly, to inclusion of additional information. Finally, the pathway authorities help in assessing whether the work of all major laboratories has been incorporated for the given signaling pathway.
            """
        ],
        'notes': [
            """
            Formats are unclear. The tab delimited format contains the pathway memberships of genes, PubMed references, but not the interaction partners! The Excel file is very weird, in fact it is not an excel table, and contains only a few rows from the tab file. The PSI-MI XML is much better. By writing a simple parser, a lot of details can be extracted.
            """
        ]
    },
    'InnateDB': {
        'urls': {
            'articles': [
                'http://msb.embopress.org/content/4/1/218.long',
                'http://www.biomedcentral.com/1752-0509/4/117',
                'http://nar.oxfordjournals.org/content/41/D1/D1228.long'
            ],
            'webpages': [
                'http://www.innatedb.com/'
            ]
        },
        'descriptions': [
            """
            To date, the InnateDB curation team has reviewed more than 1000 publications and curated more than 3500 innate immunity-relevant interactions, richly annotating them in terms of the experimental evidence and the context in which they occur.
            To date, InnateDB manual curation has prioritized molecules that are well-described members of key innate immunity signaling pathways, including the TLR pathways, the NF-kB pathway, MAPK signaling pathway, JNK signaling pathway, NOD-like receptor pathway and the RIG-I antiviral pathway (Kanneganti et al, 2007; Lee and Kim, 2007; Thompson and Locarnini, 2007). We have then curated experimentally verified interactions between these molecules and any other molecule, regardless of whether the interacting molecule has any known role in innate immunity.
            InnateDB project has had a full-time curation team employed for more than three years. As of February 15th 2010, there were 11,786 InnateDB-curated molecular interactions in InnateDB (>3,000 published articles reviewed). Currently, InnateDB only curates interactions involving human and mouse molecules, with the majority of curated interactions (72% or 8,569 interactions) involving human molecules (although there has been no specific focus on human as opposed to mouse). Additionally, there are 1,005 hybrid interactions involving both human and mouse participants. Curated interactions are primarily protein-protein interactions (9,244 interactions), however, there are also almost 2,500 protein-DNA interactions and a small, but important, number of RNA interactions (mainly microRNAs).
            As of September 2012, our curation team has reviewed >4300 publications, and >18 000 interactions of relevance to innate immunity have been annotated.
            """
        ],
        'notes': [
            """
            Probably the largest manually curated binary protein interaction dataset, developed by a dedicated full time team of curators. Formats are clear and accessible, comprising UniProt IDs, PubMed references, experimental evidences and mechanisms.
            """
        ]
    },
    'CORUM': {
        'urls': {
            'articles': [
                'http://nar.oxfordjournals.org/content/36/suppl_1/D646.long',
                'http://nar.oxfordjournals.org/content/38/suppl_1/D497.long'
            ],
            'webpages': [
                'http://mips.helmholtz-muenchen.de/genre/proj/corum'
            ]
        },
        'taxons': [
            'human',
            'mouse',
            'rat'
        ],
        'descriptions': [
            """
            The CORUM database is a collection of experimentally verified mammalian protein complexes. Information is manually derived by critical reading of the scientific literature from expert annotators. Information about protein complexes includes protein complex names, subunits, literature references as well as the function of the complexes.
            In order to provide a high-quality dataset of mammalian protein complexes, all entries are manually created. Only protein complexes which have been isolated and characterized by reliable experimental evidence are included in CORUM. To be considered for CORUM, a protein complex has to be isolated as one molecule and must not be a construct derived from several experiments. Also, artificial constructs of subcomplexes are not taken into account. Since information from high-throughput experi ments contains a significant fraction of false-positive results, this type of data is excluded. References for relevant articles were mainly found in general review articles, cross-references to related protein complexes within analysed literature and comments on referenced articles in UniProt.
            """
        ]
    },
    'CellSignalingTechnology': {
        'urls': {
            'articles': [],
            'webpages': [
                'http://www.cellsignal.com/common/content/content.jsp?id=science-pathways'
            ]
        },
        'descriptions': [
            """
            On these resource pages you can find signaling pathway diagrams, research overviews, relevant antibody products, publications, and other research resources organized by topic. The pathway diagrams associated with these topics have been assembled by CST scientists and outside experts to provide succinct and current overviews of selected signaling pathways.
            """
        ],
        'notes': [
            """
            The pathway diagrams are based on good quality, manually curated data, probably from review articles. However, those are available only in graphical (PDF and InDesign) formats. There is no programmatic way to obtain the interactions and references, as it was confirmed by the authors, who I contacted by mail. Wang's HumanSignalingNetwork includes the data from this resource, which probably has been entered manually, but Wang's data doesn't have source annotations, despite it's compiled from multiple sources.
            """
        ]
    },
    'DIP': {
        'urls': {
            'articles': [
                'http://nar.oxfordjournals.org/content/28/1/289.long',
                'http://nar.oxfordjournals.org/content/30/1/303.long',
                'http://nar.oxfordjournals.org/content/32/suppl_1/D449.full'
            ],
            'webpages': [
                'http://dip.doe-mbi.ucla.edu/dip/Main.cgi'
            ]
        },
       'descriptions': [
            """
            In the beginning (near 2000), it was a proper manually curated database:
            Currently protein–protein interactions are entered into the DIP only following publication in peer-reviewed journals. Entry is done manually by the curator, followed by automated tests that show the proteins and citations exist. Interactions are double-checked by a second curator and flagged accordingly in the database. 
            From 2001, it contains high-throughput interactions:
            Because the reliability of experimental evidence varies widely, methods of quality assessment have been developed and utilized to identify the most reliable subset of the interactions. This CORE set can be used as a reference when evaluating the reliability of high-throughput protein-protein interaction data sets, for development of prediction methods, as well as in the studies of the properties of protein interaction networks.
            """
        ],
        'notes': [
            """
            The 'core' dataset contains manually curated interactions from small-scale studies. Interactions are well annotated with PubMed IDs, evidences, and mechanism (binding, chemical reaction, etc). The format is esily accessible (MITAB).
            """
        ]
    },
    'DEPOD': {
        'urls': {
            'articles': [
                'http://stke.sciencemag.org/content/6/275/rs10.long'
            ],
            'webpages': [
                'http://www.koehn.embl.de/depod/index.php'
            ]
        },
        'taxons': [
            'human'
        ],
        'descriptions': [
            """
            DEPOD - the human DEPhOsphorylation Database (version 1.0) is a manually curated database collecting human active phosphatases, their experimentally verified protein and non-protein substrates and dephosphorylation site information, and pathways in which they are involved. It also provides links to popular kinase databases and protein-protein interaction databases for these phosphatases and substrates. DEPOD aims to be a valuable resource for studying human phosphatases and their substrate specificities and molecular mechanisms; phosphatase-targeted drug discovery and development; connecting phosphatases with kinases through their common substrates; completing the human phosphorylation/dephosphorylation network.
            """
        ],
        'notes': [
            """
            Nice manually curated dataset with PubMed references, in easily accessible MITAB format with UniProt IDs, comprises 832 dephosphorylation reactions on protein substrates, and few hundreds on small molecules.
            """
        ]
    },
    'PhosphoPoint': {
        'urls': {
            'articles': [
                'http://bioinformatics.oxfordjournals.org/content/24/16/i14.long'
            ],
            'webpages': [
                'http://kinase.bioinformatics.tw/'
            ]
        },
        'taxons': [
            'human'
        ],
        'descriptions': [
            """
            We have integrated three existing databases, including Phospho.ELM (release 6.0, total 9236 phosphorylation sites), HPRD (release 6, total 8992 phosphorylation sites), SwissProt (release 51.5, total 6529 phosphorylation sites), and our manually curated 400 kinase–substrate pairs, which are primarily from review articles.
            Among these phosphorylation sites, 7843 (6152+995+696) are from high-throughput (HTP) screening, 6329 (3828+1152+1349) are from low-throughput (LTP) analysis, and only 679 (420+97+162) are both from HTP and LTP screening. One special note is that there are 887 phosphorylation sites, which do not have annotation from literature in the SwissProt database and it is not possible distinguish whether these are from HTP or LTP.
            """
        ],
        'notes': [
            """
            It contains 400 manually curated interactions and much more from HTP methods. The manually curated set can not be distinguished in the data formats offered.
            """
        ]
    },
    'PANTHER': {
        'urls': {
            'articles': [
                'http://link.springer.com/protocol/10.1007%2F978-1-60761-175-2_7#section=82252&page=1'
            ],
            'webpages': [
                'http://www.pantherdb.org/'
            ]
        },
        'descriptions': [
            """
            References are captured at three levels. First, each pathway as a whole requires a reference. For signaling pathways, at least three references, usually review papers, are required in order to provide a more objective view of the scope of the pathway. For metabolic pathways, a textbook reference is usually sufficient. Second, references are often associated to each molecule class in the pathway. Most of these references are OMIM records or review papers. Third, references are provided to support association of specific protein sequences with a particular molecule class, e.g., the SWISS-PROT sequence P53_HUMAN annotated as an instance of the molecule class ‘‘P53’’ appearing in the pathway class ‘‘P53 pathway’’. These are usually research papers that report the experimental evidence that a particular protein or gene participates in the reactions represented in the pathway diagram.
            There are three major properties that make this infrastructure differ from other pathway curation systems, such as from Reactome and EcoCyc. First, the pathway diagrams are drawn with CellDesigner software. There are two advantages to using CellDesigner. First, controlled graphical notations are used to draw the pathway diagram, and the software automatically creates a computational representation that is compatible with the SBML standard. Second, a pathway diagram can be viewed with an exact, one-to-one correspondence with the ontological representation of the pathways stored in the back-end. The second property is that the scope of the pathway is defined first based on literature, and pathway components (proteins, genes, RNAs) are treated as ontology terms, or molecule classes, rather than specific instances. This means that multiple proteins from the same organism or different organisms can potentially play the same given role in a pathway. The advantage is that the work flow is more similar to the thinking process of the biologists who are the users of our curation software module. The third major property is that the curation software is designed to be simple enough to be used directly by bench biologists after a brief training course. All other pathway databases we are aware of employ highly trained curators, who of course cannot be experts in all areas of biology. The current set of PANTHER pathways has been curated by more than 40 different external experts from the scientific community; they must only have demonstrated their expertise with publications in the relevant field.
            """
        ]
    },
    'PhosphoSite': {
        'urls': {
            'articles': [
                'http://nar.oxfordjournals.org/content/40/D1/D261.long'
            ],
            'webpages': [
                'http://www.phosphosite.org/homeAction.do'
            ]
        },
        'taxons': [
            'eubacteria',
            'eukarya'
        ],
        'descriptions': [
            """
            PSP integrates both low- and high-throughput (LTP and HTP) data sources into a single reliable and comprehensive resource. Nearly 10,000 journal articles , including both LTP and HTP reports, have been manually curated by expert scientists from over 480 different journals since 2001.
            Information from nearly 13 000 papers and 600 different journals characterizing modification sites with LTP methods has been curated into PSP.
            Information is gathered from published literature and other sources. Published literature is searched semi-automatically with multiple intelligent search algorithms to identify reports that potentially identify phosphorylation sites in human, mouse or other species. Each identified report is then scanned by our highly trained curatorial staff (all with PhDs and extensive research experience in cell biology or related disciplines) to select only those papers that either identify new physiological phosphorylation sites or those that illuminate the biological function of the phosphorylation event. Records that are selected for inclusion into PhosphoSite are placed in the curatorial queue for processing. Note: while we gather records that describe both in vitro and in vivo phosphorylation events, we only finally submit records about in vitro sites when we have additional hard evidence that the site is also phosphorylated in vivo.
            """
        ]
    },
    'SPIKE': {
        'urls': {
            'articles': [
                'http://nar.oxfordjournals.org/content/39/suppl_1/D793.full.html'
            ],
            'webpages': [
                'http://www.cs.tau.ac.il/~spike/'
            ]
        },
        'descriptions': [
            """
            SPIKE’s data on relationships between entities come from three sources: (i) Highly curated data submitted directly to SPIKE database by SPIKE curators and experts in various biomedical domains. (ii) Data imported from external signaling pathway databaes. At present, SPIKE database imports such data from Reactome, KEGG, NetPath and The Transcription Factor Encyclopedia (http://www.cisreg.ca/cgi-bin/tfe/home.pl). (iii) Data on protein–protein interactions (PPIs) imported either directly from wide-scale studies that recorded such interactions [to date,PPI data were imported from Stelzl et al., Rual et al. and Lim et al.] or from external PPI databases [IntAct and MINT (19)]. Relationship data coming from these different sources vary greatly in their quality and this is reflected by a quality level attribute, which is attached to each relationship in SPIKE database (Supplementary Data). Each relationship in SPIKE is linked to at least one PubMed reference that supports it.
            As of August 2010, the SPIKE database contains 20 412 genes/proteins, 542 complexes (327 of high quality), 320 protein families (167 of high quality) and 39 small molecules. These entities are linked by 34 338 interactions (of which 2400 are of high quality) and 6074 regulations (4420 of high quality). These are associated with 5873 journal references in total.
            Each of the maps is constructed by a domain expert; typically the same expert will also be responsible later for keeping it up-to-date. The expert reads the relevant literature and identifies those interactions and regulations that are pertinent to the pathway.
            The regulations and interactions in the database are assigned quality values ranging from 1 to 4. In general, relationships (regulations and interactions) derived from highly focused biochemical studies are assigned high quality (2 or 1) while those derived from high-throughput experiments are assigned lower quality (4 or 3). The curator uses best judgment to assign a quality level. For example, relationships mentioned in two independent research reports, or cited repeatedly in reviews written by leading authorities will get quality 1. Relationships with cited concrete references and those imported en masse from external curated signaling DBs are initially assigned quality 2 but later can be changed to the highest quality after the curator has read and was convinced by the cited papers. Data imported from protein-protein interaction DBs and datasets are assigned quality 3 or 4, depending on the experimental technique.
            """
        ]
    },
    'NCI-PID': {
        'urls': {
            'webpages': [
                'http://pid.nci.nih.gov/index.shtml'
            ],
            'articles': [
                'http://nar.oxfordjournals.org/content/37/suppl_1/D674.long'
            ]
        },
        'descriptions': [
            """
            In curating, editors synthesize meaningful networks of events into defined pathways and adhere to the PID data model for consistency in data representation: molecules and biological processes are annotated with standardized names and unambiguous identifiers; and signaling and regulatory events are annotated with evidence codes and references. To ensure accurate data representation, editors assemble pathways from data that is principally derived from primary research publications. The majority of data in PID is human; however, if a finding discovered in another mammal is also deemed to occur in humans, editors may decide to include this finding, but will also record that the evidence was inferred from another species. Prior to publication, all pathways are reviewed by one or more experts in a field for accuracy and completeness.
            """
        ],
        'notes': [
            """
            From the NCI-XML interactions with references, directions and signs can be extracted. Complexes are ommited.
            """
        ]
    },
    'WikiPathways': {
        'urls': {
            'webpages': [
                'http://www.wikipathways.org/index.php/WikiPathways'
            ],
            'articles': [
                'http://nar.oxfordjournals.org/content/40/D1/D1301'
            ]
        },
        'descriptions': [
            """
            The goal of WikiPathways is to capture knowledge about biological pathways (the elements, their interactions and layout) in a form that is both human readable and amenable to computational analysis.
            """
        ],
        'notes': [
            """
            The data is not accessible. Interactions are available in BioPAX format, but without references.
            """
        ]
    },
    'ConsensusPathDB': {
        'urls': {
            'webpages': [
                'http://cpdb.molgen.mpg.de/CPDB'
            ],
            'articles': [
                ''
            ],
            'taxons': [
                'human',
                'mouse',
                'yeast'
            ],
            'descriptions': [
                """
                
                """
            ],
            'notes': [
                """
                ConsensusPathDB comprises data from 32 resources. The format is easy to use, tab delimited text file, with UniProtKB names and PubMed IDs. However, the dataset is extremely huge, and several databases containing HTP data is included.
                """
            ]
        }
    },
    'KEGG': {
        'urls': {
            'webpages': [
                'http://www.genome.jp/kegg/'
            ],
            'articles': [
                ''
            ]
        },
        'notes': [
            """
            From 2011, KEGG data is not freely available. The downloadable KGML files contain binary interactions, most of them between large complexes. No references available.
            """
        ]
    },
    'IntAct': {
        'urls': {
            'articles': [
                'http://nar.oxfordjournals.org/content/40/D1/D841.long'
            ],
            'webpages': [
                'http://www.ebi.ac.uk/intact/'
            ]
        },
        'descriptions': [
            """
            The information within the IntAct database primarily consists of protein–protein interaction (PPI) data. The majority of the PPI data within the database is annotated to IMEx standards, as agreed by the IMEx consortium. All such records contain a full description of the experimental conditions in which the interaction was observed. This includes full details of the constructs used in each experiment, such as the presence and position of tags, the minimal binding region defined by deletion mutants and the effect of any point mutations, referenced to UniProtKB (2), the underlying protein sequence database. Protein interactions can be described down to the isoform level, or indeed to the post-translationally cleaved mature peptide level if such information is available in the publication, using the appropriate UniProtKB identifiers.
            Each entry in IntAct is peer reviewed by a senior curator, and not released until accepted by that curator. Additional rule-based checks are run at the database level, and manually fixed when necessary. Finally, on release of the data, the original author of each publication is contacted and asked to comment on the representation of their data; again manual updates are made to the entry should the author highlight any errors.
            All binary interactions evidences in the IntAct database, including those generated by Spoke expansion of co-complex data, are clustered to produce a non-redundant set of protein pairs (R. C. Jimenez et al., manuscript in preparation). Each binary pair is then scored, using a simple addition of the cumulated value of a weighted score for the interaction detection method and the interaction type for each interaction evidence associated with that binary pair, as described using the PSI-MI CV terms. The scores are given in Table 1, all children of each given parent receives that score. Only experimental data is scored, inferred interactions, for example, would be excluded. Any low confidence data or data manually tagged by a curator for exclusion from the process, would not be scored. Isoforms and post-processed protein chains are regarded as distinct proteins for scoring purposes.
            """
        ],
        'notes': [
            """
            We can not draw a sharp distinction between low and high throughput methods, and I can agree, that this is not the only and best measure of quality considering experimental data. I see that IntAct came up with a good solution to estimate the confidence of interactions. The mi-score system gives a comprehensive way to synthetize information from multiple experiments, and weight interactions according to experimental methods, interaction type, and number of evidences.
            """
        ]
    },
    'MatrixDB': {
        'urls': {
            'articles': [
                'http://bioinformatics.oxfordjournals.org/content/25/5/690.long'
            ],
            'webpages': [
                'http://matrixdb.ibcp.fr/index.html'
            ]
        },
        'notes': [
            """
            Very nice!
            """
        ]
    }
}