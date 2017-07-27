import pytest

from tmlib.workflow.definition import WorkflowDefinition
from tmlib.workflow.definition import WorkflowStageDefinition

def test_create_definition_empty():
    with pytest.raises(ValueError):
        foo = WorkflowDefinition(
            name='foo',
            stages=[]
        )

def test_create_definition_wrong_type_1():
    with pytest.raises(TypeError):
        foo = WorkflowDefinition(
            name='foo',
            stages={}
        )

def test_create_definition_wrong_type_2():
    with pytest.raises(TypeError):
        foo = WorkflowDefinition(
            name='foo',
            stages=['bar']
        )

def test_create_definition_one_stage():
    foo = WorkflowDefinition(
        name='foo',
        stages=[
            WorkflowStageDefinition(
                name='a', steps=['metaextract']
            )
        ]
    )

def test_derive_definition_subclass():
    with pytest.raises(TypeError):
        class MyWorkflowDefinition(WorkflowDefinition):
            pass

def test_create_definition_set_attribute():
    foo = WorkflowDefinition(
        name='foo',
        stages=[
            WorkflowStageDefinition(
                name='a', steps=['metaextract']
            )
        ]
    )
    # Instance should not have a __dict__.
    with pytest.raises(AttributeError):
        foo.bar = 1
    # Attributes should not have setters.
    with pytest.raises(AttributeError):
        foo.stages = []
    with pytest.raises(AttributeError):
        foo.name = 'bar'

def test_create_definition_unknown_step():
    with pytest.raises(ValueError):
        foo = WorkflowDefinition(
            name='foo',
            stages=[
                WorkflowStageDefinition(
                    name='a', steps=['bar']
                )
            ]
        )

def test_create_definition_access_attributes():
    foo = WorkflowDefinition(
        name='foo',
        stages=[
            WorkflowStageDefinition(
                name='a', steps=['metaextract']
            )
        ]
    )
    assert isinstance(foo.stages, tuple)
    assert len(foo.stages) == 1
    assert len(foo.stages) == 1

def test_create_definition_duplicate_stage():
    with pytest.raises(ValueError):
        foo = WorkflowDefinition(
            name='foo',
            stages=[
                WorkflowStageDefinition(
                    name='a', steps=['metaextract']
                ),
                WorkflowStageDefinition(
                    name='a', steps=['metaconfig']
                )
            ]
        )
