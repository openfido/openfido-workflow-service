from unittest.mock import call, patch

import pytest
from app import db
from app.model_utils import RunStateEnum
from app.pipelines.models import PipelineRunArtifact
from app.pipelines.services import (
    create_pipeline_run,
    create_pipeline_run_state,
    create_pipeline,
)
from app.workflows import services
from app.workflows.models import WorkflowPipeline
from app.workflows.queries import find_workflow, find_workflow_pipeline
from marshmallow.exceptions import ValidationError

from ..pipelines.test_services import VALID_CALLBACK_INPUT


def _create_workflow_pipeline_json(pipeline, sources=[], dests=[]):
    return {
        "pipeline_uuid": pipeline.uuid,
        "source_workflow_pipelines": sources,
        "destination_workflow_pipelines": dests,
    }


def test_create_workflow_bad_params(app):
    with pytest.raises(ValidationError):
        services.create_workflow(None)
    with pytest.raises(ValidationError):
        services.create_workflow({})
    with pytest.raises(ValidationError):
        services.create_workflow({"name": "", "description": ""})


def test_create_workflow_bad_params(app):
    workflow = services.create_workflow({"name": "a workflow", "description": "desc"})
    assert workflow.uuid is not None
    assert workflow.name == "a workflow"
    assert workflow.description == "desc"


def test_update_workflow_bad_params(app, workflow):
    with pytest.raises(ValueError):
        services.update_workflow("no-id", {"name": "", "description": ""})
    with pytest.raises(ValidationError):
        services.update_workflow(workflow.uuid, {})
    with pytest.raises(ValidationError):
        services.update_workflow(workflow.uuid, {"name": "", "description": ""})


def test_update_workflow_bad_params(app, workflow):
    workflow = services.update_workflow(
        workflow.uuid, {"name": "updated workflow", "description": "update desc"}
    )
    assert workflow.uuid is not None
    assert workflow.name == "updated workflow"
    assert workflow.description == "update desc"


def test_delete_workflow_no_id(app):
    with pytest.raises(ValueError):
        services.delete_workflow("no-id")


def test_delete_workflow(app, workflow):
    the_uuid = workflow.uuid
    services.delete_workflow(the_uuid)
    assert find_workflow(the_uuid) is None


def test_delete_workflow_pipeline_no_id(app, workflow):
    with pytest.raises(ValueError):
        services.delete_workflow_pipeline("no-id", "no-id")
    with pytest.raises(ValueError):
        services.delete_workflow_pipeline(workflow.uuid, "no-id")


def test_delete_workflow_pipeline(app, workflow, workflow_pipeline):
    the_uuid = workflow_pipeline.uuid
    services.delete_workflow_pipeline(workflow.uuid, workflow_pipeline.uuid)
    assert workflow_pipeline.is_deleted
    assert find_workflow_pipeline(the_uuid) is None


def test_delete_workflow_pipeline_via_delete_workflow(app, workflow, workflow_pipeline):
    services.delete_workflow(workflow.uuid)
    assert find_workflow_pipeline(workflow_pipeline.uuid) is None


def test_create_workflow_pipeline_no_workflow(app):
    with pytest.raises(ValueError):
        workflow_pipeline = services.create_workflow_pipeline(
            "no-id",
            {
                "pipeline_uuid": "no-id",
                "source_workflow_pipelines": [],
                "destination_workflow_pipelines": [],
            },
        )


def test_create_workflow_pipeline_no_pipeline(app, workflow):
    with pytest.raises(ValueError):
        workflow_pipeline = services.create_workflow_pipeline(
            workflow.uuid,
            {
                "pipeline_uuid": "a" * 32,
                "source_workflow_pipelines": [],
                "destination_workflow_pipelines": [],
            },
        )


def test_create_workflow_pipeline_no_source(app, pipeline, workflow):
    with pytest.raises(ValueError):
        services.create_workflow_pipeline(
            workflow.uuid,
            {
                "pipeline_uuid": pipeline.uuid,
                "source_workflow_pipelines": ["a" * 32],
                "destination_workflow_pipelines": [],
            },
        )
    assert (
        WorkflowPipeline.query.filter(
            WorkflowPipeline.pipeline == pipeline
        ).one_or_none()
        is None
    )


