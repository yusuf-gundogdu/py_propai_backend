"""
Add new fields to GenerateModelItem
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('generatemodelitem', sa.Column('sampler_name', sa.String(), nullable=True))
    op.add_column('generatemodelitem', sa.Column('cfg', sa.Integer(), nullable=True))
    op.add_column('generatemodelitem', sa.Column('steps', sa.Integer(), nullable=True))
    op.add_column('generatemodelitem', sa.Column('model', sa.String(), nullable=True))
    op.add_column('generatemodelitem', sa.Column('positive_prompt', sa.String(), nullable=True))
    op.add_column('generatemodelitem', sa.Column('negative_prompt', sa.String(), nullable=True))
    op.add_column('generatemodelitem', sa.Column('seed', sa.Integer(), nullable=True))
    op.add_column('generatemodelitem', sa.Column('denoise', sa.Float(), nullable=True))
    op.add_column('generatemodelitem', sa.Column('scheduler', sa.String(), nullable=True))

def downgrade():
    op.drop_column('generatemodelitem', 'sampler_name')
    op.drop_column('generatemodelitem', 'cfg')
    op.drop_column('generatemodelitem', 'steps')
    op.drop_column('generatemodelitem', 'model')
    op.drop_column('generatemodelitem', 'positive_prompt')
    op.drop_column('generatemodelitem', 'negative_prompt')
    op.drop_column('generatemodelitem', 'seed')
    op.drop_column('generatemodelitem', 'denoise')
    op.drop_column('generatemodelitem', 'scheduler')
