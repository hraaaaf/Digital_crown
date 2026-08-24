from pathlib import Path

p = Path('frontend/src/features/mobile/Dashboard/hooks/useMobileDashboard.ts')
s = p.read_text()

anchor = """function resolveApiBaseUrl(stored: string): string {
  const hostname = window.location.hostname;
  if (hostname === 'localhost' || hostname === '127.0.0.1') return stored;
  if (stored.includes('localhost') || stored.includes('127.0.0.1')) {
    return `${window.location.protocol}//${hostname}:8005`;
  }
  return stored;
}
"""
replacement = anchor + """

function isQueueableNetworkError(error: unknown): boolean {
  if (error instanceof TypeError) return true;
  const name = error && typeof error === 'object' && 'name' in error
    ? String((error as { name?: unknown }).name ?? '')
    : '';
  return name === 'AbortError' || name === 'TimeoutError';
}
"""
if s.count(anchor) != 1:
    raise SystemExit(f'resolveApiBaseUrl anchor count={s.count(anchor)}')
s = s.replace(anchor, replacement)

old_snapshot_catch = """    } catch (err) {
      console.error('[MobileDashboard] fetchSnapshot failed:', err);
      const notPaired = err instanceof Error && err.message === 'Non appairé';
      const cached = await MobileStorage.getLastSnapshot();
      if (cached) {
        setSnapshot(cached);
        setSyncStatus('error');
        setError(notPaired
          ? 'Non ré-appairé — dernières données locales (scannez le QR pour synchroniser)'
          : 'Hors réseau — données en cache');
      } else {
        setError('Impossible de joindre le cabinet');
        setSyncStatus('error');
      }
    }
"""
new_snapshot_catch = """    } catch (err) {
      console.error('[MobileDashboard] fetchSnapshot failed:', err);
      const notPaired = err instanceof Error && err.message === 'Non appairé';
      if (notPaired) {
        setError('Session mobile expirée ou révoquée');
        setSyncStatus('error');
        return;
      }
      if (!isQueueableNetworkError(err)) {
        setError(err instanceof Error ? err.message : 'Erreur de synchronisation mobile');
        setSyncStatus('error');
        return;
      }
      const cached = await MobileStorage.getLastSnapshot();
      if (cached) {
        setSnapshot(cached);
        setSyncStatus('error');
        setError('Hors réseau — données en cache');
      } else {
        setError('Impossible de joindre le cabinet');
        setSyncStatus('error');
      }
    }
"""
if s.count(old_snapshot_catch) != 1:
    raise SystemExit(f'snapshot catch count={s.count(old_snapshot_catch)}')
s = s.replace(old_snapshot_catch, new_snapshot_catch)

old_status_catch = """    } catch {
      await MobileStorage.enqueueAction(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}/status`, 'PATCH', { status }, actionId);
      setQueuedActionsCount((await MobileStorage.getActionQueue()).length);
      toast('Mise à jour mise en attente (hors ligne)', { icon: '🔄' });
      setSnapshot(prev => prev ? {
        ...prev,
        appointments: prev.appointments.map(a => a.id === id ? { ...a, status } : a),
      } : prev);
    }
"""
new_status_catch = """    } catch (err) {
      if (!isQueueableNetworkError(err)) {
        toast.error(err instanceof Error && err.message === 'Non appairé'
          ? 'Session mobile expirée ou révoquée'
          : 'Erreur lors de la mise à jour');
        return;
      }
      await MobileStorage.enqueueAction(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}/status`, 'PATCH', { status }, actionId);
      setQueuedActionsCount((await MobileStorage.getActionQueue()).length);
      toast('Mise à jour mise en attente (hors ligne)', { icon: '🔄' });
      setSnapshot(prev => prev ? {
        ...prev,
        appointments: prev.appointments.map(a => a.id === id ? { ...a, status } : a),
      } : prev);
    }
"""
if s.count(old_status_catch) != 1:
    raise SystemExit(f'status catch count={s.count(old_status_catch)}')
s = s.replace(old_status_catch, new_status_catch)

old_delete_catch = """    } catch {
      await MobileStorage.enqueueAction(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}`, 'DELETE', undefined, actionId);
      setQueuedActionsCount((await MobileStorage.getActionQueue()).length);
      toast('Suppression mise en attente (hors ligne)', { icon: '🔄' });
      setSnapshot(prev => prev ? {
        ...prev,
        appointments: prev.appointments.filter(a => a.id !== id),
      } : prev);
    }
"""
new_delete_catch = """    } catch (err) {
      if (!isQueueableNetworkError(err)) {
        toast.error(err instanceof Error && err.message === 'Non appairé'
          ? 'Session mobile expirée ou révoquée'
          : 'Erreur lors de la suppression');
        return;
      }
      await MobileStorage.enqueueAction(`${resolveApiBaseUrl(creds.api_base_url)}/api/mobile/appointments/${id}`, 'DELETE', undefined, actionId);
      setQueuedActionsCount((await MobileStorage.getActionQueue()).length);
      toast('Suppression mise en attente (hors ligne)', { icon: '🔄' });
      setSnapshot(prev => prev ? {
        ...prev,
        appointments: prev.appointments.filter(a => a.id !== id),
      } : prev);
    }
"""
if s.count(old_delete_catch) != 1:
    raise SystemExit(f'delete catch count={s.count(old_delete_catch)}')
s = s.replace(old_delete_catch, new_delete_catch)
p.write_text(s)

# Strengthen the source-level gate so future refactors cannot regress to catch-all queuing.
t = Path('frontend/src/test/mobileM62OfflineTruth.test.ts')
ts = t.read_text()
needle = """    expect(hook).toContain("'X-Mobile-Action-Id': action.id");
    expect(hook).toContain('if (!res.ok)');
    expect(hook).toContain('await MobileStorage.removeActionFromQueue(action.id)');
    expect(hook).not.toContain("toast('Déplacement mis en attente (hors ligne)'");
"""
replacement = """    expect(hook).toContain("'X-Mobile-Action-Id': action.id");
    expect(hook).toContain('if (!res.ok)');
    expect(hook).toContain('await MobileStorage.removeActionFromQueue(action.id)');
    expect(hook).toContain('isQueueableNetworkError');
    expect(hook).toContain("name === 'AbortError' || name === 'TimeoutError'");
    expect(hook).not.toContain("toast('Déplacement mis en attente (hors ligne)'");
"""
if ts.count(needle) != 1:
    raise SystemExit(f'test truth needle count={ts.count(needle)}')
t.write_text(ts.replace(needle, replacement))

# Final static truth: catch-all queue patterns must be gone.
final = p.read_text()
assert final.count('if (!isQueueableNetworkError(err))') >= 3
assert "setError('Hors réseau — données en cache')" in final
