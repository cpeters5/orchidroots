from django.core.management.base import BaseCommand
from django.db.models import Count
from orchidaceae.models import Hybrid, Genus

class Command(BaseCommand):
    help = "Create ancestordescendant table "

    def handle(self, *args, **options):
        genera = Genus.objects.all()
        # relationships = [('a', ('b', 'c')), ('b', ('d', 'e'))]
        parents = Hybrid.objects.filter(genus='Vanda').values_list('pid', 'seed_id', 'pollen_id')
        relationships = [(t[0], (t[1], t[2])) for t in parents]

        # Create a dictionary to store the parents and children of each node
        tree_structure = {}

        def find_ancestors(node, tree, ancestors):
            if node not in tree:
                return
            for parent in tree[node]:
                ancestors.append((node, parent))
                find_ancestors(parent, tree, ancestors)

        # Main logic to create the desired output
        def create_ancestry_list(relationships):
            # Initialize a dictionary to store child to parent relationships
            tree = {}
            for child, parents in relationships:
                tree[child] = parents

                # Add empty parent list for any new parent nodes found
                for parent in parents:
                    if parent not in tree:
                        tree[parent] = []

            # Initialize a list to store the ancestor relationships
            ancestry_list = []

            # Populate the ancestry list
            for child in tree.keys():
                find_ancestors(child, tree, ancestry_list)

            return ancestry_list

        # Run the function and print the output
        ancestry_list = create_ancestry_list(relationships)
        for ancestor_info in ancestry_list:
            print(ancestor_info)