import { generateChatResponse } from './src/utils/ai-client.js';
import fs from 'fs';
import path from 'path';

async function batchTranslate() {
  const sourcePath = '/home/frs/.agents/web-performance-auditor.md';
  const targetPath = 'web-performance-auditor_pl.md';
  const content = fs.readFileSync(sourcePath, 'utf-8');
  
  console.log('Translating content...');
  
  const prompt = `Translate the following markdown content to Polish. Maintain all original formatting, markdown syntax, and structure.
  
  Content:
  ${content}
  `;

  try {
    const response = await generateChatResponse([
      { role: 'user', content: prompt }
    ]);
    
    fs.writeFileSync(targetPath, response);
    console.log('✅ File translated and saved to ' + targetPath);
  } catch (error) {
    console.error('❌ Error:', error);
  }
}

batchTranslate();
