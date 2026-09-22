import { fireEvent, render, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { LibreTemplatePresets } from './LibreForm';
import { api } from '../../../../services/api';

vi.mock('../../../../services/api', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}));

describe('CUST-03 document libre templates', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('loads custom DOCUMENT_LIBRE templates and applies title/content only after click', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/templates') {
        return {
          data: [{ id: 'libre-1', name: 'Lettre confrère', description: null }],
        } as never;
      }
      if (url === '/templates/libre-1') {
        return {
          data: {
            id: 'libre-1',
            name: 'Lettre confrère',
            body_html: 'Cher confrère, je vous adresse ce patient pour avis.',
          },
        } as never;
      }
      throw new Error(`Unexpected GET ${url}`);
    });

    const onApply = vi.fn();
    render(<LibreTemplatePresets title="" content="" onApply={onApply} />);

    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/templates', {
      params: { type: 'DOCUMENT_LIBRE', is_system: false },
    }));
    expect(onApply).not.toHaveBeenCalled();

    fireEvent.click(await screen.findByRole('button', { name: /Lettre confrère/i }));

    await waitFor(() => {
      expect(api.get).toHaveBeenCalledWith('/templates/libre-1');
      expect(onApply).toHaveBeenCalledWith(
        'Lettre confrère',
        'Cher confrère, je vous adresse ce patient pour avis.',
      );
    });
  });

  it('does not overwrite a current document when replacement is declined', async () => {
    vi.mocked(api.get).mockImplementation(async (url: string) => {
      if (url === '/templates') {
        return { data: [{ id: 'libre-guard', name: 'Autre titre', description: null }] } as never;
      }
      return {
        data: {
          id: 'libre-guard',
          name: 'Autre titre',
          body_html: 'Autre contenu proposé par le modèle.',
        },
      } as never;
    });

    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
    const onApply = vi.fn();
    render(
      <LibreTemplatePresets
        title="Titre actuel"
        content="Contenu actuel du praticien."
        onApply={onApply}
      />,
    );

    fireEvent.click(await screen.findByRole('button', { name: /Autre titre/i }));

    await waitFor(() => expect(confirmSpy).toHaveBeenCalledTimes(1));
    expect(onApply).not.toHaveBeenCalled();
    confirmSpy.mockRestore();
  });

  it('bounds an existing long document title to the template schema limit', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] } as never);
    const longTitle = 'T'.repeat(140);

    render(
      <LibreTemplatePresets
        title={longTitle}
        content="Contenu suffisamment long pour permettre la sauvegarde du modèle."
        onApply={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: /Enregistrer comme modèle/i }));

    expect(
      (screen.getByRole('textbox', { name: /Nom du modèle/i }) as HTMLInputElement).value,
    ).toHaveLength(100);
  });

  it('saves the current title/content through DocumentTemplate without capturing per-document metadata', async () => {
    vi.mocked(api.get).mockResolvedValue({ data: [] } as never);
    vi.mocked(api.post).mockResolvedValue({
      data: {
        id: 'libre-new',
        name: 'Lettre au médecin traitant',
        description: 'Modèle de document libre du cabinet',
        body_html: 'Cher confrère, merci de recevoir ce patient pour avis spécialisé.',
      },
    } as never);

    render(
      <LibreTemplatePresets
        title="Lettre au médecin traitant"
        content="Cher confrère, merci de recevoir ce patient pour avis spécialisé."
        onApply={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByRole('button', { name: /Enregistrer comme modèle/i }));

    expect(
      (screen.getByRole('textbox', { name: /Nom du modèle/i }) as HTMLInputElement).value,
    ).toBe('Lettre au médecin traitant');
    expect(
      (screen.getByRole('textbox', { name: /Contenu du modèle de document libre/i }) as HTMLTextAreaElement).value,
    ).toBe('Cher confrère, merci de recevoir ce patient pour avis spécialisé.');

    fireEvent.click(screen.getByRole('button', { name: /Enregistrer le modèle/i }));

    await waitFor(() => expect(api.post).toHaveBeenCalledWith('/templates', {
      type: 'DOCUMENT_LIBRE',
      style_key: 'saninova',
      name: 'Lettre au médecin traitant',
      description: 'Modèle de document libre du cabinet',
      body_html: 'Cher confrère, merci de recevoir ce patient pour avis spécialisé.',
      is_system: false,
      is_default: false,
    }));
  });
});
