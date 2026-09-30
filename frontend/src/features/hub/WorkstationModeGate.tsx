import { useEffect, useState } from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import {
  workstationModeService,
  type WorkstationBootstrapState,
} from '../../services/workstationMode';

type Props = {
  target: 'hub' | 'station' | 'control-center' | 'protected';
  children: React.ReactNode;
};

const routeFor = (mode: WorkstationBootstrapState['defaultExperience']) => {
  if (mode === 'cabinet') return '/cabinet';
  if (mode === 'station') return '/station';
  if (mode === 'control_center') return '/control-center';
  return '/hub';
};

export const WorkstationModeGate = ({ target, children }: Props) => {
  const location = useLocation();
  const [state, setState] = useState<WorkstationBootstrapState | null>(null);
  const [resolved, setResolved] = useState(false);

  useEffect(() => {
    let active = true;
    setResolved(false);

    const readState = target === 'protected'
      ? workstationModeService.getState()
      : workstationModeService.getBootstrapState();

    readState
      .then((next) => { if (active) setState(next); })
      .catch(() => { if (active) setState(null); })
      .finally(() => { if (active) setResolved(true); });

    return () => { active = false; };
  }, [location.pathname, target]);

  if (!resolved) return null;

  if (!state) {
    // Protected Cabinet routes fail closed if workstation authority cannot be read.
    if (target === 'protected') return <Navigate to="/hub?mode-check=failed" replace />;

    // Hub and Control Center remain data-free fail-soft shells while the backend is down.
    if (target === 'hub' || target === 'control-center') return <>{children}</>;

    // Direct Station entry is never authorized without server-backed workstation state.
    return <Navigate to="/hub?select=1" replace />;
  }

  // A configured Station is a workstation lock. Direct URL navigation to any other
  // server-backed experience must not bypass the owner-PIN escape authorization.
  if (state.defaultExperience === 'station' && !state.stationEscapeAuthorized && target !== 'station') {
    return <Navigate to="/station" replace />;
  }

  if (target === 'station') {
    if (state.defaultExperience !== 'station') {
      return <Navigate to="/hub?select=1" replace />;
    }
    return <>{children}</>;
  }

  if (target === 'protected' || target === 'control-center') {
    return <>{children}</>;
  }

  const explicitSelection = new URLSearchParams(location.search).get('select') === '1';
  if (!explicitSelection && state.defaultExperience) {
    return <Navigate to={routeFor(state.defaultExperience)} replace />;
  }

  return <>{children}</>;
};
