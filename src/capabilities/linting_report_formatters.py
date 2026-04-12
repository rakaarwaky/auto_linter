import json
from typing import Dict, Any

def to_sarif(results: Dict[str, Any]) -> str:
    """Convert lint results to SARIF format."""
    runs = []
    
    for adapter_name, adapter_results in results.items():
        results_list = []
        
        for error in adapter_results.get("errors", []):
            # Try to parse string error back to structured if possible, 
            # or just use generic parsing. For now, we assume errors are strings
            # In a more advanced version, analysis_use_case would return objects.
            results_list.append({
                "ruleId": adapter_name,
                "message": {"text": error},
                "locations": [{"physicalLocation": {"artifactLocation": {"uri": "unknown"}}}]
            })
            
        runs.append({
            "tool": {"driver": {"name": adapter_name}},
            "results": results_list
        })
        
    sarif = {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": runs
    }
    return json.dumps(sarif, indent=2)

def to_junit(results: Dict[str, Any]) -> str:
    """Convert lint results to JUnit XML format."""
    xml = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml.append('<testsuites name="Auto-Linter">')
    
    for adapter_name, adapter_results in results.items():
        errors = adapter_results.get("errors", [])
        failure_count = len(errors)
        xml.append(f'  <testsuite name="{adapter_name}" tests="1" failures="{failure_count}">')
        
        if failure_count == 0:
            xml.append(f'    <testcase name="lint_{adapter_name}" classname="{adapter_name}"/>')
        else:
            for i, error in enumerate(errors):
                xml.append(f'    <testcase name="lint_{adapter_name}_{i}" classname="{adapter_name}">')
                xml.append(f'      <failure message="Linting failed">{error}</failure>')
                xml.append('    </testcase>')
        
        xml.append('  </testsuite>')
        
    xml.append('</testsuites>')
    return "\n".join(xml)
