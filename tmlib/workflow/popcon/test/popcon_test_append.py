# TmLibrary - TissueMAPS library for distibuted image analysis routines.
# Copyright (C) 2016  Markus D. Herrmann, University of Zurich and Robin Hafen
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
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

	assign_mapobject_type_id = session.query(tm.MapobjectType.id).\
	    filter_by(name=batch['assign_object']).one()[0] 
	assign_seg_layer_id = session.query(tm.SegmentationLayer.id).\
	    filter_by(mapobject_type_id=assign_mapobject_type_id).one()[0]
	assign_centroids = session.query(tm.MapobjectSegmentation.geom_centroid,tm.MapobjectSegmentation.mapobject_id,tm.MapobjectSegmentation.label,tm.MapobjectSegmentation.partition_key).\
	   filter_by(segmentation_layer_id=assign_seg_layer_id).all()

	logger.info('Calculating LCC for well_id %s', well_id)
        lcc_extract = LocalCC(extract_centroids)
	real_lcc = lcc_extract.real_distances()
	random_lcc = lcc_extract.random_distances() 
	lcc = lcc_extract.get_lcc(real_lcc,random_lcc)
        
        lcc_assign = LocalCC(assign_centroids)
        
        # remap y,x coordinates of extract object with mapobject_id
        # of assign object  
        lcc_extract.df['mapobject_id'] = lcc_assign.df['mapobject_id']
    
        #features = session.query(tm.Feature).filter_by(mapobject_type_id=mapobject_type_id)

	#logger.info('No exsisting features found in the database for %s', batch['object_name']))
        feature_name = batch['extract_object']+'_{}_lcc'.format(well_id)
#        logger.debug('add feature "%s"', feature_name)
        feature = session.get_or_create(
	         tm.Feature, name=feature_name,
	         mapobject_type_id=assign_mapobject_type_id,
	         is_aggregate=False)
#        feature_values = list()
        for index, row in lcc_extract.df.iterrows():
            feature_value = session.query(tm.FeatureValues).filter_by(mapobject_id= int(row['mapobject_id']) ).one() 
            session.append_value(feature_value,str(feature.id),row['lcc'].astype(str))
            
            session.commit() 
        #session.expunge_all()   
            #session.commit()

#if __name__ == '__main__':
#    run_job(batch)
