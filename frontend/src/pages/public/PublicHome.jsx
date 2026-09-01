function PublicHome() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center">
          <h1 className="text-5xl font-bold text-emerald-800 mb-6">
            Ayurveda AI Platform
          </h1>
          <p className="text-xl text-emerald-700 mb-12">
            AI-Assisted Ayurveda Consultation Platform
          </p>
          
          <div className="grid md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="bg-white p-8 rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold text-emerald-800 mb-4">
                Patient Portal
              </h2>
              <p className="text-gray-600 mb-6">
                Book consultations, view reports, and manage your health journey
              </p>
              <button 
              onClick={() => window.location.href = '/patient/login'}
              className="bg-emerald-600 text-white px-6 py-3 rounded-lg hover:bg-emerald-700 transition">
                Patient Login
              </button>
            </div>
            
            <div className="bg-white p-8 rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold text-emerald-800 mb-4">
                Doctor Portal
              </h2>
              <p className="text-gray-600 mb-6">
                Manage patients, consultations, and leverage AI assistance
              </p>
              <button 
              onClick={() => window.location.href = '/doctor/login'}
              className="bg-emerald-600 text-white px-6 py-3 rounded-lg hover:bg-emerald-700 transition">
                Doctor Login
              </button>
            </div>
            
            <div className="bg-white p-8 rounded-lg shadow-lg">
              <h2 className="text-2xl font-semibold text-emerald-800 mb-4">
                Admin Portal
              </h2>
              <p className="text-gray-600 mb-6">
                System administration, user management, and analytics
              </p>
              <button 
              onClick={() => window.location.href = '/admin/login'}
              className="bg-emerald-600 text-white px-6 py-3 rounded-lg hover:bg-emerald-700 transition">
                Admin Login
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default PublicHome
