import { beforeEach, describe, expect, it, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';

vi.mock('../../../services/api', () => ({
  api: { get: vi.fn() },
}));

vi.mock('framer-motion', () => ({
  motion: { tr: ({ children, ...props }: any) => <tr {...props}>{children}</tr> },
  AnimatePresence: ({ children }: any) => children,
}));

import { api } from '../../../services/api';
import { AuditLogViewer } from './AuditLogViewer';

const getMock = vi.mocked(api.get);

describe('AuditLogViewer read truth', () => {
  beforeEach(() => vi.clearAllMocks());

  it('shows a degraded state instead of a false empty audit history on read failure', async () => {
    getMock.mockRejectedValueOnce(new Error('audit unavailable'));
    render(<AuditLogViewer />);

    expect(await screen.findByText("Journal d'audit indisponible")).toBeInTheDocument();
    expect(screen.queryByText('Aucun log trouvé')).not.toBeInTheDocument();
    expect(screen.getByText('— entrées')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: 'Réessayer' })).toBeInTheDocument();
  });

  it('shows a genuine empty state only after a successful backend read', async () => {
    getMock.mockResolvedValueOnce({ data: { logs: [], total: 0 } } as any);
    render(<AuditLogViewer />);

    expect(await screen.findByText('Aucun log trouvé')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByText('0 entrée')).toBeInTheDocument());
    expect(screen.queryByText("Journal d'audit indisponible")).not.toBeInTheDocument();
  });
});
