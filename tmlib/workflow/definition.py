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
import collections

from tmlib.workflow import get_step_information
from tmlib.utils import assert_type, FixMeta


_workflow_register = dict()


class WorkflowStageDefinition(object):

    '''Class for definining the computational graph of a
    :class:`WorkflowStage <tmlib.workflow.workflow.WorkflowStage>`

    Instances of the class define the name of a stage and the order of steps.
    They are used to check whether a user provided
    :class:`WorkflowStageDescription <tmlib.workflow.description.WorkflowStageDescription>`
    is valid.

    '''

    __slots__ = ('_name', '_steps', '_concurrent')

    __metaclass__ = FixMeta

    @assert_type(name='basestring', steps='list')
    def __init__(self, name, steps, concurrent=False):
        self._name = str(name)
        self._steps = list()
        for s in steps:
            if not isinstance(s, basestring):
                raise TypeError(
                    'Elements of argument "steps" must have type strings.'
                )
            try:
                info = get_step_information(s)
            except ImportError:
                raise ValueError('Unknown step "%s".')
            # TODO: Check whether step has to be __unique__
            self._steps.append(str(s))
        if not isinstance(concurrent, bool):
            raise TypeError('Argument "concurrent" must have type bool.')
        self._concurrent = concurrent

    @property
    def name(self):
        '''str: name of the stage'''
        return self._name

    @property
    def concurrent(self):
        '''bool: whether steps should be executed in parallel'''
        return self._concurrent

    @property
    def steps(self):
        '''Tuple[str]: names of steps

        Note
        ----
        The attribute defines the order in which steps must be executed
        in case ``concurrent`` is ``False``.
        '''
        return tuple(self._steps)

    def to_dict(self):
        '''Returns attributes of the class as a mapping of key-value pairs.

        Returns
        -------
        dict
        '''
        return {
            'name': self.name,
            'concurrent': self.concurrent,
            'steps': self._steps
        }


class _WorkflowDefinitionMeta(FixMeta):

    def __call__(cls, name, *args, **kwargs):
        # We store all instances of classes in a dictionary, such that we
        # can conveniently retrieve definied workflow types from the register.
        instance = type.__call__(cls, name, *args, **kwargs)
        _workflow_register[name] = instance
        return instance


class WorkflowDefinition(object):

    '''Class for definition of a
    :class:`Workflow <tmlib.workflow.workflow.Workflow>`.

    Instances of the class define the order of stages and provide information
    about each required stage in form of a
    :class:`WorkflowStageDefinition <tmlib.workflow.definition.WorkflowStageDefinition>`.
    They are used to check whether a user provided
    :class:`WorkflowDescription <tmlib.workflow.description.WorkflowDescription>`
    is valid.

    '''

    __metaclass__ = _WorkflowDefinitionMeta

    __slots__ = ('_name', '_stages')

    @assert_type(name='basestring', stages='list')
    def __init__(self, name, stages):
        '''
        Parameters
        ----------
        name: str
            name of the workflow type
        '''
        self._name = name
        if len(stages) == 0:
            raise ValueError('Argument "stages" must not be empty.')
        self._stages = list()
        for s in stages:
            if not isinstance(s, WorkflowStageDefinition):
                raise TypeError(
                    'Elements of argument "stages" must have type "%s".' %
                    WorkflowStageDefinition.__name__
                )
            existing_stages = [stage.name for stage in self._stages]
            if s.name in existing_stages:
                raise ValueError('Stage "%s" is already defined.')
            self._stages.append(s)

    @property
    def name(self):
        '''str: name of the workflow type'''
        return str(self._name)

    @property
    def stages(self):
        '''Tuple[tmlib.workflow.definition.WorkflowStageDefinition]: stages
        of the workflow
        '''
        return tuple(self._stages)

    def get_stage(self, name):
        '''Retrieves a defined stage.

        Parameters
        ----------
        name: str
            name of a defined stage

        Returns
        -------
        tmlib.workflow.definition.WorkflowStageDefinition
            stage definition

        Raises
        ------
        ValueError
            when no such stage exists
        '''
        stage_names = [s.name for s in self.stages]
        try:
            index = stage_names.index(name)
        except ValueError:
            raise ValueError('Stage "%s" is not defined.' % name)
        return self._stages[index]

    def to_dict(self):
        '''Returns attributes of the class as a mapping of key-value pairs.

        Returns
        -------
        dict
        '''
        return {
            'name': self.name,
            'stages': [s.to_dict() for s in self.stages]
        }


def get_workflow_types():
    '''Provides the names of available workflow types.

    Returns
    -------
    Set[str]
        names of workflow types

    '''
    return set(_workflow_register.keys())


def get_workflow_definition(name):
    '''Provides a
    :class:`WorkflowDefinition <tmlib.workflow.definition.WorkflowDefinition>`.

    Parameters
    ----------
    name: str
        name of a workflow type

    Returns
    -------
    tmlib.workflow.definition.WorkflowDefinition
        workflow definition
    '''
    try:
        return _workflow_register[name]
    except KeyError:
        raise KeyError('Worflow type "%s" is not defined.' % name)


_canonical = WorkflowDefinition(
    name='canonical',
    stages = [
        WorkflowStageDefinition(
            name='image_conversion', concurrent=False,
            steps=['metaextract', 'metaconfig', 'imextract']
        ),
        WorkflowStageDefinition(
            name='image_preprocessing', concurrent=True,
            steps=['corilla']
        ),
        WorkflowStageDefinition(
            name='pyramid_creation', concurrent=False,
            steps=['illuminati']
        ),
        WorkflowStageDefinition(
            name='pyramid_creation', concurrent=False,
            steps=['jterator']
        )
    ]
)


_multiplexing = WorkflowDefinition(
    name='multiplexing',
    stages = [
        WorkflowStageDefinition(
            name='image_conversion', concurrent=False,
            steps=['metaextract', 'metaconfig', 'imextract']
        ),
        WorkflowStageDefinition(
            name='image_preprocessing', concurrent=False,
            steps=['corilla', 'align']
        ),
        WorkflowStageDefinition(
            name='pyramid_creation', concurrent=False,
            steps=['illuminati']
        ),
        WorkflowStageDefinition(
            name='pyramid_creation', concurrent=False,
            steps=['jterator']
        )
    ]
)

