import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import { DocumentHub } from './features/admin/DocumentHub';
import './index.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <main className="min-h-screen bg-slate-100 p-4">
        <DocumentHub patientId="1" patientName="Patient Test" />
      </main>
    </BrowserRouter>
  </React.StrictMode>,
);
