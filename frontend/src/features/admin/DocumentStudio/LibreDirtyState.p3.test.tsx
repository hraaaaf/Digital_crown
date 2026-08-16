import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { LibreForm } from './Forms/LibreForm';
import { isLibreDirty, setLibreDirty } from './LibreDirtyState';
import { shouldGuardDocumentTabTransition } from './DocumentTabNavigationPolicy';

const renderLibreForm = () => {
  let content = '';
  return render(
    <LibreForm
      title="Note Médicale"
      setTitle={vi.fn()}
      content={content}
      setContent={(value) => { content = value; }}
      customPatient=""
      setCustomPatient={vi.fn()}
      customDate=""
      setCustomDate={vi.fn()}
      hideHeader={false}
      setHideHeader={vi.fn()}
      pageSize="A5"
      setPageSize={vi.fn()}
      alignment="justify"
      setAlignment={vi.fn()}
      validationErrors={[]}
    />,
  );
};

const dirtySnapshot = (libre: boolean) => ({
  prescription: false,
  certificate: false,
  accounting: false,
  installment: false,
  libre,
  plan: false,
});

describe('P3 Document Libre dirty-state', () => {
  beforeEach(() => {
    setLibreDirty(false);
    vi.restoreAllMocks();
  });

  it('marks the draft dirty as soon as the practitioner edits the content', () => {
    renderLibreForm();

    fireEvent.change(
      screen.getByPlaceholderText(/Rédigez votre document ici/i),
      { target: { value: 'Brouillon en cours' } },
    );

    expect(isLibreDirty()).toBe(true);
  });

  it('blocks browser unload while the Libre draft is dirty', () => {
    const { unmount } = renderLibreForm();
    setLibreDirty(true);

    const event = new Event('beforeunload', { cancelable: true });
    window.dispatchEvent(event);

    expect(event.defaultPrevented).toBe(true);
    unmount();
  });

  it('delegates dirty tab-abandonment protection to the centralized navigation policy', () => {
    setLibreDirty(true);

    expect(
      shouldGuardDocumentTabTransition('libre', 'ordonnance', dirtySnapshot(isLibreDirty())),
    ).toBe(true);
  });

  it('allows the transition once explicit discard clears the Libre dirty state', () => {
    setLibreDirty(true);
    expect(
      shouldGuardDocumentTabTransition('libre', 'ordonnance', dirtySnapshot(isLibreDirty())),
    ).toBe(true);

    setLibreDirty(false);
    expect(
      shouldGuardDocumentTabTransition('libre', 'ordonnance', dirtySnapshot(isLibreDirty())),
    ).toBe(false);
  });
});