"""LOT06 B06 product bridge facade.

The Win32 client and the backend use exactly the same ORM-free gateway
implementation. Importing this facade is backend-only; do not import
`backend` in the restricted separate-account Windows helper process.
"""
from tools.imaging_gateway.native_product_bridge_v15 import (
    LocalNativeCaptureBridge, windows_native_bridge,
)

__all__ = ["LocalNativeCaptureBridge", "windows_native_bridge"]
