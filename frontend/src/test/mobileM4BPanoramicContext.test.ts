import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const readSource = (path: string) => readFileSync(resolve(process.cwd(), path), 'utf8');
const historySource = readSource('src/features/panoramic/PanoramicHistory.tsx');
const bridgeSource = readSource('src/features/panoramic/PanoramicMobileBridge.tsx');
const contextSource = readSource('src/features/mobile/Context/MobileContext.tsx');

describe('M4-B panoramic contextual mobile bridge', () => {
  it('removes the fictional trash lifecycle and keeps the real active history endpoint', () => {
    expect(historySource).toContain('/panoramic-analyses');
    expect(historySource).not.toContain('/panoramic-trash');
    expect(historySource).not.toContain('/restore');
    expect(historySource).toContain('Supprimer définitivement');
  });

  it('adds an exact panoramic bridge action on each analysis row with 44px touch controls', () => {
    expect(historySource).toContain('<PanoramicMobileBridge analysisId={analysis.id}');
    expect(historySource).toContain('data-m4b-touch');
    expect(historySource).toContain('min-w-11 min-h-11');
  });

  it('sends only the resource type, internal resource id and target user to the backend', () => {
    expect(bridgeSource).toContain("resource_type: 'panoramic'");
    expect(bridgeSource).toContain('resource_id: analysisId');
    expect(bridgeSource.match(/contains_resource_data !== false/g)?.length ?? 0).toBeGreaterThanOrEqual(2);
    expect(bridgeSource).not.toContain('image_path:');
    expect(bridgeSource).not.toContain('patient_id:');
  });

  it('loads panoramic metadata and image only through the context key and rejects non-image media', () => {
    expect(contextSource).toContain("'panoramic'");
    expect(contextSource).toContain("request('resource-context', creds.access_token)");
    expect(contextSource).toContain("request('resource-context-media', creds.access_token)");
    expect(contextSource).toContain("/api/mobile/${path}");
    expect(contextSource).toContain('context_key: stored.key');
    expect(contextSource).toContain("stored.type === 'panoramic' && !blob.type.startsWith('image/')");
    expect(contextSource).toContain('URL.createObjectURL(blob)');
    expect(contextSource).not.toContain('/ia/panoramic/${');
  });

  it('renders the locked mobile panoramic hierarchy and keeps the context route generic', () => {
    expect(contextSource).toContain('Radio panoramique');
    expect(contextSource).toContain('Contexte cabinet vérifié');
    expect(contextSource).toContain('Rapport enregistré');
    expect(contextSource).toContain('data-m4b-context');
  });
});
