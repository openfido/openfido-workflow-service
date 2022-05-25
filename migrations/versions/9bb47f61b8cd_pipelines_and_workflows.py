"""pipelines and workflows

Revision ID: 9bb47f61b8cd
Revises: 
Create Date: 2020-09-28 13:39:16.797018

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '9bb47f61b8cd'
down_revision = None
branch_labels = None
depends_on = None

conn = op.get_bind()
inspector = Inspector.from_engine(conn)
tables = inspector.get_table_names()

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    if table_name not in tables:
        op.create_table(
            'application',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.String(length=32), server_default='', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('name', sa.String(length=50), nullable=False),
            sa.Column('api_key', sa.String(length=32), server_default='', nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_table(
            'pipeline',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.String(length=32), server_default='', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('name', sa.String(length=50), nullable=False),
            sa.Column('description', sa.String(length=300), nullable=False),
            sa.Column('docker_image_url', sa.String(length=2000), nullable=True),
            sa.Column('repository_ssh_url', sa.String(length=2000), nullable=True),
            sa.Column('repository_branch', sa.String(length=100), nullable=True),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_table(
            'runstatetype',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.String(length=32), server_default='', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('name', sa.String(length=20), nullable=False),
            sa.Column('description', sa.String(length=300), nullable=False),
            sa.Column('code', sa.Numeric(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_table(
            'systempermission',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.String(length=32), server_default='', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('name', sa.String(length=50), nullable=False),
            sa.Column('code', sa.Integer(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_table(
            'workflow',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.String(length=32), server_default='', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('name', sa.String(length=50), nullable=False),
            sa.Column('description', sa.String(length=300), nullable=False),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_table(
            'applicationsystempermission',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.String(length=32), server_default='', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('application_id', sa.Integer(), nullable=False),
            sa.Column('system_permission_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['application_id'], ['application.id'], ),
            sa.ForeignKeyConstraint(['system_permission_id'], ['systempermission.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_table(
            'pipelinerun',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.String(length=32), server_default='', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('sequence', sa.Integer(), nullable=False),
            sa.Column('worker_ip', sa.String(length=50), nullable=True),
            sa.Column('callback_url', sa.String(length=2000), nullable=True),
            sa.Column('started_at', sa.DateTime(), nullable=True),
            sa.Column('completed_at', sa.DateTime(), nullable=True),
            sa.Column('std_out', sa.Unicode(), nullable=True),
            sa.Column('std_err', sa.Unicode(), nullable=True),
            sa.Column('pipeline_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['pipeline_id'], ['pipeline.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_table(
            'workflowpipeline',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.String(length=32), server_default='', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('pipeline_id', sa.Integer(), nullable=False),
            sa.Column('workflow_id', sa.Integer(), nullable=False),
            sa.Column('is_deleted', sa.Boolean(), nullable=False),
            sa.ForeignKeyConstraint(['pipeline_id'], ['pipeline.id'], ),
            sa.ForeignKeyConstraint(['workflow_id'], ['workflow.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_table(
            'workflowrun',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.String(length=32), server_default='', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('workflow_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['workflow_id'], ['workflow.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_table(
            'pipelinerunartifact',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.String(length=32), server_default='', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('name', sa.String(length=255), nullable=False),
            sa.Column('pipeline_run_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['pipeline_run_id'], ['pipelinerun.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_table(
            'pipelineruninput',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.String(length=32), server_default='', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('filename', sa.String(length=255), nullable=False),
            sa.Column('url', sa.String(length=2000), nullable=False),
            sa.Column('pipeline_run_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['pipeline_run_id'], ['pipelinerun.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_table(
            'pipelinerunstate',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.String(length=32), server_default='', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('name', sa.String(length=20), nullable=False),
            sa.Column('description', sa.String(length=300), nullable=False),
            sa.Column('code', sa.Integer(), nullable=False),
            sa.Column('run_state_type_id', sa.Integer(), nullable=False),
            sa.Column('pipeline_run_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['pipeline_run_id'], ['pipelinerun.id'], ),
            sa.ForeignKeyConstraint(['run_state_type_id'], ['runstatetype.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_table(
            'workflowpipelinedependency',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.String(length=32), server_default='', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('from_workflow_pipeline_id', sa.Integer(), nullable=False),
            sa.Column('to_workflow_pipeline_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['from_workflow_pipeline_id'], ['workflowpipeline.id'], ),
            sa.ForeignKeyConstraint(['to_workflow_pipeline_id'], ['workflowpipeline.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_table(
            'workflowpipelinerun',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.String(length=32), server_default='', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('workflow_run_id', sa.Integer(), nullable=False),
            sa.Column('pipeline_run_id', sa.Integer(), nullable=False),
            sa.Column('workflow_pipeline_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['pipeline_run_id'], ['pipelinerun.id'], ),
            sa.ForeignKeyConstraint(['workflow_pipeline_id'], ['workflowpipeline.id'], ),
            sa.ForeignKeyConstraint(['workflow_run_id'], ['workflowrun.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_table(
            'workflowrunstate',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('uuid', sa.String(length=32), server_default='', nullable=False),
            sa.Column('created_at', sa.DateTime(), nullable=False),
            sa.Column('updated_at', sa.DateTime(), nullable=False),
            sa.Column('workflow_run_id', sa.Integer(), nullable=False),
            sa.Column('run_state_type_id', sa.Integer(), nullable=False),
            sa.ForeignKeyConstraint(['run_state_type_id'], ['runstatetype.id'], ),
            sa.ForeignKeyConstraint(['workflow_run_id'], ['workflowrun.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('workflowrunstate')
    op.drop_table('workflowpipelinerun')
    op.drop_table('workflowpipelinedependency')
    op.drop_table('pipelinerunstate')
    op.drop_table('pipelineruninput')
    op.drop_table('pipelinerunartifact')
    op.drop_table('workflowrun')
    op.drop_table('workflowpipeline')
    op.drop_table('pipelinerun')
    op.drop_table('applicationsystempermission')
    op.drop_table('workflow')
    op.drop_table('systempermission')
    op.drop_table('runstatetype')
    op.drop_table('pipeline')
    op.drop_table('application')
    # ### end Alembic commands ###
