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
})
