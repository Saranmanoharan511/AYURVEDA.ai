import { useState } from 'react';
import { useParams } from 'react-router-dom';
import apiClient from '../../services/api';

export default function UploadReport() {
  const { consultationId, patientId } = useParams();
  const [file, setFile] = useState(null);
  const [reportType, setReportType] = useState('prescription');
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile) {
      setFile(selectedFile);
      setError('');
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    if (!consultationId || !patientId) {
      setError('Consultation ID and Patient ID are required');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess(false);

    try {
      // Step 1: Create report metadata via API
      const reportResponse = await apiClient.post('/api/v1/documents/reports', {
        consultation_id: consultationId,
        patient_id: patientId,
        report_type: reportType,
        original_filename: file.name,
        content_type: file.type,
        file_size: file.size
      });

      const { report_id, upload_url } = reportResponse.data;

      // Step 2: Upload file directly to S3 using report-specific presigned URL
      await fetch(upload_url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type
        }
      });

      // Step 3: Confirm upload completion to trigger patient notification
      await apiClient.post(`/api/v1/documents/reports/${report_id}/confirm`);

      setSuccess(true);
      setFile(null);
      setReportType('prescription');
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.response?.data?.detail || 'Failed to upload report');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-blue-700 mb-6">Upload Report</h1>

      {consultationId && patientId && (
        <div className="mb-4 p-3 bg-blue-50 rounded-md">
          <p className="text-sm text-blue-800">
            <strong>Patient ID:</strong> {patientId}
          </p>
          <p className="text-sm text-blue-800">
            <strong>Consultation ID:</strong> {consultationId}
          </p>
        </div>
      )}

      <div className="bg-white rounded-lg shadow-md p-6">
        {success && (
          <div className="mb-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded">
            Report uploaded successfully! The patient will be notified.
          </div>
        )}

        {error && (
          <div className="mb-4 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Report Type
            </label>
            <select
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="prescription">Prescription</option>
              <option value="medical_report">Medical Report</option>
              <option value="lab_results">Lab Results</option>
              <option value="treatment_plan">Treatment Plan</option>
              <option value="follow_up_note">Follow-up Note</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select Report File
            </label>
            <input
              type="file"
              onChange={handleFileChange}
              accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            <p className="mt-1 text-sm text-gray-500">
              Accepted formats: PDF, JPG, PNG, DOC, DOCX
            </p>
          </div>

          {file && (
            <div className="p-3 bg-gray-50 rounded-md">
              <p className="text-sm text-gray-700">
                <strong>Selected file:</strong> {file.name}
              </p>
              <p className="text-sm text-gray-500">
                <strong>Size:</strong> {(file.size / 1024 / 1024).toFixed(2)} MB
              </p>
            </div>
          )}

          <button
            onClick={handleUpload}
            disabled={uploading || !file}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {uploading ? 'Uploading...' : 'Upload Report'}
          </button>
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded-md">
          <h3 className="font-semibold text-blue-900 mb-2">Report Upload Information</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Reports are securely stored in encrypted cloud storage</li>
            <li>• Patient will be automatically notified when report is uploaded</li>
            <li>• Patient can download the report from their portal</li>
            <li>• Supported file types: PDF, images (JPG, PNG), documents (DOC, DOCX)</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
