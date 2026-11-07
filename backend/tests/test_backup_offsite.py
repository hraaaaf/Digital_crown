"""Collect the single-source offsite copy tests in the normal backend suite.

The same test functions run in the standalone, dependency-light LAB workflow.
Integration with the actual scheduled-backup orchestrator is separately covered
by backend/tests/test_scheduled_backup.py.
"""
from offsite_backup_fue.test_offsite_copy_lab import *  # noqa: F401,F403
