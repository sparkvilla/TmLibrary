# Create Nuclei feature and new feature-values


import os
import re
import sys
import shutil
import logging
import subprocess
import numpy as np
import pandas as pd
import collections
import shapely.geometry
import shapely.ops
from cached_property import cached_property
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import func
from sqlalchemy.dialects.postgresql import FLOAT
from psycopg2 import ProgrammingError
from psycopg2.extras import Json
from gc3libs.quantity import Duration, Memory

import tmlib.models as tm
from tmlib.utils import autocreate_directory_property
from tmlib.utils import flatten
from tmlib.readers import TextReader
from tmlib.readers import ImageReader
from tmlib.writers import TextWriter
from tmlib.models.types import ST_GeomFromText
from tmlib.workflow.api import WorkflowStepAPI
from tmlib.errors import PipelineDescriptionError
from tmlib.errors import JobDescriptionError
from tmlib.workflow.jobs import SingleRunPhase
from tmlib.workflow.jterator.jobs import DebugRunJob
from tmlib.workflow import register_step_api
from tmlib import cfg

from tmlib.workflow.popcon.lcc_forTM import LocalCC

logger = logging.getLogger(__name__)

batch = {'well_ids': [3],
         'extract_object': 'Nuclei',
         'assign_object': 'Cells'}


   
for well_id in batch['well_ids']:
    logger.info('process well %d', well_id)
    with tm.utils.ExperimentSession(77) as session:
	#sites = session.query(tm.Site.id, tm.Site.height, tm.Site.width, tm.Site.y, tm.Site.x).\
	#filter_by(well_id=well_id).all()
	#wellY = sites[0][1]*len(set([i[3] for i in sites]))
	#wellX = sites[0][2]*len(set([i[4]for i in sites]))
	 
	extract_mapobject_type_id = session.query(tm.MapobjectType.id).\
	    filter_by(name=batch['extract_object']).one()[0] 
	extract_seg_layer_id = session.query(tm.SegmentationLayer.id).\
	    filter_by(mapobject_type_id=extract_mapobject_type_id).one()[0]
	extract_centroids = session.query(tm.MapobjectSegmentation.geom_centroid,tm.MapobjectSegmentation.mapobject_id,tm.MapobjectSegmentation.label,tm.MapobjectSegmentation.partition_key).\
	   filter_by(segmentation_layer_id=extract_seg_layer_id).all()

	logger.info('Calculating LCC for well_id %s', well_id)
        lcc_extract = LocalCC(extract_centroids)
	real_lcc = lcc_extract.real_distances()
	random_lcc = lcc_extract.random_distances() 
	lcc = lcc_extract.get_lcc(real_lcc,random_lcc)
        
        
    

	#logger.info('No exsisting features found in the database for %s', batch['object_name']))
        feature_name = batch['extract_object']+'_{}_lcc'.format(well_id)
#        logger.debug('add feature "%s"', feature_name)
        feature = session.get_or_create(
	         tm.Feature, name=feature_name,
	         mapobject_type_id=extract_mapobject_type_id,
	         is_aggregate=False)
        feature_values = list()
        for index, row in lcc_extract.df.iterrows():
            t=0
            logger.debug(
            'add values for mapobject #%d at time point %d',
             row['mapobject_id'], t
              )
            values = {str(int(row['mapobject_id'])): row['lcc'].astype(str)}
            feature_values.append(
                 tm.FeatureValues(
                       partition_key=int(row['site']),
                       mapobject_id=int(row['mapobject_id']),
                       tpoint=t, values=values
                       )
                 )
            logger.debug('insert feature values into db table')

        session.add_all(feature_values)


        session.expunge_all()   
#            session.commit()

#if __name__ == '__main__':
#    run_job(batch)
