import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ErrorBoundary } from './ErrorBoundary'

// Composant qui crash intentionnellement pour les tests
const CrashingComponent = ({ shouldCrash }: { shouldCrash: boolean }) => {
  if (shouldCrash) throw new Error('Test crash message')
  return <div>Contenu normal</div>
}

// Supprimer les console.error de React pendant les tests de crash
beforeEach(() => {
  vi.spyOn(console, 'error').mockImplementation(() => {})
})

describe('ErrorBoundary', () => {
  it('affiche les enfants quand aucune erreur', () => {
    render(
      <ErrorBoundary>
        <CrashingComponent shouldCrash={false} />
      </ErrorBoundary>
    )
    expect(screen.getByText('Contenu normal')).toBeInTheDocument()
  })

  it("affiche l'écran d'erreur quand un composant crash", () => {
    render(
      <ErrorBoundary>
        <CrashingComponent shouldCrash={true} />
      </ErrorBoundary>
    )
    expect(screen.getByText(/erreur inattendue/i)).toBeInTheDocument()
    expect(screen.getByText('Test crash message')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /recharger/i })).toBeInTheDocument()
  })

  it('affiche un fallback personnalisé si fourni', () => {
    render(
      <ErrorBoundary fallback={<div>Fallback custom</div>}>
        <CrashingComponent shouldCrash={true} />
      </ErrorBoundary>
    )
    expect(screen.getByText('Fallback custom')).toBeInTheDocument()
  })

  it('le bouton recharger appelle window.location.reload', async () => {
    const reloadMock = vi.fn()
    Object.defineProperty(window, 'location', {
      value: { reload: reloadMock },
      writable: true,
    })

    render(
      <ErrorBoundary>
        <CrashingComponent shouldCrash={true} />
      </ErrorBoundary>
    )

    await userEvent.click(screen.getByRole('button', { name: /recharger/i }))
    expect(reloadMock).toHaveBeenCalledOnce()
  })
})
