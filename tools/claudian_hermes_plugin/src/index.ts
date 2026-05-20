import * as fs from 'fs';
import * as path from 'path';
import { z } from 'zod';
import { startServer } from './server.js';
import type { HermesConfig } from './types.js';

const ConfigSchema = z.object({
  hermes: z.object({
    base_url: z.string().url(),
    token: z.string().min(1),
  }),
  mcp: z.object({
    transport: z.enum(['stdio', 'sse', 'http']).default('stdio'),
  }).default({ transport: 'stdio' }),
});

function loadConfig(): HermesConfig {
  // 优先从环境变量读取
  const envBaseUrl = process.env.HERMES_BASE_URL;
  const envToken = process.env.HERMES_TOKEN;

  if (envBaseUrl && envToken) {
    return {
      hermes: {
        base_url: envBaseUrl,
        token: envToken,
      },
      mcp: {
        transport: 'stdio',
      },
    };
  }

  // 从配置文件读取
  const configPaths = [
    path.join(process.env.HOME || '', '.config', 'hermes-mcp', 'config.json'),
    path.join(process.env.HOME || '', '.hermes-mcp', 'config.json'),
    '/etc/hermes-mcp/config.json',
  ];

  for (const configPath of configPaths) {
    try {
      if (fs.existsSync(configPath)) {
        const content = fs.readFileSync(configPath, 'utf-8');
        const raw = JSON.parse(content);
        return ConfigSchema.parse(raw);
      }
    } catch (error) {
      console.error(`[hermes-mcp] Failed to load config from ${configPath}: ${error}`);
    }
  }

  throw new Error(
    'No config found. Set HERMES_BASE_URL and HERMES_TOKEN environment variables, ' +
    'or create ~/.config/hermes-mcp/config.json'
  );
}

async function main() {
  try {
    const config = loadConfig();
    await startServer(config);
  } catch (error) {
    console.error('[hermes-mcp] Fatal error:', error instanceof Error ? error.message : String(error));
    process.exit(1);
  }
}

main();