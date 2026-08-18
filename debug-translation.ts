import { generateChatResponse } from './src/utils/ai-client.js';

async function debugTranslation() {
  const userPrompt = "przetumacz na polski zachowujac formatowanie /home/frs/.agents/web-performance-auditor.md do web-performance-auditor_pl.md";
  console.log(`User Prompt: ${userPrompt}
`);

  try {
    // We simulate the call from the App component
    const response = await generateChatResponse([
      { role: 'user', content: userPrompt }
    ], undefined, {
      onToolCall: (name, args) => console.log(`[TOOL CALL] ${name}: ${JSON.stringify(args)}`),
      onToolResult: (name, result) => console.log(`[TOOL RESULT] ${name}: ${JSON.stringify(result).substring(0, 100)}...`),
      onStatusChange: (status) => console.log(`[STATUS] ${status}`),
    });

    console.log('
--- FINAL RESPONSE ---');
    console.log(response);
    console.log('----------------------');
  } catch (error) {
    console.error('❌ ERROR:', error);
  }
}

debugTranslation();
