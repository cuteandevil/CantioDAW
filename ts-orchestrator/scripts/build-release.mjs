#!/usr/bin/env node
import { execSync } from 'child_process';
import { existsSync, copyFileSync, mkdirSync, rmSync, readdirSync, statSync, writeFileSync } from 'fs';
import { join, dirname, resolve } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const ROOT = resolve(__dirname, '..');
const RELEASE = resolve(ROOT, '..', 'release');

function run(cmd, opts = {}) {
  console.log(`\n> ${cmd}`);
  execSync(cmd, { stdio: 'inherit', cwd: ROOT, ...opts });
}

function step(msg) {
  console.log(`\n${'='.repeat(60)}`);
  console.log(`  ${msg}`);
  console.log('='.repeat(60));
}

// Clean previous release
step('Cleaning previous builds');
if (existsSync(RELEASE)) rmSync(RELEASE, { recursive: true, force: true });
mkdirSync(RELEASE, { recursive: true });

// 1. Build TS with production config (no sourcemaps, no declarations)
step('Step 1: Compile TypeScript (production)');
run('npx tsc -p tsconfig.prod.json');

// Verify dist exists
const distDir = join(ROOT, 'dist');
if (!existsSync(distDir)) {
  console.error('ERROR: dist/ not created. TS compilation failed.');
  process.exit(1);
}

const jsFiles = readdirSync(distDir, { recursive: true }).filter(f => f.endsWith('.js'));
console.log(`  Compiled ${jsFiles.length} JS files`);

// 2. Remove .d.ts, .d.ts.map, .js.map from dist
step('Step 2: Stripping type declarations and source maps');
let stripped = 0;
function stripRecursive(dir) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = join(dir, entry.name);
    if (entry.isDirectory()) stripRecursive(full);
    else if (entry.name.endsWith('.d.ts') || entry.name.endsWith('.d.ts.map') || entry.name.endsWith('.js.map')) {
      rmSync(full);
      stripped++;
    }
  }
}
stripRecursive(distDir);
console.log(`  Stripped ${stripped} files`);

// 3. Bundle with esbuild into single CJS file (all deps included)
step('Step 3: Bundling with esbuild (all deps included)');
const entryPoint = join(distDir, 'index.js');
if (!existsSync(entryPoint)) {
  console.error(`ERROR: Entry point not found: ${entryPoint}`);
  process.exit(1);
}
run(`npx esbuild ${entryPoint} --bundle --platform=node --format=cjs --outfile=${join(distDir, 'bundle.cjs')} --external:none`);

const bundlePath = join(distDir, 'bundle.cjs');
if (!existsSync(bundlePath)) {
  console.error('ERROR: Bundle not created');
  process.exit(1);
}
const bundleSize = statSync(bundlePath).size;
console.log(`  Bundle size: ${(bundleSize / 1024).toFixed(1)} KB`);

// 4. Obfuscate the bundle
step('Step 4: Obfuscating bundle (anti-reverse-engineering)');
run(`npx javascript-obfuscator ${join(distDir, 'bundle.cjs')} --output ${join(distDir, 'obfuscated.cjs')} --compact true --control-flow-flattening true --control-flow-flattening-threshold 0.75 --numbers-to-expressions true --simplify false --string-array-encoding rc4 --string-array-threshold 0.8 --transform-object-keys true --unicode-escape-sequence true --identifier-names-generator mangled --rename-globals false --self-defending true --disable-console-output false`);

const obfPath = join(distDir, 'obfuscated.cjs');
if (!existsSync(obfPath)) {
  console.error('ERROR: Obfuscation failed');
  process.exit(1);
}
const obfSize = statSync(obfPath).size;
console.log(`  Obfuscated size: ${(obfSize / 1024).toFixed(1)} KB (${((obfSize / bundleSize - 1) * 100).toFixed(1)}% overhead)`);

// 5. Create sea-config.json for Node.js SEA (CJS entry)
step('Step 5: Creating Node.js Single Executable Application');
const seaConfig = {
  main: join(distDir, 'obfuscated.cjs'),
  output: join(ROOT, 'sea-prep.blob'),
  disableExperimentalSEAWarning: true,
};
writeFileSync(join(ROOT, 'sea-config.json'), JSON.stringify(seaConfig, null, 2));

// Generate the blob
run('node --experimental-sea-config sea-config.json');

const blobPath = join(ROOT, 'sea-prep.blob');
if (!existsSync(blobPath)) {
  console.error('ERROR: SEA blob not created');
  process.exit(1);
}

