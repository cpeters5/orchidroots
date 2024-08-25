import string
alpha_list = string.ascii_uppercase
applications = ['orchidaceae', 'other', 'fungi', 'aves', 'animalia']
app_descriptions = {
    'aves': 'Birds',
    'animalia': 'Animalia',
    'fungi': 'Fungi',
    'orchidaceae': 'Orchids',
    'other': 'Other Plants',
}

big_genera = [
    'Phalaenopsis',
    'Paphiopedilum',
    'Cattleya',
    'Dendrobium',
    'Cymbidium',
    'Rhyncholaeliocattleya',
    'Oncidium',
    'Laeliocattleya',
    'Brassolaeliocattleya',
    'Doritaenopsis'
]

default_genus = {
    'animalia': 'Zygaena',
    'aves': 'Falco',
    'fungi': 'Amanita',
    'orchidaceae': 'Cattleya',
    'other': 'Silene',
}