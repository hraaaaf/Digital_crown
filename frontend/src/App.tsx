import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import { lazy, Suspense, useEffect, useState } from 'react';
import { MainLayout } from './components/Layout/MainLayout';
import { cabinetApi } from './services/templateApi';
import { safeStorage } from './hooks/useLocalStorage';

// Chargés immédiatement (première interaction utilisateur)
import { Dashboard } from './pages/Dashboard';
import { LoginPage } from './pages/LoginPage';
import { WelcomeScreen } from './pages/WelcomeScreen';
import { authService } from './services/auth';

// Chargés à la demande
const PatientList     = lazy(() => import('./features/patients/PatientList').then(m => ({ default: m.PatientList })));
const PatientDetails  = lazy(() => import('./features/patients/PatientDetails').then(m => ({ default: m.PatientDetails })));
const AddPatientForm  = lazy(() => import('./features/patients/AddPatientForm').then(m => ({ default: m.AddPatientForm })));
const EditPatientForm = lazy(() => import('./features/patients/EditPatientForm').then(m => ({ default: m.EditPatientForm })));
const PatientDocuments = lazy(() => import('./features/patients/PatientDocuments').then(m => ({ default: m.PatientDocuments })));
const AgendaPage      = lazy(() => import('./pages/AgendaPage').then(m => ({ default: m.AgendaPage })));
const AccountingPage  = lazy(() => import('./pages/AccountingPage').then(m => ({ default: m.AccountingPage })));
const Settings        = lazy(() => import('./pages/Settings').then(m => ({ default: m.Settings })));
const SetupWizard     = lazy(() => import('./features/admin/SetupWizard').then(m => ({ default: m.SetupWizard })));
const EliteLibrary    = lazy(() => import('./features/clinical-ref/EliteLibrary').then(m => ({ default: m.EliteLibrary })));
const EliteScienceHub = lazy(() => import('./features/clinical-ref/EliteScienceHub').then(m => ({ default: m.EliteScienceHub })));

// MOBILE PWA
const OnboardingScanner = lazy(() => import('./features/mobile/Onboarding/OnboardingScanner').then(m => ({ default: m.OnboardingScanner })));
const MobileDashboard  = lazy(() => import('./features/mobile/Dashboard/MobileDashboard').then(m => ({ default: m.MobileDashboard })));

import { MobileStorage } from './services/zka/MobileStorage';

const PageLoader = () => (
  <div className="flex items-center justify-center h-full min-h-[60vh]">
    <div className="animate-spin rounded-full h-10 w-10 border-b-2" style={{ borderColor: 'var(--primary)' }} />
  </div>
);

// ==============================================================================
// COMPOSANT DE PROTECTION DES ROUTES
// ==============================================================================

interface ProtectedRouteProps {
  children: React.ReactNode;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children }) => {
  const [isLoading, setIsLoading] = useState(true);
  const [isInitialized, setIsInitialized] = useState<boolean | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const location = useLocation();

  useEffect(() => {
    const checkAuthAndInit = async () => {
      try {
        const authStatus = await authService.isAuthenticated();
        setIsAuthenticated(authStatus);
        
        if (authStatus) {
          const status = await cabinetApi.checkInitStatus();
          setIsInitialized(status.is_initialized);
          
          if (status.is_initialized && !safeStorage.get('appMode')) {
            safeStorage.set('appMode', 'prod');
          }
        }
      } catch (error) {
        console.error('Erreur vérification statut:', error);
        setIsInitialized(false);
      } finally {
        setIsLoading(false);
      }
    };

    checkAuthAndInit();
  }, [location.pathname]);

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

  // BYPASS AUTH : Si on est sur /login et pas connecté, on laisse passer pour afficher la page
  if (!isAuthenticated) {
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

  // Force le choix du mode s'il n'existe pas (Mode PROD par défaut désormais)
  const appMode = safeStorage.get('appMode');
  if (!appMode && location.pathname !== '/welcome') {
    return <Navigate to="/welcome" replace />;
  }

  // Si mode réel, on impose /setup si non init.
  if (!isInitialized && location.pathname !== '/setup') {
    return <Navigate to="/setup" replace />;
  }
  if (isInitialized && location.pathname === '/setup') {
    return <Navigate to="/dashboard" replace />;
  }


  return <>{children}</>;
};

// ==============================================================================
// PROTECTION PWA MOBILE (ZKA)
// ==============================================================================

const MobileProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const [isPaired, setIsPaired] = useState<boolean | null>(null);

  useEffect(() => {
    MobileStorage.isPaired().then(setIsPaired);
  }, []);

  if (isPaired === null) return <PageLoader />;
  if (!isPaired) return <Navigate to="/mobile/onboarding" replace />;

  return <>{children}</>;
};



// =============================================================================
// ROUTES PROTÉGÉES (avec layout)
// =============================================================================

const ProtectedRoutes = () => (
  <MainLayout>
    <Suspense fallback={<PageLoader />}>
      <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<Dashboard />} />
        <Route path="/agenda" element={<AgendaPage />} />
        <Route path="/accounting" element={<AccountingPage />} />
        <Route path="/patients" element={<PatientList />} />
        <Route path="/patients/new" element={<AddPatientForm />} />
        <Route path="/patients/:id" element={<PatientDetails />} />
        <Route path="/patients/:id/archives" element={<PatientDocuments />} />
        <Route path="/patients/:id/edit" element={<EditPatientForm />} />
        <Route path="/settings" element={<Settings />} />
        <Route path="/bibliotheque" element={<EliteLibrary />} />
        <Route path="/bibliotheque/:code" element={<EliteLibrary />} />
        <Route path="/science-hub" element={<EliteScienceHub />} />
        <Route path="*" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </Suspense>
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
      <Routes>
        {/* Route d'entrée absolue (sans protection) */}
        <Route path="/welcome" element={<WelcomeScreen />} />
        
        {/* ROUTES PWA MOBILE (Accès Direct) */}
        <Route path="/mobile/onboarding" element={
          <Suspense fallback={<PageLoader />}><OnboardingScanner /></Suspense>
        } />
        <Route path="/mobile/dashboard" element={
          <MobileProtectedRoute>
            <Suspense fallback={<PageLoader />}><MobileDashboard /></Suspense>
          </MobileProtectedRoute>
        } />

        {/* Toutes les autres routes passent par le filtre Mode/Init */}
        <Route path="/*" element={
          <ProtectedRoute>
            <Suspense fallback={<PageLoader />}>
              <Routes>
                <Route path="/login" element={<LoginPage />} />
                <Route path="/setup" element={<SetupWizard />} />
                <Route path="/*" element={<ProtectedRoutes />} />
              </Routes>
            </Suspense>
          </ProtectedRoute>
        } />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
