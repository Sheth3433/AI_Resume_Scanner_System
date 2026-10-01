import { existsSync } from 'node:fs'
import { spawn } from 'node:child_process'
import { delimiter, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const root = fileURLToPath(new URL('../', import.meta.url))
const windows = process.platform === 'win32'
const environmentPython = join(root, '.venv', windows ? 'Scripts' : 'bin', windows ? 'python.exe' : 'python')
const command = existsSync(environmentPython) ? environmentPython : windows ? 'py' : 'python3'
const args = [
  '-m', 'uvicorn', 'app.main:app', '--reload', '--app-dir', 'backend',
  '--host', '127.0.0.1', '--port', '8000',
]

const child = spawn(command, args, {
  cwd: root,
  stdio: 'inherit',
  env: {
    ...process.env,
    PATH: `${join(root, '.venv', windows ? 'Scripts' : 'bin')}${delimiter}${process.env.PATH || ''}`,
  },
})

for (const signal of ['SIGINT', 'SIGTERM']) {
  process.on(signal, () => child.kill(signal))
}

child.on('error', (error) => {
  console.error(`Could not start the backend with ${command}: ${error.message}`)
  process.exitCode = 1
})

child.on('close', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal)
  } else {
    process.exitCode = code ?? 1
  }
})