def test_create_workflow_pipeline_no_dest(app, pipeline, workflow):
    with pytest.raises(ValueError):
        services.create_workflow_pipeline(
            workflow.uuid,
            {
                "pipeline_uuid": pipeline.uuid,
                "source_workflow_pipelines": [],
                "destination_workflow_pipelines": ["a" * 32],
            },
        )
    assert (
        WorkflowPipeline.query.filter(
            WorkflowPipeline.pipeline == pipeline
        ).one_or_none()
        is None
    )


@patch("app.workflows.services.is_dag")
def test_create_workflow_pipeline_from_cycle(is_dag_mock, app, pipeline, workflow):
    is_dag_mock.return_value = False

    workflow_pipeline = services.create_workflow_pipeline(
        workflow.uuid,
        {
            "pipeline_uuid": pipeline.uuid,
            "source_workflow_pipelines": [],
            "destination_workflow_pipelines": [],
        },
    )

    with pytest.raises(ValidationError):
        services.create_workflow_pipeline(
            workflow.uuid,
            {
                "pipeline_uuid": pipeline.uuid,
                "source_workflow_pipelines": [workflow_pipeline.uuid],
                "destination_workflow_pipelines": [],
            },
        )

    with pytest.raises(ValidationError):
        services.create_workflow_pipeline(
            workflow.uuid,
            {
                "pipeline_uuid": pipeline.uuid,
                "source_workflow_pipelines": [],
                "destination_workflow_pipelines": [workflow_pipeline.uuid],
            },
        )


def test_create_workflow_pipeline(app, pipeline, workflow):
    # Creating a workflow pipeline with no sources/destinations is possible.
    workflow_pipeline = services.create_workflow_pipeline(
        workflow.uuid,
        _create_workflow_pipeline_json(pipeline),
    )
    assert workflow_pipeline.pipeline == pipeline
    assert workflow_pipeline.source_workflow_pipelines == []
    assert workflow_pipeline.dest_workflow_pipelines == []

    # Creating a workflow pipeline with a source
    source_workflow_pipeline = services.create_workflow_pipeline(
        workflow.uuid,
        {
            "pipeline_uuid": pipeline.uuid,
            "source_workflow_pipelines": [workflow_pipeline.uuid],
            "destination_workflow_pipelines": [],
        },
    )
    assert source_workflow_pipeline.pipeline == pipeline
    assert len(source_workflow_pipeline.source_workflow_pipelines) == 1
    assert len(source_workflow_pipeline.dest_workflow_pipelines) == 0
    assert (
        source_workflow_pipeline.source_workflow_pipelines[0].from_workflow_pipeline
        == workflow_pipeline
    )
    assert (
        source_workflow_pipeline.source_workflow_pipelines[0].to_workflow_pipeline
        == source_workflow_pipeline
    )

    # Creating a workflow pipeline with a destination
    source_workflow_pipeline = services.create_workflow_pipeline(
        workflow.uuid,
        {
            "pipeline_uuid": pipeline.uuid,
            "source_workflow_pipelines": [],
            "destination_workflow_pipelines": [workflow_pipeline.uuid],
        },
    )
    assert source_workflow_pipeline.pipeline == pipeline
    assert len(source_workflow_pipeline.source_workflow_pipelines) == 0
    assert len(source_workflow_pipeline.dest_workflow_pipelines) == 1
    assert (
        source_workflow_pipeline.dest_workflow_pipelines[0].from_workflow_pipeline
        == source_workflow_pipeline
    )
    assert (
        source_workflow_pipeline.dest_workflow_pipelines[0].to_workflow_pipeline
        == workflow_pipeline
    )

    # Creating a workflow pipeline with a destination
    with_both_pipeline = services.create_workflow_pipeline(
        workflow.uuid,
        {
            "pipeline_uuid": pipeline.uuid,
            "source_workflow_pipelines": [source_workflow_pipeline.uuid],
            "destination_workflow_pipelines": [workflow_pipeline.uuid],
        },
    )
    assert with_both_pipeline.pipeline == pipeline
    assert len(with_both_pipeline.source_workflow_pipelines) == 1
    assert len(with_both_pipeline.dest_workflow_pipelines) == 1
    assert (
        with_both_pipeline.source_workflow_pipelines[0].from_workflow_pipeline
        == source_workflow_pipeline
    )
    assert (
        with_both_pipeline.source_workflow_pipelines[0].to_workflow_pipeline
        == with_both_pipeline
    )
    assert (
        with_both_pipeline.dest_workflow_pipelines[0].from_workflow_pipeline
        == with_both_pipeline
    )
    assert (
        with_both_pipeline.dest_workflow_pipelines[0].to_workflow_pipeline
        == workflow_pipeline
    )


