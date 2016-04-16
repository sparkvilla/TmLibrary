'''Settings for the canonical `TissueMAPS` workflow.

In principle, workflow steps can be arranged in arbitrary order and
interdependencies between steps are checked dynamically while the workflow
progresses. If a dependency is not fullfilled upon progression to the
next step, i.e. if a required input has not been generated by another
upstream step, the workflow would stop. However, for the standard
workflow we would like to ensure that the sequence of steps in the workflow
description is correct and thereby prevent submission of an incorrectly
described workflow in the first place.
'''
from collections import OrderedDict
import logging


from tmlib.utils import same_docstring_as
from tmlib.utils import flatten
from tmlib.utils import assert_type
from tmlib.workflow.description import WorkflowDescription
from tmlib.workflow.description import WorkflowStageDescription
from tmlib.workflow.description import WorkflowStepDescription
from tmlib.errors import WorkflowDescriptionError
from tmlib.workflow.registry import workflow

logger = logging.getLogger(__name__)

#: List[str]: names of workflow stages
STAGES = [
    'image_conversion', 'image_preprocessing',
    'pyramid_creation', 'image_analysis'
]

#: Dict[str, str]: mode for each workflow stage, i.e. whether setps of a stage
#: should be submitted in parallel or sequentially
STAGE_MODES = {
    'image_conversion': 'sequential',
    'image_preprocessing': 'parallel',
    'pyramid_creation': 'sequential',
    'image_analysis': 'sequential'
}

#: collections.OrderedDict[str, List[str]]: names of steps within each stage
STEPS_PER_STAGE = OrderedDict({
    'image_conversion':
        ['metaextract', 'metaconfig', 'imextract'],
    'image_preprocessing':
        ['corilla', 'align'],
    'pyramid_creation':
        ['illuminati'],
    'image_analysis':
        ['jterator']
})

#: collections.OrderedDict[str, Set[str]]: dependencies between workflow stages
INTER_STAGE_DEPENDENCIES = OrderedDict({
    'image_conversion': {

    },
    'image_preprocessing': {
        'image_conversion'
    },
    'pyramid_creation': {
        'image_conversion', 'image_preprocessing'
    },
    'image_analysis': {
        'image_conversion', 'image_preprocessing'
    }
})

#: Dict[str, Set[str]: dependencies between workflow steps within one stage
INTRA_STAGE_DEPENDENCIES = {
    'metaextract': {

    },
    'metaconfig': {
        'metaextract'
    },
    'imextract': {
        'metaconfig'
    }
}


@workflow('canonical')
class CanonicalWorkflowDescription(WorkflowDescription):

    '''Description of the canonical `TissueMAPS` workflow.'''

    def __init__(self, stages=None):
        '''
        Parameters
        ----------
        **kwargs: dict, optional
            workflow description as a mapping of as key-value pairs
        '''
        super(CanonicalWorkflowDescription, self).__init__()
        if stages is not None:
            for stage in stages:
                self.add_stage(CanonicalWorkflowStageDescription(**stage))
        else:
            for name in STAGES:
                mode = STAGE_MODES[name]
                stage = {'name': name, 'mode': mode}
                self.add_stage(CanonicalWorkflowStageDescription(**stage))

    def add_stage(self, stage_description):
        '''Adds an additional stage to the workflow.

        Parameters
        ----------
        stage_description: tmlib.tmaps.canonical.CanonicalWorkflowStageDescription
            description of the stage that should be added

        Raises
        ------
        TypeError
            when `stage_description` doesn't have type
            :py:class:`tmlib.tmaps.canonical.CanonicalWorkflowStageDescription`
        WorkflowDescriptionError
            when stage already exists or when a required step is not described
        '''
        if not isinstance(stage_description, CanonicalWorkflowStageDescription):
            raise TypeError(
                'Argument "stage_description" must have type '
                'tmlib.workflow.canonical.CanonicalWorkflowStageDescription.'
            )
        for stage in self.stages:
            if stage.name == stage_description.name:
                raise WorkflowDescriptionError(
                    'Stage "%s" already exists.' % stage_description.name
                )
        if stage_description.name not in STAGES:
            raise WorkflowDescriptionError(
                'Unknown stage "%s". Implemented stages are: "%s"'
                % (stage_description.name, '", "'.join(STAGES))
            )
        for step in stage_description.steps:
            implemented_steps = STEPS_PER_STAGE[stage_description.name]
            if step.name not in implemented_steps:
                raise WorkflowDescriptionError(
                    'Unknown step "%s" for stage "%s". '
                    'Implemented steps are: "%s"'
                    % (step.name, stage_description.name,
                        '", "'.join(implemented_steps))
                )
        stage_names = [s.name for s in self.stages]
        if stage_description.name in INTER_STAGE_DEPENDENCIES:
            for dep in INTER_STAGE_DEPENDENCIES[stage_description.name]:
                if dep not in stage_names:
                    logger.warning(
                        'stage "%s" requires upstream stage "%s"',
                        stage_description.name, dep
                    )
        for name in stage_names:
            if stage_description.name in INTER_STAGE_DEPENDENCIES[name]:
                raise WorkflowDescriptionError(
                    'Stage "%s" must be upstream of stage "%s".'
                    % (stage_description.name, name)
                )
        step_names = [s.name for s in stage_description.steps]
        required_steps = STEPS_PER_STAGE[stage_description.name]
        for name in step_names:
            if name not in required_steps:
                raise WorkflowDescriptionError(
                    'Stage "%s" requires the following steps: "%s" '
                    % '", "'.join(required_steps)
                )
        self.stages.append(stage_description)


