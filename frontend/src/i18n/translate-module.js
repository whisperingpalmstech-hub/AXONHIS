const fs = require('fs');
const path = require('path');
const { translate } = require('@vitalets/google-translate-api');

const en = JSON.parse(fs.readFileSync(path.join(__dirname, 'locales/en.json'), 'utf8'));
const LANGUAGES = ['hi', 'mr', 'es', 'fr', 'de', 'ar', 'zh', 'ja', 'pt', 'ru'];

async function translateModule(moduleName) {
  if (!en[moduleName]) {
    console.error(`Module ${moduleName} not found in en.json`);
    return;
  }

  const moduleKeys = Object.entries(en[moduleName]);
  console.log(`Translating module: ${moduleName} (${moduleKeys.length} keys)`);

  for (const lang of LANGUAGES) {
    const localeFile = path.join(__dirname, `locales/${lang}.json`);
    let trData = {};
    if (fs.existsSync(localeFile)) {
      trData = JSON.parse(fs.readFileSync(localeFile, 'utf8'));
    }
    
    if (!trData[moduleName]) trData[moduleName] = {};

    console.log(`  Language: ${lang}`);
    for (const [key, value] of moduleKeys) {
      if (typeof value === 'object') continue; // Skip nested objects for now or handle them
      
      // Skip if already translated (not same as English or different from placeholder)
      if (trData[moduleName][key] && trData[moduleName][key] !== value) {
        // console.log(`    Skipping key: ${key}`);
        continue;
      }

      try {
        console.log(`    Translating key: ${key} -> ${value}`);
        const res = await translate(value, { to: lang });
        trData[moduleName][key] = res.text;
        // Wait a bit to avoid rate limiting
        await new Promise(r => setTimeout(r, 500)); 
      } catch (err) {
        console.error(`    Error translating ${key} to ${lang}:`, err.message);
        if (err.message.includes('Too Many Requests')) {
            console.log('    Rate limited. Stopping for this language.');
            break;
        }
      }
    }
    fs.writeFileSync(localeFile, JSON.stringify(trData, null, 2) + '\n');
  }
}

const moduleToProcess = process.argv[2];
if (moduleToProcess) {
    translateModule(moduleToProcess);
} else {
    console.error('Please provide a module name as argument.');
}
