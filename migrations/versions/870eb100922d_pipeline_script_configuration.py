"""pipeline script configuration

Revision ID: 870eb100922d
Revises: 61429c72a7bf
Create Date: 2020-11-02 20:20:27.568517

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '870eb100922d'
down_revision = '61429c72a7bf'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('pipeline', sa.Column('repository_script', sa.String(length=4096), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('pipeline', 'repository_script')
    # ### end Alembic commands ###