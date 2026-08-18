import { generateChatResponse } from './src/utils/ai-client.js';
import fs from 'fs';
import path from 'path';

async function testToolCalling() {
  console.log('Testing Tool Calling with updated prompt...');
  
  const testFilePath = path.join(process.cwd(), 'test-translation.txt');
  fs.writeFileSync(testFilePath, 'Hello world, this is a test file for tool calling.');

  try {
    const response = await generateChatResponse([
      { role: 'user', content: `Translate this file to Polish: ${testFilePath}` }
    ]);
    
    console.log('--- AI Response ---');
    console.log(response);
    console.log('------------------');

    if (response.includes('{') && response.includes('file_reader')) {
      console.error('❌ FAILURE: Model still returned JSON tool call as text!');
      process.exit(1);
    } else if (response.toLowerCase().includes('cześć') || response.toLowerCase().includes('test') || response.toLowerCase().includes('świat')) {
      console.log('✅ SUCCESS: Model performed tool call and returned translation!');
    } else {
      console.log('⚠️ UNCERTAIN: Response received but not clearly a translation.');
      console.log('Response was:', response);
    }
  } catch (error) {
    console.error('❌ ERROR during execution:', error);
    process.exit(1);
  } finally {
    if (fs.existsSync(testFilePath)) {
      fs.unlinkSync(testFilePath);
    }
  }
}

testToolCalling();
