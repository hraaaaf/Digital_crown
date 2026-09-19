import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import '../index.css';
import { TeamManager } from '../features/admin/TeamManager';
import { SuperAdminDashboard } from '../features/superadmin/SuperAdminDashboard';

const params = new URLSearchParams(window.location.search);
const view = params.get('view') || 'team';

function Preview() {
  if (view === 'superadmin') {
    return <SuperAdminDashboard />;
  }

  return (
    <main className="min-h-screen bg-white p-6 md:p-10">
      <div className="mx-auto max-w-6xl">
        <TeamManager />
      </div>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Preview />
    </BrowserRouter>
  </React.StrictMode>,
);
