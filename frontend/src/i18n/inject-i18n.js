#!/usr/bin/env node
/**
 * AXONHIS i18n Injector
 * Injects useTranslation hook into all pages that don't have it yet.
 * Adds the import and `const { t } = useTranslation();` inside the component.
 */
const fs = require('fs');
const path = require('path');

const DASHBOARD_DIR = path.join(__dirname, '..', 'app', 'dashboard');

// Find all page.tsx files recursively
function findPages(dir) {
  let results = [];
  const items = fs.readdirSync(dir, { withFileTypes: true });
  for (const item of items) {
    const fullPath = path.join(dir, item.name);
    if (item.isDirectory()) {
      results = results.concat(findPages(fullPath));
    } else if (item.name === 'page.tsx') {
      results.push(fullPath);
    }
  }
  return results;
}

const pages = findPages(DASHBOARD_DIR);
let updated = 0;
let skipped = 0;

for (const pagePath of pages) {
  let content = fs.readFileSync(pagePath, 'utf-8');
  
  // Skip if already has useTranslation
  if (content.includes('useTranslation')) {
    skipped++;
    continue;
  }
  
  // 1. Add the import after "use client"; or at the top
  const importLine = 'import { useTranslation } from "@/i18n";\n';
  
  if (content.includes('"use client"')) {
    content = content.replace('"use client";', '"use client";\n' + importLine);
  } else if (content.includes("'use client'")) {
    content = content.replace("'use client';", "'use client';\n" + importLine);
  } else {
    // Add "use client" directive and import at top
    content = '"use client";\n' + importLine + '\n' + content;
  }
  
  // 2. Add `const { t } = useTranslation();` inside the default export component
  // Match: export default function XxxPage() {
  const funcMatch = content.match(/(export\s+default\s+function\s+\w+\s*\([^)]*\)\s*\{)/);
  if (funcMatch) {
    const insertion = funcMatch[1] + '\n  const { t } = useTranslation();';
    content = content.replace(funcMatch[1], insertion);
  }
  
  fs.writeFileSync(pagePath, content);
  updated++;
  const rel = path.relative(DASHBOARD_DIR, pagePath);
  console.log(`✅ Injected i18n into: ${rel}`);
}

console.log(`\n📊 Summary: ${updated} pages updated, ${skipped} already had i18n`);
console.log(`📊 Total pages processed: ${pages.length}`);
