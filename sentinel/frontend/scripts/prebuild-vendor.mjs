/**
 * Pre-bundles CJS react / react-dom / jsx-runtime to ESM using pure-JS Rollup.
 * Run once: node scripts/prebuild-vendor.mjs
 * Output: public/vendor/{react,react-dom-client,react-jsx-runtime,react-jsx-dev-runtime}.js
 *
 * Why: Vite's dep optimizer (the standard CJS→ESM path) calls the esbuild binary,
 * which is rejected by system security policy on this machine.  Rollup (pure JS)
 * achieves the same result without any native binary.
 */

import { rollup } from 'rollup'
import commonjs from '@rollup/plugin-commonjs'
import nodeResolve from '@rollup/plugin-node-resolve'
import replace from '@rollup/plugin-replace'
import { writeFileSync, mkdirSync } from 'fs'
import { fileURLToPath } from 'url'
import path from 'path'

const __dirname = path.dirname(fileURLToPath(import.meta.url))
const root = path.resolve(__dirname, '..')
const outDir = path.join(root, 'public', 'vendor')
mkdirSync(outDir, { recursive: true })

// Point directly at development CJS files to avoid the conditional
// if (process.env.NODE_ENV === 'production') branch in package entry points,
// which prevents @rollup/plugin-commonjs from detecting named exports statically.
const rCjs = path.join(root, 'node_modules/react/cjs')
const rdCjs = path.join(root, 'node_modules/react-dom/cjs')

// react.js is standalone.  The other three depend on react — mark it external so
// they all share the SAME react instance at runtime (no duplicate ReactCurrentDispatcher).
// Rollup paths maps 'react' → './react.js' in the generated ESM import statements.
const bundles = [
  { input: path.join(rCjs,  'react.development.js'),               out: 'react.js',             external: [] },
  // Use the react-dom/client entry so createRoot goes through the usingClientEntryPoint wrapper
  { input: path.join(root, 'node_modules/react-dom/client.js'),    out: 'react-dom-client.js',  external: ['react'] },
  { input: path.join(rCjs,  'react-jsx-runtime.development.js'),   out: 'react-jsx-runtime.js', external: ['react'] },
  { input: path.join(rCjs,  'react-jsx-dev-runtime.development.js'), out: 'react-jsx-dev-runtime.js', external: ['react'] },
]

// Named exports to append post-bundle for each entry.
// @rollup/plugin-commonjs (current version) cannot statically resolve named exports from
// IIFE-wrapped CJS dev files.  After bundling, the main exports object is always named
// `xxxExports` (the last `var \w+Exports = require\w+()` before the default export line).
// We locate it via regex and append explicit named re-exports.
const knownNamedExports = {
  [path.join(rCjs, 'react.development.js')]: [
    'Children', 'Component', 'Fragment', 'Profiler', 'PureComponent', 'StrictMode',
    'Suspense', 'cloneElement', 'createContext', 'createElement', 'createRef',
    'forwardRef', 'isValidElement', 'lazy', 'memo', 'startTransition',
    'useCallback', 'useContext', 'useDebugValue', 'useDeferredValue', 'useEffect',
    'useId', 'useImperativeHandle', 'useInsertionEffect', 'useLayoutEffect', 'useMemo',
    'useReducer', 'useRef', 'useState', 'useSyncExternalStore', 'useTransition', 'version',
  ],
  [path.join(root, 'node_modules/react-dom/client.js')]: ['createRoot', 'hydrateRoot'],
  [path.join(rCjs, 'react-jsx-runtime.development.js')]: ['jsx', 'jsxs', 'Fragment'],
  [path.join(rCjs, 'react-jsx-dev-runtime.development.js')]: ['jsxDEV', 'Fragment'],
}

for (const { input, out, external } of bundles) {
  console.log(`bundling ${path.basename(input)} → public/vendor/${out}`)
  const bundle = await rollup({
    input,
    external,
    plugins: [
      replace({ 'process.env.NODE_ENV': '"development"', preventAssignment: true }),
      nodeResolve({ browser: true, rootDir: root }),
      commonjs({ transformMixedEsModules: true }),
    ],
  })
  const { output } = await bundle.generate({
    format: 'es',
    exports: 'named',
    generatedCode: 'es2015',
    intro: `/* pre-bundled by Rollup — esbuild-free */`,
    // Remap bare 'react' import → co-located react.js so the browser resolves it correctly
    paths: external.includes('react') ? { react: './react.js' } : undefined,
  })
  let code = output[0].code

  // Append named re-exports by locating the main CJS exports object variable.
  // Pattern: last occurrence of `var xxxExports = requireXxx();` just before the
  // `getDefaultExportFromCjs` call — that variable is the live exports object.
  const namedExps = knownNamedExports[input]
  if (namedExps) {
    const match = code.match(/var (\w+Exports) = \w+\(\);\n(?:const \w+ = \/\*@__PURE__\*\/getDefaultExportFromCjs)/)
    if (match) {
      const exportsVar = match[1]
      const lines = namedExps.map(n => `export const ${n} = ${exportsVar}.${n};`)
      code += '\n// named re-exports\n' + lines.join('\n') + '\n'
    } else {
      console.warn(`  ⚠ could not locate exports variable in ${out} — named exports skipped`)
    }
  }

  writeFileSync(path.join(outDir, out), code)
  await bundle.close()
  console.log(`  ✓ wrote public/vendor/${out}`)
}

console.log('vendor prebuild complete')
