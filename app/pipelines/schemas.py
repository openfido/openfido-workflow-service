from marshmallow import Schema, fields, validate
from marshmallow_enum import EnumField

from ..model_utils import RunStateEnum
from openfido.schemas import UUID


class InputSchema(Schema):
    """ A pipeline run input. """

    name = fields.Str()
    url = fields.Url()


class InputExportSchema(Schema):
    """ A run input export schema. """

    name = fields.Str(attribute="filename")
    url = fields.Url()


class CreateRunSchema(Schema):
    """ Validation schema for create_run() """

    inputs = fields.Nested(InputSchema, many=True, required=True)
    callback_url = fields.Url(required=True)


class UpdateRunStateSchema(Schema):
    """ Validation schema for update_run_status() """

    state = EnumField(RunStateEnum, required=True)


class RunStateSchema(Schema):
    """ Export RunState """

    state = fields.Function(lambda obj: RunStateEnum(obj.code).name)
    created_at = fields.DateTime()


class PipelineSchema(Schema):
    """ Serialized public view of a Workflow. """

    uuid = fields.Str()
    name = fields.Str()
    description = fields.Str()
    docker_image_url = fields.Str()
    repository_ssh_url = fields.Str()
    repository_branch = fields.Str()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class SearchPipelinesSchema(Schema):
    """ Schema for find_pipelines() queries. """

    uuids = fields.List(UUID(), required=True)


class ArtifactSchema(Schema):
    """ Schema of an artifact. """

    uuid = fields.Str()
    name = fields.Str()
    url = fields.Function(lambda obj: obj.public_url())


class PipelineRunSchema(Schema):
    """ Schema of PipelineRun """

    uuid = UUID()
    sequence = fields.Int()
    created_at = fields.DateTime()
    inputs = fields.Nested(
        InputExportSchema, many=True, attribute="pipeline_run_inputs"
    )
    states = fields.Nested(RunStateSchema, many=True, attribute="pipeline_run_states")
    artifacts = fields.Nested(
        ArtifactSchema, many=True, attribute="pipeline_run_artifacts"
    )
