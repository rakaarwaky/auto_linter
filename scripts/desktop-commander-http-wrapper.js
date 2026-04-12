#!/usr/bin/env node
/**
 * HTTP Wrapper for DesktopCommanderMCP
 * Exposes DesktopCommander as HTTP API for auto_linter integration
 */

import { spawn } from 'child_process';
import http from 'http';

const PORT = process.env.DESKTOP_COMMANDER_PORT || 8080;
const DESKTOP_COMMANDER_PATH = process.env.DESKTOP_COMMANDER_PATH || '/persistent/home/raka/mcp-servers/DesktopCommanderMCP/dist/index.js';

const server = http.createServer(async (req, res) => {
  // CORS headers
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    res.writeHead(200);
    res.end();
    return;
  }
  
  if (req.method !== 'POST' || req.url !== '/execute') {
    res.writeHead(404);
    res.end('Not Found');
    return;
  }
  
  let body = '';
  req.on('data', chunk => {
    body += chunk.toString();
  });
  
  req.on('end', async () => {
    try {
      const { command, working_dir, timeout = 300 } = JSON.parse(body);
      
      if (!Array.isArray(command)) {
        res.writeHead(400);
        res.end(JSON.stringify({ error: 'command must be an array' }));
        return;
      }
      
      // Execute command via DesktopCommander
      const result = await executeCommand(command, working_dir, timeout);
      
      res.writeHead(200, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify(result));
    } catch (error) {
      res.writeHead(500);
      res.end(JSON.stringify({ error: error.message }));
    }
  });
});

async function executeCommand(command, workingDir, timeout) {
  return new Promise((resolve, reject) => {
    const [cmd, ...args] = command;
    
    const proc = spawn(cmd, args, {
      cwd: workingDir || process.cwd(),
      stdio: ['pipe', 'pipe', 'pipe'],
      timeout: timeout * 1000
    });
    
    let stdout = '';
    let stderr = '';
    
    proc.stdout.on('data', (data) => {
      stdout += data.toString();
    });
    
    proc.stderr.on('data', (data) => {
      stderr += data.toString();
    });
    
    proc.on('close', (code) => {
      resolve({
        stdout,
        stderr,
        returncode: code,
        execution_time: 0
      });
    });
    
    proc.on('error', (err) => {
      reject(err);
    });
  });
}

server.listen(PORT, () => {
  console.log(`DesktopCommander HTTP Wrapper listening on port ${PORT}`);
  console.log(`Endpoint: http://localhost:${PORT}/execute`);
});
