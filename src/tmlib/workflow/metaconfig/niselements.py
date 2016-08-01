'''Implementation of classes for reading microscope image and metadata files
provided in a format specific to microscopes equipped
with
`Nikon NISElements <https://www.nikoninstruments.com/Products/Software>`_
software.
'''

import os
import re
import logging
import bioformats
from collections import defaultdict

from tmlib import utils
from tmlib.workflow.metaconfig.base import MetadataReader
from tmlib.workflow.metaconfig.base import MetadataHandler
from tmlib.workflow.metaconfig.omexml import XML_DECLARATION

logger = logging.getLogger(__name__)

#: Regular expression pattern to identify image files
# TODO: how are time points encoded?
IMAGE_FILE_REGEX_PATTERN = '.+_t(?P<t>\d+)_(?P<w>[A-Z]\d+)_(?P<s>\d+)-(?P<c>\d+)\.nd2'

#: Supported extensions for metadata files
METADATA_FILE_REGEX_PATTERN = r'(?!.*)'


class NISElementsMetadataHandler(MetadataHandler):

    '''Class for handling metadata specific to microscopes equipped with
    NISElements software.
    '''

    #: Regular expression pattern to identify image files
    IMAGE_FILE_REGEX_PATTERN = IMAGE_FILE_REGEX_PATTERN

    def __init__(self, omexml_images, omexml_metadata=None):
        '''
        Parameters
        ----------
        omexml_images: Dict[str, bioformats.omexml.OMEXML]
            metadata extracted from microscope image files
        omexml_metadata: bioformats.omexml.OMEXML
            metadata extracted from microscope metadata files
        '''
        super(NISElementsMetadataHandler, self).__init__(
            omexml_images, omexml_metadata
        )


class NISElementsMetadataReader(MetadataReader):

    '''Class for reading metadata from files formats specific to microscopes
    equipped with NISElements software.

    Note
    ----
    The microscope doens't provide any metadata files.
    '''

    def read(self, microscope_metadata_files, microscope_image_files):
        '''Read metadata from "nd" metadata file.

        Parameters
        ----------
        microscope_metadata_files: List[str]
            absolute path to the microscope metadata files
        microscope_image_files: List[str]
            absolute path to the microscope image files

        Returns
        -------
        bioformats.omexml.OMEXML
            OMEXML image metadata
        '''
        return bioformats.OMEXML(XML_DECLARATION)
