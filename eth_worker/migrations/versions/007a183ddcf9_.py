"""empty message

Revision ID: 007a183ddcf9
Revises: b1d4118a005b
Create Date: 2019-09-29 18:05:13.809735

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007a183ddcf9'
down_revision = 'b1d4118a005b'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('blockchain_wallet', sa.Column('wei_target_balance', sa.BigInteger(), nullable=True))
    op.drop_column('blockchain_wallet', 'wei_topup_target')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('blockchain_wallet', sa.Column('wei_topup_target', sa.BIGINT(), autoincrement=False, nullable=True))
    op.drop_column('blockchain_wallet', 'wei_target_balance')
    # ### end Alembic commands ###