class CanonicalWorkflowStageDescription(WorkflowStageDescription):

    '''Description of a stage of the canonical `TissueMAPS` workflow.'''

    def __init__(self, name, mode, steps=None):
        '''
        Parameters
        ----------
        name: str
            name of the stage
        mode: str
            mode of workflow stage submission
        steps: list, optional
            description of individual steps as a mapping of key-value pairs
        **kwargs: dict, optional
            description of a workflow stage in form of key-value pairs
        '''
        super(CanonicalWorkflowStageDescription, self).__init__(name, mode)
        if steps is not None:
            for step in steps:
                self.add_step(CanonicalWorkflowStepDescription(**step))
        else:
            for name in STEPS_PER_STAGE[self.name]:
                step = {'name': name}
                self.add_step(CanonicalWorkflowStepDescription(**step))

    def add_step(self, step_description):
        '''Adds an additional step to the stage.

        Parameters
        ----------
        step_description: tmlib.tmaps.canonical.CanonicalWorkflowStepDescription
            description of the step that should be added

        Raises
        ------
        TypeError
            when `step_description` doesn't have type
            :py:class:`tmlib.tmaps.canonical.CanonicalWorkflowStepDescription`
        workflowDescriptionError
            when step already exists or a required upstream step is missing
        '''
        if not isinstance(step_description, CanonicalWorkflowStepDescription):
            raise TypeError(
                'Argument "step_description" must have type '
                'tmlib.cfg.CanonicalWorkflowStepDescription.'
            )
        for step in self.steps:
            if step.name == step_description.name:
                raise WorkflowDescriptionError(
                    'Step "%s" already exists.' % step_description.name
                )
        steps = STEPS_PER_STAGE[self.name]
        if step_description.name not in steps:
            raise WorkflowDescriptionError(
                'Unknown step "%s" for stage "%s". Known steps are: "%s"'
                % (step_description.name, self.name, '", "'.join(steps))
            )
        name = step_description.name
        step_names = [s.name for s in self.steps]
        if name in INTRA_STAGE_DEPENDENCIES:
            for dep in INTRA_STAGE_DEPENDENCIES[name]:
                if dep not in step_names:
                    raise WorkflowDescriptionError(
                        'Step "%s" requires upstream step "%s".' % (name, dep)
                    )
        self.steps.append(step_description)


class CanonicalWorkflowStepDescription(WorkflowStepDescription):

    '''Description of a step of a canonical `TissueMAPS` workflow.'''

    @same_docstring_as(WorkflowStepDescription.__init__)
    def __init__(self, name, batch_args=dict(), submission_args=dict(),
            extra_args=dict()):
        super(CanonicalWorkflowStepDescription, self).__init__(
            name, batch_args, submission_args, extra_args
        )
