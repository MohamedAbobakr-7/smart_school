import { spawn } from 'node:child_process'

// Force rolldown to use WASM bindings instead of native Windows bindings.
// This avoids: "Cannot find native binding ... binding-win32-x64-msvc"
process.env.NAPI_RS_FORCE_WASI = '1'

// Forward all args passed after `npm run dev -- <args>`
const args = process.argv.slice(2)

const child = spawn('vite', args, {
  stdio: 'inherit',
  shell: true,
  env: process.env,
})

child.on('exit', (code) => {
  process.exit(code ?? 0)
})

