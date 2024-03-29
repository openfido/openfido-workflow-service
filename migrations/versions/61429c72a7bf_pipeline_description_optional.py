"""pipeline_description_optional

Revision ID: 61429c72a7bf
Revises: 9bb47f61b8cd
Create Date: 2020-11-03 22:31:29.906656

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector


# revision identifiers, used by Alembic.
revision = '61429c72a7bf'
down_revision = '9bb47f61b8cd'
branch_labels = None
depends_on = None

conn = op.get_bind()
inspector = Inspector.from_engine(conn)
tables = inspector.get_table_names()

def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    if 'pipeline' not in tables:
        op.alter_column('pipeline', 'description',
                existing_type=sa.VARCHAR(length=300),
                nullable=True)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('pipeline', 'description',
               existing_type=sa.VARCHAR(length=300),
               nullable=False)
    # ### end Alembic commands ###
