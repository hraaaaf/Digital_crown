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

  it('converts rich HTML formatting into clean plain text before filling the certificate textarea', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/templates') {
        return { data: [{ id: 'tpl-rich', name: 'Texte enrichi', description: null }] } as never;
      }
      if (url === '/templates/tpl-rich') {
        return {
          data: {
            id: 'tpl-rich',
            name: 'Texte enrichi',
            body_html: '<p>Je certifie que <strong>le patient</strong> a été examiné.</p><p>Repos&nbsp;recommandé<br>pendant 3 jours.</p>',
          },
        } as never;
      }
      throw new Error(`Unexpected GET ${url}`);
    });

    const onApply = vi.fn();
    render(<CertificateTemplatePresets content="" onApply={onApply} />);

    fireEvent.click(await screen.findByRole('button', { name: /Texte enrichi/i }));

    await waitFor(() => {
      expect(onApply).toHaveBeenCalledWith(
        'Je certifie que le patient a été examiné.\nRepos recommandé\npendant 3 jours.',
      );
    });
  });

  it('rejects document-layout template code instead of exposing it in the free-text certificate', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/templates') {
        return { data: [{ id: 'tpl-layout', name: 'Mise en page', description: null }] } as never;
      }
      return {
        data: {
          id: 'tpl-layout',
          name: 'Mise en page',
          body_html: '<div><b>Patient : {{ patient.nom }}</b></div>',
        },
      } as never;
    });

    const onApply = vi.fn();
    render(<CertificateTemplatePresets content="" onApply={onApply} />);

    fireEvent.click(await screen.findByRole('button', { name: /Mise en page/i }));

    expect(await screen.findByRole('alert')).toHaveTextContent(/code de mise en page/i);
    expect(onApply).not.toHaveBeenCalled();
  });

  it('does not overwrite an existing certificate draft when replacement is declined', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/templates') {
        return { data: [{ id: 'tpl-guard', name: 'Nouveau modèle', description: null }] } as never;
      }
      return {
        data: {
          id: 'tpl-guard',
          name: 'Nouveau modèle',
          body_html: 'Nouveau texte proposé par le modèle.',
        },
      } as never;
    });

    const onApply = vi.fn();
    render(<CertificateTemplatePresets content="Brouillon actuel du praticien." onApply={onApply} />);

    fireEvent.click(await screen.findByRole('button', { name: /Nouveau modèle/i }));

    expect(await screen.findByRole('dialog', { name: /Remplacer le brouillon actuel/i })).toBeTruthy();
    expect(onApply).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: /Conserver mon brouillon/i }));
    await waitFor(() => expect(screen.queryByRole('dialog', { name: /Remplacer le brouillon actuel/i })).toBeNull());
    expect(onApply).not.toHaveBeenCalled();
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
