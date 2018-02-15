# TmLibrary - TissueMAPS library for distibuted image analysis routines.
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

from tmlib.workflow.popcon.lcc import LocalCC

logger = logging.getLogger(__name__)


@register_step_api('popcon')
class CrowdingEstimator(WorkflowStepAPI):

    '''Class for running image analysis pipelines.'''

    def __init__(self, experiment_id):
        '''
        Parameters
        ----------
        experiment_id: int
            ID of the processed experiment
        '''
        super(CrowdingEstimator, self).__init__(experiment_id)

    def create_run_batches(self, args):
        '''Creates job descriptions for parallel computing.

        Parameters
        ----------
        args: tmlib.workflow.jterator.args.BatchArguments
            step-specific arguments

        Returns
        -------
        generator
            job descriptions
        '''
        with tm.utils.ExperimentSession(self.experiment_id) as session:
            # Distribute wells randomly. Thereby we achieve a certain level
            # of load balancing in case wells have different number of cells,
            # for example.
            wells = session.query(tm.Well.id).order_by(func.random()).all()
            well_ids = [w.id for w in wells]
            batches = self._create_batches(well_ids, args.batch_size)
            for j, batch in enumerate(batches):
                yield {
                    'id': j + 1,  # job IDs are one-based!
                    'well_ids': batch,
                    'extract_object': args.extract_object,
                    'assign_object': args.assign_object
                }


    def run_job(self, batch, assume_clean_state):
        '''Runs the pipeline, i.e. executes modules sequentially. After
         Parameters
        ----------
        batch: dict
            job description
        assume_clean_state: bool, optional
            assume that output of previous runs has already been cleaned up
        '''

        for well_id in batch['well_ids']:
            logger.info('process well %d', well_id)
            with tm.utils.ExperimentSession(self.experiment_id) as session:
#	        sites = session.query(tm.Site.id, tm.Site.height, tm.Site.width, tm.Site.y, tm.Site.x).\
#                filter_by(well_id=well_id).all()
#                wellY = sites_per_well[0][1]*len(set([i[3] for i in sites_per_well]))
#                wellX = sites_per_well[0][2]*len(set([i[4]for i in sites_per_well]))
                 
                extract_mapobject_type_id = session.query(tm.MapobjectType.id).\
                    filter_by(name=batch['extract_object']).one()[0] 
                extract_seg_layer_id = session.query(tm.SegmentationLayer.id).\
                    filter_by(mapobject_type_id=mapobject_type_id).one()[0]
                extract_centroids = session.query(tm.MapobjectSegmentation.geom_centroid,tm.MapobjectSegmentation.mapobject_id,tm.MapobjectSegmentation.label,tm.MapobjectSegmentation.partition_key).\
                   filter_by(segmentation_layer_id=extract_seg_layer_id).all()
                assign_mapobject_type_id = session.query(tm.MapobjectType.id).\
                    filter_by(name=batch['assign_object']).one()[0] 
                assign_seg_layer_id = session.query(tm.SegmentationLayer.id).\
                    filter_by(mapobject_type_id=assign_mapobject_type_id).one()[0]
                assign_centroids = session.query(tm.MapobjectSegmentation.geom_centroid,tm.MapobjectSegmentation.mapobject_id,tm.MapobjectSegmentation.label,tm.MapobjectSegmentation.partition_kye).\
                   filter_by(segmentation_layer_id=assign_seg_layer_id).all()
 
                logger.info('Calculating LCC for well_id %s', well_id)
                lcc_extract = LocalCC(extract_centroids)
                real_lcc = lcc_extract.real_distances()
                random_lcc = lcc_extract.random_distances() 
                lcc = lcc_extract.get_lcc(real_lcc,random_lcc)

                lcc_assign = Local(assign_centroids)

                # remap y,x coordinates of extract object with mapobject_id
                # of assign object
                lcc_extract.df['mapobject_id'] = lcc_assign.df['mapobject_id'] 


                feature_name = batch['extract_object']+'_{}_lcc'.format(well_id)
                feature = session.get_or_create(
                          tm.Feature, name=feature_name, 
                          mapobject_type_id=assign_mapobject_type_id,   
                          is_aggregate=False) 


                for index, row in lcc_extract.df.iterrows():    
                    feature_value = session.query(tm.FeatureValues).filter_by(mapobject_id= int(row['mapobject_id']) ).one()
                    session.append_value(feature_value,str(feature.id),row['lcc'].astype(str))
                    session.commit()




    def collect_job_output(self, batch):
        pass

