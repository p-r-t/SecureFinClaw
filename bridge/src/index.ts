#!/usr/bin/env node
/**
 * finclaw WhatsApp Bridge
 * 
 * This bridge connects WhatsApp Web to finclaw's Python backend
 * via WebSocket. It handles authentication, message forwarding,
 * and reconnection logic.
 * 
 * Usage:
 *   npm run build && npm start
 *   
 * Or with custom settings:
 *   BRIDGE_PORT=3001 AUTH_DIR=~/.finclaw/whatsapp npm start
 */

// Polyfill crypto for Baileys in ESM
import { webcrypto } from 'crypto';
if (!globalThis.crypto) {
  (globalThis as any).crypto = webcrypto;
}

import { BridgeServer } from './server.js';
import { homedir } from 'os';
import { join } from 'path';

// NemoClaw #1995: use os.homedir() instead of process.env.HOME to prevent
// env-var manipulation redirecting auth storage to attacker-controlled paths.
const PORT = parseInt(process.env.BRIDGE_PORT || '3001', 10);
if (isNaN(PORT) || PORT < 1 || PORT > 65535) {
  console.error('❌ BRIDGE_PORT must be a valid port number (1-65535)');
  process.exit(1);
}
const AUTH_DIR = process.env.AUTH_DIR || join(homedir(), '.finclaw', 'whatsapp-auth');
const TOKEN = process.env.BRIDGE_TOKEN || undefined;

if (!TOKEN) {
  console.warn('⚠️  BRIDGE_TOKEN not set — WebSocket bridge has NO authentication. Set BRIDGE_TOKEN for production use.');
}

console.log('📊 FinClaw WhatsApp Bridge');
console.log('========================\n');

const server = new BridgeServer(PORT, AUTH_DIR, TOKEN);

// Handle graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n\nShutting down...');
  await server.stop();
  process.exit(0);
});

process.on('SIGTERM', async () => {
  await server.stop();
  process.exit(0);
});

// Start the server
server.start().catch((error) => {
  console.error('Failed to start bridge:', error);
  process.exit(1);
});
