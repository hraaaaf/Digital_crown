import { readFileSync } from 'node:fs';
import { resolve } from 'node:path';
import { describe, expect, it } from 'vitest';

const readSource = (path: string) => readFileSync(resolve(process.cwd(), path), 'utf8');
const documentsSource = readSource('src/features/patients/PatientDocuments.tsx');
const bridgeSource = readSource('src/features/patients/DocumentMobileBridge.tsx');
const contextSource = readSource('src/features/mobile/Context/MobileContext.tsx');

describe('M4-C document contextual mobile bridge', () => {
  it('keeps legacy documents explicit and desktop-only for mutations and mobile bridge', () => {
    expect(documentsSource).toContain("doc.id.startsWith('legacy:')");
    expect(documentsSource).toContain('Ancien format · desktop uniquement');
    expect(documentsSource).toContain('Non portable sur mobile');
    expect(documentsSource).toContain("if (docId.startsWith('legacy:')) return");
    expect(documentsSource).toContain("if (doc.id.startsWith('legacy:')) return");
  });

  it('routes all desktop view/download actions through the canonical authenticated document endpoint', () => {
    expect(documentsSource).toContain("/documents/${encodeURIComponent(docId)}/download");
    expect(documentsSource).toContain('handleView(doc.id)');
    expect(documentsSource).toContain('handleDownload(doc.id, doc.name)');
    expect(documentsSource).not.toContain('handleView(doc.url)');
    expect(documentsSource).not.toContain('handleDownload(doc.url');
  });

  it('adds the exact bridge only to canonical numeric archive ids with touch-safe actions', () => {
    expect(documentsSource).toContain("/^\\d+$/.test(doc.id)");
    expect(documentsSource).toContain('<DocumentMobileBridge documentId={canonicalId}');
    expect(documentsSource).toContain('data-m4c-touch');
    expect(documentsSource).toContain('min-w-11 min-h-11');
    expect(documentsSource).toContain('min-h-[48px]');
  });

  it('sends only document resource identity and target user to the opaque pairing endpoint', () => {
    expect(bridgeSource).toContain("resource_type: 'document'");
    expect(bridgeSource).toContain('resource_id: documentId');
    expect(bridgeSource.match(/contains_resource_data !== false/g)?.length ?? 0).toBeGreaterThanOrEqual(2);
    expect(bridgeSource).not.toContain('file_path:');
    expect(bridgeSource).not.toContain('patient_id:');
  });

  it('loads document metadata and binary only through the server context key', () => {
    expect(contextSource).toContain("'document'");
    expect(contextSource).toContain("request('resource-context', creds.access_token)");
    expect(contextSource).toContain("request('resource-context-media', creds.access_token)");
    expect(contextSource).toContain('context_key: stored.key');
    expect(contextSource).toContain('URL.createObjectURL(blob)');
    expect(contextSource).toContain('data-m4c-context');
    expect(contextSource).not.toContain('/documents/${');
  });

  it('renders the locked mobile document hierarchy and keeps the route idless', () => {
    expect(contextSource).toContain('Contexte cabinet vérifié');
    expect(contextSource).toContain('<h1 className="mt-2 text-3xl font-black tracking-tight text-text-main">Document</h1>');
    expect(contextSource).toContain('Ouvrir');
    expect(contextSource).toContain('Télécharger');
    expect(contextSource).toContain('aucun identifiant document dans l’URL');
  });
});
