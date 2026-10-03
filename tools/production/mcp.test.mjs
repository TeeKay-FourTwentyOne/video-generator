import test from 'node:test';
import assert from 'node:assert/strict';
import path from 'node:path';
import { Client } from '../../mcp/video-generator/node_modules/@modelcontextprotocol/sdk/dist/esm/client/index.js';
import { StdioClientTransport } from '../../mcp/video-generator/node_modules/@modelcontextprotocol/sdk/dist/esm/client/stdio.js';

test('default MCP exposes only the maintained production surface', async () => {
  const transport = new StdioClientTransport({ command: process.execPath,
    args: [path.resolve('mcp/video-generator/dist/server.js')], env: { VIDEO_MCP_PROFILE: 'production' }, stderr: 'pipe' });
  const client = new Client({ name: 'offline-profile-test', version: '1' });
  try {
    await client.connect(transport);
    const { tools } = await client.listTools();
    assert.equal(tools.length, 10);
    for (const name of ['production_init', 'production_doctor', 'production_image', 'production_assemble'])
      assert.ok(tools.some(t => t.name === name), name);
    assert.ok(!tools.some(t => ['save_config', 'execute_project', 'create_job'].includes(t.name)));
    const refusal = await client.callTool({ name: 'production_status', arguments: { workspace: 'outside-workspace' } });
    assert.equal(refusal.isError, true);
  } finally { await client.close(); }
});
test('legacy MCP retains budget guards and protocol errors', async () => {
  const transport = new StdioClientTransport({ command: process.execPath,
    args: [path.resolve('mcp/video-generator/dist/server.js')], env: { VIDEO_MCP_PROFILE: 'legacy' }, stderr: 'pipe' });
  const client = new Client({ name: 'offline-production-test', version: '1' });
  try {
    await client.connect(transport);
    const { tools } = await client.listTools();
    for (const name of ['production_plan', 'production_submit', 'production_poll', 'production_review', 'resume_job'])
      assert.ok(tools.some(t => t.name === name), name);
    for (const name of ['submit_veo_generation', 'create_job']) {
      const schema = tools.find(t => t.name === name).inputSchema;
      assert.ok(schema.required.includes('budgetFile'));
      assert.ok(schema.required.includes('requestId'));
    }
    const refusal = await client.callTool({ name: 'production_status', arguments: { workspace: 'outside-workspace' } });
    assert.equal(refusal.isError, true);
    const missing = await client.callTool({ name: 'get_job', arguments: { jobId: 'offline-nonexistent-job' } });
    assert.equal(missing.isError, true);
  } finally { await client.close(); }
});