def test_update_workflow_pipeline_bad_id(app, workflow_pipeline):
    with pytest.raises(ValueError):
        services.update_workflow_pipeline(
            "0" * 32,
            "0" * 32,
            _create_workflow_pipeline_json(workflow_pipeline.pipeline),
        )

    with pytest.raises(ValueError):
        services.update_workflow_pipeline(
            "0" * 32,
            workflow_pipeline.uuid,
            _create_workflow_pipeline_json(workflow_pipeline.pipeline),
        )

    with pytest.raises(ValueError):
        services.update_workflow_pipeline(
            workflow_pipeline.workflow.uuid,
            "0" * 32,
            _create_workflow_pipeline_json(workflow_pipeline.pipeline),
        )


def test_update_workflow_pipeline_remove_bad_ids(app, pipeline, workflow_pipeline):
    with pytest.raises(ValueError):
        workflow_pipeline = services.update_workflow_pipeline(
            workflow_pipeline.workflow.uuid,
            workflow_pipeline.uuid,
            _create_workflow_pipeline_json(workflow_pipeline.pipeline, ["0" * 32]),
        )

    with pytest.raises(ValueError):
        workflow_pipeline = services.update_workflow_pipeline(
            workflow_pipeline.workflow.uuid,
            workflow_pipeline.uuid,
            _create_workflow_pipeline_json(workflow_pipeline.pipeline, [], ["0" * 32]),
        )

    with pytest.raises(ValueError):
        workflow_pipeline = services.update_workflow_pipeline(
            workflow_pipeline.workflow.uuid,
            workflow_pipeline.uuid,
            {
                "pipeline_uuid": "0" * 32,
                "source_workflow_pipelines": [],
                "destination_workflow_pipelines": [],
            },
        )


def test_update_workflow_pipeline_no_change(app, pipeline, workflow_pipeline):
    workflow_pipeline = services.update_workflow_pipeline(
        workflow_pipeline.workflow.uuid,
        workflow_pipeline.uuid,
        _create_workflow_pipeline_json(workflow_pipeline.pipeline),
    )
    assert workflow_pipeline.pipeline == pipeline
    assert workflow_pipeline.source_workflow_pipelines == []
    assert workflow_pipeline.dest_workflow_pipelines == []


def test_update_workflow_pipeline_update_pipeline(app, pipeline, workflow_pipeline):
    new_pipeline = create_pipeline(
        "new p", "dest", "python", "https://example.com", "master"
    )
    db.session.commit()
    new_json = _create_workflow_pipeline_json(workflow_pipeline.pipeline)
    new_json["pipeline_uuid"] = new_pipeline.uuid
    workflow_pipeline = services.update_workflow_pipeline(
        workflow_pipeline.workflow.uuid, workflow_pipeline.uuid, new_json
    )
    assert workflow_pipeline.pipeline == new_pipeline
    assert workflow_pipeline.source_workflow_pipelines == []
    assert workflow_pipeline.dest_workflow_pipelines == []


