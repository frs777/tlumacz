import { getLanguageModel } from './src/utils/ai-client.js';
import { generateText } from 'ai';
import fs from 'fs';

async function simpleTranslate() {
  const content = fs.readFileSync('/home/frs/.agents/web-performance-auditor.md', 'utf-8');
  console.log('Model is generating translation...');

  const model = getLanguageModel();
  
  const { text } = await generateText({
    model: model,
    prompt: `Przetłumacz poniższy tekst na język polski, zachowując formatowanie markdown. Zwróć tylko przetłumaczony tekst.\n\n${content}`
  });

  fs.writeFileSync('web-performance-auditor_pl.md', text);
  console.log('✅ Zapisano!');
}

simpleTranslate();
