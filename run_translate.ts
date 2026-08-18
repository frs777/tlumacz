import { generateChatResponse } from './src/utils/ai-client.js';
import fs from 'fs';

const [,, src, dest] = process.argv;

if (!src || !dest) {
  console.log("Użycie: npx tsx run_translate.ts <plik_zródłowy> <plik_docelowy>");
  process.exit(1);
}

async function run() {
  try {
    if (!fs.existsSync(src)) {
      console.error(`❌ Błąd: Plik źródłowy ${src} nie istnieje.`);
      process.exit(1);
    }

    const content = fs.readFileSync(src, 'utf-8');
    console.log(`Translating ${src} -> ${dest}...`);
    
    // Używamy naszego stabilnego silnika tłumaczącego
    const response = await generateChatResponse([
      { role: 'user', content: `Przetłumacz na polski, zachowując formatowanie markdown:\n\n${content}` }
    ]);
    
    fs.writeFileSync(dest, response);
    console.log(`✅ Zapisano: ${dest}`);
  } catch (error) {
    console.error('❌ Błąd:', error);
    process.exit(1);
  }
}

run();
