"use client";
import React, { useState, useEffect } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface AiSuggestion {
  id: string;
  target_role: string;
  suggestion_type: string;
  title: string;
  content: string;
  status: string;
  structured_data: any;
  created_at: string;
}

interface AiAlert {
  id: string;
  risk_category: string;
  severity: string;
  message: string;
  is_acknowledged: boolean;
  detected_at: string;
}

export default function AiAssistantPanel({ 
  patientUhid, 
  userRole = "doctor" 
}: { 
  patientUhid: string, 
  userRole?: string 
}) {
  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [suggestions, setSuggestions] = useState<AiSuggestion[]>([]);
  const [alerts, setAlerts] = useState<AiAlert[]>([]);
  const [message, setMessage] = useState<{type: 'success'|'error', text: string} | null>(null);

  const fetchAiState = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API}/api/v1/rpiw-ai/state/${patientUhid}/${userRole}`);
      if (res.ok) {
        const data = await res.json();
        setSuggestions(data.suggestions || []);
        setAlerts(data.alerts || []);
      }
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchAiState();
  }, [patientUhid, userRole]);

  const generateInsights = async () => {
    setGenerating(true);
    setMessage(null);
    try {
      const res = await fetch(`${API}/api/v1/rpiw-ai/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_uhid: patientUhid,
          user_id: `UID-${userRole.toUpperCase()}-001`,
          role_code: userRole
        })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Failed to generate insights");
      
      setSuggestions(data.suggestions || []);
      setAlerts(data.alerts || []);
      setMessage({ type: 'success', text: "AI insights generated successfully." });
    } catch (e: any) {
      setMessage({ type: 'error', text: e.message });
    }
    setGenerating(false);
  };

  const handleSuggestionAction = async (id: string, action: string) => {
    try {
      const res = await fetch(`${API}/api/v1/rpiw-ai/suggestions/${id}/action?action=${action}&user_id=UID-${userRole.toUpperCase()}-001&role_code=${userRole}`, {
        method: "POST"
      });
      if (res.ok) {
        // Refresh state
        fetchAiState();
      }
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border overflow-hidden">
      <div className="bg-gradient-to-r from-indigo-900 to-purple-800 p-6 flex justify-between items-center text-white">
        <div>
          <h3 className="text-xl font-bold flex items-center gap-2">
            <span>✨</span> AI Clinical Co-Pilot
          </h3>
          <p className="text-indigo-200 text-sm mt-1">Context-aware suggestions for {userRole}s</p>
        </div>
        <button 
          onClick={generateInsights} 
          disabled={generating}
          className="bg-white/20 hover:bg-white/30 px-4 py-2 rounded-xl text-sm font-bold backdrop-blur-sm transition-colors flex items-center gap-2"
        >
          {generating ? <div className="animate-spin w-4 h-4 border-2 border-white/20 border-t-white rounded-full"></div> : null}
          {generating ? 'Analyzing Context...' : 'Generate Insights'}
        </button>
      </div>

      <div className="p-6">
        {message && (
          <div className={`p-4 rounded-xl text-sm font-medium mb-6 ${message.type === 'success' ? 'bg-green-50 text-green-700 border border-green-200' : 'bg-red-50 text-red-700 border border-red-200'}`}>
             {message.type === 'success' ? '✅' : '⚠️'} {message.text}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Active Alerts Panel */}
          <div>
            <h4 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></span> Critical Risk Alerts
            </h4>
            
            {loading ? (
              <p className="text-sm text-gray-400">Loading alerts...</p>
            ) : alerts.length === 0 ? (
              <div className="bg-gray-50 border border-dashed rounded-xl p-6 text-center text-gray-400 text-sm">
                 No active alerts detected.
              </div>
            ) : (
              <div className="space-y-3">
                {alerts.map(a => (
                  <div key={a.id} className={`p-4 rounded-xl border-l-4 ${a.severity === 'High' ? 'bg-red-50 border-red-500' : 'bg-amber-50 border-amber-500'}`}>
                    <div className="flex justify-between items-start mb-1">
                      <span className={`text-xs font-bold uppercase ${a.severity === 'High' ? 'text-red-700' : 'text-amber-700'}`}>{a.risk_category}</span>
                      <span className="text-[10px] text-gray-400">{new Date(a.detected_at).toLocaleTimeString()}</span>
                    </div>
                    <p className={`text-sm ${a.severity === 'High' ? 'text-red-900 font-medium' : 'text-amber-900'}`}>{a.message}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* AI Suggestions Panel */}
          <div>
            <h4 className="font-bold text-gray-800 mb-4 flex items-center gap-2">
              <span>💡</span> AI Suggestions
            </h4>
            
            {loading ? (
              <p className="text-sm text-gray-400">Loading suggestions...</p>
            ) : suggestions.length === 0 ? (
              <div className="bg-gray-50 border border-dashed rounded-xl p-6 text-center text-gray-400 text-sm">
                 Click 'Generate Insights' to analyze this patient's data.
              </div>
            ) : (
              <div className="space-y-4">
                {suggestions.map(s => (
                  <div key={s.id} className="p-4 rounded-xl border bg-white shadow-sm hover:shadow-md transition-shadow">
                    <div className="flex items-center gap-2 mb-2">
                      <span className="px-2 py-0.5 bg-indigo-100 text-indigo-700 rounded text-[10px] font-bold uppercase">{s.suggestion_type}</span>
                      <h5 className="font-bold text-gray-800 text-sm">{s.title}</h5>
                    </div>
                    <p className="text-sm text-gray-600 mb-4 bg-gray-50 p-3 rounded-lg border">{s.content}</p>
                    
                    {/* Actions */}
                    <div className="flex items-center justify-between border-t pt-3">
                      <div className="text-xs text-indigo-600 font-medium">Ready for review</div>
                      <div className="flex gap-2">
                        <button onClick={() => handleSuggestionAction(s.id, 'reject')} className="px-3 py-1.5 rounded-lg text-xs font-medium text-gray-600 hover:bg-red-50 hover:text-red-600 transition-colors">
                          Reject
                        </button>
                        <button onClick={() => handleSuggestionAction(s.id, 'accept')} className="px-3 py-1.5 rounded-lg text-xs font-medium bg-indigo-600 hover:bg-indigo-700 text-white transition-colors">
                          Accept & Apply
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
