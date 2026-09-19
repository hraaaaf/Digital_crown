import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import '../index.css';
import { TeamManager } from '../features/admin/TeamManager';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <main className="min-h-screen bg-white p-6 md:p-10">
        <div className="mx-auto max-w-6xl">
          <TeamManager />
        </div>
      </main>
    </BrowserRouter>
  </React.StrictMode>,
);
