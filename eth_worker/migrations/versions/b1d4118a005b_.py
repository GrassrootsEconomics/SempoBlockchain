"""empty message

Revision ID: b1d4118a005b
Revises: 334ff08dacf9
Create Date: 2019-09-29 17:58:15.119011

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1d4118a005b'
down_revision = '334ff08dacf9'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('blockchain_wallet', sa.Column('wei_topup_target', sa.BigInteger(), nullable=True))
    op.drop_column('blockchain_wallet', 'wei_topup_amount')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('blockchain_wallet', sa.Column('wei_topup_amount', sa.BIGINT(), autoincrement=False, nullable=True))
    op.drop_column('blockchain_wallet', 'wei_topup_target')
    # ### end Alembic commands ###
