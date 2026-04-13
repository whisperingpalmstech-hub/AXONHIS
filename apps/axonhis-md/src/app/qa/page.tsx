"use client";

import { useState, useEffect } from "react";

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

export default function QA() {
  const [suites, setSuites] = useState<TestSuite[]>([]);
  const [selectedSuite, setSelectedSuite] = useState<string | null>(null);
  const [results, setResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [reports, setReports] = useState<QAReport[]>([]);

  useEffect(() => {
    fetchSuites();
    fetchReports();
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
          reportName: `AxonHIS MD QA Report ${new Date().toISOString()}`,
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
        return "text-green-600 bg-green-100";
      case "failed":
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
      <h1 className="text-3xl font-bold mb-6">AxonHIS MD QA Panel</h1>
      
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
