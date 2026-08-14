import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { fileURLToPath } from 'url'
import path from 'path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const restricted = process.env.VITE_NO_ESBUILD === '1'
const vendor = (f) => path.resolve(__dirname, 'public/vendor', f)

// Blocks the esbuild binary (SIGKILL'd by system security policy on this machine).
// Only applied when VITE_NO_ESBUILD=1 — normal machines use standard Vite/esbuild.
function noEsbuild() {
  return {
    name: 'no-esbuild',
    enforce: 'post',
    config: () => ({ esbuild: false }),
    configResolved(config) {
      config.optimizeDeps.include = []
    },
  }
}

export default defineConfig(restricted ? {
  plugins: [
    react({ babel: { presets: [['@babel/preset-react', { runtime: 'automatic' }]] } }),
    noEsbuild(),
  ],
  server: { port: 5173 },
  resolve: {
    alias: {
      'react/jsx-dev-runtime': vendor('react-jsx-dev-runtime.js'),
      'react/jsx-runtime':     vendor('react-jsx-runtime.js'),
      'react-dom/client':      vendor('react-dom-client.js'),
      'react':                 vendor('react.js'),
    },
  },
  optimizeDeps: { noDiscovery: true },
} : {
  plugins: [react()],
  server: { port: 5173 },
})
