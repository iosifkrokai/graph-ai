// Browser driver for the Graph AI web app (frontend :3000 + backend :5000).
//
// Drives the real running stack with a headless Playwright Chromium:
// registers/logs in a user through the UI and screenshots the auth screen
// and the workflow-builder canvas. Screenshots land in ./shots/.
//
// Usage (from this skill dir, after `npm install && npx playwright install chromium`):
//   node driver.mjs                      # default flow, demo@graph.ai
//   node driver.mjs --email a@b.co --password secret123
//   BASE=http://localhost:3000 node driver.mjs
//
// Exit code is non-zero if any step fails, so it doubles as a smoke test.

import { chromium } from 'playwright'
import { mkdirSync } from 'node:fs'
import { dirname, join } from 'node:path'
import { fileURLToPath } from 'node:url'

const HERE = dirname(fileURLToPath(import.meta.url))
const SHOTS = join(HERE, 'shots')
mkdirSync(SHOTS, { recursive: true })

const BASE = process.env.BASE ?? 'http://localhost:3000'

function arg(flag, fallback) {
  const i = process.argv.indexOf(flag)
  return i !== -1 && process.argv[i + 1] ? process.argv[i + 1] : fallback
}

// A fresh-ish email each run avoids "already registered" collisions while
// staying deterministic within a run (no Math.random needed).
const stamp = process.env.STAMP ?? String(process.pid)
const email = arg('--email', `demo+${stamp}@graph.ai`)
const password = arg('--password', 'demopass123')

async function shot(page, name) {
  const path = join(SHOTS, `${name}.png`)
  await page.screenshot({ path, fullPage: false })
  console.log(`  📸 ${path}`)
}

let pageRef = null

async function main() {
  const browser = await chromium.launch()
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } })
  pageRef = page
  page.on('console', (m) => {
    if (m.type() === 'error') console.log(`  [console.error] ${m.text()}`)
  })

  console.log(`→ open ${BASE}`)
  await page.goto(BASE, { waitUntil: 'networkidle' })
  await page.getByRole('heading', { name: /pixel flow studio/i }).waitFor()
  await shot(page, '01-auth')

  // Register the user (Register tab). On success the app auto-logs-in
  // (handleRegister → handleLogin in useAuthSession).
  console.log(`→ register ${email}`)
  await page.getByRole('button', { name: 'Register', exact: true }).click()
  await page.getByPlaceholder('you@graph.ai').fill(email)
  await page.getByPlaceholder('••••••••').fill(password)
  await page.getByRole('button', { name: 'Create Account' }).click()

  // Post-auth the builder shell renders. The email is NOT in the top bar
  // (it lives inside the closed Profile dropdown), so wait on the "Settings"
  // top-bar button, which only exists once authenticated.
  console.log('→ wait for workflow builder')
  await page.getByRole('button', { name: 'Settings', exact: true }).waitFor({ timeout: 15000 })
  await page.waitForTimeout(500)
  await shot(page, '02-builder')

  // Create a workflow: fill the "New workflow" input in the sidebar + click Add.
  console.log('→ create a workflow')
  await page.getByPlaceholder('New workflow').fill('Demo Flow')
  await page.getByRole('button', { name: 'Add', exact: true }).click()
  await page.getByText('Demo Flow').first().waitFor({ timeout: 10000 })
  await page.waitForTimeout(500)
  await shot(page, '03-workflow')

  console.log('✓ driver flow complete')
  await browser.close()
}

main().catch(async (err) => {
  console.error('✗ driver failed:', err.message)
  if (pageRef) await shot(pageRef, 'error').catch(() => {})
  process.exit(1)
})
