import { generateChatResponse } from './src/utils/ai-client.js';
import fs from 'fs';

async function batchTranslate() {
  const sourcePath = '/home/frs/.agents/web-performance-auditor.md';
  const targetPath = 'web-performance-auditor_pl.md';
  
  if (!fs.existsSync(sourcePath)) {
    console.error('❌ Plik źródłowy nie istnieje!');
    return;
  }

  const content = fs.readFileSync(sourcePath, 'utf-8');
  console.log('Translating content, please wait...');
  
  const prompt = `Translate the following markdown content to Polish. Maintain all original formatting (markdown syntax, headers, tables, etc.). Just return the translated content, no introduction or conclusion.\n\nContent:\n${content}`;

  try {
    // Używamy generateChatResponse bezpośrednio, aby uzyskać tekst tłumaczenia
    const response = await generateChatResponse([
      { role: 'user', content: prompt }
    ]);
    
    // Zapisujemy czystą odpowiedź modelu
    fs.writeFileSync(targetPath, response);
    console.log('✅ Plik przetłumaczony i zapisany do: ' + targetPath);
  } catch (error) {
    console.error('❌ Error:', error);
  }
}

batchTranslate();
