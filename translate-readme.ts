import { generateChatResponse } from './src/utils/ai-client.js';
import fs from 'fs';

async function translate() {
  const content = fs.readFileSync('README.md', 'utf-8');
  console.log('Translating README.md...');
  
  const response = await generateChatResponse([
    { role: 'user', content: `Przetłumacz na polski, zachowując formatowanie markdown:\n\n${content}` }
  ]);
  
  fs.writeFileSync('README_PL.md', response);
  console.log('✅ Zapisano do README_PL.md');
}

translate();
