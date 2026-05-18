
import { Routes, Route, Navigate } from 'react-router-dom';
import { Suspense, lazy } from 'react';
import { Spin } from 'antd';
import { useAuthStore } from './stores/authStore';
import AppLayout from './components/Layout/AppLayout';

// Lazy load pages
const Login = lazy(() => import('./pages/auth/Login'));
const Register = lazy(() => import('./pages/auth/Register'));
const ForgotPassword = lazy(() => import('./pages/auth/ForgotPassword'));
const ResetPassword = lazy(() => import('./pages/auth/ResetPassword'));

// User pages
const UserDashboard = lazy(() => import('./pages/user/Dashboard'));
const AssetList = lazy(() => import('./pages/user/assets/AssetList'));
const AssetForm = lazy(() => import('./pages/user/assets/AssetForm'));
const GuardrailList = lazy(() => import('./pages/user/guardrails/GuardrailList'));
const GuardrailForm = lazy(() => import('./pages/user/guardrails/GuardrailForm'));
const TrafficConfigList = lazy(() => import('./pages/user/traffic/TrafficConfigList'));
const TrafficConfigForm = lazy(() => import('./pages/user/traffic/TrafficConfigForm'));
const Billing = lazy(() => import('./pages/user/Billing'));
const Alerts = lazy(() => import('./pages/user/Alerts'));
const Logs = lazy(() => import('./pages/user/Logs'));
const ApiKeys = lazy(() => import('./pages/user/ApiKeys'));

// Admin pages
const AdminDashboard = lazy(() => import('./pages/admin/Dashboard'));
const Users = lazy(() => import('./pages/admin/Users'));
const Settings = lazy(() => import('./pages/admin/Settings'));

const Loading = () => (
  <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
    <Spin size="large" />
  </div>
);

function PrivateRoute({ children, roles }: { children: React.ReactNode; roles?: string[] }) {
  const user = useAuthStore((s) => s.user);
  if (!user) return <Navigate to="/login" />;
  if (roles && !roles.includes(user.role)) {
    return <Navigate to={user.role === 'user' ? '/user/dashboard' : '/admin/dashboard'} />;
  }
  return <>{children}</>;
}

export default function App() {
  return (
    <Suspense fallback={<Loading />}>
      <Routes>
        {/* Auth */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/activate" element={<Navigate to="/login" />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />

        {/* User routes */}
        <Route path="/user" element={<PrivateRoute><AppLayout /></PrivateRoute>}>
          <Route path="dashboard" element={<UserDashboard />} />
          <Route path="assets" element={<AssetList />} />
          <Route path="assets/create" element={<AssetForm />} />
          <Route path="assets/:id/edit" element={<AssetForm />} />
          <Route path="guardrails" element={<GuardrailList />} />
          <Route path="guardrails/create" element={<GuardrailForm />} />
          <Route path="guardrails/:id/edit" element={<GuardrailForm />} />
          <Route path="traffic-configs" element={<TrafficConfigList />} />
          <Route path="traffic-configs/create" element={<TrafficConfigForm />} />
          <Route path="traffic-configs/:id/edit" element={<TrafficConfigForm />} />
          <Route path="billing" element={<Billing />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="logs" element={<Logs />} />
          <Route path="logs/:id" element={<Logs />} />
          <Route path="api-keys" element={<ApiKeys />} />
        </Route>

        {/* Admin routes */}
        <Route path="/admin" element={<PrivateRoute roles={['admin', 'super_admin']}><AppLayout /></PrivateRoute>}>
          <Route path="dashboard" element={<AdminDashboard />} />
          <Route path="users" element={<Users />} />
          <Route path="users/:id" element={<Users />} />
          <Route path="assets" element={<AssetList />} />
          <Route path="assets/create" element={<AssetForm />} />
          <Route path="assets/:id/edit" element={<AssetForm />} />
          <Route path="guardrails" element={<GuardrailList />} />
          <Route path="guardrails/create" element={<GuardrailForm />} />
          <Route path="guardrails/:id/edit" element={<GuardrailForm />} />
          <Route path="traffic-configs" element={<TrafficConfigList />} />
          <Route path="traffic-configs/create" element={<TrafficConfigForm />} />
          <Route path="traffic-configs/:id/edit" element={<TrafficConfigForm />} />
          <Route path="billing" element={<Billing />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="logs" element={<Logs />} />
          <Route path="logs/:id" element={<Logs />} />
          <Route path="api-keys" element={<ApiKeys />} />
          <Route path="settings" element={<Settings />} />
        </Route>

        {/* Default redirect */}
        <Route path="/" element={<Navigate to="/login" />} />
        <Route path="*" element={<Navigate to="/login" />} />
      </Routes>
    </Suspense>
  );
}
