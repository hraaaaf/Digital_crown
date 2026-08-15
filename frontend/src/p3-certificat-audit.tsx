import React from 'react';
import ReactDOM from 'react-dom/client';
import { CertificateForm } from './features/admin/DocumentStudio/Forms/CertificateForm';
import './index.css';

const params = new URLSearchParams(window.location.search);
const mode = params.get('mode') || 'work';

const initialType = mode === 'presence'
  ? 'Certificat de Présence'
  : mode === 'free'
    ? 'Certificat médical'
    : 'Arrêt de travail';

const App = () => {
  const [certifType, setCertifType] = React.useState(initialType);
  const [certifDays, setCertifDays] = React.useState(3);
  const [certifCustomMotif, setCertifCustomMotif] = React.useState(
    mode === 'free'
      ? 'Je certifie avoir reçu ce patient en consultation et lui avoir prodigué les soins bucco-dentaires indiqués dans son dossier médical.'
      : '',
  );

  return (
    <main className="min-h-screen bg-slate-100 p-4 sm:p-8">
      <CertificateForm
        patientId=""
        certifType={certifType}
        setCertifType={setCertifType}
        certifDays={certifDays}
        setCertifDays={setCertifDays}
        certifCustomMotif={certifCustomMotif}
        setCertifCustomMotif={setCertifCustomMotif}
      />
    </main>
  );
};

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
