/** DEV-ONLY static route used by isolated responsive CI. Never built as production entry. */
import React from 'react';
import { createRoot } from 'react-dom/client';
import '../../../index.css';
import { MappingStudio } from './MappingStudio';

createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <main className="min-h-screen bg-medical-pearl p-3 sm:p-5 lg:p-8">
      <MappingStudio />
    </main>
  </React.StrictMode>,
);
