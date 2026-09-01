import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';
import apiClient from '../../services/api';

function BookConsultation() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [formData, setFormData] = useState({
    reason: '',
    description: ''
  });

  const handleChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await apiClient.post('/api/v1/clinical/consultations', formData);
      alert('Consultation booked successfully!');
      navigate('/patient/dashboard');
    } catch (err) {
      setError('Failed to book consultation. Please try again.');
      console.error('Error booking consultation:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-teal-50 to-cyan-100">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white rounded-lg shadow-lg p-8">
            <h1 className="text-3xl font-bold text-teal-800 mb-6">Book a Consultation</h1>
            
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
                {error}
              </div>
            )}

            <form onSubmit={handleSubmit}>
              <div className="space-y-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Reason for Consultation *
                  </label>
                  <input
                    type="text"
                    name="reason"
                    value={formData.reason}
                    onChange={handleChange}
                    className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    placeholder="e.g., Skin allergy, Digestive issues, Joint pain"
                    required
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description
                  </label>
                  <textarea
                    name="description"
                    value={formData.description}
                    onChange={handleChange}
                    rows={6}
                    className="w-full px-4 py-3 border rounded-lg focus:outline-none focus:ring-2 focus:ring-teal-500"
                    placeholder="Please describe your symptoms, how long you've been experiencing them, and any previous treatments..."
                  />
                </div>

                <div className="bg-teal-50 p-4 rounded-lg">
                  <h3 className="font-semibold text-teal-800 mb-2">What happens next?</h3>
                  <ul className="text-sm text-gray-700 space-y-1">
                    <li>• Your consultation request will be submitted</li>
                    <li>• The doctor will review your request</li>
                    <li>• You'll receive a notification when the meeting is scheduled</li>
                    <li>• A Zoom meeting link will be provided</li>
                  </ul>
                </div>

                <div className="flex space-x-4">
                  <button
                    type="button"
                    onClick={() => navigate('/patient/dashboard')}
                    className="flex-1 px-4 py-3 border rounded-lg hover:bg-gray-50 transition font-medium"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={loading}
                    className="flex-1 px-4 py-3 bg-teal-600 text-white rounded-lg hover:bg-teal-700 transition font-medium disabled:opacity-50"
                  >
                    {loading ? 'Submitting...' : 'Book Consultation'}
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default BookConsultation;
