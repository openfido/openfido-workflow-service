from app.pipelines.schemas import PipelineRunSchema
from marshmallow import Schema, fields, validate

from openfido.schemas import UUID
from .models import Workflow


class WorkflowSchema(Schema):
    """ Serialized public view of a Workflow. """

    uuid = UUID()
    name = fields.Str()
    description = fields.Str()
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class SearchWorkflowsSchema(Schema):
    """ Schema for find_workflows() queries. """

    uuids = fields.List(UUID())


class CreateWorkflowSchema(Schema):
    """ Schema for create_workflow() service. """

    name = fields.Str(
        required=True, validate=validate.Length(min=1, max=Workflow.name.type.length)
    )
    description = fields.Str(
        required=True, validate=validate.Length(max=Workflow.description.type.length)
    )


class CreateWorkflowPipelineSchema(Schema):
    """ Schema for create_workflow_pipeline() service. """

    pipeline_uuid = UUID(required=True)
    source_workflow_pipelines = fields.List(UUID(), required=True)
    destination_workflow_pipelines = fields.List(UUID(), required=True)


class WorkflowPipelineSchema(Schema):
    """ Serialized public view of a WorkflowPipeline. """

    uuid = UUID()
    pipeline_uuid = UUID(attribute="pipeline.uuid")

    def dump_sources(obj):
        """ dump the source uuids of the from uuid. """
        return [wp.to_workflow_pipeline.uuid for wp in obj.source_workflow_pipelines]

    source_workflow_pipelines = fields.Function(dump_sources)

    def dump_dests(obj):
        """ dump the destination uuids of the from uuid. """
        return [wp.to_workflow_pipeline.uuid for wp in obj.dest_workflow_pipelines]

    destination_workflow_pipelines = fields.Function(dump_dests)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()


class WorkflowPipelineRunSchema(Schema):
    """ Serialized public view of WorkflowRun """

    uuid = UUID()
    pipeline_run = fields.Nested(PipelineRunSchema)


class WorkflowRunStateSchema(Schema):
    """ Export WorkflowRunState """

    state = fields.Function(lambda obj: obj.run_state_enum().name)
    created_at = fields.DateTime()


class WorkflowRunSchema(Schema):
    """ Serialized public view of WorkflowRun """

    uuid = UUID()
    states = fields.Nested(
        WorkflowRunStateSchema, many=True, attribute="workflow_run_states"
    )
    workflow_pipeline_runs = fields.Nested(WorkflowPipelineRunSchema, many=True)
    # state = EnumField(RunStateEnum)
    created_at = fields.DateTime()
    updated_at = fields.DateTime()
