"""Initial schema bootstrap leveraging SQLAlchemy metadata."""

from alembic import op
from ecommerce_platform.db import models as _registration  # noqa: F401,F403,E402 pylint: disable=W0611
from ecommerce_platform.db.base import Base

revision = "0001_initial_mesh"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