def test_update_workflow_pipeline_add_source(app, pipeline, workflow_pipeline):
    pipeline_with_source = services.create_workflow_pipeline(
        workflow_pipeline.workflow.uuid,
        _create_workflow_pipeline_json(
            workflow_pipeline.pipeline, [workflow_pipeline.uuid]
        ),
    )
    new_source = services.create_workflow_pipeline(
        workflow_pipeline.workflow.uuid,
        _create_workflow_pipeline_json(workflow_pipeline.pipeline),
    )
    updated_pipeline = services.update_workflow_pipeline(
        pipeline_with_source.workflow.uuid,
        pipeline_with_source.uuid,
        _create_workflow_pipeline_json(
            workflow_pipeline.pipeline,
            [workflow_pipeline.uuid, workflow_pipeline.uuid, new_source.uuid],
        ),
    )
    assert updated_pipeline.pipeline == pipeline
    assert [
        s.from_workflow_pipeline for s in updated_pipeline.source_workflow_pipelines
    ] == [workflow_pipeline, new_source]
    assert [
        s.to_workflow_pipeline for s in updated_pipeline.source_workflow_pipelines
    ] == [updated_pipeline, updated_pipeline]
    assert updated_pipeline.dest_workflow_pipelines == []

    # removing a source also happens!
    updated_pipeline = services.update_workflow_pipeline(
        pipeline_with_source.workflow.uuid,
        pipeline_with_source.uuid,
        _create_workflow_pipeline_json(
            workflow_pipeline.pipeline, [workflow_pipeline.uuid]
        ),
    )
    assert [
        s.from_workflow_pipeline for s in updated_pipeline.source_workflow_pipelines
    ] == [workflow_pipeline]

    updated_pipeline = services.update_workflow_pipeline(
        pipeline_with_source.workflow.uuid,
        pipeline_with_source.uuid,
        _create_workflow_pipeline_json(workflow_pipeline.pipeline),
    )
    assert updated_pipeline.source_workflow_pipelines == []
    assert updated_pipeline.dest_workflow_pipelines == []


def test_update_workflow_pipeline_add_dest(app, pipeline, workflow_pipeline):
    pipeline_with_dest = services.create_workflow_pipeline(
        workflow_pipeline.workflow.uuid,
        _create_workflow_pipeline_json(
            workflow_pipeline.pipeline, [], [workflow_pipeline.uuid]
        ),
    )
    new_dest = services.create_workflow_pipeline(
        workflow_pipeline.workflow.uuid,
        _create_workflow_pipeline_json(workflow_pipeline.pipeline),
    )
    updated_pipeline = services.update_workflow_pipeline(
        pipeline_with_dest.workflow.uuid,
        pipeline_with_dest.uuid,
        _create_workflow_pipeline_json(
            workflow_pipeline.pipeline,
            [],
            [workflow_pipeline.uuid, new_dest.uuid, new_dest.uuid],
        ),
    )
    assert updated_pipeline.pipeline == pipeline
    assert [
        s.to_workflow_pipeline for s in updated_pipeline.dest_workflow_pipelines
    ] == [workflow_pipeline, new_dest]
    assert [
        s.from_workflow_pipeline for s in updated_pipeline.dest_workflow_pipelines
    ] == [updated_pipeline, updated_pipeline]
    assert updated_pipeline.source_workflow_pipelines == []

    # removing a dest also happens!
    updated_pipeline = services.update_workflow_pipeline(
        pipeline_with_dest.workflow.uuid,
        pipeline_with_dest.uuid,
        _create_workflow_pipeline_json(
            workflow_pipeline.pipeline, [], [workflow_pipeline.uuid]
        ),
    )
    assert [
        s.to_workflow_pipeline for s in updated_pipeline.dest_workflow_pipelines
    ] == [workflow_pipeline]

    updated_pipeline = services.update_workflow_pipeline(
        pipeline_with_dest.workflow.uuid,
        pipeline_with_dest.uuid,
        _create_workflow_pipeline_json(workflow_pipeline.pipeline),
    )
    assert updated_pipeline.source_workflow_pipelines == []
    assert updated_pipeline.dest_workflow_pipelines == []


def test_create_workflow_run_no_workflow(app, pipeline, workflow):
    with pytest.raises(ValueError):
        services.create_workflow_run("no-id", {"inputs": []})


