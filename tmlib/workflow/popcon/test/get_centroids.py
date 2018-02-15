# Code tried in ipython to get the centroid coordinate of Cells object (id=5) for experiment 77 

import tmlib.models as tm # from within TmLibrary/tmlib directory
from shapely import wkb
import pandas as pd
import numpy as np
import math
from scipy.spatial import distance

def query_mapobjectsegmentation(object_name):
    object_name_id = 


def db_interact():
    with tm.utils.ExperimentSession(77) as session:
        wells = session.query(tm.Well.id,tm.Well.name).all()
        for well_id, well_name in wells:
            sites = session.query(tm.Site.id, tm.Site.height, tm.Site.width, tm.Site.y, tm.Site.x).filter_by(well_id=well_id).all()
     	    wellY = sites[0][1]*len(set([i[3] for i in sites])) 
	    wellX = sites[0][2]*len(set([i[4]for i in sites]))
            well_diagonal = math.sqrt(wellX**2+wellY**2)
	    object_id = session.query(tm.MapobjectType.id).filter_by(name="Nuclei").one()[0]

	    seg_layer_id = session.query(tm.SegmentationLayer.id).filter_by(mapobject_type_id=object_id).one()[0]
	    centroids = session.query(tm.MapobjectSegmentation.geom_centroid,tm.MapobjectSegmentation.mapobject_id,tm.MapobjectSegmentation.label, tm.MapobjectSegmentation.partition_key).filter_by(segmentation_layer_id=seg_layer_id).all()
        session.expunge_all()
    return wellY, wellX, centroids              	
            # check whether features for object already exist
#            features = session.query(tm.Feature).filter_by(mapobject_type_id=object_id).all()
#            if not features:
#	        print 'No features found for object_id={}'.format(object_id)
#            last_feature_id = session.query(tm.Feature)./
#                          order_by(tm.Feature.id.desc()).first()
#            feature_name = 'lcc_'+well
#            print 'add feature "%s"', feature_name
#            feature = session.get_or_create(
#                        tm.Feature, name=feature_name,
#                        mapobject_type_id=mapobject_type_ids[obj_name],
#                        is_aggregate=False
#                        )   

if __name__ == '__main__':

    wellY,wellX,centroids = db_interact()

