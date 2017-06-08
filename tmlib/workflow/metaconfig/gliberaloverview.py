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
'''Implementation of classes for reading microscope image files
provided in a custom well-overview format specfic to the Liberali group at FMI.
'''
import logging

from tmlib.workflow.metaconfig.base import MetadataHandler

logger = logging.getLogger(__name__)

#: Regular expression pattern to identify image files
IMAGE_FILE_REGEX_PATTERN = r'.*_(?P<w>[A-Z]\d{2})_[A-Z0-9]*Z(?P<z>\d{2})C(?P<c>\d{2}).tif'

#: Supported extensions for metadata files
METADATA_FILE_REGEX_PATTERN = r'(?!.*)'


class GLiberalOverviewMetadataHandler(MetadataHandler):

    '''Class for handling metadata of well-overview images specific to the
    Liberali group.
    '''

    def __init__(self, omexml_images, omexml_metadata=None):
        '''
        Parameters
        ----------
        omexml_images: Dict[str, bioformats.omexml.OMEXML]
            metadata extracted from microscope image files
        omexml_metadata: bioformats.omexml.OMEXML
            metadata extracted from microscope metadata files 
        '''
        super(GLiberalOverviewMetadataHandler, self).__init__(
            omexml_images, omexml_metadata
        )

