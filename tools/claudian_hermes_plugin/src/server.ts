import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js';

import { HermesClient } from './api/hermes_client.js';
import { listSpacesTool, listSpacesHandler } from './tools/list_spaces.js';
import { syncToWikiTool, syncToWikiHandler } from './tools/sync_to_wiki.js';
import { searchWikiTool, searchWikiHandler } from './tools/search_wiki.js';
import { getSyncStatusTool, getSyncStatusHandler } from './tools/get_sync_status.js';
import { fullSyncStartTool, fullSyncStartHandler } from './tools/full_sync_start.js';
import { fullSyncBatchTool, fullSyncBatchHandler } from './tools/full_sync_batch.js';
import { fullSyncGraphTool, fullSyncGraphHandler } from './tools/full_sync_graph.js';
import { fullSyncStatusTool, fullSyncStatusHandler } from './tools/full_sync_status.js';
import { fullSyncAbortTool, fullSyncAbortHandler } from './tools/full_sync_abort.js';
import { checkInTool, checkInHandler } from './tools/check_in.js';
import type { ToolDefinition, ToolResult, HermesConfig } from './types.js';

// Tool definitions with their handlers
const tools: Array<{ definition: ToolDefinition; handler: (args: unknown, hermes: HermesClient) => Promise<ToolResult> }> = [
  { definition: listSpacesTool, handler: listSpacesHandler },
  { definition: syncToWikiTool, handler: syncToWikiHandler },
  { definition: searchWikiTool, handler: searchWikiHandler },
  { definition: getSyncStatusTool, handler: getSyncStatusHandler },
  { definition: fullSyncStartTool, handler: fullSyncStartHandler },
  { definition: fullSyncBatchTool, handler: fullSyncBatchHandler },
  { definition: fullSyncGraphTool, handler: fullSyncGraphHandler },
  { definition: fullSyncStatusTool, handler: fullSyncStatusHandler },
  { definition: fullSyncAbortTool, handler: fullSyncAbortHandler },
  { definition: checkInTool, handler: checkInHandler },
];

export function createHermesMCPServer(config: HermesConfig): Server {
  const hermes = new HermesClient(config.hermes.base_url, config.hermes.token);

  const server = new Server(
    {
      name: 'hermes-mcp',
      version: '1.0.0',
    },
    {
      capabilities: {
        tools: {},
      },
    }
  );

  // Register tools list handler
  server.setRequestHandler(ListToolsRequestSchema, async () => {
    return {
      tools: tools.map(t => t.definition),
    };
  });

  // Register tool call handler
  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;

    const tool = tools.find(t => t.definition.name === name);

    if (!tool) {
      return {
        content: [
          {
            type: 'text',
            text: `未知的工具: ${name}`,
          },
        ],
        isError: true,
      } as any;
    }

    try {
      const result = await tool.handler(args ?? {}, hermes);
      return result as any;
    } catch (error) {
      return {
        content: [
          {
            type: 'text',
            text: `工具执行错误：${error instanceof Error ? error.message : String(error)}`,
          },
        ],
        isError: true,
      } as any;
    }
  });

  return server;
}

export async function startServer(config: HermesConfig): Promise<void> {
  const server = createHermesMCPServer(config);
  const transport = new StdioServerTransport();

  console.error('[hermes-mcp] Starting server...');
  console.error(`[hermes-mcp] Connected to: ${config.hermes.base_url}`);

  await server.connect(transport);

  console.error('[hermes-mcp] Server ready');
}