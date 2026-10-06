import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it } from 'vitest';
import { ProfileTab } from './ProfileTab';
import { useSettingsStore } from '../hooks/useSettingsStore';
import { useAuthStore } from '../../../../stores/useAuthStore';

describe('ProfileTab wall display identity setting', () => {
  beforeEach(() => {
    const current = useSettingsStore.getState();
    useSettingsStore.setState({
      profile: {
        ...current.profile,
        nom: 'Cabinet Test',
        adresse: '',
        telephone: '',
        inpe: '',
        wall_display_identity_mode: 'initials',
      },
      contacts: current.contacts,
      isDirty: false,
      saving: false,
      saveSuccess: false,
    });
    useAuthStore.setState({
      user: {
        id: 1,
        email: 'admin@test.local',
        nom_complet: 'Admin Test',
        role: 'ADMIN',
        is_superadmin: true,
        employer_id: null,
      } as any,
    });
  });

  it('offers initials, full name and number-only choices and stages the selected mode', () => {
    render(<ProfileTab />);

    const initials = screen.getByRole('button', { name: /Initiales/i });
    const fullName = screen.getByRole('button', { name: /Nom complet/i });
    const numberOnly = screen.getByRole('button', { name: /Numéro uniquement/i });

    expect(initials).toHaveAttribute('aria-pressed', 'true');
    expect(fullName).toHaveAttribute('aria-pressed', 'false');
    expect(numberOnly).toHaveAttribute('aria-pressed', 'false');

    fireEvent.click(numberOnly);

    expect(useSettingsStore.getState().profile.wall_display_identity_mode).toBe('number_only');
    expect(useSettingsStore.getState().isDirty).toBe(true);
  });

  it('makes the privacy consequence of full-name mode explicit', () => {
    render(<ProfileTab />);

    expect(screen.getByText(/rend volontairement l’identité du patient visible sur un écran public/i)).toBeInTheDocument();
  });
});
