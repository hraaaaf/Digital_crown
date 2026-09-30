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

const FALLBACK_REVALIDATION_MS = 5_000;

export const WorkstationModeGate = ({ target, children }: Props) => {
  const location = useLocation();
  const [state, setState] = useState<WorkstationBootstrapState | null>(null);
  const [resolved, setResolved] = useState(false);

  useEffect(() => {
    let active = true;
    let expiryTimer: number | undefined;
    setResolved(false);

    const scheduleEscapeExpiry = (next: WorkstationBootstrapState | null) => {
      if (expiryTimer !== undefined) {
        window.clearTimeout(expiryTimer);
        expiryTimer = undefined;
      }
      if (!next?.stationEscapeAuthorized || !next.stationEscapeExpiresAt) return;

      const delay = Math.max(0, next.stationEscapeExpiresAt * 1000 - Date.now() + 50);
      expiryTimer = window.setTimeout(() => {
        void readState();
      }, delay);
    };

    const readState = async () => {
      try {
        const next = target === 'protected'
          ? await workstationModeService.getState()
          : await workstationModeService.getBootstrapState();
        if (!active) return;
        setState(next);
        scheduleEscapeExpiry(next);
      } catch {
        if (!active) return;
        setState(null);
        scheduleEscapeExpiry(null);
      } finally {
        if (active) setResolved(true);
      }
    };

    void readState();

    const unsubscribe = workstationModeService.subscribe(() => {
      void readState();
    });
    const onFocus = () => { void readState(); };
    const onVisibility = () => {
      if (document.visibilityState === 'visible') void readState();
    };
    window.addEventListener('focus', onFocus);
    document.addEventListener('visibilitychange', onVisibility);

    // BroadcastChannel gives immediate same-browser convergence for normal mode
    // changes. This bounded fallback also catches direct API/DevTools changes.
    const interval = window.setInterval(() => {
      void readState();
    }, FALLBACK_REVALIDATION_MS);

    return () => {
      active = false;
      unsubscribe();
      window.removeEventListener('focus', onFocus);
      document.removeEventListener('visibilitychange', onVisibility);
      window.clearInterval(interval);
      if (expiryTimer !== undefined) window.clearTimeout(expiryTimer);
    };
  }, [location.pathname, target]);

  if (!resolved) return null;

  if (!state) {
    // Clinical routes fail closed when workstation authority cannot be read.
    // The data-free Hub, restrictive Station shell, and local Control Center remain recovery surfaces.
    if (target === 'hub' || target === 'station' || target === 'control-center') return <>{children}</>;
    if (target === 'protected') {
      return <Navigate to="/hub?mode-check=failed" replace />;
    }

    return <Navigate to="/hub?mode-check=failed" replace />;
  }

  if (state.enrollmentRequired && target !== 'hub') {
    return <Navigate to="/hub?enroll=1" replace />;
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
