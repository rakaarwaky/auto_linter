import json
import xml.sax.saxutils as saxutils
from typing import Dict, Any

def _get_severity(sev: str) -> str:
    mapping = {
        "high": "error",
        "medium": "warning",
        "low": "note"
    }
    return mapping.get(sev.lower(), "warning")

def to_sarif(results: Dict[str, Any]) -> str:
    """Convert lint results to SARIF format."""
    results_list = []
    
    for adapter_name, adapter_results in results.items():
        if adapter_name in ["score", "is_passing", "summary", "governance"]:
            continue
            
        if not isinstance(adapter_results, list):
            continue
            
        for error in adapter_results:
            results_list.append({
                "ruleId": f"{adapter_name}/{error.get('code', 'unknown')}",
                "level": _get_severity(error.get("severity", "medium")),
                "message": {"text": error.get("message", "")},
                "locations": [{
                    "physicalLocation": {
                        "artifactLocation": {
                            "uri": error.get("file", "unknown")
                        },
                        "region": {
                            "startLine": error.get("line", 1),
                            "startColumn": error.get("column", 1)
                        }
                    }
                }]
            })
            
    sarif = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [{
            "tool": {
                "driver": {
                    "name": "Auto-Linter"
                }
            },
            "results": results_list
        }]
    }
    return json.dumps(sarif, indent=2)

def to_junit(results: Dict[str, Any]) -> str:
    """Convert lint results to JUnit XML format."""
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    
    total_tests = 0
    total_failures = 0
    testsuites = []
    
    for adapter_name, adapter_results in results.items():
        if adapter_name in ["score", "is_passing", "summary", "governance"]:
            continue
            
        if not isinstance(adapter_results, list):
            continue
            
        failure_count = len(adapter_results)
        testsuite_lines = []
        testsuite_lines.append(f'  <testsuite name="{adapter_name}" tests="{max(1, failure_count)}" failures="{failure_count}">')
        
        if failure_count == 0:
            testsuite_lines.append(f'    <testcase name="lint_{adapter_name}" classname="{adapter_name}"/>')
            total_tests += 1
        else:
            for i, error in enumerate(adapter_results):
                msg = saxutils.escape(error.get("message", ""), entities={'"': "&quot;", "'": "&apos;"})
                testsuite_lines.append(f'    <testcase name="lint_{adapter_name}_{i}" classname="{adapter_name}">')
                testsuite_lines.append(f'      <failure message="Linting failed">{msg}</failure>')
                testsuite_lines.append('    </testcase>')
                total_tests += 1
                total_failures += 1
                
        testsuite_lines.append('  </testsuite>')
        testsuites.extend(testsuite_lines)
        
    xml.append(f'<testsuites name="Auto-Linter" tests="{total_tests}" failures="{total_failures}">')
    xml.extend(testsuites)
    xml.append('</testsuites>')
    
    return "\n".join(xml)
