from django.core.management.base import BaseCommand
from django.apps import apps
# import sys

Species = apps.get_model('other', 'Species')
Accepted = apps.get_model('other', 'Accepted')
# Location = apps.get_model('other', 'Location')
# Distribution = apps.get_model('other', 'Distribution')


class Command(BaseCommand):
    help = "Read description from other/Description and print out unique values / load to database. "

    def add_arguments(self, parser):
        parser.add_argument('family', type=str, help='Family')
        parser.add_argument('-g', '--genus', type=str, help='Genus', )

    def handle(self, *args, **kwargs):
        # 0 id, 28-orig_id, 2 type, 3 status, 4 family, 6 genus, 8 species, 9 infraspr, 10 infrspe, 16 year, 18 geoloc, 19 life form, 20 climate, 22 author, 23 acc_id, 29 formula, 30 reviewed
        family = kwargs['family']
        genus = kwargs['genus']
        input_file = "data/input/wcvp_names.csv"
        if genus:
            syn = []
            synid = []
            extracted_file = "data/powo_species.txt"
            with open(input_file, 'r+', encoding="utf8") as f, open(extracted_file, 'w', encoding="utf8") as out1:
                for count, line in enumerate(f, 1):
                    words = line.rstrip().split('|')
                    if words[4] != family:
                        continue
                    if words[6] != genus:
                        continue
                    # print(count, line)
                    if words[2] == 'Genus':
                        print(
                            words[0] + "\t" + words[28] + "\t" + words[6] + "\t" + words[22] + "\t" + words[16].strip("()") + "\t" +
                            words[2].lower() + '\tPOWO\t' + family + '\n')
                        out1.write(
                            words[0] + "\t" + words[28] + "\t" + words[6] + "\t" + words[22] + "\t" + words[16].strip("()") + "\t" +
                            words[3].lower() + '\tPOWO\t' + family + '\n')
                    else:
                        if words[3] == 'Synonym':
                            syn = syn + [[words[0], words[23], words[21]]]
                            synid = synid + [words[23]]
                            print(words[0] + "\t" + words[28] + "\t" + words[6] + "\t" + words[8] + "\t" + words[22] + "\t" + words[16].strip("()") + "\t" + words[2].lower() + "\t" + words[3].lower() + '\t' + words[9] + '\t' + words[10])
                            out1.write(words[0] + "\t" + words[28] + "\t" + words[6] + "\t" + words[8] + "\t" + words[22] + "\t" + words[16].strip("()") + "\t" + words[3].lower() + "\t" +  "species" + '\tPOWO\t' + words[9] + '\t' + words[10] + '\t' + words[23] + '\n')
                        else:
                            print(words[0] + "\t" + words[28] + "\t" + words[6] + "\t" + words[8] + "\t" + words[22] + "\t" + words[16].strip("()") + "\t" + words[2].lower() + "\t" + words[3].lower() + '\t' + words[9] + '\t' + words[10])
                            out1.write(words[0] + "\t" + words[28] + "\t" + words[6] + "\t" + words[8] + "\t" + words[22] + "\t" + words[16].strip("()") + "\t" + words[3].lower() + "\t" + "species" + '\tPOWO\t' + words[9] + '\t' + words[10] + '\n')
            f.close()
            # Loop through all synonyms in the Family/genus
            if synid:
                words = []
                with open(input_file, 'r', encoding="utf8") as f, open(extracted_file, 'a', encoding="utf8") as out1:
                    for count, line in enumerate(f, 1):
                        # print(line)
                        words = line.rstrip().split('|')
                        if words[4] and words[4] != family:
                            continue
                        if words[0] not in synid:
                            continue
                        for spid, acc_id, binomial in syn:
                            # Found accepted species
                            # TODO Check if accepted is already in the database
                            if words[0] == acc_id:
                                print(spid, words[0], binomial, words[21])
                                out1.write(
                                    words[0] + "\t" + words[28] + "\t" + words[6] + "\t" + words[8] + "\t" + words[22] + "\t" + words[16].strip("()") + "\t" + words[3].lower() + "\t" +
                                    words[2].lower() + '\tPOWO\t' + words[9] + '\t' + words[10] + '\t' + spid + '\n')
                                break
        else:
            # If genus is not given, then extract all genera in the family
            extracted_file = "data/powo_genus.txt"
            with open(input_file, 'r+', encoding="utf8") as f, open(extracted_file, 'w', encoding="utf8") as out1:
                for count, line in enumerate(f, 1):
                    words = line.rstrip().split('|')
                    if words[4] != family or words[2] != 'Genus':
                        continue
                    print(words[0] + "\t" + words[28] + "\t" + words[6] + "\t" + words[22] + "\t" + words[16].strip(
                        "()") + "\t" + words[2].lower() + '\tPOWO\t' + family + '\n')
                    out1.write(
                        words[0] + "\t" + words[28] + "\t" + words[6] + "\t" + words[22] + "\t" + words[16].strip(
                            "()") + "\t" + words[3].lower() + '\tPOWO\t' + family + '\n')
