"use client";

import { useState, useEffect } from "react";

interface Module {
  name: string;
  status: 'healthy' | 'degraded' | 'unknown';
  endpointCount: number;
  lastChecked: string;
}

interface TestSuite {
  id: string;
  name: string;
  module: string;
  is_active: boolean;
}

interface TestResult {
  id: string;
  name: string;
  module: string;
  test_type: string;
  status: string;
  execution_time_ms: number;
  error_message: string | null;
}

interface QAReport {
  id: string;
  report_name: string;
  suite_id: string | null;
  total_tests: number;
  passed_tests: number;
  failed_tests: number;
  skipped_tests: number;
  error_tests: number;
  execution_time_ms: number;
  summary: string;
  generated_at: string;
  file_path: string | null;
}

const MODULES = [
  { name: 'auth', label: 'Authentication', icon: '🔐' },
  { name: 'patients', label: 'Patients', icon: '👥' },
  { name: 'opd', label: 'OPD', icon: '🏥' },
  { name: 'ipd', label: 'IPD', icon: '🛏️' },
  { name: 'er', label: 'Emergency', icon: '🚑' },
  { name: 'lab', label: 'Laboratory', icon: '🔬' },
  { name: 'radiology', label: 'Radiology', icon: '📷' },
  { name: 'pharmacy', label: 'Pharmacy', icon: '💊' },
  { name: 'inventory', label: 'Inventory', icon: '📦' },
  { name: 'billing', label: 'Billing', icon: '💰' },
  { name: 'ot', label: 'Operating Theatre', icon: '🏥' },
  { name: 'qa', label: 'QA Module', icon: '✅' },
];

