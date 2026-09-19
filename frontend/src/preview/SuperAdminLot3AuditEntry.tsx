import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import '../index.css';
import { SuperAdminDashboard } from '../features/superadmin/SuperAdminDashboard';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <SuperAdminDashboard />
      <Toaster position="top-right" />
    </BrowserRouter>
  </React.StrictMode>,
);
