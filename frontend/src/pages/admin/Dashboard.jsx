import { useState, useEffect } from 'react';
import apiClient from '../../services/api';

function AdminDashboard() {
  const [activeTab, setActiveTab] = useState('analytics');
  const [analytics, setAnalytics] = useState(null);
  const [users, setUsers] = useState([]);
  const [doctors, setDoctors] = useState([]);
  const [systemSettings, setSystemSettings] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  const [failedDocuments, setFailedDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboardData();
  }, [activeTab]);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);
    try {
      switch (activeTab) {
        case 'analytics':
          await loadAnalytics();
          break;
        case 'users':
          await loadUsers();
          break;
        case 'doctors':
          await loadDoctors();
          break;
        case 'settings':
          await loadSettings();
          break;
        case 'audit':
          await loadAuditLogs();
          break;
        case 'dlq':
          await loadFailedDocuments();
          break;
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const loadAnalytics = async () => {
    const response = await apiClient.get('/api/v1/admin/analytics');
    setAnalytics(response.data);
  };

  const loadUsers = async () => {
    const response = await apiClient.get('/api/v1/admin/users');
    setUsers(response.data.users);
  };

  const loadDoctors = async () => {
    const response = await apiClient.get('/api/v1/admin/doctors');
    setDoctors(response.data.doctors);
  };

  const loadSettings = async () => {
    const response = await apiClient.get('/api/v1/admin/settings');
    setSystemSettings(response.data);
  };

  const loadAuditLogs = async () => {
    const response = await apiClient.get('/api/v1/admin/audit-logs');
    setAuditLogs(response.data.logs);
  };

  const loadFailedDocuments = async () => {
    const response = await apiClient.get('/api/v1/admin/dlq/documents');
    setFailedDocuments(response.data.failed_documents);
  };

  const updateUserStatus = async (userId, newStatus) => {
    try {
      await apiClient.put(`/api/v1/admin/users/${userId}/status`, { status: newStatus });
      await loadUsers();
    } catch (err) {
      alert('Failed to update user status');
    }
  };

  const updateDoctorStatus = async (doctorId, newStatus) => {
    try {
      await apiClient.put(`/api/v1/admin/doctors/${doctorId}/status`, { status: newStatus });
      await loadDoctors();
    } catch (err) {
      alert('Failed to update doctor status');
    }
  };

  const retryDocument = async (documentId) => {
    try {
      await apiClient.post(`/api/v1/admin/dlq/documents/${documentId}/retry`);
      await loadFailedDocuments();
      alert('Document retry initiated');
    } catch (err) {
      alert('Failed to retry document');
    }
  };

  const updateSettings = async (newSettings) => {
    try {
      await apiClient.put('/api/v1/admin/settings', newSettings);
      await loadSettings();
      alert('Settings updated successfully');
    } catch (err) {
      alert('Failed to update settings');
    }
  };

  const tabs = [
    { id: 'analytics', label: 'Analytics', icon: '📊' },
    { id: 'users', label: 'Users', icon: '👥' },
    { id: 'doctors', label: 'Doctors', icon: '👨‍⚕️' },
    { id: 'settings', label: 'Settings', icon: '⚙️' },
    { id: 'audit', label: 'Audit Logs', icon: '📝' },
    { id: 'dlq', label: 'Failed Documents', icon: '📁' },
  ];

  if (loading && !analytics) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-slate-100 flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-slate-100">
      <div className="container mx-auto px-4 py-8">
        <div className="bg-white rounded-lg shadow-lg">
          {/* Header */}
          <div className="border-b border-gray-200 px-8 py-6">
            <h1 className="text-3xl font-bold text-gray-800">Admin Dashboard</h1>
            <p className="text-gray-600 mt-2">Platform administration and management</p>
          </div>

          {/* Tabs */}
          <div className="border-b border-gray-200 px-8">
            <nav className="flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`py-4 px-1 border-b-2 font-medium text-sm ${
                    activeTab === tab.id
                      ? 'border-purple-500 text-purple-600'
                      : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                  }`}
                >
                  <span className="mr-2">{tab.icon}</span>
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          {/* Content */}
          <div className="px-8 py-6">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
                {error}
              </div>
            )}

            {activeTab === 'analytics' && analytics && (
              <AnalyticsView analytics={analytics} />
            )}

            {activeTab === 'users' && (
              <UsersView users={users} onUpdateStatus={updateUserStatus} loading={loading} />
            )}

            {activeTab === 'doctors' && (
              <DoctorsView doctors={doctors} onUpdateStatus={updateDoctorStatus} loading={loading} />
            )}

            {activeTab === 'settings' && (
              <SettingsView settings={systemSettings} onUpdate={updateSettings} loading={loading} />
            )}

            {activeTab === 'audit' && (
              <AuditLogsView logs={auditLogs} loading={loading} />
            )}

            {activeTab === 'dlq' && (
              <DLQView documents={failedDocuments} onRetry={retryDocument} loading={loading} />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

// Analytics View Component
function AnalyticsView({ analytics }) {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard title="Total Patients" value={analytics.total_patients} color="blue" />
        <StatCard title="Total Doctors" value={analytics.total_doctors} color="green" />
        <StatCard title="Total Consultations" value={analytics.total_consultations} color="purple" />
        <StatCard title="Active Consultations" value={analytics.active_consultations} color="orange" />
        <StatCard title="Completed Consultations" value={analytics.completed_consultations} color="teal" />
        <StatCard title="Total Documents" value={analytics.total_documents} color="indigo" />
        <StatCard title="Total Reports" value={analytics.total_reports} color="pink" />
        <StatCard title="New Patients (This Month)" value={analytics.patients_this_month} color="cyan" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="font-semibold text-gray-800 mb-4">Most Common Conditions</h3>
          <div className="space-y-3">
            {analytics.most_common_conditions.map((item, index) => (
              <div key={index} className="flex justify-between items-center">
                <span className="text-gray-700">{item.condition}</span>
                <span className="bg-purple-100 text-purple-800 px-3 py-1 rounded-full text-sm">
                  {item.count}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="bg-gray-50 rounded-lg p-6">
          <h3 className="font-semibold text-gray-800 mb-4">Patient Distribution by City</h3>
          <div className="space-y-3">
            {analytics.patient_distribution_by_city.map((item, index) => (
              <div key={index} className="flex justify-between items-center">
                <span className="text-gray-700">{item.city}</span>
                <span className="bg-blue-100 text-blue-800 px-3 py-1 rounded-full text-sm">
                  {item.count}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="bg-gray-50 rounded-lg p-6">
        <h3 className="font-semibold text-gray-800 mb-4">Document Processing Status</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {Object.entries(analytics.document_processing_status).map(([status, count]) => (
            <div key={status} className="bg-white p-4 rounded-lg shadow-sm">
              <div className="text-sm text-gray-600">{status}</div>
              <div className="text-2xl font-bold text-gray-800">{count}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

// Stat Card Component
function StatCard({ title, value, color }) {
  const colorClasses = {
    blue: 'bg-blue-500',
    green: 'bg-green-500',
    purple: 'bg-purple-500',
    orange: 'bg-orange-500',
    teal: 'bg-teal-500',
    indigo: 'bg-indigo-500',
    pink: 'bg-pink-500',
    cyan: 'bg-cyan-500',
  };

  return (
    <div className="bg-white rounded-lg shadow-sm p-6 border-l-4 border-gray-200">
      <div className="text-sm text-gray-600 mb-2">{title}</div>
      <div className="text-3xl font-bold text-gray-800">{value}</div>
    </div>
  );
}

// Users View Component
function UsersView({ users, onUpdateStatus, loading }) {
  if (loading) return <div className="text-gray-600">Loading users...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-800">User Management</h3>
        <span className="text-sm text-gray-600">{users.length} users</span>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Role</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {users.map((user) => (
              <tr key={user.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{user.email}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {user.given_name} {user.family_name}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{user.role}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    user.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {user.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <select
                    value={user.status}
                    onChange={(e) => onUpdateStatus(user.id, e.target.value)}
                    className="border border-gray-300 rounded px-2 py-1 text-sm"
                  >
                    <option value="ACTIVE">Active</option>
                    <option value="BLOCKED">Blocked</option>
                    <option value="SUSPENDED">Suspended</option>
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Doctors View Component
function DoctorsView({ doctors, onUpdateStatus, loading }) {
  if (loading) return <div className="text-gray-600">Loading doctors...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-800">Doctor Management</h3>
        <span className="text-sm text-gray-600">{doctors.length} doctors</span>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Name</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Email</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Specialization</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {doctors.map((doctor) => (
              <tr key={doctor.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{doctor.name}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{doctor.email}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{doctor.specialization || 'N/A'}</td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    doctor.status === 'ACTIVE' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {doctor.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <select
                    value={doctor.status}
                    onChange={(e) => onUpdateStatus(doctor.id, e.target.value)}
                    className="border border-gray-300 rounded px-2 py-1 text-sm"
                  >
                    <option value="ACTIVE">Active</option>
                    <option value="INACTIVE">Inactive</option>
                  </select>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// Settings View Component
function SettingsView({ settings, onUpdate, loading }) {
  const [localSettings, setLocalSettings] = useState(settings || {
    booking_enabled: true,
    booking_message: '',
    holiday_dates: [],
    maintenance_mode: false,
    maintenance_message: '',
  });

  if (loading) return <div className="text-gray-600">Loading settings...</div>;

  const handleSave = () => {
    onUpdate(localSettings);
  };

  return (
    <div className="space-y-6">
      <h3 className="text-lg font-semibold text-gray-800">System Settings</h3>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <label className="block text-sm font-medium text-gray-700">Booking Enabled</label>
            <p className="text-sm text-gray-500">Allow patients to book new consultations</p>
          </div>
          <input
            type="checkbox"
            checked={localSettings.booking_enabled}
            onChange={(e) => setLocalSettings({ ...localSettings, booking_enabled: e.target.checked })}
            className="h-5 w-5 text-purple-600 rounded"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Booking Disabled Message</label>
          <input
            type="text"
            value={localSettings.booking_message || ''}
            onChange={(e) => setLocalSettings({ ...localSettings, booking_message: e.target.value })}
            className="w-full border border-gray-300 rounded px-3 py-2"
            placeholder="Message to show when booking is disabled"
          />
        </div>

        <div className="flex items-center justify-between">
          <div>
            <label className="block text-sm font-medium text-gray-700">Maintenance Mode</label>
            <p className="text-sm text-gray-500">Put the system in maintenance mode</p>
          </div>
          <input
            type="checkbox"
            checked={localSettings.maintenance_mode}
            onChange={(e) => setLocalSettings({ ...localSettings, maintenance_mode: e.target.checked })}
            className="h-5 w-5 text-purple-600 rounded"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Maintenance Message</label>
          <input
            type="text"
            value={localSettings.maintenance_message || ''}
            onChange={(e) => setLocalSettings({ ...localSettings, maintenance_message: e.target.value })}
            className="w-full border border-gray-300 rounded px-3 py-2"
            placeholder="Message to show during maintenance"
          />
        </div>

        <button
          onClick={handleSave}
          className="bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700"
        >
          Save Settings
        </button>
      </div>
    </div>
  );
}

// Audit Logs View Component
function AuditLogsView({ logs, loading }) {
  if (loading) return <div className="text-gray-600">Loading audit logs...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-800">Audit Logs</h3>
        <span className="text-sm text-gray-600">{logs.length} entries</span>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actor</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Resource</th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {logs.slice(0, 50).map((log) => (
              <tr key={log.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {new Date(log.timestamp).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{log.actor_role}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{log.action}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {log.resource_type} - {log.resource_identifier || 'N/A'}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className={`px-2 py-1 text-xs rounded-full ${
                    log.success ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
                  }`}>
                    {log.success ? 'Success' : 'Failed'}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// DLQ View Component
function DLQView({ documents, onRetry, loading }) {
  if (loading) return <div className="text-gray-600">Loading failed documents...</div>;

  return (
    <div className="space-y-6">
      <div className="flex justify-between items-center">
        <h3 className="text-lg font-semibold text-gray-800">Failed Report Processing</h3>
        <span className="text-sm text-gray-600">{documents.length} failed reports</span>
      </div>

      {documents.length === 0 ? (
        <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded">
          No failed reports to process
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Patient</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Report</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Error</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Retries</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {documents.map((doc) => (
                <tr key={doc.document_id}>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{doc.patient_name}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{doc.filename}</td>
                  <td className="px-6 py-4 text-sm text-gray-900 max-w-xs truncate">{doc.error_message}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">{doc.retry_count}</td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm">
                    {doc.can_retry ? (
                      <button
                        onClick={() => onRetry(doc.document_id)}
                        className="bg-blue-600 text-white px-3 py-1 rounded hover:bg-blue-700 text-sm"
                      >
                        Retry
                      </button>
                    ) : (
                      <span className="text-gray-500 text-sm">Max retries reached</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default AdminDashboard;
