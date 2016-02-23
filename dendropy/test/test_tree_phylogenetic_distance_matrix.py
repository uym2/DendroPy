#! /usr/bin/env python
##############################################################################
##  DendroPy Phylogenetic Computing Library.
##
##  Copyright 2010-2015 Jeet Sukumaran and Mark T. Holder.
##  All rights reserved.
##
##  See "LICENSE.rst" for terms and conditions of usage.
##
##  If you use this work or any portion thereof in published work,
##  please cite it as:
##
##     Sukumaran, J. and M. T. Holder. 2010. DendroPy: a Python library
##     for phylogenetic computing. Bioinformatics 26: 1569-1571.
##
##############################################################################

import unittest
import dendropy
import csv
from dendropy.utility import container
from dendropy.test.support import pathmap
from dendropy.calculate import treemeasure
from dendropy.calculate import probability
from dendropy.calculate import combinatorics

class PhylogeneticDistanceMatrixCloneTest(unittest.TestCase):

    def setUp(self):
        self.tree = dendropy.Tree.get_from_string("(((a:1, b:1):1, c:2):1, (d:2, (e:1,f:1):1):1):0;", schema="newick")

    def test_clone(self):
        pdm0 = self.tree.phylogenetic_distance_matrix()
        pdm1 = pdm0.clone()
        self.assertIsNot(pdm0, pdm1)
        self.assertIs(pdm0.taxon_namespace, pdm1.taxon_namespace)
        self.assertEqual(len(pdm0.taxon_namespace), len(pdm0._mapped_taxa))
        self.assertEqual(len(pdm1.taxon_namespace), len(pdm1._mapped_taxa))
        for src, dest in (
                    (pdm0._taxon_phylogenetic_distances, pdm1._taxon_phylogenetic_distances,),
                    (pdm0._taxon_phylogenetic_path_steps, pdm1._taxon_phylogenetic_path_steps,),
                    (pdm0._mrca, pdm1._mrca,),
                ):
            self.assertIsNot(src, dest)
            for t1 in src:
                self.assertIn(t1, dest)
                self.assertIsNot(src[t1], dest[t1])
        for t1 in self.tree.taxon_namespace:
            for t2 in self.tree.taxon_namespace:
                self.assertEqual(pdm0.patristic_distance(t1, t2), pdm1.patristic_distance(t1, t2))
                self.assertEqual(pdm0.mrca(t1, t2), pdm1.mrca(t1, t2))
                self.assertEqual(pdm0.path_edge_count(t1, t2), pdm1.path_edge_count(t1, t2))
        self.assertEqual(set(pdm0.distances()), set(pdm1.distances()))
        self.assertEqual(pdm0.sum_of_distances(), pdm1.sum_of_distances())
        self.assertEqual(pdm0, pdm1)

