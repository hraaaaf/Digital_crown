import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { CertificateTemplatePresets } from './CertificateFormInner';
import { api } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('CUST-03 certificate templates', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads only custom CERTIFICAT templates and applies one only after explicit click', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/templates') {
        return {
          data: [{ id: 'tpl-1', name: 'Aptitude traitement', description: null }],
        } as never;
      }
      if (url === '/templates/tpl-1') {
        return {
          data: {
            id: 'tpl-1',
            name: 'Aptitude traitement',
            body_html: 'Je certifie que le patient peut poursuivre le traitement proposé.',
          },
        } as never;
      }
      throw new Error(`Unexpected GET ${url}`);
    });

    const onApply = vi.fn();
    render(<CertificateTemplatePresets content="" onApply={onApply} />);

    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/templates', {
      params: { type: 'CERTIFICAT', is_system: false },
    }));
    expect(onApply).not.toHaveBeenCalled();

    fireEvent.click(await screen.findByRole('button', { name: /Aptitude traitement/i }));

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/templates/tpl-1');
      expect(onApply).toHaveBeenCalledWith(
        'Je certifie que le patient peut poursuivre le traitement proposé.',
      );
    });
  });

  it('creates through DocumentTemplate and copies the saved draft into the editable certificate', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] } as never);
    vi.mocked(api.post).mockResolvedValue({
      data: {
        id: 'tpl-new',
        name: 'Contrôle médical',
        description: 'Modèle de certificat médical du cabinet',
        body_html: 'Je certifie avoir examiné ce patient ce jour.',
      },
    } as never);

    const onApply = vi.fn();
    render(
      <CertificateTemplatePresets
        content="Je certifie avoir examiné ce patient ce jour."
        onApply={onApply}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: /Créer un modèle/i }));

    fireEvent.change(screen.getByRole('textbox', { name: /Nom du modèle/i }), {
      target: { value: 'Contrôle médical' },
    });
    expect(
      (screen.getByRole('textbox', { name: /Contenu du modèle/i }) as HTMLTextAreaElement).value,
    ).toBe('Je certifie avoir examiné ce patient ce jour.');

    fireEvent.click(screen.getByRole('button', { name: /^Enregistrer$/i }));

    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/templates', {
        type: 'CERTIFICAT',
        style_key: 'saninova',
        name: 'Contrôle médical',
        description: 'Modèle de certificat médical du cabinet',
        body_html: 'Je certifie avoir examiné ce patient ce jour.',
        is_system: false,
        is_default: false,
      });
      expect(onApply).toHaveBeenCalledWith('Je certifie avoir examiné ce patient ce jour.');
    });
  });
});