@patch("app.pipelines.services.execute_pipeline")
def test_create_workflow_run_deleted_workflow_pipeline(
    execute_pipeline_mock, app, pipeline, workflow_pipeline
):
    services.delete_workflow_pipeline(
        workflow_pipeline.workflow.uuid, workflow_pipeline.uuid
    )
    create_data = {
        "inputs": [],
    }
    workflow = workflow_pipeline.workflow
    with pytest.raises(ValueError):
        services.create_workflow_run(workflow.uuid, create_data)
    assert len(workflow.workflow_runs) == 0


@patch("app.pipelines.services.execute_pipeline")
def test_create_workflow_run(execute_pipeline_mock, app, pipeline, workflow_pipeline):
    create_data = {
        "inputs": [
            {
                "name": "aname.pdf",
                "url": "https://example.com/ex.pdf",
            }
        ],
    }
    # A new WorkflowPipelineRun creates new PipelineRuns as QUEUED...when the
    # celery worker runs it'll update their states appropriately.
    workflow_pipeline_run = services.create_workflow_run(
        workflow_pipeline.workflow.uuid, create_data
    )
    assert len(workflow_pipeline_run.workflow_run_states) == 1
    assert (
        workflow_pipeline_run.workflow_run_states[0].run_state_type.code
        == RunStateEnum.NOT_STARTED
    )
    assert len(workflow_pipeline_run.workflow_pipeline_runs) == 1
    pipeline_run = workflow_pipeline_run.workflow_pipeline_runs[0].pipeline_run
    assert [prs.code for prs in pipeline_run.pipeline_run_states] == [
        RunStateEnum.QUEUED,
        RunStateEnum.NOT_STARTED,
    ]
    assert len(pipeline_run.pipeline_run_inputs) == 1
    assert (
        pipeline_run.pipeline_run_inputs[0].filename == create_data["inputs"][0]["name"]
    )
    assert pipeline_run.pipeline_run_inputs[0].url == create_data["inputs"][0]["url"]


@patch("app.pipelines.services.execute_pipeline")
def test_create_workflow_run(execute_pipeline_mock, app, workflow_square):
    create_data = {
        "inputs": [
            {
                "name": "aname.pdf",
                "url": "https://example.com/ex.pdf",
            }
        ],
    }
    # A complex workflow with only one WorkflowPipeline w/o input should be the
    # only thing to start initially.
    workflow_pipeline_run = services.create_workflow_run(
        workflow_square.uuid, create_data
    )
    assert len(workflow_pipeline_run.workflow_run_states) == 1
    assert (
        workflow_pipeline_run.workflow_run_states[0].run_state_type.code
        == RunStateEnum.NOT_STARTED
    )
    assert len(workflow_pipeline_run.workflow_pipeline_runs) == 4
    assert [
        wpr.run_state_enum() for wpr in workflow_pipeline_run.workflow_pipeline_runs
    ] == [
        RunStateEnum.NOT_STARTED,
        RunStateEnum.QUEUED,
        RunStateEnum.QUEUED,
        RunStateEnum.QUEUED,
    ]


@patch("app.pipelines.services.execute_pipeline")
def test_update_workflow_run_no_workflow(execute_pipeline_mock, app, pipeline):
    # a pipeline_run not associated with workflow_pipeline_run nothing breaks
    pipeline_run = create_pipeline_run(pipeline.uuid, VALID_CALLBACK_INPUT)
    assert services.update_workflow_run(pipeline_run) is None


def _configure_run_state(workflow, run_state_enum, delay_mock):
    """ Update first PipelineRun to run_state_enum and call update_workflow_run() """
    services.create_workflow_run(
        workflow.uuid,
        {
            "inputs": [],
        },
    )
    pipeline_runs = [
        wpr.pipeline_run for wpr in workflow.workflow_runs[0].workflow_pipeline_runs
    ]
    pipeline_runs[0].pipeline_run_states.append(
        create_pipeline_run_state(run_state_enum)
    )
    pipeline_runs[0].pipeline_run_artifacts.append(
        PipelineRunArtifact(name="afile.txt")
    )
    db.session.commit()

    delay_mock.reset_mock()

    return (services.update_workflow_run(pipeline_runs[0]), pipeline_runs)


