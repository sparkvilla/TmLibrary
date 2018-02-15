# Code tried in ipython to get the centroid coordinate of Cells object (id=5) for experiment 77 

import tmlib.models as tm # from within TmLibrary/tmlib directory
from shapely import wkb
import pandas as pd
import numpy as np
import math
from scipy.spatial import distance
from sqlalchemy.sql import func



with tm.utils.ExperimentSession(77) as session:
    wells = session.query(tm.Well.id,tm.Well.name).all()
   # well_ids = [w.id for w in wells]
    segmentation_layers = session.query(tm.SegmentationLayer).all()
    feature_name = 'Nuclei_{}_lcc'.format(str(3))
    feature = session.get_or_create(
        tm.Feature, name=feature_name,
        mapobject_type_id=6,
        is_aggregate=False)
    feature_value = session.query(tm.FeatureValues.values).filter_by(mapobject_id=943).one()
    

#    for well_id in wells_id:
#        sites_per_well = session.query(tm.Site.id, tm.Site.height, tm.Site.width, tm.Site.y, tm.Site.x).filter_by(well_id=well_id).all()
#        well_to_sites_map[well_id[0]] = sites_per_well   

#    wellY = sites_per_well[0][1]*len(set([i[3] for i in sites_per_well])) 
#    wellX = sites_per_well[0][2]*len(set([i[4]for i in sites_per_well]))

#    nuclei_id = session.query(tm.MapobjectType.id).filter_by(name="Nuclei").one()[0]
#    seg_layer_id = session.query(tm.SegmentationLayer.id).filter_by(mapobject_type_id=nuclei_id).one()[0]
#    centroids = session.query(tm.MapobjectSegmentation.partition_key, tm.MapobjectSegmentation.geom_centroid,tm.MapobjectSegmentation.mapobject_id,tm.MapobjectSegmentation.label).filter_by(segmentation_layer_id=seg_layer_id).all()
    session.expunge_all() # use this only if you want objects produced by querying a session to be usable outside the scope of the session 



#if __name__ == '__main__':

