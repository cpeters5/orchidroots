from django.core.management.base import BaseCommand
from django.db.models import Count
from orchidaceae.models import Hybrid, Species
import sys
import time
import os
# Set a higher recursion depth limit
sys.setrecursionlimit(2000)
start_time = time.time()
DEBUG = 0

class Command(BaseCommand):
    help = "Create ancestordescendant table "

    def handle(self, *args, **options):
        seedobj = ''
        pollobj = ''
        # relationships = [('a', ('b', 'c')), ('b', ('d', 'e'))]
        mylist = Hybrid.objects.filter(genus='Vanda').values_list('pid', 'seed_id', 'pollen_id').order_by('pid')

        # Check if seed is a synonym. If so set seed_id to accepted value
        parents = []
        for t in mylist:
            if isinstance(t[2], int) and t[2] > 0:
                try:
                    seedobj = Species.objects.get(pk=t[1])
                    if seedobj.status == 'synonym':
                        if seedobj.getAccepted():
                            parents.append((t[0], seedobj.getAcc(), t[2]))
                        else:
                            parents.append(t)
                except Species.DoesNotExist:
                        parents.append((t[0], 0, t[2]))
                else:
                    parents.append(t)

        # Check if seed is a synonym. If so set seed_id to accepted value
        mylist = parents
        parents = []
        for t in mylist:
            if isinstance(t[2], int) and t[2] > 0:
                try:
                    pollobj = Species.objects.get(pk=t[2])
                    if pollobj.status == 'synonym':
                        if pollobj.getAccepted():
                            parents.append((t[0], t[1], pollobj.getAcc()))
                        else:
                            parents.append(t)
                except Species.DoesNotExist:
                    parents.append((t[0], t[1], 0))
                else:
                    parents.append(t)


        relationships = [(t[0], (t[1], t[2])) for t in parents]

        # Create a dictionary to store the parents and children of each node
        tree_structure = {}

        # Populate the dictionary with the given relationships

        for child, parents in relationships:
            if child not in tree_structure:
                tree_structure[child] = {'parents': [], 'children': [], 'is_leaf': True}
            for parent in parents:
                if parent not in tree_structure:
                    tree_structure[parent] = {'parents': [], 'children': [], 'is_leaf': False}
                tree_structure[parent]['children'].append(child)
                tree_structure[child]['parents'].append(parent)
                tree_structure[parent]['is_leaf'] = False

        # Function to recursively calculate the percentage for each ancestor with depth limit
        def calculate_pct(node, pct, ancestors_pct, tree_structure, depth, max_depth):
            if depth > max_depth:  # Stop recursion if max depth is reached
                return
            if node not in tree_structure or not tree_structure[node]['parents']:
                return
            split_pct = pct / len(tree_structure[node]['parents'])
            # if split_pct < .01:
            #     split_pct = 0
            for parent in tree_structure[node]['parents']:
                ancestors_pct[(node, parent, tree_structure[parent]['is_leaf'])] = split_pct
                # Recur with increased depth
                calculate_pct(parent, split_pct, ancestors_pct, tree_structure, depth + 1, max_depth)

        # Main logic to create the desired output with a depth limit
        def create_tree_pct(tree_structure, max_depth):
            # Initialize dictionary to hold percentages and leaf information
            ancestors_pct = {}

            # Calculate percentages for each node with depth control
            for child in tree_structure.keys():
                calculate_pct(child, 1, ancestors_pct, tree_structure, 0, max_depth)

            # Convert to the desired output format (node, ancestor, pct, is_leaf)
            output = [(child, parent, pct, is_leaf) for (child, parent, is_leaf), pct in ancestors_pct.items()]
            return output

        # Specify the maximum depth for recursion
        max_recursion_depth = 1000  # For example, stop recursion after 10 levels

        # Run the function and print the output
        output = create_tree_pct(tree_structure, max_recursion_depth)
        end_time = time.time()
        # Total lines you want to write
        # total_lines = 50000

        # Lines per file
        lines_per_file = 50000

        # Counter for lines written
        lines_written = 0

        # File number
        file_number = 1
        filename = f'output_{file_number}.txt'
        if os.path.exists(filename):
            os.remove(filename)
        i = 0
        for line in output:
            # If the current line count is a multiple of lines_per_file, increment the file_number
            if i % lines_per_file == 0 and i != 0:
                file_number += 1
                lines_written = 0  # Reset the lines written for the new file
                filename = f'output_{file_number}.txt'
                if os.path.exists(filename):
                    os.remove(filename)
                print(f"Write to output_{file_number}.txt\n")

            # Open the file for this batch
            # Using 'a' to append to the file in case the loop cycles before writing all lines
            with open(filename, 'a') as file:
                file.write(f"{str(line)[1:-1]}\n")
                lines_written += 1
            i += 1



        # i = 0
        # for b in blocks:
        #     filename = 'ancestordescendant_'+ b + '.txt'
        #     with open(filename, 'a') as file:
        #         for line in output:
        #             file.write(str(line)[1:-1])
        #             if DEBUG:
        #                 i += 1
        #                 if line[2] < .25:
        #                     print(i, line)

        duration = (end_time - start_time)/60
        print(f"The process took {duration} minutes.")
