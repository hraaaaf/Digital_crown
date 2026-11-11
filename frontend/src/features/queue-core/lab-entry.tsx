import React from 'react';
import { createRoot } from 'react-dom/client';
import '../../index.css';
import QueueCoreLabPane from './QueueCoreLabPane';

// Vite development only: production clients never render this fixture.
if (import.meta.env.DEV && import.meta.env.VITE_QUEUE_CORE_LAB_PREVIEW === 'true') {
  const root = document.getElementById('root');
  if (root) createRoot(root).render(<React.StrictMode><QueueCoreLabPane /></React.StrictMode>);
} else {
  document.body.textContent = 'FUE-G laboratoire désactivé';
}
