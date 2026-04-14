"use client";

import { useState, useEffect } from "react";

interface EndpointInfo {
  path: string;
  methods: string[];
}

interface ModuleInfo {
  name: string;
  endpointCount: number;
  endpoints: EndpointInfo[];
}

interface TestResult {
  endpoint: string;
  method: string;
  status: string;
  time_ms: number;
  status_code: number | null;
  error: string | null;
}

interface ModuleTestResult {
  module: string;
  total: number;
  passed: number;
  failed: number;
  results: TestResult[];
}

export default function QAPage() {
  const [modules, setModules] = useState<ModuleInfo[]>([]);
  const [activeTab, setActiveTab] = useState("modules");
  const [isRunning, setIsRunning] = useState(false);
  const [runningModule, setRunningModule] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<ModuleTestResult | null>(null);
  const [allResults, setAllResults] = useState<Record<string, ModuleTestResult>>({});
  const [loadingModules, setLoadingModules] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchModules();
  }, []);

  const fetchModules = async () => {
    setLoadingModules(true);
    setError(null);
    try {
      const response = await fetch("/api/v1/qa/modules?app=axonhis_md");
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      setModules(data.modules || []);
    } catch (err: any) {
      console.error("Failed to fetch modules:", err);
      setError(`Failed to load modules: ${err.message}`);
    } finally {
      setLoadingModules(false);
    }
  };

  const testModule = async (moduleName: string) => {
    setIsRunning(true);
    setRunningModule(moduleName);
    setError(null);
    try {
      const response = await fetch(`/api/v1/qa/test/module/${moduleName}`, {
        method: "POST",
      });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data: ModuleTestResult = await response.json();
      setTestResults(data);
      setAllResults((prev) => ({ ...prev, [moduleName]: data }));
      setActiveTab("results");
    } catch (err: any) {
      console.error("Failed to test module:", err);
      setError(`Failed to test ${moduleName}: ${err.message}`);
    } finally {
      setIsRunning(false);
      setRunningModule(null);
    }
  };

  const testAllModules = async () => {
    setIsRunning(true);
    setRunningModule("all");
    setError(null);
    try {
      const response = await fetch(`/api/v1/qa/test/all?app=axonhis_md`, { method: "POST" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      const newResults: Record<string, ModuleTestResult> = {};
      let combined: TestResult[] = [];
      if (data.modules) {
        Object.entries(data.modules).forEach(([name, mod]: [string, any]) => {
          newResults[name] = mod;
          if (mod.results) combined = [...combined, ...mod.results];
        });
      }
      setAllResults(newResults);
      setTestResults({
        module: "All Modules",
        total: combined.length,
        passed: data.total_passed || 0,
        failed: data.total_failed || 0,
        results: combined,
      });
      setActiveTab("results");
    } catch (err: any) {
      console.error("Failed to test all:", err);
      setError(`Failed to test all modules: ${err.message}`);
    } finally {
      setIsRunning(false);
      setRunningModule(null);
    }
  };

  const generateReport = () => {
    if (!testResults) return;
    const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
    const lines: string[] = [];
    lines.push("AXONHIS QA TEST REPORT");
    lines.push("=".repeat(60));
    lines.push(`Generated: ${new Date().toLocaleString()}`);
    lines.push(`Module: ${testResults.module}`);
    lines.push(`Total: ${testResults.total} | Passed: ${testResults.passed} | Failed: ${testResults.failed}`);
    lines.push(`Pass Rate: ${testResults.total > 0 ? ((testResults.passed / testResults.total) * 100).toFixed(1) : 0}%`);
    lines.push("");
    lines.push("-".repeat(60));
    lines.push("DETAILED RESULTS");
    lines.push("-".repeat(60));
    testResults.results.forEach((r, i) => {
      lines.push(`${i + 1}. [${r.status.toUpperCase()}] ${r.method} ${r.endpoint}`);
      lines.push(`   Status Code: ${r.status_code ?? "N/A"} | Time: ${r.time_ms}ms`);
      if (r.error) lines.push(`   Error: ${r.error}`);
    });
    lines.push("");
    lines.push("=".repeat(60));
    lines.push("END OF REPORT");

    const blob = new Blob([lines.join("\n")], { type: "text/plain" });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `axonhis-qa-report-${timestamp}.txt`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);
  };

  const getStatusBadge = (status: string) => {
    const colors: Record<string, string> = {
      passed: "background: #dcfce7; color: #166534; border: 1px solid #86efac",
      failed: "background: #fee2e2; color: #991b1b; border: 1px solid #fca5a5",
      error: "background: #fef3c7; color: #92400e; border: 1px solid #fcd34d",
    };
    return colors[status] || "background: #f3f4f6; color: #374151; border: 1px solid #d1d5db";
  };

  const totalEndpoints = modules.reduce((sum, m) => sum + m.endpointCount, 0);

  return (
    <div style={{ padding: "24px", fontFamily: "'Inter', -apple-system, sans-serif", background: "#f8fafc", minHeight: "100vh" }}>
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "24px" }}>
        <div>
          <h1 style={{ fontSize: "28px", fontWeight: 700, color: "#0f172a", margin: 0 }}>
            AxonHIS MD QA Testing Center
          </h1>
          <p style={{ color: "#64748b", marginTop: "4px", fontSize: "14px" }}>
            {modules.length} modules · {totalEndpoints} endpoints
          </p>
        </div>
        <div style={{ display: "flex", gap: "8px" }}>
          {["modules", "results", "report"].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                padding: "8px 18px",
                borderRadius: "8px",
                border: "none",
                fontWeight: 600,
                fontSize: "13px",
                cursor: "pointer",
                background: activeTab === tab ? "#3b82f6" : "#e2e8f0",
                color: activeTab === tab ? "#fff" : "#475569",
                transition: "all 0.2s",
              }}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </div>
      </div>

      {error && (
        <div style={{ background: "#fee2e2", color: "#991b1b", padding: "12px 16px", borderRadius: "8px", marginBottom: "16px", fontSize: "14px" }}>
          ⚠️ {error}
        </div>
      )}

      {/* Modules Tab */}
      {activeTab === "modules" && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <h2 style={{ fontSize: "20px", fontWeight: 600, color: "#1e293b" }}>API Modules</h2>
            <button
              onClick={testAllModules}
              disabled={isRunning}
              style={{
                padding: "10px 24px",
                borderRadius: "8px",
                border: "none",
                fontWeight: 600,
                fontSize: "14px",
                cursor: isRunning ? "not-allowed" : "pointer",
                background: isRunning ? "#94a3b8" : "linear-gradient(135deg, #7c3aed, #6366f1)",
                color: "#fff",
                boxShadow: "0 2px 8px rgba(99, 102, 241, 0.3)",
              }}
            >
              {isRunning && runningModule === "all" ? "⏳ Testing All..." : "🚀 Test All Modules"}
            </button>
          </div>

          {loadingModules ? (
            <div style={{ textAlign: "center", padding: "48px", color: "#64748b" }}>
              <div style={{ fontSize: "32px", marginBottom: "8px" }}>⏳</div>
              Loading modules...
            </div>
          ) : (
            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: "16px" }}>
              {modules.map((mod) => {
                const modResult = allResults[mod.name];
                return (
                  <div
                    key={mod.name}
                    style={{
                      background: "#fff",
                      borderRadius: "12px",
                      padding: "20px",
                      border: "1px solid #e2e8f0",
                      boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
                      transition: "all 0.2s",
                    }}
                  >
                    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
                      <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#1e293b", textTransform: "uppercase", margin: 0 }}>
                        {mod.name}
                      </h3>
                      <span style={{ fontSize: "12px", padding: "2px 10px", borderRadius: "12px", background: "#f1f5f9", color: "#475569", fontWeight: 500 }}>
                        {mod.endpointCount} endpoints
                      </span>
                    </div>

                    {modResult && (
                      <div style={{ display: "flex", gap: "8px", marginBottom: "12px", fontSize: "12px", fontWeight: 600 }}>
                        <span style={{ color: "#16a34a" }}>✅ {modResult.passed}</span>
                        <span style={{ color: "#dc2626" }}>❌ {modResult.failed}</span>
                      </div>
                    )}

                    <button
                      onClick={() => testModule(mod.name)}
                      disabled={isRunning}
                      style={{
                        width: "100%",
                        padding: "8px",
                        borderRadius: "8px",
                        border: "1px solid #bfdbfe",
                        background: isRunning && runningModule === mod.name ? "#e0e7ff" : "#eff6ff",
                        color: "#2563eb",
                        fontWeight: 600,
                        fontSize: "13px",
                        cursor: isRunning ? "not-allowed" : "pointer",
                      }}
                    >
                      {isRunning && runningModule === mod.name ? "⏳ Running..." : "▶ Run Tests"}
                    </button>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Results Tab */}
      {activeTab === "results" && (
        <div>
          {testResults ? (
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
                <h2 style={{ fontSize: "20px", fontWeight: 600, color: "#1e293b" }}>
                  Results: {testResults.module}
                </h2>
                <div style={{ display: "flex", gap: "16px", fontSize: "14px", fontWeight: 600 }}>
                  <span style={{ color: "#64748b" }}>Total: {testResults.total}</span>
                  <span style={{ color: "#16a34a" }}>Passed: {testResults.passed}</span>
                  <span style={{ color: "#dc2626" }}>Failed: {testResults.failed}</span>
                  <span style={{ color: "#0ea5e9" }}>
                    Rate: {testResults.total > 0 ? ((testResults.passed / testResults.total) * 100).toFixed(0) : 0}%
                  </span>
                </div>
              </div>

              {/* Progress bar */}
              <div style={{ height: "8px", background: "#e2e8f0", borderRadius: "4px", marginBottom: "20px", overflow: "hidden" }}>
                <div
                  style={{
                    height: "100%",
                    width: `${testResults.total > 0 ? (testResults.passed / testResults.total) * 100 : 0}%`,
                    background: "linear-gradient(90deg, #22c55e, #16a34a)",
                    borderRadius: "4px",
                    transition: "width 0.5s ease",
                  }}
                />
              </div>

              <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                {testResults.results.map((r, i) => (
                  <div
                    key={i}
                    style={{
                      background: "#fff",
                      borderRadius: "8px",
                      padding: "14px 18px",
                      border: "1px solid #e2e8f0",
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                    }}
                  >
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: 600, fontSize: "14px", color: "#1e293b" }}>
                        <span style={{ display: "inline-block", width: "50px", fontSize: "11px", padding: "2px 6px", borderRadius: "4px", background: "#f1f5f9", color: "#475569", fontWeight: 700, textAlign: "center", marginRight: "8px" }}>
                          {r.method}
                        </span>
                        {r.endpoint}
                      </div>
                      {r.error && (
                        <div style={{ fontSize: "12px", color: "#dc2626", marginTop: "4px" }}>
                          {r.error}
                        </div>
                      )}
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                      <span style={{ fontSize: "12px", color: "#94a3b8" }}>{r.time_ms}ms</span>
                      {r.status_code && (
                        <span style={{ fontSize: "12px", color: "#64748b", fontWeight: 500 }}>{r.status_code}</span>
                      )}
                      <span
                        style={{
                          padding: "4px 12px",
                          borderRadius: "6px",
                          fontSize: "12px",
                          fontWeight: 700,
                          ...Object.fromEntries(
                            getStatusBadge(r.status)
                              .split(";")
                              .map((s) => s.trim().split(":").map((v) => v.trim()))
                          ),
                        }}
                      >
                        {r.status.toUpperCase()}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "64px", color: "#94a3b8" }}>
              <div style={{ fontSize: "48px", marginBottom: "12px" }}>🧪</div>
              <p style={{ fontSize: "16px" }}>No test results yet. Run a module test to see results here.</p>
            </div>
          )}
        </div>
      )}

      {/* Report Tab */}
      {activeTab === "report" && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px" }}>
            <h2 style={{ fontSize: "20px", fontWeight: 600, color: "#1e293b" }}>QA Reports</h2>
            {testResults && (
              <button
                onClick={generateReport}
                style={{
                  padding: "10px 24px",
                  borderRadius: "8px",
                  border: "none",
                  fontWeight: 600,
                  fontSize: "14px",
                  cursor: "pointer",
                  background: "linear-gradient(135deg, #0ea5e9, #3b82f6)",
                  color: "#fff",
                  boxShadow: "0 2px 8px rgba(59, 130, 246, 0.3)",
                }}
              >
                📥 Download Report
              </button>
            )}
          </div>

          {testResults ? (
            <div style={{ background: "#fff", borderRadius: "12px", padding: "24px", border: "1px solid #e2e8f0" }}>
              <h3 style={{ fontSize: "16px", fontWeight: 600, marginBottom: "16px", color: "#1e293b" }}>
                Latest Test Summary
              </h3>

              {/* Summary cards */}
              <div style={{ display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: "12px", marginBottom: "24px" }}>
                <div style={{ padding: "16px", borderRadius: "8px", background: "#f8fafc", textAlign: "center" }}>
                  <div style={{ fontSize: "28px", fontWeight: 700, color: "#0f172a" }}>{testResults.total}</div>
                  <div style={{ fontSize: "12px", color: "#64748b", fontWeight: 500 }}>Total Tests</div>
                </div>
                <div style={{ padding: "16px", borderRadius: "8px", background: "#f0fdf4", textAlign: "center" }}>
                  <div style={{ fontSize: "28px", fontWeight: 700, color: "#16a34a" }}>{testResults.passed}</div>
                  <div style={{ fontSize: "12px", color: "#16a34a", fontWeight: 500 }}>Passed</div>
                </div>
                <div style={{ padding: "16px", borderRadius: "8px", background: "#fef2f2", textAlign: "center" }}>
                  <div style={{ fontSize: "28px", fontWeight: 700, color: "#dc2626" }}>{testResults.failed}</div>
                  <div style={{ fontSize: "12px", color: "#dc2626", fontWeight: 500 }}>Failed</div>
                </div>
                <div style={{ padding: "16px", borderRadius: "8px", background: "#eff6ff", textAlign: "center" }}>
                  <div style={{ fontSize: "28px", fontWeight: 700, color: "#2563eb" }}>
                    {testResults.total > 0 ? ((testResults.passed / testResults.total) * 100).toFixed(0) : 0}%
                  </div>
                  <div style={{ fontSize: "12px", color: "#2563eb", fontWeight: 500 }}>Pass Rate</div>
                </div>
              </div>

              {/* Module breakdown */}
              {Object.keys(allResults).length > 0 && (
                <div>
                  <h4 style={{ fontSize: "14px", fontWeight: 600, color: "#475569", marginBottom: "12px" }}>
                    Module Breakdown
                  </h4>
                  <table style={{ width: "100%", borderCollapse: "collapse", fontSize: "13px" }}>
                    <thead>
                      <tr style={{ borderBottom: "2px solid #e2e8f0" }}>
                        <th style={{ textAlign: "left", padding: "8px 12px", color: "#475569", fontWeight: 600 }}>Module</th>
                        <th style={{ textAlign: "center", padding: "8px 12px", color: "#475569", fontWeight: 600 }}>Total</th>
                        <th style={{ textAlign: "center", padding: "8px 12px", color: "#16a34a", fontWeight: 600 }}>Passed</th>
                        <th style={{ textAlign: "center", padding: "8px 12px", color: "#dc2626", fontWeight: 600 }}>Failed</th>
                        <th style={{ textAlign: "center", padding: "8px 12px", color: "#475569", fontWeight: 600 }}>Rate</th>
                      </tr>
                    </thead>
                    <tbody>
                      {Object.entries(allResults).map(([name, res]) => (
                        <tr key={name} style={{ borderBottom: "1px solid #f1f5f9" }}>
                          <td style={{ padding: "10px 12px", fontWeight: 600, textTransform: "uppercase" }}>{name}</td>
                          <td style={{ textAlign: "center", padding: "10px 12px" }}>{res.total}</td>
                          <td style={{ textAlign: "center", padding: "10px 12px", color: "#16a34a", fontWeight: 600 }}>{res.passed}</td>
                          <td style={{ textAlign: "center", padding: "10px 12px", color: "#dc2626", fontWeight: 600 }}>{res.failed}</td>
                          <td style={{ textAlign: "center", padding: "10px 12px" }}>
                            {res.total > 0 ? ((res.passed / res.total) * 100).toFixed(0) : 0}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          ) : (
            <div style={{ textAlign: "center", padding: "64px", color: "#94a3b8" }}>
              <div style={{ fontSize: "48px", marginBottom: "12px" }}>📊</div>
              <p style={{ fontSize: "16px" }}>Run tests first to generate a report.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
