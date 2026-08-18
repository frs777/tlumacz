import { generateChatResponse } from './src/utils/ai-client.js';
import fs from 'fs';
import path from 'path';

async function debugTranslation() {
  const userPrompt = "przetumacz na polski zachowujac formatowanie /home/frs/.agents/web-performance-auditor.md do web-performance-auditor_pl.md";
  console.log(`User Prompt: ${userPrompt}\n`);

  try {
    // Symulujemy cykl pracy agenta
    // 1. Wysyłamy prompt
    console.log('[1/3] Wysyłanie zapytania...');
    const response = await generateChatResponse([
      { role: 'user', content: userPrompt }
    ], undefined, {
      onToolCall: (name, args) => console.log(`[TOOL CALL] Wywołuję narzędzie: ${name} z argumentami: ${JSON.stringify(args)}`),
      onToolResult: (name, result) => console.log(`[TOOL RESULT] Wynik ${name} odebrany.`),
      onStatusChange: (status) => console.log(`[STATUS] ${status}`),
    });

    console.log('\n[2/3] Sprawdzanie czy plik istnieje...');
    const targetFilePath = path.join(process.cwd(), 'web-performance-auditor_pl.md');
    
    if (fs.existsSync(targetFilePath)) {
      console.log('✅ Plik istnieje!');
      const content = fs.readFileSync(targetFilePath, 'utf-8');
      console.log(`[3/3] Treść pliku (pierwsze 200 znaków):\n${content.substring(0, 200)}...`);
    } else {
      console.log('❌ Plik nie został utworzony.');
      console.log('Odpowiedź AI była:', response);
    }

  } catch (error) {
    console.error('❌ BŁĄD:', error);
  }
}

debugTranslation();
