import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import '@testing-library/jest-dom/vitest'

import { LivePreview } from './LivePreview'

describe('LivePreview R7', () => {
  it('utilise une terminologie déterministe et explicite quand aucun PDF n’est généré', () => {
    render(
      <LivePreview
        pdfUrl={null}
        loading={false}
        onClose={vi.fn()}
        onRefresh={vi.fn()}
        title="Ordonnance"
        inline
      />,
    )

    expect(screen.getByText('Aperçu document')).toBeInTheDocument()
    expect(screen.getByText('Aperçu non généré')).toBeInTheDocument()
    expect(screen.getByText(/lecture seule/)).toBeInTheDocument()
    expect(screen.queryByText(/Intelligence/i)).not.toBeInTheDocument()
  })

  it('expose des actions explicites Actualiser et Fermer', () => {
    const onRefresh = vi.fn()
    const onClose = vi.fn()
    render(
      <LivePreview
        pdfUrl={null}
        loading={false}
        onClose={onClose}
        onRefresh={onRefresh}
        title="Ordonnance"
        inline
      />,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Actualiser' }))
    fireEvent.click(screen.getByRole('button', { name: 'Fermer' }))
    expect(onRefresh).toHaveBeenCalledTimes(1)
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('expose la preview non-inline comme dialogue, place le focus sur Fermer et gère Escape', () => {
    const onClose = vi.fn()
    render(
      <LivePreview
        pdfUrl={null}
        loading={false}
        onClose={onClose}
        title="Ordonnance"
      />,
    )

    const dialog = screen.getByRole('dialog', { name: 'Ordonnance' })
    const closeButton = screen.getByRole('button', { name: 'Fermer' })
    expect(dialog).toHaveAttribute('aria-modal', 'true')
    expect(closeButton).toHaveFocus()

    fireEvent.keyDown(window, { key: 'Escape' })
    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('utilise un overlay modal responsive au lieu du drawer droit historique', () => {
    const { unmount } = render(
      <LivePreview
        pdfUrl={null}
        loading={false}
        onClose={vi.fn()}
        title="Document Libre"
      />,
    )

    const overlay = document.querySelector('.document-studio-live-preview')
    const dialog = screen.getByRole('dialog', { name: 'Document Libre' })

    expect(overlay).toHaveClass('fixed', 'inset-0')
    expect(overlay).toHaveClass('bg-slate-950/60', 'backdrop-blur-sm')
    expect(dialog.className).toContain('w-full')
    expect(dialog.className).toContain('sm:max-w-4xl')
    expect(dialog.className).toContain('lg:max-w-5xl')
    expect(dialog.className).not.toContain('sm:left-auto')
    expect(dialog.className).not.toContain('w-[550px]')
    expect(document.body.style.overflow).toBe('hidden')

    unmount()
    expect(document.body.style.overflow).toBe('')
  })
})
