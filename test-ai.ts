import { generateChatResponse } from './src/utils/ai-client.js';

async function test() {
  console.log('Testing connection to local LLM...');
  try {
    const response = await generateChatResponse([
      { role: 'user', content: 'Hello! Are you working?' }
    ]);
    console.log('Response from AI:', response);
    console.log('✅ Connection successful!');
  } catch (error) {
    console.error('❌ Connection failed:', error);
    process.exit(1);
  }
}

test();
