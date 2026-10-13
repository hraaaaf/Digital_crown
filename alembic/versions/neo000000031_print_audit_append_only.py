"""Protect print evidence and investigation audit from SQL UPDATE/DELETE.

Revision ID: neo000000031
Revises: neo000000030

Protects normal SQL writers by database triggers on the four print audit
tables. Does not grant permissions, certify devices, allow print or erase
existing rows. DBA/superuser control remains outside these protections.
"""
from alembic import op
from backend.core.print_audit_ddl import (
    install_append_only_print_audit_guards,
    remove_append_only_print_audit_guards,
)

revision = "neo000000031"
down_revision = "neo000000030"
branch_labels = None
depends_on = None


def upgrade():
    install_append_only_print_audit_guards(op.get_bind())


def downgrade():
    # Approved operator-managed test rehearsal only. Removing an audit
    # trigger in a production Cabinet requires a separate security review.
    remove_append_only_print_audit_guards(op.get_bind())
