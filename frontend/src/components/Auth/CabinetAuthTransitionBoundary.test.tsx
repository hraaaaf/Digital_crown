import { fireEvent, render, screen, cleanup } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';
import { useState } from 'react';
import { MemoryRouter, useLocation, useNavigate } from 'react-router-dom';
import { CabinetAuthTransitionBoundary } from './CabinetAuthTransitionBoundary';

afterEach(() => cleanup());

describe('CB-01 fresh UI login — fail-closed auth boundary lifecycle', () => {
  it('rechecks the actual guard after login, never reuses anonymous state in protected app', () => {
    let mounts = 0;
    function GuardInstance() {
      const [born] = useState(() => ++mounts);
      const { pathname } = useLocation();
      return <output data-testid="guard">{born}:{pathname}</output>;
    }
    function NavigatePaths() {
      const navigate = useNavigate();
      return (
        <>
          <button onClick={() => navigate('/dashboard')}>Dashboard</button>
          <button onClick={() => navigate('/patients')}>Patients</button>
          <button onClick={() => navigate('/login')}>Login</button>
        </>
      );
    }

    render(
      <MemoryRouter initialEntries={['/login']}>
        <NavigatePaths />
        <CabinetAuthTransitionBoundary><GuardInstance /></CabinetAuthTransitionBoundary>
      </MemoryRouter>,
    );
    expect(screen.getByTestId('guard').textContent).toBe('1:/login');
    fireEvent.click(screen.getByRole('button', { name: 'Dashboard' }));
    expect(screen.getByTestId('guard').textContent).toBe('2:/dashboard');
    fireEvent.click(screen.getByRole('button', { name: 'Patients' }));
    expect(screen.getByTestId('guard').textContent).toBe('2:/patients');
    fireEvent.click(screen.getByRole('button', { name: 'Login' }));
    expect(screen.getByTestId('guard').textContent).toBe('3:/login');
  });

  it('does not remount within the public-entry family', () => {
    let mounts = 0;
    function Probe() {
      const [born] = useState(() => ++mounts);
      return <output data-testid="guard">{born}</output>;
    }
    function Go() {
      const navigate = useNavigate();
      return <button onClick={() => navigate('/register')}>Register</button>;
    }
    render(
      <MemoryRouter initialEntries={['/login']}>
        <Go />
        <CabinetAuthTransitionBoundary><Probe /></CabinetAuthTransitionBoundary>
      </MemoryRouter>,
    );
    expect(screen.getByTestId('guard').textContent).toBe('1');
    fireEvent.click(screen.getByRole('button', { name: 'Register' }));
    expect(screen.getByTestId('guard').textContent).toBe('1');
  });
});
