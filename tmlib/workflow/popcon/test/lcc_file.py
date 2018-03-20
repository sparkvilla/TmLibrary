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
    def _get_df(centroids):
        '''Helper. Takes a list of centroids coords.
        Return a sorted dataframe by site and label          
        '''
        data = np.zeros( (len(centroids),5) )
        headers = ['y','x','mapobject_id','label','site']
        data[:] = centroids
        data_df = pd.DataFrame(data, columns=headers)
        df = data_df.sort_values(['site', 'label'])
        return df

   


    def __init__(self, centroids, wellY, wellX):
        '''
        Parameters
        ----------
        centroids: list of tuples (centroid WKB element, mapobject_id, label,site); 
        i.e. query objects from MapobjectSegmentation table
        '''
       
        self.centroids_coordinates = [
              ( round(element[0],1),\
                round(element[1],1 ),\
                int(element[1]),\
                int(element[2]),\
                int(element[3]) ) for element in centroids]
               
        self.df = self._get_df(self.centroids_coordinates)
        self.yx_coordinates = np.asarray((self.df['y'],self.df['x'])).transpose()
        self.wellY = wellY
        self.wellX = wellX
        self.well_diagonal = np.round(math.sqrt(self.wellX**2+self.wellY**2))
        

    def gen_real_distances(self):
        '''
        Returns
        -------
        generator
        Sum of distances calculated from real positions    
        '''

        for yx_real in self.yx_coordinates:
            real_dist = distance.cdist(np.transpose(yx_real[:,np.newaxis]), self.yx_coordinates, 'euclidean')
            real_masked = np.ma.masked_where(real_dist==0,real_dist) # mask 0 values 
            real_masked_divide = np.divide(self.well_diagonal, real_masked)
            yield np.sum(real_masked_divide.filled(fill_value=0))
       
   
    def gen_random_distances(self):
	'''
	Returns
	-------
	generator 
        Sum of distances calculated from random positions    
	''' 
	   
	for yx_real in self.yx_coordinates:
	    y_rand= np.random.uniform(0,self.wellY,len(self.yx_coordinates)-1)
	    x_rand= np.random.uniform(0,self.wellX,len(self.yx_coordinates)-1) 
	    yx_coordinates_random = np.concatenate( (y_rand[:,np.newaxis],x_rand[:,np.newaxis]), axis=1)
       
	    rand_dist = np.divide(self.well_diagonal, distance.cdist(np.transpose(yx_real[:,np.newaxis]), yx_coordinates_random, 'euclidean') )
	    yield np.sum(np.squeeze(rand_dist))
        

    def get_lcc(self,real_dists,random_dists):
	'''
	Parameters
	----------
	real_dists: generator of real distances  
	random_dists: generator of random distances

	Returns
	-------
	a pandas Dataframe i.e. y,x,mapobject_id,label,site,lcc     
	''' 
	lcc = [re_d-rn_d for re_d,rn_d in zip(real_dists,random_dists)]
	
        self.df['lcc'] = pd.Series(lcc)   
	return self.df
	

    