def test_update_workflow_run_state(app, workflow_pipeline):
    workflow = workflow_pipeline.workflow
    services.create_workflow_run(
        workflow.uuid,
        {
            "inputs": [],
        },
    )
    workflow = workflow_pipeline.workflow
    db.session.add(workflow)
    # Setting a pipeline to its current state does nothing.
    services.update_workflow_run_state(
        workflow.workflow_runs[0], RunStateEnum.NOT_STARTED
    )
    assert workflow.workflow_runs[0].run_state_enum() == RunStateEnum.NOT_STARTED

    # Trying to make an bad state transition is an error.
    with pytest.raises(ValueError):
        services.update_workflow_run_state(
            workflow.workflow_runs[0], RunStateEnum.COMPLETED
        )


@patch("app.pipelines.services.execute_pipeline")
def test_update_workflow_run_QUEUE(execute_pipeline_mock, app, pipeline, workflow_line):
    # when a PipelineRun gives some unexpected state, an error is thrown
    with pytest.raises(ValueError):
        (workflow_run, pipeline_runs) = _configure_run_state(
            workflow_line, RunStateEnum.QUEUED, execute_pipeline_mock
        )


@patch("app.pipelines.services.execute_pipeline")
def test_update_workflow_run_FAILED(
    execute_pipeline_mock, app, pipeline, workflow_line
):
    # when a PipelineRun fails, then all the remaining PRs should be marked as
    # CANCELLED -- and the WorkflowRun itself should be CANCELLED.
    (workflow_run, pipeline_runs) = _configure_run_state(
        workflow_line, RunStateEnum.FAILED, execute_pipeline_mock
    )

    assert workflow_run.run_state_enum() == RunStateEnum.CANCELLED
    assert pipeline_runs[1].run_state_enum() == RunStateEnum.CANCELLED
    assert pipeline_runs[2].run_state_enum() == RunStateEnum.CANCELLED
    assert not execute_pipeline_mock.called


@patch("app.pipelines.services.execute_pipeline")
def test_update_workflow_run_RUNNING(
    execute_pipeline_mock, app, pipeline, workflow_line
):
    (workflow_run, pipeline_runs) = _configure_run_state(
        workflow_line, RunStateEnum.RUNNING, execute_pipeline_mock
    )

    assert workflow_run.run_state_enum() == RunStateEnum.RUNNING
    assert pipeline_runs[1].run_state_enum() == RunStateEnum.QUEUED
    assert pipeline_runs[2].run_state_enum() == RunStateEnum.QUEUED
    assert not execute_pipeline_mock.called


@patch("app.workflows.services.copy_pipeline_run_artifact")
@patch("app.pipelines.services.execute_pipeline.delay")
def test_update_workflow_run_RUNNING_line(
    delay_mock, copy_mock, app, pipeline, workflow_line
):
    (workflow_run, pipeline_runs) = _configure_run_state(
        workflow_line, RunStateEnum.COMPLETED, delay_mock
    )
    workflow_run.workflow_run_states.append(
        services.create_workflow_run_state(RunStateEnum.RUNNING)
    )

    assert workflow_run.run_state_enum() == RunStateEnum.RUNNING
    copy_mock.assert_called_once_with(
        pipeline_runs[0].pipeline_run_artifacts[0], pipeline_runs[1]
    )
    assert pipeline_runs[1].run_state_enum() == RunStateEnum.NOT_STARTED
    assert pipeline_runs[2].run_state_enum() == RunStateEnum.QUEUED
    delay_mock.assert_called_once()

    # when the second run finished it'll start the last one
    delay_mock.reset_mock()
    copy_mock.reset_mock()
    pipeline_runs[1].pipeline_run_artifacts.append(
        PipelineRunArtifact(name="anotherfile.txt")
    )
    pipeline_runs[1].pipeline_run_states.append(
        create_pipeline_run_state(RunStateEnum.COMPLETED)
    )
    services.update_workflow_run(pipeline_runs[1])
    assert workflow_run.run_state_enum() == RunStateEnum.RUNNING
    copy_mock.assert_called_once_with(
        pipeline_runs[1].pipeline_run_artifacts[0], pipeline_runs[2]
    )
    assert pipeline_runs[2].run_state_enum() == RunStateEnum.NOT_STARTED

    # Finally, when the last run finishes, the workflow is finished
    delay_mock.reset_mock()
    copy_mock.reset_mock()
    pipeline_runs[2].pipeline_run_states.append(
        create_pipeline_run_state(RunStateEnum.COMPLETED)
    )
    services.update_workflow_run(pipeline_runs[2])
    assert workflow_run.run_state_enum() == RunStateEnum.COMPLETED
    assert not copy_mock.called


