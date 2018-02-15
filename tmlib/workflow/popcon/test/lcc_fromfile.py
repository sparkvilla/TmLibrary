import tmlib.models as tm # from within TmLibrary/tmlib directory
from shapely import wkb
import pandas as pd
import numpy as np
import math
from scipy.spatial import distance


class LocalCC(object):
    '''Class for calculatiing local cell crowding per single well.
    '''
    def __init__(self, yx_coordinates):
        '''
        Parameters
        ----------
        yx_coordinates: y,x numpy array
        '''
 
        self.yx_coordinates = yx_coordinates
        
        self.wellY = np.ceil(self.yx_coordinates[:,0].max())
        
        self.wellX = np.ceil(self.yx_coordinates[:,0].max())
       
        
        self.well_diagonal = np.round(math.sqrt(self.wellX**2+self.wellY**2))
        
       
   
    def real_distances(self):
	'''
	Returns
	-------
	numpy array of distances from real positions    
	'''     
	real_dists = distance.cdist(self.yx_coordinates, self.yx_coordinates, 'euclidean')
	real_masked = np.ma.masked_where(real_dists==0,real_dists) # mask 0 values 
	real_masked_divide = np.divide(self.well_diagonal, real_masked)
	return real_masked_divide.filled(fill_value=0)

    def random_distances(self):
	'''
	Returns
	-------
	numpy array of distances from random positions    
	''' 
	rand_dists= list() 
	   
	for yx_real in self.yx_coordinates:
	    y_rand= np.random.uniform(0,self.wellY,len(self.yx_coordinates)-1)
	    x_rand= np.random.uniform(0,self.wellX,len(self.yx_coordinates)-1) 
	    yx_coordinates_random = np.concatenate( (y_rand[:,np.newaxis],x_rand[:,np.newaxis]), axis=1)
       
	    rand_dist = np.divide(self.well_diagonal, distance.cdist(np.transpose(yx_real[:,np.newaxis]), yx_coordinates_random, 'euclidean') )
	    rand_dists.append(np.squeeze(rand_dist))
	return np.asarray(rand_dists)
        

    def get_lcc(self,real_dists,random_dists):
	'''
	Parameters
	----------
	real_dists: numpy arrays of real distances  
	random_dists: numpy array of random distances

	Returns
	-------
	a numpy array i.e. a LCC value and mapobject_id for centroid     
	''' 
	sum_real = np.sum(real_dists, axis=1)
	sum_random = np.sum(random_dists, axis=1)     
	lcc = sum_real-sum_random
	
        #lcc_final = np.concatenate( (lcc[:,np.newaxis],self.mapobject_ids[:,np.newaxis] ,self.label[:,np.newaxis],self.sites[:,np.newaxis]) ,axis = 1)   
	# lcc[lcc[:,1].argsort()] sort array based on mapobject_id
	# lcc[lcc[:,0].argsort()] sort array based on lcc value
	return lcc

    
