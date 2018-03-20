import pickle
import numpy as np
import pandas as pd
import shapely.geometry

from lcc_file import LocalCC


#batch = {'well_ids': [1],
#         'extract_object': 'Circles',
#         'assign_object': 'Circles'}


   
#for well_id in batch['well_ids']:
with open('coordinates_canonical.db', 'r') as f:
    data = pickle.load(f)  

extract_lcc = LocalCC(data,8640,7680)

#real_lcc = lcc_extract.real_distances()
#random_lcc = lcc_extract.random_distances() 
#lcc = lcc_extract.get_lcc(real_lcc,random_lcc)
        