@patch("app.workflows.services.copy_pipeline_run_artifact")
@patch("app.pipelines.services.execute_pipeline.delay")
def test_update_workflow_run_RUNNING_square(
    delay_mock, copy_mock, app, pipeline, workflow_square
):
    (workflow_run, pipeline_runs) = _configure_run_state(
        workflow_square, RunStateEnum.COMPLETED, delay_mock
    )
    workflow_run.workflow_run_states.append(
        services.create_workflow_run_state(RunStateEnum.RUNNING)
    )

    assert workflow_run.run_state_enum() == RunStateEnum.RUNNING
    copy_mock.assert_has_calls(
        [
            call(pipeline_runs[0].pipeline_run_artifacts[0], pipeline_runs[1]),
            call(pipeline_runs[0].pipeline_run_artifacts[0], pipeline_runs[2]),
        ]
    )
    assert pipeline_runs[1].run_state_enum() == RunStateEnum.NOT_STARTED
    assert pipeline_runs[2].run_state_enum() == RunStateEnum.NOT_STARTED
    assert pipeline_runs[3].run_state_enum() == RunStateEnum.QUEUED
    assert delay_mock.call_count == 2

    # when one of the second ones finishes - the third one gets its artifact,
    # but it doesn't start (b/c it needs artifacts from both!)
    delay_mock.reset_mock()
    copy_mock.reset_mock()
    pipeline_runs[1].pipeline_run_artifacts.append(
        PipelineRunArtifact(name="anotherfile.txt")
    )
    pipeline_runs[1].pipeline_run_states.append(
        create_pipeline_run_state(RunStateEnum.COMPLETED)
    )
    services.update_workflow_run(pipeline_runs[1])
    assert workflow_run.run_state_enum() == RunStateEnum.RUNNING
    copy_mock.assert_called_once_with(
        pipeline_runs[1].pipeline_run_artifacts[0], pipeline_runs[3]
    )
    assert pipeline_runs[3].run_state_enum() == RunStateEnum.QUEUED

    # when the third one finishes - the fourth starts b/c it has all its inputs
    delay_mock.reset_mock()
    copy_mock.reset_mock()
    pipeline_runs[2].pipeline_run_artifacts.append(
        PipelineRunArtifact(name="anotherfile.txt")
    )
    pipeline_runs[2].pipeline_run_states.append(
        create_pipeline_run_state(RunStateEnum.COMPLETED)
    )
    services.update_workflow_run(pipeline_runs[2])
    assert workflow_run.run_state_enum() == RunStateEnum.RUNNING
    copy_mock.assert_called_once_with(
        pipeline_runs[2].pipeline_run_artifacts[0], pipeline_runs[3]
    )
    assert pipeline_runs[3].run_state_enum() == RunStateEnum.NOT_STARTED

    # Finally, when the last run finishes, the workflow is finished
    delay_mock.reset_mock()
    copy_mock.reset_mock()
    pipeline_runs[3].pipeline_run_states.append(
        create_pipeline_run_state(RunStateEnum.COMPLETED)
    )
    services.update_workflow_run(pipeline_runs[3])
    assert workflow_run.run_state_enum() == RunStateEnum.COMPLETED
    assert not copy_mock.called
