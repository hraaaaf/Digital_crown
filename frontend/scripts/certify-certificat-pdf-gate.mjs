// Targeted Certificat entrypoint for local revalidation of certificate PDF regressions.
process.env.REMAINING_DOCUMENT_FILTER = 'certificat';
await import('./certify-remaining-documents-pdf-gate.mjs');