class PhylogeneticDistanceMatrixCompileTest(unittest.TestCase):

        def setUp(self):
            # library(ape)
            # tree = read.nexus("data/pythonidae.mle.nex")
            # pdm = cophenetic.phylo(tree)
            # write.csv(format(pdm,digits=22), "pythonidae.mle.weighted.pdm.csv")
            with open(pathmap.tree_source_path("pythonidae.mle.weighted.pdm.csv")) as src:
                reader = csv.reader(src, delimiter=",")
                self.reference_pdm_weighted_table = container.DataTable.get_from_csv_reader(reader, default_data_type=float)
            with open(pathmap.tree_source_path("pythonidae.mle.unweighted.pdm.csv")) as src:
                reader = csv.reader(src, delimiter=",")
                self.reference_pdm_unweighted_table = container.DataTable.get_from_csv_reader(reader, default_data_type=float)
            self.tree = dendropy.Tree.get(path=pathmap.tree_source_path(
                "pythonidae.mle.nex"),
                schema="nexus",
                preserve_underscores=True)
            self.pdm = self.tree.phylogenetic_distance_matrix()

        def test_mapped_taxa(self):
            n1 = len(self.tree.taxon_namespace)
            self.assertEqual(self.pdm.taxon_namespace, self.tree.taxon_namespace)
            self.assertEqual(n1, len(self.tree.taxon_namespace))
            for taxon1 in self.tree.taxon_namespace:
                self.assertIn(taxon1, self.pdm._mapped_taxa)
            for taxon in self.pdm.iter_taxa():
                self.assertIn(taxon1, self.pdm._mapped_taxa)
                self.assertIn(taxon1, self.tree.taxon_namespace)

        def test_all_distinct_mapped_taxa_pairs(self):
            n1 = len(self.tree.taxon_namespace)
            taxon_pair_iter1 = iter(self.pdm._all_distinct_mapped_taxa_pairs)
            taxon_pair_iter2 = self.pdm.iter_distinct_taxon_pairs()
            for tpi in (taxon_pair_iter1, taxon_pair_iter2):
                seen_pairs = set()
                visited_taxa = set()
                for taxon1, taxon2 in tpi:
                    s = frozenset([taxon1, taxon2])
                    self.assertIn(taxon1, self.pdm._mapped_taxa)
                    self.assertIn(taxon1, self.tree.taxon_namespace)
                    self.assertIn(taxon2, self.pdm._mapped_taxa)
                    self.assertIn(taxon2, self.tree.taxon_namespace)
                    self.assertNotIn(s, seen_pairs)
                    seen_pairs.add(s)
                    visited_taxa.add(taxon1)
                    visited_taxa.add(taxon2)
                self.assertEqual(len(visited_taxa), n1)
                self.assertEqual(len(seen_pairs), combinatorics.choose(n1, 2))

        def test_tree_length(self):
            self.assertEqual(self.pdm._tree_length, self.tree.length())

        def test_tree_num_edges(self):
            self.assertEqual(self.pdm._num_edges, combinatorics.num_edges_on_tree(
                num_leaves=len(self.tree.taxon_namespace), is_rooted=True))

        def test_tree_weighted_pairwise_distances(self):
            for taxon1 in self.tree.taxon_namespace:
                for taxon2 in self.tree.taxon_namespace:
                    exp = self.reference_pdm_weighted_table[taxon1.label, taxon2.label]
                    obs1 = self.pdm._taxon_phylogenetic_distances[taxon1][taxon2]
                    self.assertAlmostEqual(obs1, exp, 6)

class PhylogeneticDistanceMatrixShuffleTest(unittest.TestCase):

    def test_shuffle(self):
        tree = dendropy.Tree.get_from_path(
                    src=pathmap.tree_source_path("community.tree.newick"),
                    schema="newick",
                    rooting="force-rooted")
        pdc0 = tree.phylogenetic_distance_matrix()
        pdc1 = tree.phylogenetic_distance_matrix()
        current_to_shuffled_taxon_map = pdc1.shuffle_taxa()
        keys = set(current_to_shuffled_taxon_map.keys())
        values = set(current_to_shuffled_taxon_map.values())
        self.assertEqual(len(keys), len(values), "\n\n({}): {}\n\n({}): {}".format(len(keys), keys, len(values), values))
        self.assertEqual(keys, values)
        for taxon in tree.taxon_namespace:
            self.assertIn(taxon, current_to_shuffled_taxon_map)
        for nd in tree.leaf_node_iter():
            self.assertIn(current_to_shuffled_taxon_map[nd.taxon], tree.taxon_namespace)
            nd.taxon = current_to_shuffled_taxon_map[nd.taxon]
        pdc2 = tree.phylogenetic_distance_matrix()
        same_as_before = []
        different = []
        for t1 in tree.taxon_namespace:
            for t2 in tree.taxon_namespace:
                d2 = pdc2.patristic_distance(t1, t2)
                d1 = pdc1.patristic_distance(t1, t2)
                self.assertEqual(d1, d2)
                if t1 is not t2:
                    d0 = pdc0.patristic_distance(t1, t2)
                    if d0 == d1:
                        same_as_before.append( (t1, t2) )
                    else:
                        different.append( (t1, t2) )
                else:
                    self.assertEqual(d1, 0)
        self.assertTrue(len(different) > 0)
        self.assertEqual(pdc1, pdc2)
        self.assertNotEqual(pdc0, pdc1)

