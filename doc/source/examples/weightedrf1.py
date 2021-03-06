import dendropy
from dendropy.calculate import treecompare

s1 = "((t5:0.161175,t6:0.161175):0.392293,((t4:0.104381,(t2:0.075411,t1:0.075411):0.028969):0.065840,t3:0.170221):0.383247);"
s2 = "((t5:2.161175,t6:0.161175):0.392293,((t4:0.104381,(t2:0.075411,t1:0.075411):1):0.065840,t3:0.170221):0.383247);"

tns = dendropy.TaxonNamespace()

tree1 = dendropy.Tree.get(
        data=s1,
        schema='newick',
        taxon_namespace=tns)
tree2 = dendropy.Tree.get(
        data=s2,
        schema='newick',
        taxon_namespace=tns)

## Weighted Robinson-Foulds distance = 2.971031
print(treecompare.weighted_robinson_foulds_distance(tree1, tree2))

## Compare to unweighted Robinson-Foulds distance: 0
print(treecompare.symmetric_difference(tree1, tree2))
