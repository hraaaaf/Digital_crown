import { Navigate } from 'react-router-dom';

/**
 * SuperAdmin is a desktop/web control-plane only.
 * Mobile JWTs are device/cabinet sessions and must never expose platform controls.
 */
export function MobileSuperAdminView() {
  return <Navigate to="/mobile/dashboard" replace />;
}
