import tmlib.models as tm # from within TmLibrary/tmlib directory
from shapely import wkb
import pandas as pd
import numpy as np
import math
from scipy.spatial import distance


class LocalCC(object):
    '''Class for calculatiing local cell crowding per single well.
    '''
    @staticmethod
    def _get_yx(element):
        ''' Helper. Takes in a WKBElement.
        Return a shapely.geometry.point.Point object  
        '''
        return wkb.loads(bytes(element.data))

    @staticmethod
    def _get_df(np_centroids):
        '''Helper. Takes numpy centroids array
        Return a sorted dataframe by site and label          
        '''
        data = np.zeros( (len(np_centroids),5) )
        headers = ['y','x','mapobject_id','label','site']
        data[:] = np_centroids
        data_df = pd.DataFrame(data, columns=headers)
        df = data_df.sort_values(['site', 'label'])
        return df

    def __init__(self, centroids):
        '''
        Parameters
        ----------
        centroids: list of tuples (centroid WKB element, mapobject_id, label,site); 
        i.e. query objects from MapobjectSegmentation table
        '''
        self.centroids = centroids
       
        self.centroids_coordinates = [(self._get_yx(element[0]).y,self._get_yx(element[0]).x, int(element[1]), int(element[2]), int(element[3])) for element in self.centroids]
               
        self.df = self._get_df(self.centroids_coordinates)
        self.yx_coordinates = np.asarray((self.df['y'],self.df['x'])).transpose()
        self.wellY = np.floor(self.df['y'].min())
        self.wellX = np.ceil(self.df['x'].max())
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
	    y_rand= np.random.uniform(self.wellY,0,len(self.yx_coordinates)-1)
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
	
        self.df['lcc'] = pd.Series(lcc)   
	return self.df
        # lcc[lcc[:,1].argsort()] sort array based on mapobject_id
	# lcc[lcc[:,0].argsort()] sort array based on lcc value
	

    
