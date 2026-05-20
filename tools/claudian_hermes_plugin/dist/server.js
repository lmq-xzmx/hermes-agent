import { Server } from '@modelcontextprotocol/sdk/server/index.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { CallToolRequestSchema, ListToolsRequestSchema, } from '@modelcontextprotocol/sdk/types.js';
import { HermesClient } from './api/hermes_client.js';
import { listSpacesTool, listSpacesHandler } from './tools/list_spaces.js';
import { syncToWikiTool, syncToWikiHandler } from './tools/sync_to_wiki.js';
import { searchWikiTool, searchWikiHandler } from './tools/search_wiki.js';
import { getSyncStatusTool, getSyncStatusHandler } from './tools/get_sync_status.js';
// Tool definitions with their handlers
const tools = [
    { definition: listSpacesTool, handler: listSpacesHandler },
    { definition: syncToWikiTool, handler: syncToWikiHandler },
    { definition: searchWikiTool, handler: searchWikiHandler },
    { definition: getSyncStatusTool, handler: getSyncStatusHandler },
];
export function createHermesMCPServer(config) {
    const hermes = new HermesClient(config.hermes.base_url, config.hermes.token);
    const server = new Server({
        name: 'hermes-mcp',
        version: '1.0.0',
    }, {
        capabilities: {
            tools: {},
        },
    });
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
            };
        }
        try {
            const result = await tool.handler(args ?? {}, hermes);
            return result;
        }
        catch (error) {
            return {
                content: [
                    {
                        type: 'text',
                        text: `工具执行错误：${error instanceof Error ? error.message : String(error)}`,
                    },
                ],
                isError: true,
            };
        }
    });
    return server;
}
export async function startServer(config) {
    const server = createHermesMCPServer(config);
    const transport = new StdioServerTransport();
    console.error('[hermes-mcp] Starting server...');
    console.error(`[hermes-mcp] Connected to: ${config.hermes.base_url}`);
    await server.connect(transport);
    console.error('[hermes-mcp] Server ready');
}
//# sourceMappingURL=server.js.map