// 6. Inject blob into Node binary to create exe
step('Step 6: Injecting blob into executable');

// Get the Node.js executable path
const nodePath = process.execPath;
console.log(`  Host Node: ${nodePath}`);

// Copy node.exe to release folder
const exeName = 'cantiodaw-mcp.exe';
const exePath = join(RELEASE, exeName);
copyFileSync(nodePath, exePath);

// Post-process the binary: inject the SEA blob
if (process.platform === 'win32') {
  run(`npx postject ${exePath} NODE_SEA_BLOB ${blobPath} --sentinel-fuse NODE_SEA_FUSE_fce680ab2cc467b6e072b8b5df1996b2`, { shell: true });
} else {
  run(`npx postject ${exePath} NODE_SEA_BLOB ${blobPath} --sentinel-fuse NODE_SEA_FUSE_fce680ab2cc467b6e072b8b5df1996b2 --macho-segment-name NODE_SEA`);
}

// 7. Copy additional release assets
step('Step 7: Copying release assets');

// Copy Python bridge script
const bridgePy = join(ROOT, 'src', 'bridge', 'python_bridge.py');
if (existsSync(bridgePy)) {
  copyFileSync(bridgePy, join(RELEASE, 'python_bridge.py'));
  console.log('  Copied python_bridge.py');
}

// Copy demucs Python package
const demucsSrc = join(ROOT, '..', '..', 'demucs-main', 'demucs');
const demucsDst = join(RELEASE, 'demucs');
if (existsSync(demucsSrc)) {
  function copyDir(src, dst) {
    mkdirSync(dst, { recursive: true });
    for (const entry of readdirSync(src, { withFileTypes: true })) {
      const s = join(src, entry.name), d = join(dst, entry.name);
      if (entry.isDirectory()) copyDir(s, d);
      else if (!entry.name.endsWith('.pyc') && entry.name !== '__pycache__') copyFileSync(s, d);
    }
  }
  copyDir(demucsSrc, demucsDst);
  let pyCount = 0;
  function countPys(dir) {
    for (const e of readdirSync(dir, { withFileTypes: true })) {
      if (e.isDirectory() && e.name !== '__pycache__') countPys(join(dir, e.name));
      else if (e.name.endsWith('.py')) pyCount++;
    }
  }
  countPys(demucsDst);
  console.log(`  Copied demucs/ (${pyCount} .py files)`);
} else {
  console.log('  WARNING: demucs-main not found — skipping');
}

// Copy README
const readme = join(ROOT, '..', 'README.md');
if (existsSync(readme)) copyFileSync(readme, join(RELEASE, 'README.md'));

// Create install script
const installBat = `@echo off
echo CantioDAW MCP Orchestrator
echo ===========================
echo.
echo The executable is ready: cantiodaw-mcp.exe
echo.
echo Usage:
echo   cantiodaw-mcp.exe            Start MCP server
echo   cantiodaw-mcp.exe --test     Run self-test
echo   cantiodaw-mcp.exe toollist   List all tools
echo.
echo Requirements:
echo   - Python 3.9+ (for the Python bridge)
echo   - torch + torchaudio (pip install torch torchaudio)
echo   - soundfile, numpy, mido (pip install soundfile numpy mido)
echo   - Optional: scipy (pip install scipy)
echo   - CantioDAW project root (set CANTIODAW_ROOT or run from project dir)
echo.
echo First-time setup:
echo   pip install torch torchaudio soundfile numpy mido scipy
echo.
pause
`;
writeFileSync(join(RELEASE, 'README.txt'), installBat);

// 8. Cleanup temp files
step('Step 8: Cleaning up temp files');
if (existsSync(join(ROOT, 'sea-config.json'))) rmSync(join(ROOT, 'sea-config.json'));
if (existsSync(blobPath)) rmSync(blobPath);
if (existsSync(join(ROOT, 'dist'))) rmSync(join(ROOT, 'dist'), { recursive: true, force: true });

// 9. Verify release
step('Step 9: Verifying release');
const releaseFiles = readdirSync(RELEASE);
console.log(`  Release folder: ${RELEASE}`);
for (const f of releaseFiles) {
  const size = statSync(join(RELEASE, f)).size;
  console.log(`    ${f}  (${(size / 1024).toFixed(1)} KB)`);
}

console.log(`\n${'='.repeat(60)}`);
console.log('  Release build complete!');
console.log(`  Output: ${RELEASE}`);
console.log('='.repeat(60));
