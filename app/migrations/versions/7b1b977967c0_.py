"""Adds table to persist reward data.

Revision ID: 7b1b977967c0
Revises: 6d8a938930ff
Create Date: 2020-04-07 15:44:43.679079

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '7b1b977967c0'
down_revision = '6d8a938930ff'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('reward',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('authorising_user_id', sa.Integer(), nullable=True),
    sa.Column('created', sa.DateTime(), nullable=True),
    sa.Column('updated', sa.DateTime(), nullable=True),
    sa.Column('tag', sa.String(), nullable=True),
    sa.Column('recipients_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('reward')
    # ### end Alembic commands ###
