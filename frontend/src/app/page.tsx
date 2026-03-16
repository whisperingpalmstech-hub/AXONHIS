export default function Home() {
  return (
    <main className="min-h-screen flex items-center justify-center bg-gradient-to-br from-primary-50 to-accent-50">
      <div className="text-center space-y-6">
        <div className="flex items-center justify-center space-x-3">
          <div className="w-12 h-12 bg-primary-600 rounded-xl flex items-center justify-center">
            <span className="text-white text-2xl font-bold">A</span>
          </div>
          <h1 className="text-4xl font-bold text-surface-900">
            AXON<span className="text-primary-600">HIS</span>
          </h1>
        </div>
        <p className="text-lg text-surface-700 max-w-md mx-auto">
          AI-First Hospital Information System
        </p>
        <div className="flex gap-4 justify-center">
          <a href="/login" className="btn-primary">
            Sign In
          </a>
          <a href="/docs" className="btn-secondary" target="_blank">
            API Docs ↗
          </a>
        </div>
        <div className="grid grid-cols-3 gap-4 mt-12 max-w-lg mx-auto">
          {[
            { icon: "🏥", label: "OPD / IPD / ER" },
            { icon: "🧪", label: "Laboratory" },
            { icon: "💊", label: "Pharmacy" },
            { icon: "📋", label: "Order Engine" },
            { icon: "💰", label: "Billing" },
            { icon: "🤖", label: "AI Assistant" },
          ].map((item) => (
            <div
              key={item.label}
              className="card flex flex-col items-center py-4 hover:shadow-md transition-shadow"
            >
              <span className="text-2xl mb-2">{item.icon}</span>
              <span className="text-sm font-medium text-surface-700">
                {item.label}
              </span>
            </div>
          ))}
        </div>
      </div>
    </main>
  );
}
