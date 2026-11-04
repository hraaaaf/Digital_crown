"""LOT06 B06 local-only service adapter; not mounted in backend.main.

The lightweight Win32 transport lives in tools/imaging_gateway to avoid
importing the backend ORM into the LocalService subprocess. The product
does not expose this function to patients or activate clinical ingestion.
"""

from tools.imaging_gateway.native_inventory_windows_v15 import read_native_unassigned

__all__ = ["read_native_unassigned"]
