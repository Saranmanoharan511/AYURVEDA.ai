import { useState } from 'react';
import apiClient from '../../services/api';

export default function UploadDocument() {
  const [file, setFile] = useState(null);
  const [documentType, setDocumentType] = useState('medical_report');
  const [consultationId, setConsultationId] = useState('');
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

    setUploading(true);
    setError('');
    setSuccess(false);

    try {
      // Step 1: Get pre-signed upload URL
      const uploadUrlResponse = await apiClient.post('/api/v1/documents/upload-url', {
        filename: file.name,
        content_type: file.type,
        consultation_id: consultationId || null,
        document_type: documentType
      });

      const { upload_url, object_key } = uploadUrlResponse.data;

      // Step 2: Upload file directly to S3
      await fetch(upload_url, {
        method: 'PUT',
        body: file,
        headers: {
          'Content-Type': file.type
        }
      });

      // Step 3: Save document metadata
      await apiClient.post('/api/v1/documents/metadata', {
        object_key: object_key,
        original_filename: file.name,
        content_type: file.type,
        file_size: file.size,
        consultation_id: consultationId || null,
        document_type: documentType
      });

      setSuccess(true);
      setFile(null);
      setConsultationId('');
      setDocumentType('medical_report');
    } catch (err) {
      console.error('Upload error:', err);
      setError(err.response?.data?.detail || 'Failed to upload document');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <h1 className="text-3xl font-bold text-teal-700 mb-6">Upload Document</h1>

      <div className="bg-white rounded-lg shadow-md p-6">
        {success && (
          <div className="mb-4 p-4 bg-green-100 border border-green-400 text-green-700 rounded">
            Document uploaded successfully!
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
              Document Type
            </label>
            <select
              value={documentType}
              onChange={(e) => setDocumentType(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500"
            >
              <option value="medical_report">Medical Report</option>
              <option value="prescription">Prescription</option>
              <option value="lab_results">Lab Results</option>
              <option value="scan_report">Scan Report</option>
              <option value="other">Other</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Consultation ID (Optional)
            </label>
            <input
              type="text"
              value={consultationId}
              onChange={(e) => setConsultationId(e.target.value)}
              placeholder="Enter consultation ID if applicable"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Select File
            </label>
            <input
              type="file"
              onChange={handleFileChange}
              accept=".pdf,.jpg,.jpeg,.png,.doc,.docx"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-teal-500"
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
            className="w-full bg-teal-600 text-white py-2 px-4 rounded-md hover:bg-teal-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
          >
            {uploading ? 'Uploading...' : 'Upload Document'}
          </button>
        </div>

        <div className="mt-6 p-4 bg-blue-50 rounded-md">
          <h3 className="font-semibold text-blue-900 mb-2">Upload Information</h3>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Documents are securely stored in encrypted cloud storage</li>
            <li>• Files are uploaded directly to secure storage</li>
            <li>• Your doctor will be able to access uploaded documents</li>
            <li>• Supported file types: PDF, images (JPG, PNG), documents (DOC, DOCX)</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
