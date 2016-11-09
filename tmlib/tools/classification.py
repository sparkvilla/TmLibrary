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
import logging

import tmlib.models as tm
from tmlib.utils import same_docstring_as

from tmlib.tools.base import Tool, Classifier

logger = logging.getLogger(__name__)


class Classification(Classifier):

    '''Tool for supervised classification.'''

    __icon__ = 'SVC'

    __description__ = '''
        Classifies mapobjects based on the values of selected features and
        labels provided by the user.
    '''

    __options__ = {'method': ['randomforest'], 'n_fold_cv': 10}

    @same_docstring_as(Tool.__init__)
    def __init__(self, experiment_id):
        super(Classification, self).__init__(experiment_id)

    def process_request(self, submission_id, payload):
        '''Processes a client tool request and inserts the generated result
        into the database.
        The `payload` is expected to have the following form::

            {
                "choosen_object_type": str,
                "selected_features": [str, ...],
                "training_classes": [
                    {
                        "name": str,
                        "object_ids": [int, ...],
                        "color": str
                    },
                    ...
                ],
                "options": {
                    "method": str,
                    "n_fold_cv": int
                }

            }

        Parameters
        ----------
        submission_id: int
            ID of the corresponding job submission
        payload: dict
            description of the tool job
        '''
        # Get mapobject
        mapobject_type_name = payload['chosen_object_type']
        feature_names = payload['selected_features']
        method = payload['options']['method']
        n_fold_cv = payload['options']['n_fold_cv']

        if method not in self.__options__['method']:
            raise ValueError('Unknown method "%s".' % method)

        labeled_mapobjects = list()
        label_map = dict()
        for i, cls in enumerate(payload['training_classes']):
            labels = [(j, i) for j in cls['object_ids']]
            labeled_mapobjects.extend(labels)
            label_map[float(i)] = {
                'name': cls['name'],
                'color': cls['color']
            }

        unlabeled_feature_data = self.load_feature_values(
            mapobject_type_name, feature_names
        )
        labeled_feature_data = self.label_feature_data(
            unlabeled_feature_data, labeled_mapobjects
        )
        predicted_labels = self.classify_supervised(
            unlabeled_feature_data, labeled_feature_data, method, n_fold_cv
        )

        unique_labels = self.calculate_unique(predicted_labels, 'label')
        result_id = self.initialize_result(
            submission_id, mapobject_type_name,
            layer_type='SupervisedClassifierLabelLayer',
            unique_labels=unique_labels, label_map=label_map
        )

        self.save_label_values(result_id, predicted_labels)