export default function QA() {
  const [suites, setSuites] = useState<TestSuite[]>([]);
  const [selectedSuite, setSelectedSuite] = useState<string | null>(null);
  const [results, setResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [reports, setReports] = useState<QAReport[]>([]);
  const [moduleStatus, setModuleStatus] = useState<Record<string, Module>>({});
  const [testingModule, setTestingModule] = useState<string | null>(null);

  useEffect(() => {
    fetchSuites();
    fetchReports();
    checkAllModules();
  }, []);

  const fetchSuites = async () => {
    try {
      const response = await fetch("/api/v1/qa/suites");
      const data = await response.json();
      setSuites(data);
    } catch (error) {
      console.error("Failed to fetch test suites:", error);
    }
  };

  const fetchReports = async () => {
    try {
      const response = await fetch("/api/v1/qa/reports");
      const data = await response.json();
      setReports(data);
    } catch (error) {
      console.error("Failed to fetch reports:", error);
    }
  };

  const checkModuleHealth = async (moduleName: string) => {
    setTestingModule(moduleName);
    try {
      const response = await fetch(`/api/v1/qa/modules/${moduleName}/health`, {
        method: "GET",
      });
      const data = await response.json();
      setModuleStatus(prev => ({
        ...prev,
        [moduleName]: {
          name: moduleName,
          status: data.status || 'unknown',
          endpointCount: data.endpointCount || 0,
          lastChecked: new Date().toISOString(),
        }
      }));
    } catch (error) {
      setModuleStatus(prev => ({
        ...prev,
        [moduleName]: {
          name: moduleName,
          status: 'degraded',
          endpointCount: 0,
          lastChecked: new Date().toISOString(),
        }
      }));
    } finally {
      setTestingModule(null);
    }
  };

  const checkAllModules = async () => {
    for (const mod of MODULES) {
      await checkModuleHealth(mod.name);
    }
  };

  const runModuleTests = async (moduleName: string) => {
    setIsRunning(true);
    setSelectedSuite(moduleName);
    try {
      const response = await fetch(`/api/v1/qa/modules/${moduleName}/run`, {
        method: "POST",
      });
      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error("Failed to run module tests:", error);
    } finally {
      setIsRunning(false);
    }
  };

  const runTestSuite = async (suiteId: string) => {
    setIsRunning(true);
    setSelectedSuite(suiteId);
    try {
      const response = await fetch(`/api/v1/qa/suites/${suiteId}/run`, {
        method: "POST",
      });
      const data = await response.json();
      setResults(data.results || []);
    } catch (error) {
      console.error("Failed to run test suite:", error);
    } finally {
      setIsRunning(false);
    }
  };

  const generateReport = async (suiteId: string) => {
    try {
      const response = await fetch("/api/v1/qa/reports/generate", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          suiteId,
          reportName: `QA Report ${new Date().toISOString()}`,
        }),
      });
      const data = await response.json();
      fetchReports();
      return data;
    } catch (error) {
      console.error("Failed to generate report:", error);
    }
  };

  const downloadReport = async (reportId: string, reportName: string) => {
    try {
      const response = await fetch(`/api/v1/qa/reports/${reportId}/download`);
      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `${reportName}.pdf`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error("Failed to download report:", error);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "passed":
      case "healthy":
        return "text-green-600 bg-green-100";
      case "failed":
      case "degraded":
        return "text-red-600 bg-red-100";
      case "skipped":
        return "text-yellow-600 bg-yellow-100";
      case "error":
        return "text-purple-600 bg-purple-100";
      default:
        return "text-gray-600 bg-gray-100";
    }
  };

  return (
    <div className="p-6">
      <h1 className="text-3xl font-bold mb-6">Quality Assurance Panel</h1>
      
      {/* Module Health Check */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-xl font-semibold">Module Health Check</h2>
          <button
            onClick={checkAllModules}
            disabled={testingModule !== null}
            className="px-4 py-2 bg-indigo-600 text-white rounded hover:bg-indigo-700 disabled:bg-gray-400"
          >
            {testingModule ? "Checking..." : "Check All Modules"}
          </button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {MODULES.map((mod) => {
            const status = moduleStatus[mod.name];
            return (
              <div
                key={mod.name}
                className="p-4 border rounded-lg hover:shadow-md transition-shadow cursor-pointer"
                onClick={() => checkModuleHealth(mod.name)}
              >
                <div className="text-3xl mb-2">{mod.icon}</div>
                <div className="font-medium text-sm">{mod.label}</div>
                <div className="mt-2">
                  <span className={`px-2 py-1 rounded text-xs ${status ? getStatusColor(status.status) : 'text-gray-600 bg-gray-100'}`}>
                    {testingModule === mod.name ? 'Checking...' : (status?.status || 'Unknown')}
                  </span>
                </div>
                {status && (
                  <div className="text-xs text-gray-500 mt-1">
                    {status.endpointCount} endpoints
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Test Suites */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Test Suites</h2>
          <div className="space-y-2">
            {suites.map((suite) => (
              <div
                key={suite.id}
                className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50"
              >
                <div>
                  <div className="font-medium">{suite.name}</div>
                  <div className="text-sm text-gray-500">
                    Module: {suite.module} | Active: {suite.is_active ? "Yes" : "No"}
                  </div>
                </div>
                <button
                  onClick={() => runTestSuite(suite.id)}
                  disabled={isRunning}
                  className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:bg-gray-400"
                >
                  {isRunning ? "Running..." : "Run"}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Test Results */}
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Test Results</h2>
          {results.length > 0 ? (
            <div className="space-y-2">
              {results.map((result) => (
                <div
                  key={result.id}
                  className="p-4 border rounded-lg"
                >
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium">{result.name}</div>
                      <div className="text-sm text-gray-500">
                        {result.test_type} | {result.execution_time_ms.toFixed(2)}ms
                      </div>
                    </div>
                    <span className={`px-2 py-1 rounded text-sm ${getStatusColor(result.status)}`}>
                      {result.status}
                    </span>
                  </div>
                  {result.error_message && (
                    <div className="mt-2 text-sm text-red-600">
                      {result.error_message}
                    </div>
                  )}
                </div>
              ))}
            </div>
          ) : (
            <div className="text-gray-500 text-center py-8">
                No test results. Run a test suite to see results.
              </div>
          )}
        </div>
      </div>

      {/* Reports Section */}
      <div className="mt-6 bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-semibold mb-4">QA Reports</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b">
                <th className="text-left py-2 px-4">Report Name</th>
                <th className="text-left py-2 px-4">Total Tests</th>
                <th className="text-left py-2 px-4">Passed</th>
                <th className="text-left py-2 px-4">Failed</th>
                <th className="text-left py-2 px-4">Generated At</th>
                <th className="text-left py-2 px-4">Actions</th>
              </tr>
            </thead>
            <tbody>
              {reports.map((report) => (
                <tr key={report.id} className="border-b">
                  <td className="py-2 px-4">{report.report_name}</td>
                  <td className="py-2 px-4">{report.total_tests}</td>
                  <td className="py-2 px-4 text-green-600">{report.passed_tests}</td>
                  <td className="py-2 px-4 text-red-600">{report.failed_tests}</td>
                  <td className="py-2 px-4">
                    {new Date(report.generated_at).toLocaleString()}
                  </td>
                  <td className="py-2 px-4">
                    <button
                      onClick={() => downloadReport(report.id, report.report_name)}
                      className="px-3 py-1 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                    >
                      Download PDF
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
