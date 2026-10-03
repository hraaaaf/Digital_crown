import { cleanup, render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import {
  CnssInsuranceAction,
  insuranceOrganizationFromAssurance,
} from './CnssInsuranceAction';

vi.mock('../../services/api', () => ({
  api: {
    post: vi.fn(),
  },
}));

afterEach(() => cleanup());

describe('insuranceOrganizationFromAssurance', () => {
  it.each([
    ['CNSS', 'CNSS'],
    ['cnops', 'CNOPS'],
    ['FAR', 'FAR'],
    ['MUTUELLE_FAR', 'FAR'],
    [' AUCUNE ', null],
    [null, null],
  ])('maps %s to %s', (value, expected) => {
    expect(insuranceOrganizationFromAssurance(value)).toBe(expected);
  });
});

describe('CnssInsuranceAction preferred organization UX', () => {
  const baseProps = {
    honorairesDocumentId: 42,
    onArchived: vi.fn(),
    onCloseMenu: vi.fn(),
  };

  it('puts FAR first for a FAR patient and keeps an explicit organization override', () => {
    const { container } = render(
      <CnssInsuranceAction {...baseProps} preferredOrganization="FAR" />,
    );

    const preferred = container.querySelector('[data-insurance-preferred="true"]');
    expect(preferred?.getAttribute('data-insurance-action')).toBe('prepare-far');
    expect(preferred?.textContent).toContain('Préparer feuille FAR');
    expect(screen.getByText('Changer d’organisme')).toBeTruthy();
    expect(container.querySelector('[data-insurance-action="prepare-cnss"]')).toBeTruthy();
    expect(container.querySelector('[data-insurance-action="prepare-cnops"]')).toBeTruthy();
  });

  it('puts CNSS first for a CNSS patient', () => {
    const { container } = render(
      <CnssInsuranceAction {...baseProps} preferredOrganization="CNSS" />,
    );
    expect(container.querySelector('[data-insurance-preferred="true"]')?.getAttribute('data-insurance-action')).toBe('prepare-cnss');
  });

  it('keeps the legacy three choices when no supported assurance is known', () => {
    const { container } = render(<CnssInsuranceAction {...baseProps} />);
    expect(container.querySelector('[data-insurance-preferred="true"]')).toBeNull();
    expect(container.querySelector('[data-insurance-action="prepare-cnss"]')).toBeTruthy();
    expect(container.querySelector('[data-insurance-action="prepare-cnops"]')).toBeTruthy();
    expect(container.querySelector('[data-insurance-action="prepare-far"]')).toBeTruthy();
  });
});
