import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {tmpdir} from 'node:os';
import {pathToFileURL} from 'node:url';

// Copy the built module into a disposable checkout so tests never touch real config.
async function fixture(t) {
  const root = fs.mkdtempSync(path.join(tmpdir(),'config-privacy-'));
  t.after(()=>fs.rmSync(root,{recursive:true,force:true}));
  const utils = path.join(root,'mcp/video-generator/dist/utils');
  fs.mkdirSync(utils,{recursive:true}); fs.mkdirSync(path.join(root,'data'));
  fs.writeFileSync(path.join(root,'package.json'),JSON.stringify({type:'module'}));
  for (const file of ['config.js','paths.js'])
    fs.copyFileSync(path.resolve('mcp/video-generator/dist/utils',file),path.join(utils,file));
  const config = await import(pathToFileURL(path.join(utils,'config.js')).href);
  return {config,filename:path.join(root,'data/config.json')};
}

test('configuration saves and updates keep provider credentials owner-only', {skip:process.platform==='win32'}, async t => {
  const {config,filename} = await fixture(t);
  const value = 'synthetic-config-credential';
  config.saveConfig({runwayApiKey:value,currentProject:'fixture'});
  assert.equal(fs.statSync(filename).mode & 0o777,0o600);
  fs.chmodSync(filename,0o644);
  config.updateConfig({minimaxApiKey:value});
  assert.equal(fs.statSync(filename).mode & 0o777,0o600);
  assert.deepEqual(config.loadConfig(),{runwayApiKey:value,minimaxApiKey:value,currentProject:'fixture'});
});

test('invalid configuration never echoes credential fragments or parser details', async t => {
  const {config,filename} = await fixture(t);
  const value = 'synthetic-config-credential';
  fs.writeFileSync(filename,JSON.stringify({runwayApiKey:value})+'BROKEN');
  const messages=[];
  t.mock.method(console,'error',(...args)=>messages.push(args.join(' ')));
  assert.deepEqual(config.loadConfig(),{});
  assert.equal(messages.length,1);
  assert.match(messages[0],/Unable to read local configuration/);
  assert.ok(!messages[0].includes(value));
  assert.ok(!messages[0].includes(filename));
});
