import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { api } from '../../services/api';
import { TeamManager } from './TeamManager';

vi.mock('../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
    put: vi.fn(),
    delete: vi.fn(),
  },
}));

type Member = {
  id: number;
  email: string;
  role: string;
  nom_complet: string;
  telephone_mobile: string | null;
  is_active: boolean;
  approval_status: string;
  approval_note: string | null;
  created_at: string | null;
  permissions: Record<string, boolean>;
};

let membersState: Member[] = [];
let quotaState = {
  plan: 'GOLD',
  dentistes_used: 1,
  dentistes_max: 1 as number | null,
  secretaires_used: 0,
  secretaires_max: 2 as number | null,
  pending_count: 0,
  can_add_dentiste: false,
  can_add_secretaire: true,
};

const activeMember: Member = {
  id: 11,
  email: 'active@example.com',
  role: 'SECRETAIRE',
  nom_complet: 'Active User',
  telephone_mobile: null,
  is_active: true,
  approval_status: 'approved',
  approval_note: null,
  created_at: null,
  permissions: { agenda: true, patients: true },
};

const inactiveMember: Member = {
  ...activeMember,
  id: 12,
  email: 'inactive@example.com',
  nom_complet: 'Inactive User',
  is_active: false,
};

const pendingMember: Member = {
  ...activeMember,
  id: 10,
  email: 'pending@example.com',
  nom_complet: 'Pending User',
  is_active: false,
  approval_status: 'pending',
};

function installGetMock() {
  vi.mocked(api.get).mockImplementation(async (url: string) => {
    if (url.startsWith('/team/?')) return { data: membersState } as never;
    if (url === '/team/quota') return { data: quotaState } as never;
    throw new Error(`Unexpected GET ${url}`);
  });
}

beforeEach(() => {
  vi.clearAllMocks();
  membersState = [];
  quotaState = {
    plan: 'GOLD',
    dentistes_used: 1,
    dentistes_max: 1,
    secretaires_used: 0,
    secretaires_max: 2,
    pending_count: 0,
    can_add_dentiste: false,
    can_add_secretaire: true,
  };
  installGetMock();
  vi.mocked(api.post).mockResolvedValue({ data: {} } as never);
  vi.mocked(api.put).mockResolvedValue({ data: {} } as never);
  vi.mocked(api.delete).mockResolvedValue({ data: {} } as never);
  vi.stubGlobal('confirm', vi.fn(() => true));
});

afterEach(() => {
  cleanup();
  vi.unstubAllGlobals();
});

