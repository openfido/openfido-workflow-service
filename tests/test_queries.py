from app.models import Pipeline, RunStateEnum, RunStateType, db
from app.queries import (
    find_pipeline,
    find_pipelines,
    find_run_state_type,
    find_pipeline_run,
)
from app.services import create_pipeline_run


def test_find_pipeline_no_uuid(app):
    assert find_pipeline("no-id") is None


def test_find_pipeline_is_deleted(app):
    pipeline = Pipeline(name="a pipeline", description="a description", is_deleted=True)
    db.session.add(pipeline)
    db.session.commit()

    assert find_pipeline(pipeline.uuid) is None


def test_find_pipeline(app):
    pipeline = Pipeline(
        name="a pipeline",
        description="a description",
    )
    db.session.add(pipeline)
    db.session.commit()

    assert find_pipeline(pipeline.uuid) == pipeline


def test_find_pipelines_no_pipelines(app):
    assert list(find_pipelines()) == []


def test_find_pipelines(app, pipeline):
    p2 = Pipeline(
        name="pipeline 2",
        description="description 2",
    )
    deleted_p = Pipeline(
        name="a pipeline", description="a description", is_deleted=True
    )
    db.session.add(p2)
    db.session.add(deleted_p)
    db.session.commit()

    assert set(find_pipelines()) == set([pipeline, p2])
    assert set(find_pipelines("2")) == set([p2])


def test_find_run_state_type(app):
    # when there is no type, it is created and then inserted.
    run_state_type = find_run_state_type(RunStateEnum.NOT_STARTED)
    assert run_state_type.code == RunStateEnum.NOT_STARTED.value
    assert run_state_type.name == RunStateEnum.NOT_STARTED.name

    assert set(RunStateType.query) == set([run_state_type])

    # subsequent finds don't create new records:
    run_state_type = find_run_state_type(RunStateEnum.NOT_STARTED)
    assert set(RunStateType.query) == set([run_state_type])


def test_find_pipeline_run(app, pipeline):
    assert find_pipeline_run("no-uid") is None

    pipeline_run = create_pipeline_run(pipeline.uuid, [])
    db.session.commit()

    assert find_pipeline_run(pipeline_run.uuid) == pipeline_run

    # does not rutern a pipeline run if the pipeline is soft-deleted
    pipeline.is_deleted = True
    db.session.commit()

    assert find_pipeline_run(pipeline_run.uuid) is None
