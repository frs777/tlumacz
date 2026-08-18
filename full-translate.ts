import { getLanguageModel } from './src/utils/ai-client.js';
import { generateText } from 'ai';
import fs from 'fs';

async function fullTranslate() {
  const sourcePath = '/home/frs/.agents/web-performance-auditor.md';
  const targetPath = 'web-performance-auditor_pl.md';
  
  if (!fs.existsSync(sourcePath)) {
    console.error('❌ Plik źródłowy nie istnieje!');
    return;
  }

  const content = fs.readFileSync(sourcePath, 'utf-8');
  // Dzielimy na większe części, aby zachować kontekst, ale mieścić się w oknie modelu
  const CHUNK_SIZE = 2000;
  // Dzielenie przyjazne dla markdownu (szukanie końca linii lub akapitu)
  const chunks = content.match(/[\s\S]{1,2000}(\n|$)/g) || [content];
  
  console.log(`Zaczynam tłumaczenie ${chunks.length} części...`);
  
  let translatedContent = '';
  const model = getLanguageModel();
  
  for (let i = 0; i < chunks.length; i++) {
    console.log(`Tłumaczę część ${i + 1}/${chunks.length}...`);
    try {
      const { text } = await generateText({
        model: model,
        prompt: `Jesteś profesjonalnym tłumaczem technicznym. Przetłumacz poniższy fragment dokumentu markdown na język polski. Zachowaj dokładnie formatowanie markdown (nagłówki, tabele, linki, style). Zwróć tylko przetłumaczony tekst, bez wstępu i podsumowania:\n\n${chunks[i]}`
      });
      translatedContent += text;
    } catch (error) {
      console.error(`❌ Błąd przy tłumaczeniu części ${i + 1}:`, error);
      translatedContent += chunks[i]; // W razie błędu zachowaj oryginał
    }
  }

  fs.writeFileSync(targetPath, translatedContent);
  console.log('✅ Całość przetłumaczona i zapisana do: ' + targetPath);
}

fullTranslate();
