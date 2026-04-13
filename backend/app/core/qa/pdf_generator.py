"""PDF report generation with templates for QA module."""
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path


def generate_qa_report_html(
    test_results: List[Dict[str, Any]],
    suite_name: str,
    generated_by: str = "System"
) -> str:
    """
    Generate HTML report for QA test results.
    
    Args:
        test_results: List of test result dictionaries
        suite_name: Name of the test suite
        generated_by: Name of the user who generated the report
    
    Returns:
        HTML string for the report
    """
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r.get("status") == "passed")
    failed_tests = sum(1 for r in test_results if r.get("status") == "failed")
    skipped_tests = sum(1 for r in test_results if r.get("status") == "skipped")
    error_tests = sum(1 for r in test_results if r.get("status") == "error")
    
    total_execution_time_ms = sum(r.get("execution_time_ms", 0) for r in test_results)
    
    # Group results by module
    module_groups: Dict[str, List[Dict[str, Any]]] = {}
    for result in test_results:
        module = result.get("module", "unknown")
        if module not in module_groups:
            module_groups[module] = []
        module_groups[module].append(result)
    
    html = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QA Report - {suite_name}</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .header {{
            border-bottom: 3px solid #4CAF50;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .header h1 {{
            color: #333;
            margin: 0;
        }}
        .header .meta {{
            color: #666;
            margin-top: 10px;
            font-size: 14px;
        }}
        .summary {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .summary-card {{
            background-color: #f9f9f9;
            padding: 20px;
            border-radius: 6px;
            border-left: 4px solid #ddd;
        }}
        .summary-card.passed {{
            border-left-color: #4CAF50;
        }}
        .summary-card.failed {{
            border-left-color: #f44336;
        }}
        .summary-card.skipped {{
            border-left-color: #FF9800;
        }}
        .summary-card.error {{
            border-left-color: #9C27B0;
        }}
        .summary-card h3 {{
            margin: 0 0 10px 0;
            color: #333;
            font-size: 14px;
            text-transform: uppercase;
        }}
        .summary-card .value {{
            font-size: 32px;
            font-weight: bold;
            color: #333;
        }}
        .module-section {{
            margin-bottom: 30px;
        }}
        .module-section h2 {{
            color: #333;
            border-bottom: 2px solid #ddd;
            padding-bottom: 10px;
        }}
        .test-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 15px;
        }}
        .test-table th {{
            background-color: #f5f5f5;
            text-align: left;
            padding: 12px;
            border-bottom: 2px solid #ddd;
            color: #333;
        }}
        .test-table td {{
            padding: 12px;
            border-bottom: 1px solid #eee;
        }}
        .status-badge {{
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            text-transform: uppercase;
        }}
        .status-badge.passed {{
            background-color: #4CAF50;
            color: white;
        }}
        .status-badge.failed {{
            background-color: #f44336;
            color: white;
        }}
        .status-badge.skipped {{
            background-color: #FF9800;
            color: white;
        }}
        .status-badge.error {{
            background-color: #9C27B0;
            color: white;
        }}
        .status-badge.pending {{
            background-color: #9E9E9E;
            color: white;
        }}
        .execution-time {{
            color: #666;
            font-size: 14px;
        }}
        .error-message {{
            color: #f44336;
            font-size: 13px;
            margin-top: 5px;
        }}
        .footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            color: #666;
            font-size: 14px;
            text-align: center;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>QA Test Report</h1>
            <div class="meta">
                <strong>Suite:</strong> {suite_name}<br>
                <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
                <strong>Generated By:</strong> {generated_by}
            </div>
        </div>
        
        <div class="summary">
            <div class="summary-card">
                <h3>Total Tests</h3>
                <div class="value">{total_tests}</div>
            </div>
            <div class="summary-card passed">
                <h3>Passed</h3>
                <div class="value">{passed_tests}</div>
            </div>
            <div class="summary-card failed">
                <h3>Failed</h3>
                <div class="value">{failed_tests}</div>
            </div>
            <div class="summary-card skipped">
                <h3>Skipped</h3>
                <div class="value">{skipped_tests}</div>
            </div>
            <div class="summary-card error">
                <h3>Errors</h3>
                <div class="value">{error_tests}</div>
            </div>
        </div>
        
        <div class="summary-card" style="margin-bottom: 30px;">
            <h3>Total Execution Time</h3>
            <div class="value">{total_execution_time_ms:.2f} ms</div>
        </div>
"""
    
    # Add module sections
    for module, results in module_groups.items():
        html += f"""
        <div class="module-section">
            <h2>{module.capitalize()}</h2>
            <table class="test-table">
                <thead>
                    <tr>
                        <th>Test Name</th>
                        <th>Type</th>
                        <th>Status</th>
                        <th>Execution Time</th>
                        <th>Error Message</th>
                    </tr>
                </thead>
                <tbody>
"""
        for result in results:
            status = result.get("status", "pending")
            html += f"""
                    <tr>
                        <td>{result.get("name", "N/A")}</td>
                        <td>{result.get("test_type", "N/A")}</td>
                        <td><span class="status-badge {status}">{status}</span></td>
                        <td class="execution-time">{result.get("execution_time_ms", 0):.2f} ms</td>
                        <td class="error-message">{result.get("error_message", "")}</td>
                    </tr>
"""
        html += """
                </tbody>
            </table>
        </div>
"""
    
    html += f"""
        <div class="footer">
            <p>Generated by AXONHIS QA Module | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        </div>
    </div>
</body>
</html>
"""
    
    return html


def generate_qa_report_pdf(
    test_results: List[Dict[str, Any]],
    suite_name: str,
    output_path: str,
    generated_by: str = "System"
) -> str:
    """
    Generate PDF report for QA test results.
    
    Args:
        test_results: List of test result dictionaries
        suite_name: Name of the test suite
        output_path: Path to save the PDF file
        generated_by: Name of the user who generated the report
    
    Returns:
        Path to the generated PDF file
    """
    try:
        # Generate HTML
        html_content = generate_qa_report_html(test_results, suite_name, generated_by)
        
        # Save HTML file
        html_path = output_path.replace(".pdf", ".html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(html_content)
        
        # Note: For actual PDF generation, you would use weasyprint or reportlab
        # For now, we save the HTML which can be converted to PDF
        # To enable PDF generation, install weasyprint and uncomment below:
        
        # from weasyprint import HTML
        # HTML(string=html_content).write_pdf(output_path)
        
        # For now, return the HTML path
        return html_path
    
    except Exception as e:
        raise Exception(f"Failed to generate PDF report: {str(e)}")


def generate_summary_chart_data(test_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate chart data for test results summary.
    
    Args:
        test_results: List of test result dictionaries
    
    Returns:
        Dictionary with chart data
    """
    total_tests = len(test_results)
    passed_tests = sum(1 for r in test_results if r.get("status") == "passed")
    failed_tests = sum(1 for r in test_results if r.get("status") == "failed")
    skipped_tests = sum(1 for r in test_results if r.get("status") == "skipped")
    error_tests = sum(1 for r in test_results if r.get("status") == "error")
    
    return {
        "total": total_tests,
        "passed": passed_tests,
        "failed": failed_tests,
        "skipped": skipped_tests,
        "error": error_tests,
        "success_rate": (passed_tests / total_tests * 100) if total_tests > 0 else 0
    }
