import { render, screen } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import { LibreForm } from './LibreForm';

const noop = vi.fn();

describe('LibreForm P3-C', () => {
  it('affiche les erreurs canoniques libreTitle/libreContent sur les champs correspondants', () => {
    render(
      <LibreForm
        title=""
        setTitle={noop}
        content=""
        setContent={noop}
        customPatient=""
        setCustomPatient={noop}
        customDate=""
        setCustomDate={noop}
        hideHeader={false}
        setHideHeader={noop}
        pageSize="A4"
        setPageSize={noop}
        alignment="left"
        setAlignment={noop}
        validationErrors={[
          { field: 'libreTitle', message: 'Le titre du document libre est requis.' },
          { field: 'libreContent', message: 'Le contenu du document libre est vide.' },
        ]}
      />,
    );

    expect(screen.getByText(/Titre Requis/i)).toBeTruthy();
    expect(screen.getByText(/Le contenu ne peut être vide/i)).toBeTruthy();
  });

  it('utilise des boutons non-submit pour la mise en forme', () => {
    render(
      <LibreForm
        title="Lettre"
        setTitle={noop}
        content="Texte"
        setContent={noop}
        customPatient=""
        setCustomPatient={noop}
        customDate=""
        setCustomDate={noop}
        hideHeader={false}
        setHideHeader={noop}
        pageSize="A4"
        setPageSize={noop}
        alignment="left"
        setAlignment={noop}
      />,
    );

    expect(screen.getByTitle('Gras').getAttribute('type')).toBe('button');
    expect(screen.getByTitle('Tableau').getAttribute('type')).toBe('button');
  });
});
