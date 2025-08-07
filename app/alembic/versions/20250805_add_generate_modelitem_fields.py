"""
Add new fields to GenerateModelItem
"""

revision = '20250805_add_gmi_fields'
down_revision = None
branch_labels = None
depends_on = None
from alembic import op
import sqlalchemy as sa

def upgrade():
    # Sadece eksik olan lora kolonunu ekle
    op.add_column('generatemodelitem', sa.Column('lora', sa.JSON(), nullable=True))

def downgrade():
    op.drop_column('generatemodelitem', 'sampler_name')
    op.drop_column('generatemodelitem', 'cfg')
    op.drop_column('generatemodelitem', 'steps')
    op.drop_column('generatemodelitem', 'model')
    pass
    op.drop_column('generatemodelitem', 'positive_prompt')
    op.drop_column('generatemodelitem', 'negative_prompt')
    op.drop_column('generatemodelitem', 'seed')
    op.drop_column('generatemodelitem', 'denoise')
    op.drop_column('generatemodelitem', 'scheduler')
    op.drop_column('generatemodelitem', 'lora')
