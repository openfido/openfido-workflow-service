from flask import current_app
from flask_sqlalchemy import SQLAlchemy

from ..constants import S3_BUCKET, S3_PRESIGNED_TIMEOUT
from ..model_utils import CommonColumnsMixin, get_db
from ..utils import get_s3

db = get_db()


class Pipeline(CommonColumnsMixin, db.Model):
    """ Represents a 'pipeline' job. """

    __tablename__ = "pipeline"

    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    docker_image_url = db.Column(db.String(2000), nullable=True)
    repository_ssh_url = db.Column(db.String(2000), nullable=True)
    repository_branch = db.Column(db.String(100), nullable=True)
    is_deleted = db.Column(db.Boolean(), default=False, nullable=False)

    pipeline_runs = db.relationship("PipelineRun", backref="pipeline", lazy="select")
    workflow_pipelines = db.relationship(
        "WorkflowPipeline", backref="pipeline", lazy="select"
    )


class RunStateType(CommonColumnsMixin, db.Model):
    """ Lookup table of run states. """

    __tablename__ = "runstatetype"

    name = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    code = db.Column(db.Numeric(), nullable=False)

    pipeline_run_states = db.relationship(
        "PipelineRunState", backref="run_state_type", lazy="immediate"
    )


class PipelineRunState(CommonColumnsMixin, db.Model):
    """ Lookup table of run states. """

    __tablename__ = "pipelinerunstate"

    name = db.Column(db.String(20), nullable=False)
    description = db.Column(db.String(300), nullable=False)
    code = db.Column(db.Integer, nullable=False)
    run_state_type_id = db.Column(
        db.Integer, db.ForeignKey("runstatetype.id"), nullable=False
    )
    pipeline_run_id = db.Column(
        db.Integer, db.ForeignKey("pipelinerun.id"), nullable=False
    )


class PipelineRunArtifact(CommonColumnsMixin, db.Model):
    """ An artifact created by a PipelineRun. """

    __tablename__ = "pipelinerunartifact"

    name = db.Column(db.String(255), nullable=False)

    pipeline_run_id = db.Column(
        db.Integer, db.ForeignKey("pipelinerun.id"), nullable=False
    )

    def public_url(self):
        """ Generate a publicly visible URL for this artifact. """

        return get_s3().generate_presigned_url(
            "get_object",
            Params={
                "Bucket": current_app.config[S3_BUCKET],
                "Key": f"{self.pipeline_run.pipeline.uuid}/{self.pipeline_run.uuid}/{self.uuid}-{self.name}",
            },
            ExpiresIn=S3_PRESIGNED_TIMEOUT,
        )


class PipelineRunInput(CommonColumnsMixin, db.Model):
    """ Inputs used to execute a PipelineRun. """

    __tablename__ = "pipelineruninput"

    filename = db.Column(db.String(255), nullable=False)
    url = db.Column(db.String(2000), nullable=False)

    pipeline_run_id = db.Column(
        db.Integer, db.ForeignKey("pipelinerun.id"), nullable=False
    )


class PipelineRun(CommonColumnsMixin, db.Model):
    """ A pipeline run """

    __tablename__ = "pipelinerun"

    sequence = db.Column(db.Integer, nullable=False)
    worker_ip = db.Column(db.String(50), nullable=True)
    callback_url = db.Column(db.String(2000), nullable=True)
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    std_out = db.Column(db.Unicode, nullable=True)
    std_err = db.Column(db.Unicode, nullable=True)

    pipeline_id = db.Column(db.Integer, db.ForeignKey("pipeline.id"), nullable=False)

    pipeline_run_states = db.relationship(
        "PipelineRunState", backref="pipeline_run", lazy="immediate"
    )
    pipeline_run_artifacts = db.relationship(
        "PipelineRunArtifact", backref="pipeline_run", lazy="immediate"
    )
    pipeline_run_inputs = db.relationship(
        "PipelineRunInput", backref="pipeline_run", lazy="immediate"
    )
