import React from 'react';
import ReactDOM from 'react-dom/client';
import './../../../index.css';
import { MigrationMappingStudio } from './MigrationMappingStudio';
import type { SchemaInventory, TargetInventory } from './MappingStudioPolicy';

// All identifiers below are synthetic; no patient records or connected DB.
const source: SchemaInventory = {
  sourceSha256: 'a'.repeat(64), sourceFormat: 'sqlite-copy',
  tables: [
    { name: 'patients', columns: [
      { name: 'id', declared_type: 'INTEGER' },
      { name: 'name', declared_type: 'TEXT' },
      { name: 'password_hash', declared_type: 'TEXT' },
    ] },
    { name: 'old_documents', columns: [{ name: 'legacy_ref', declared_type: 'VARCHAR' }] },
  ],
};
const target: TargetInventory = {
  schemaRevision: 'synthetic-only',
  tables: [
    { name: 'patients', columns: [{ name: 'id' }, { name: 'name' }] },
    { name: 'documents', columns: [{ name: 'id' }, { name: 'patient_id' }] },
  ],
};
const filled = new URLSearchParams(window.location.search).get('filled') === '1';
document.documentElement.dataset.dcMigrationVisualFixture = 'synthetic';
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <div className="min-h-screen bg-medical-pearl p-4 text-text-main sm:p-8">
      <MigrationMappingStudio initialSource={filled ? source : undefined} initialTarget={filled ? target : undefined} />
    </div>
  </React.StrictMode>,
);