describe('TeamManager commercial pack button matrix', () => {
  it.each([
    {
      plan: 'GOLD',
      quota: { dentists: '1/1', assistants: '0/2', canDentist: false, canAssistant: true },
      warning: true,
    },
    {
      plan: 'PREMIUM',
      quota: { dentists: '1/2', assistants: '0/6', canDentist: true, canAssistant: true },
      warning: false,
    },
    {
      plan: 'ELITE',
      quota: { dentists: '7/Illimité', assistants: '18/Illimité', canDentist: true, canAssistant: true },
      warning: false,
    },
  ])('renders $plan quota semantics and keeps Add/Cancel usable', async ({ plan, quota, warning }) => {
    quotaState = {
      plan,
      dentistes_used: Number(quota.dentists.split('/')[0]),
      dentistes_max: quota.dentists.includes('Illimité') ? null : Number(quota.dentists.split('/')[1]),
      secretaires_used: Number(quota.assistants.split('/')[0]),
      secretaires_max: quota.assistants.includes('Illimité') ? null : Number(quota.assistants.split('/')[1]),
      pending_count: 0,
      can_add_dentiste: quota.canDentist,
      can_add_secretaire: quota.canAssistant,
    };

    render(<TeamManager />);

    expect(await screen.findByText(plan)).toBeTruthy();
    expect(screen.getByText(quota.dentists)).toBeTruthy();
    expect(screen.getByText(quota.assistants)).toBeTruthy();
    if (warning) {
      expect(screen.getByText(/Quota dentistes atteint/i)).toBeTruthy();
      expect(screen.getByText(/2 place\(s\) assistante\(s\) disponible\(s\)/i)).toBeTruthy();
    } else {
      expect(screen.queryByText(/Quota .* atteint/i)).toBeNull();
    }

    fireEvent.click(screen.getByRole('button', { name: /Ajouter un membre/i }));
    expect(screen.getByText('Nouveau sous-compte')).toBeTruthy();

    const password = screen.getByPlaceholderText('••••••••') as HTMLInputElement;
    expect(password.type).toBe('password');
    const reveal = password.parentElement?.querySelector('button');
    expect(reveal).toBeTruthy();
    fireEvent.click(reveal!);
    expect(password.type).toBe('text');

    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
    expect(screen.queryByText('Nouveau sous-compte')).toBeNull();
  });

  it.each([
    ['GOLD', 1, 1, 0, 2, false, true],
    ['PREMIUM', 1, 2, 0, 6, true, true],
    ['ELITE', 7, null, 18, null, true, true],
  ])('creates an assistant successfully on %s when assistant capacity is available', async (
    plan,
    dentistsUsed,
    dentistsMax,
    assistantsUsed,
    assistantsMax,
    canDentist,
    canAssistant,
  ) => {
    quotaState = {
      plan,
      dentistes_used: dentistsUsed,
      dentistes_max: dentistsMax,
      secretaires_used: assistantsUsed,
      secretaires_max: assistantsMax,
      pending_count: 0,
      can_add_dentiste: canDentist,
      can_add_secretaire: canAssistant,
    };

    render(<TeamManager />);
    await screen.findByText(plan);

    fireEvent.click(screen.getByRole('button', { name: /Ajouter un membre/i }));
    fireEvent.change(screen.getByPlaceholderText('Ex: Fatima Zahra'), { target: { value: `Assistant ${plan}` } });
    fireEvent.change(screen.getByPlaceholderText('assistante@cabinet.com'), { target: { value: `assistant-${String(plan).toLowerCase()}@example.com` } });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'TestPass123!' } });
    fireEvent.click(screen.getByRole('button', { name: 'Créer le compte' }));

    await waitFor(() => expect(vi.mocked(api.post)).toHaveBeenCalledWith(
      '/team/',
      expect.objectContaining({
        role: 'SECRETAIRE',
        email: `assistant-${String(plan).toLowerCase()}@example.com`,
      }),
    ));
    expect(await screen.findByText(`Compte créé pour Assistant ${plan} !`)).toBeTruthy();
    expect(screen.queryByText('Nouveau sous-compte')).toBeNull();
  });

  it('surfaces the backend quota refusal from Create account without false success', async () => {
    vi.mocked(api.post).mockRejectedValueOnce({
      response: { data: { detail: 'Quota assistantes atteint (2/2) pour le plan GOLD. Passez au plan superieur pour ajouter une assistante.' } },
    });

    render(<TeamManager />);
    await screen.findByText('GOLD');

    fireEvent.click(screen.getByRole('button', { name: /Ajouter un membre/i }));
    fireEvent.change(screen.getByPlaceholderText('Ex: Fatima Zahra'), { target: { value: 'Fatima Test' } });
    fireEvent.change(screen.getByPlaceholderText('assistante@cabinet.com'), { target: { value: 'fatima@example.com' } });
    fireEvent.change(screen.getByPlaceholderText('••••••••'), { target: { value: 'TestPass123!' } });
    fireEvent.click(screen.getByRole('button', { name: 'Créer le compte' }));

    expect(await screen.findByText(/Quota assistantes atteint/)).toBeTruthy();
    expect(screen.queryByText(/Compte créé pour/)).toBeNull();
    expect(vi.mocked(api.post)).toHaveBeenCalledTimes(1);
  });

  it('executes Validate, Reject cancel/confirm and Delete cancel/confirm for a pending member', async () => {
    membersState = [pendingMember];
    quotaState = {
      ...quotaState,
      secretaires_used: 1,
      pending_count: 1,
    };

    render(<TeamManager />);
    expect(await screen.findByText('Pending User')).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Valider' }));
    await waitFor(() => expect(vi.mocked(api.post)).toHaveBeenCalledWith('/team/10/approve'));

    vi.mocked(api.post).mockClear();
    const confirmMock = vi.mocked(confirm);
    confirmMock.mockReturnValueOnce(false);
    fireEvent.click(screen.getByRole('button', { name: 'Refuser' }));
    expect(api.post).not.toHaveBeenCalled();

    confirmMock.mockReturnValueOnce(true);
    fireEvent.click(screen.getByRole('button', { name: 'Refuser' }));
    await waitFor(() => expect(vi.mocked(api.post)).toHaveBeenCalledWith('/team/10/reject'));

    vi.mocked(api.delete).mockClear();
    confirmMock.mockReturnValueOnce(false);
    fireEvent.click(screen.getByTitle('Supprimer définitivement'));
    expect(api.delete).not.toHaveBeenCalled();

    confirmMock.mockReturnValueOnce(true);
    fireEvent.click(screen.getByTitle('Supprimer définitivement'));
    await waitFor(() => expect(vi.mocked(api.delete)).toHaveBeenCalledWith('/team/10'), { timeout: 3000 });
  });

  it('executes permissions save, suspend, reactivate and permanent delete for existing members', async () => {
    membersState = [activeMember, inactiveMember];

    render(<TeamManager />);
    expect(await screen.findByText('Active User')).toBeTruthy();

    const permissionButtons = screen.getAllByTitle('Gérer les permissions');
    fireEvent.click(permissionButtons[0]);
    expect(screen.getByText(/Droits d'accès : Active User/)).toBeTruthy();

    fireEvent.click(screen.getByRole('button', { name: 'Enregistrer' }));
    await waitFor(() => expect(vi.mocked(api.put)).toHaveBeenCalledWith(
      '/team/11',
      expect.objectContaining({ permissions: expect.any(Object) }),
    ));

    vi.mocked(api.put).mockClear();
    fireEvent.click(screen.getByTitle("Suspendre l'accès"));
    await waitFor(() => expect(vi.mocked(api.put)).toHaveBeenCalledWith('/team/11', { is_active: false }));

    vi.mocked(api.put).mockClear();
    fireEvent.click(screen.getByTitle("Réactiver l'accès"));
    await waitFor(() => expect(vi.mocked(api.put)).toHaveBeenCalledWith('/team/12', { is_active: true }));

    vi.mocked(api.delete).mockClear();
    fireEvent.click(screen.getAllByTitle('Supprimer définitivement')[0]);
    await waitFor(() => expect(vi.mocked(api.delete)).toHaveBeenCalledWith('/team/11'));
  });

  it('does not expose Reactivate or Suspend for a rejected identity', async () => {
    membersState = [{ ...inactiveMember, id: 77, nom_complet: 'Rejected User', approval_status: 'rejected' }];

    render(<TeamManager />);
    expect(await screen.findByText('Rejected User')).toBeTruthy();
    expect(screen.getByText('Refusé')).toBeTruthy();
    expect(screen.queryByTitle("Réactiver l'accès")).toBeNull();
    expect(screen.queryByTitle("Suspendre l'accès")).toBeNull();
    expect(screen.getByTitle('Supprimer définitivement')).toBeTruthy();
  });

  it('shows an explicit load error and Retry recovers to the real empty state', async () => {
    let failFirstTeamLoad = true;
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url.startsWith('/team/?') && failFirstTeamLoad) {
        failFirstTeamLoad = false;
        throw new Error('load failed');
      }
      if (url.startsWith('/team/?')) return { data: membersState } as never;
      if (url === '/team/quota') return { data: quotaState } as never;
      throw new Error(`Unexpected GET ${url}`);
    });
    render(<TeamManager />);

    expect(await screen.findByText('Équipe non chargée')).toBeTruthy();
    expect(screen.queryByText("Aucun membre dans l'équipe")).toBeNull();

    fireEvent.click(screen.getByRole('button', { name: 'Réessayer' }));

    expect(await screen.findByText("Aucun membre dans l'équipe")).toBeTruthy();
    expect(screen.queryByText('Équipe non chargée')).toBeNull();
  });

  it('closes the permissions modal through both Cancel and the explicit close button', async () => {
    membersState = [activeMember];
    render(<TeamManager />);
    expect(await screen.findByText('Active User')).toBeTruthy();

    fireEvent.click(screen.getByTitle('Gérer les permissions'));
    expect(screen.getByText(/Droits d'accès : Active User/)).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Annuler' }));
    expect(screen.queryByText(/Droits d'accès : Active User/)).toBeNull();

    fireEvent.click(screen.getByTitle('Gérer les permissions'));
    expect(screen.getByText(/Droits d'accès : Active User/)).toBeTruthy();
    fireEvent.click(screen.getByRole('button', { name: 'Fermer les permissions' }));
    expect(screen.queryByText(/Droits d'accès : Active User/)).toBeNull();
  });

  it('locks Validate against accidental double click', async () => {
    membersState = [pendingMember];
    let releaseApprove: () => void = () => {};
    vi.mocked(api.post).mockImplementationOnce(
      () => new Promise((resolve) => { releaseApprove = () => resolve({ data: {} }); }) as never,
    );

    render(<TeamManager />);
    expect(await screen.findByText('Pending User')).toBeTruthy();

    const validate = screen.getByRole('button', { name: 'Valider' });
    fireEvent.click(validate);
    fireEvent.click(validate);
    expect(vi.mocked(api.post)).toHaveBeenCalledTimes(1);

    releaseApprove();
  });

  it('locks a member mutation against accidental double click', async () => {
    membersState = [activeMember];
    let releasePut: () => void = () => {};
    vi.mocked(api.put).mockImplementationOnce(
      () => new Promise((resolve) => { releasePut = () => resolve({ data: {} }); }) as never,
    );

    render(<TeamManager />);
    expect(await screen.findByText('Active User')).toBeTruthy();

    const suspend = screen.getByTitle("Suspendre l'accès");
    fireEvent.click(suspend);
    fireEvent.click(suspend);
    expect(vi.mocked(api.put)).toHaveBeenCalledTimes(1);

    releasePut();
  });

  it('shows and dismisses a mutation error instead of silently failing', async () => {
    membersState = [activeMember];
    vi.mocked(api.put).mockRejectedValueOnce(new Error('network'));

    render(<TeamManager />);
    expect(await screen.findByText('Active User')).toBeTruthy();

    fireEvent.click(screen.getByTitle("Suspendre l'accès"));
    const message = await screen.findByText('Erreur lors de la modification du statut.');
    const banner = message.parentElement;
    expect(banner).toBeTruthy();
    fireEvent.click(within(banner!).getByRole('button', { name: "Fermer l'erreur" }));
    expect(screen.queryByText('Erreur lors de la modification du statut.')).toBeNull();
  });
});