class TreePatristicDistTest(unittest.TestCase):

    def setUp(self):
        self.tree = dendropy.Tree.get_from_string("(((a:1, b:1):1, c:2):1, (d:2, (e:1,f:1):1):1):0;", schema="newick")

    def testPatDistMatrix(self):
        pdm = treemeasure.PhylogeneticDistanceMatrix.from_tree(self.tree)
        def _chk_distance(pdm, t1, t2, exp_distance):
            tax1 = self.tree.taxon_namespace.require_taxon(label=t1)
            tax2 = self.tree.taxon_namespace.require_taxon(label=t2)
            pd = pdm(tax1, tax2)
            self.assertEqual(pd, exp_distance, "{}: {} <-> {}: {} instead of {}".format(self.tree, t1, t2, pd, exp_distance))
        _chk_distance(pdm, "a", "b", 2)
        _chk_distance(pdm, "a", "c", 4)
        _chk_distance(pdm, "b", "c", 4)
        _chk_distance(pdm, "a", "d", 6)
        _chk_distance(pdm, "f", "d", 4)
        _chk_distance(pdm, "c", "d", 6)

    def testPatDistFunc(self):
        self.tree.encode_bipartitions()
        def _chk_distance(t1, t2, exp_distance):
            tax1 = self.tree.taxon_namespace.get_taxon(label=t1)
            tax2 = self.tree.taxon_namespace.get_taxon(label=t2)
            pd = treemeasure.patristic_distance(self.tree, tax1, tax2)
            self.assertEqual(pd, exp_distance)
        _chk_distance("a", "b", 2)
        _chk_distance("a", "c", 4)
        _chk_distance("b", "c", 4)
        _chk_distance("a", "d", 6)
        _chk_distance("f", "d", 4)
        _chk_distance("c", "d", 6)

class PhylogeneticEcologyStatsTests(unittest.TestCase):

    def setUp(self):
        with open(pathmap.char_source_path("community.data.tsv")) as src:
            reader = csv.reader(src, delimiter="\t")
            self.data_table = container.DataTable.get_from_csv_reader(reader, default_data_type=int)
        self.tree = dendropy.Tree.get_from_path(
                src=pathmap.tree_source_path("community.tree.newick"),
                schema="newick",
                rooting="force-rooted")
        self.pdm = treemeasure.PhylogeneticDistanceMatrix.from_tree(self.tree)

    def test_nonabundance_weighted_mpd(self):
        # my.sample = read.table("data/PD.example.sample.txt", sep = "\t", row.names = 1, header = T)
        # my.phylo = read.tree("data/PD.example.phylo.txt")
        # pd.matrix = cophenetic(my.phylo)
        # mpd(my.sample, cophenetic(my.phylo), abundance.weighted=F)
        #    [1] 3.2225706087019050372078 1.9156605943056665974922 1.9156605943290001548007
        #    [4] 1.9395923093204667786438 0.1934132401466666650869
        expected_results = {
                "C1": 3.222570608701905037208,
                "C2": 1.915660594305666597492,
                "C3": 1.915660594329000154801,
                "C4": 1.939592309320466778644,
                "C5": 0.1934132401466666650869,
        }
        for row_name in self.data_table.iter_row_names():
            filter_fn = lambda taxon: self.data_table[row_name, taxon.label] > 0
            d = self.pdm.mean_pairwise_distance(filter_fn=filter_fn)
            self.assertAlmostEqual(d, expected_results[row_name])

    def test_nonabundance_weighted_mntd(self):
        # my.sample = read.table("data/PD.example.sample.txt", sep = "\t", row.names = 1, header = T)
        # my.phylo = read.tree("data/PD.example.phylo.txt")
        # pd.matrix = cophenetic(my.phylo)
        # mntd(my.sample, cophenetic(my.phylo), abundance.weighted=F)
        #   [1] 1.6347319809428570991372 1.0891173926393333815099 1.0891173926543333827510
        #   [4] 0.1180230301583333335502 0.1426761318733333339104
        expected_results = {
                "C1": 1.6347319809428570991372,
                "C2": 1.0891173926393333815099,
                "C3": 1.0891173926543333827510,
                "C4": 0.1180230301583333335502,
                "C5": 0.1426761318733333339104,
        }
        for row_name in self.data_table.iter_row_names():
            filter_fn = lambda taxon: self.data_table[row_name, taxon.label] > 0
            d = self.pdm.mean_nearest_taxon_distance(filter_fn=filter_fn)
            self.assertAlmostEqual(d, expected_results[row_name])

