"""empty message

Revision ID: 40f1f3f33f0a
Revises: fee617363e27
Create Date: 2019-05-01 15:41:04.542018

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '40f1f3f33f0a'
down_revision = 'fee617363e27'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('credit_transfer', sa.Column('uuid', sa.String(), nullable=True))
    op.create_unique_constraint(None, 'credit_transfer', ['uuid'])
    op.drop_column('credit_transfer', 'old_uuid')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('credit_transfer', sa.Column('old_uuid', sa.VARCHAR(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'credit_transfer', type_='unique')
    op.drop_column('credit_transfer', 'uuid')
    # ### end Alembic commands ###
