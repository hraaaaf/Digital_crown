import { Navigate } from 'react-router-dom';
import { Settings as SettingsComponent } from '../features/admin/Settings';
import { useAuthStore } from '../stores/useAuthStore';
import { getSettingsAccess } from '../utils/settingsAccess';

export const Settings = () => {
  const user = useAuthStore((state) => state.user);
  const { canOpenSettingsCenter } = getSettingsAccess(user);

  if (!canOpenSettingsCenter) {
    return <Navigate to="/dashboard" replace />;
  }

  return <SettingsComponent />;
};

export default Settings;
