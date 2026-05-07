import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { useEffect, useState } from 'react';
import { MainLayout } from './components/Layout/MainLayout';
import { cabinetApi } from './services/templateApi';

// --- PAGES DASHBOARD & LISTES ---
import { Dashboard } from './pages/Dashboard';
import { AddPatientForm } from './features/patients/AddPatientForm';
import { PatientList } from './features/patients/PatientList';

// --- LE NOUVEAU HUB PATIENT ---
import { PatientDetails } from './features/patients/PatientDetails';
import { AgendaPage } from './pages/AgendaPage';
import { AccountingPage } from './pages/AccountingPage';

// --- ADMINISTRATION & ARCHIVES ---
import { EditPatientForm } from './features/patients/EditPatientForm';
import { PatientDocuments } from './features/patients/PatientDocuments';
import { Settings } from './pages/Settings';

// --- WIZARD SETUP & WELCOME ---
import { SetupWizard } from './features/admin/SetupWizard';
import { WelcomeScreen } from './pages/WelcomeScreen';
import { LoginPage } from './pages/LoginPage';
import { authService } from './services/auth';
import { MarketingDemo } from './components/MarketingDemo';
import { EliteLibrary } from './features/clinical-ref/EliteLibrary';

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
    if (authService.isAuthenticated()) {
      checkInitStatus();
    }
  }, [authService.isAuthenticated()]);

  const checkInitStatus = async () => {
    try {
      const status = await cabinetApi.checkInitStatus();
      setIsInitialized(status.is_initialized);
      
      // AUTO-BYPASS : Si le cabinet est déjà initialisé (ancien compte), 
      // on active le mode réel par défaut pour éviter l'écran de bienvenue.
      if (status.is_initialized && !localStorage.getItem('appMode')) {
        console.log("Installation existante détectée. Activation du mode réel.");
        localStorage.setItem('appMode', 'prod');
      }
    } catch (error) {
      console.error('Erreur vérification statut:', error);
      setIsInitialized(false);
    } finally {
      setIsLoading(false);
    }
  };

  // BYPASS AUTH : Si on est sur /login et pas connecté, on laisse passer pour afficher la page
  if (!authService.isAuthenticated()) {
    if (location.pathname === '/login') return <>{children}</>;
    return <Navigate to="/login" replace />;
  }

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

  // Force le choix du mode s'il n'existe pas
  const appMode = localStorage.getItem('appMode');
  if (!appMode && location.pathname !== '/welcome') {
    return <Navigate to="/welcome" replace />;
  }

  // En mode démo, on ignore la redirection forcée vers setup si on veut explorer librement
  // mais on autorise l'accès au setup. Si mode réel, on impose /setup si non init.
  if (appMode === 'prod') {
    if (!isInitialized && location.pathname !== '/setup') {
      return <Navigate to="/setup" replace />;
    }
    if (isInitialized && location.pathname === '/setup') {
      return <Navigate to="/dashboard" replace />;
    }
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
      <Route path="/agenda" element={<AgendaPage />} />
      <Route path="/accounting" element={<AccountingPage />} />

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

      <Route path="/bibliotheque" element={<EliteLibrary />} />
      
      {/* Route par défaut */}
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  </MainLayout>
);

// =============================================================================
// APP PRINCIPAL
// =============================================================================

function App() {
  // Application globale du thème (Persistance)
  useEffect(() => {
    const savedTheme = localStorage.getItem('digitalcrown_theme');
    if (savedTheme) {
      document.body.dataset.theme = savedTheme;
    }
  }, []);

  return (
    <BrowserRouter>
      <Toaster
        position="bottom-right"
        toastOptions={{
          style: { borderRadius: '16px', fontWeight: 700, fontSize: '13px' },
          success: { duration: 3000 },
          error: { duration: 5000 },
        }}
      />
      <MarketingDemo />
      <Routes>
        {/* Route d'entrée absolue (sans protection) */}
        <Route path="/welcome" element={<WelcomeScreen />} />
        
        {/* Toutes les autres routes passent par le filtre Mode/Init */}
        <Route path="/*" element={
          <ProtectedRoute>
            <Routes>
              <Route path="/login" element={<LoginPage />} />
              <Route path="/setup" element={<SetupWizard />} />
              <Route path="/*" element={<ProtectedRoutes />} />
            </Routes>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
