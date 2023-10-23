"""Games fix

Revision ID: 0df0a1e2c035
Revises: a55e77b6ae05
Create Date: 2023-10-18 17:00:36.397384

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0df0a1e2c035'
down_revision = 'a55e77b6ae05'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('games',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('team1_id', sa.Integer(), nullable=False),
    sa.Column('team2_id', sa.Integer(), nullable=False),
    sa.Column('date', sa.String(length=10), nullable=False),
    sa.Column('score1', sa.Integer(), nullable=False),
    sa.Column('score2', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['team1_id'], ['teams.id'], ),
    sa.ForeignKeyConstraint(['team2_id'], ['teams.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('games')
    # ### end Alembic commands ###
