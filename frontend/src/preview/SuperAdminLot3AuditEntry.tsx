import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import '../index.css';
import { SuperAdminDashboard } from '../features/superadmin/SuperAdminDashboard';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <SuperAdminDashboard />
    </BrowserRouter>
  </React.StrictMode>,
);
