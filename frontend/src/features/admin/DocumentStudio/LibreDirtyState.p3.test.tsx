import { fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';

import { LibreForm } from './Forms/LibreForm';
import { isLibreDirty, setLibreDirty } from './LibreDirtyState';
import { StudioTabs } from './StudioTabs';

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

  it('keeps the user on Document Libre when tab abandonment is refused', () => {
    const onTabChange = vi.fn();
    const confirmSpy = vi.spyOn(window, 'confirm').mockReturnValue(false);
    setLibreDirty(true);

    render(<StudioTabs activeTab="libre" onTabChange={onTabChange} />);
    fireEvent.click(screen.getByRole('button', { name: /Ordonnance/i }));

    expect(confirmSpy).toHaveBeenCalledOnce();
    expect(onTabChange).not.toHaveBeenCalled();
    expect(isLibreDirty()).toBe(true);
  });

  it('abandons the draft only after explicit confirmation and clears dirty state', () => {
    const onTabChange = vi.fn();
    vi.spyOn(window, 'confirm').mockReturnValue(true);
    setLibreDirty(true);

    render(<StudioTabs activeTab="libre" onTabChange={onTabChange} />);
    fireEvent.click(screen.getByRole('button', { name: /Ordonnance/i }));

    expect(onTabChange).toHaveBeenCalledWith('ordonnance');
    expect(isLibreDirty()).toBe(false);
  });
});
