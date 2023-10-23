"""user perferct Games

Revision ID: bd66afdd92dc
Revises: f96cc24b00fb
Create Date: 2023-10-23 02:57:01.257308

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bd66afdd92dc'
down_revision = 'f96cc24b00fb'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('perfectGames', sa.Integer(), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('users', schema=None) as batch_op:
        batch_op.drop_column('perfectGames')

    # ### end Alembic commands ###