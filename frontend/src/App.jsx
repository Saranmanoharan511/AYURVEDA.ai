import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './contexts/AuthContext'
import ProtectedRoute from './components/ProtectedRoute'
import PublicHome from './pages/public/PublicHome'
import PatientDashboard from './pages/patient/Dashboard'
import PatientRegister from './pages/patient/Register'
import PatientLogin from './pages/patient/Login'
import BookConsultation from './pages/patient/BookConsultation'
import UploadDocument from './pages/patient/UploadDocument'
import DoctorDashboard from './pages/doctor/Dashboard'
import DoctorLogin from './pages/doctor/Login'
import ClientSearch from './pages/doctor/ClientSearch'
import UploadReport from './pages/doctor/UploadReport'
import AddPrescription from './pages/doctor/AddPrescription'
import AIChat from './pages/doctor/AIChat'
import AdminDashboard from './pages/admin/Dashboard'
import AdminLogin from './pages/admin/Login'

function App() {
  return (
    <AuthProvider>
      <Router>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<PublicHome />} />
          
          {/* Patient routes */}
          <Route path="/patient/register" element={<PatientRegister />} />
          <Route path="/patient/login" element={<PatientLogin />} />
          <Route 
            path="/patient/dashboard" 
            element={
              <ProtectedRoute allowedRoles={['patient']}>
                <PatientDashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/patient/book-consultation" 
            element={
              <ProtectedRoute allowedRoles={['patient']}>
                <BookConsultation />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/patient/upload-document" 
            element={
              <ProtectedRoute allowedRoles={['patient']}>
                <UploadDocument />
              </ProtectedRoute>
            } 
          />
          
          {/* Doctor routes */}
          <Route path="/doctor/login" element={<DoctorLogin />} />
          <Route 
            path="/doctor/dashboard" 
            element={
              <ProtectedRoute allowedRoles={['doctor']}>
                <DoctorDashboard />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/doctor/client-search" 
            element={
              <ProtectedRoute allowedRoles={['doctor']}>
                <ClientSearch />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/doctor/upload-report/:consultationId/:patientId" 
            element={
              <ProtectedRoute allowedRoles={['doctor']}>
                <UploadReport />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/doctor/upload-report" 
            element={
              <ProtectedRoute allowedRoles={['doctor']}>
                <UploadReport />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/doctor/add-prescription/:consultationId" 
            element={
              <ProtectedRoute allowedRoles={['doctor']}>
                <AddPrescription />
              </ProtectedRoute>
            } 
          />
          <Route 
            path="/doctor/ai-chat" 
            element={
              <ProtectedRoute allowedRoles={['doctor']}>
                <AIChat />
              </ProtectedRoute>
            } 
          />
          
          {/* Admin routes */}
          <Route path="/admin/login" element={<AdminLogin />} />
          <Route 
            path="/admin/dashboard" 
            element={
              <ProtectedRoute allowedRoles={['admin']}>
                <AdminDashboard />
              </ProtectedRoute>
            } 
          />
        </Routes>
      </Router>
    </AuthProvider>
  )
}

export default App
