import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useEffect, useState } from 'react';
import { MainLayout } from './components/Layout/MainLayout';
import { cabinetApi } from './services/templateApi';

// --- PAGES DASHBOARD & LISTES ---
import { Dashboard } from './pages/Dashboard';
import { AddPatientForm } from './features/patients/AddPatientForm';
import { PatientList } from './features/patients/PatientList';

// --- LE NOUVEAU HUB PATIENT ---
import { PatientDetails } from './features/patients/PatientDetails';

// --- ADMINISTRATION & ARCHIVES ---
import { EditPatientForm } from './features/patients/EditPatientForm';
import { PatientDocuments } from './features/patients/PatientDocuments';
import { Settings } from './pages/Settings';

// --- WIZARD SETUP (NOUVEAU) ---
import { SetupWizard } from './features/admin/SetupWizard';

// ==============================================================================
// COMPOSANT DE PROTECTION DES ROUTES
// ==============================================================================

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState<boolean | null>(null);
  const location = useLocation();

  useEffect(() => {
    checkInitStatus();
  }, []);

  const checkInitStatus = async () => {
    try {
      const status = await cabinetApi.checkInitStatus();
      setIsInitialized(status.is_initialized);
    } catch (error) {
      console.error('Erreur vérification statut:', error);
      // En cas d'erreur, on suppose non initialisé pour être sûr
      setIsInitialized(false);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-screen bg-slate-50">
        <div className="flex flex-col items-center gap-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
          <p className="text-slate-600">Vérification de la configuration...</p>
        </div>
      </div>
    );
  }

  // Si non initialisé et pas déjà sur /setup, rediriger vers setup
  if (!isInitialized && location.pathname !== '/setup') {
    return <Navigate to="/setup" replace />;
  }

  // Si déjà initialisé et sur /setup, rediriger vers dashboard
  if (isInitialized && location.pathname === '/setup') {
    return <Navigate to="/dashboard" replace />;
  }

  return <>{children}</>;
};



// =============================================================================
// ROUTES PROTÉGÉES (avec layout)
// =============================================================================

const ProtectedRoutes = () => (
  <MainLayout>
    <Routes>
      {/* Redirection de la racine vers le dashboard */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<Dashboard />} />

      {/* Routes Patients */}
      <Route path="/patients" element={<PatientList />} />
      <Route path="/patients/new" element={<AddPatientForm />} />

      {/* ROUTE UNIQUE : Le Super-Composant PatientDetails gère tout */}
      <Route path="/patients/:id" element={<PatientDetails />} />
      <Route path="/patients/:id/archives" element={<PatientDocuments />} />
      
      {/* ROUTE DE MODIFICATION */}
      <Route path="/patients/:id/edit" element={<EditPatientForm />} />

      {/* ROUTE PARAMÈTRES */}
      <Route path="/settings" element={<Settings />} />
      
      {/* Route par défaut */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  </MainLayout>
);

// =============================================================================
// APP PRINCIPAL
// =============================================================================

function App() {
  return (
    <BrowserRouter>
      <ProtectedRoute>
        <Routes>
          {/* Route publique : Setup Wizard (sans layout) */}
          <Route path="/setup" element={<SetupWizard />} />
          
          {/* Toutes les autres routes sont protégées */}
          <Route path="/*" element={<ProtectedRoutes />} />
        </Routes>
      </ProtectedRoute>
    </BrowserRouter>
  );
}

export default App;
