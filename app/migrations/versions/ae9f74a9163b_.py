"""empty message

Revision ID: ae9f74a9163b
Revises: df0fbf496520
Create Date: 2020-02-01 14:47:59.066894

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'ae9f74a9163b'
down_revision = 'df0fbf496520'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('device_info', 'serial_number')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('device_info', sa.Column('serial_number', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
