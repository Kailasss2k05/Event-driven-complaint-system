import { BrowserRouter as Router, Routes, Route, Navigate, Link } from 'react-router-dom';
import { useEffect, Suspense, lazy } from 'react';
import { useAuthStore } from './hooks/useAuthStore';
import { Loader } from './components/Loader';
import { Toaster } from 'sonner';

// Layout
import { MainLayout } from './layout/MainLayout';

// Auth
import { Login } from './auth/Login';

// Guards
import { ProtectedRoute, RoleRoute } from './components/ProtectedRoute';

// Lazy load pages
const SubmitComplaint = lazy(() => import('./citizen/SubmitComplaint').then(m => ({ default: m.SubmitComplaint })));
const MyComplaints = lazy(() => import('./citizen/MyComplaints').then(m => ({ default: m.MyComplaints })));
const ComplaintDetail = lazy(() => import('./citizen/ComplaintDetail').then(m => ({ default: m.ComplaintDetail })));
const StaffDashboard = lazy(() => import('./staff/StaffDashboard').then(m => ({ default: m.StaffDashboard })));
const AdminDashboard = lazy(() => import('./admin/AdminDashboard').then(m => ({ default: m.AdminDashboard })));
const Notifications = lazy(() => import('./notifications/Notifications').then(m => ({ default: m.Notifications })));

const SuspenseWrapper = ({ children }) => (
  <Suspense fallback={<Loader size="lg" className="h-64 pt-32" />}>
    {children}
  </Suspense>
);

const Unauthorized = () => (
  <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
    <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center">
      <span className="text-4xl font-bold text-red-600">403</span>
    </div>
    <h1 className="text-2xl font-bold text-gray-900">Access Denied</h1>
    <p className="text-gray-500 max-w-sm text-center">You don't have permission to access this page. Please contact an administrator.</p>
    <Link to="/login" className="mt-4 px-5 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition">Back to Login</Link>
  </div>
);

const NotFound = () => (
  <div className="min-h-[60vh] flex flex-col items-center justify-center space-y-4">
    <div className="w-20 h-20 bg-gray-100 rounded-full flex items-center justify-center">
      <span className="text-4xl font-bold text-gray-500">404</span>
    </div>
    <h1 className="text-2xl font-bold text-gray-900">Page Not Found</h1>
    <p className="text-gray-500 max-w-sm text-center">The page you're looking for doesn't exist or has been moved.</p>
    <Link to="/" className="mt-4 px-5 py-2 bg-primary-600 text-white rounded-lg font-medium hover:bg-primary-700 transition">Go Home</Link>
  </div>
);

function App() {
  const { fetchUser, isAuthenticated } = useAuthStore();

  useEffect(() => {
    fetchUser();
  }, []);

  return (
    <>
      <Toaster position="top-right" richColors closeButton />
      <Router>
        <Routes>
          <Route path="/login" element={<Login />} />

          <Route path="/" element={<Navigate to="/login" replace />} />

        {/* Unauthorized */}
        <Route path="/unauthorized" element={<MainLayout />}>
          <Route index element={<Unauthorized />} />
        </Route>

        {/* Protected Routes inside Layout */}
        <Route element={<ProtectedRoute><MainLayout /></ProtectedRoute>}>

          {/* Shared Routes */}
          <Route path="/complaints/:id" element={<SuspenseWrapper><ComplaintDetail /></SuspenseWrapper>} />
          <Route path="/notifications" element={<SuspenseWrapper><Notifications /></SuspenseWrapper>} />

          {/* Citizen Routes */}
          <Route
            path="/submit"
            element={
              <RoleRoute allowedRoles={['user', 'department_admin', 'super_admin']}>
                <SuspenseWrapper><SubmitComplaint /></SuspenseWrapper>
              </RoleRoute>
            }
          />
          <Route
            path="/my-complaints"
            element={
              <RoleRoute allowedRoles={['user']}>
                <SuspenseWrapper><MyComplaints /></SuspenseWrapper>
              </RoleRoute>
            }
          />

          {/* Staff Routes */}
          <Route
            path="/staff"
            element={
              <RoleRoute allowedRoles={['department_admin']}>
                <SuspenseWrapper><StaffDashboard /></SuspenseWrapper>
              </RoleRoute>
            }
          />

          {/* Admin Routes */}
          <Route
            path="/admin"
            element={
              <RoleRoute allowedRoles={['super_admin']}>
                <SuspenseWrapper><AdminDashboard /></SuspenseWrapper>
              </RoleRoute>
            }
          />

          {/* 404 */}
          <Route path="*" element={<NotFound />} />
        </Route>
      </Routes>
    </Router>
    </>
  );
}

export default App;
