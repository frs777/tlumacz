import { generateChatResponse } from './src/utils/ai-client.js';
import fs from 'fs';
import path from 'path';

async function translate(inputPath: string, outputPath: string) {
  const absoluteInputPath = path.resolve(inputPath);
  console.log(`Przetwarzanie pliku: ${absoluteInputPath}...`);
  
  const content = fs.readFileSync(absoluteInputPath, 'utf8');
  
  // Przekazujemy treść bezpośrednio
  const prompt = `Przetłumacz poniższą treść na język polski, zachowując formatowanie markdown:\n\n${content}`;
  
  const response = await generateChatResponse([
    { role: 'user', content: prompt }
  ]);
  
  fs.writeFileSync(outputPath, response);
  console.log(`✅ Zapisano tłumaczenie do: ${outputPath}`);
}

const input = process.argv[2];
const output = process.argv[3];

if (!input || !output) {
  console.error("Użycie: npx tsx translate-file.ts <input_path> <output_path>");
  process.exit(1);
}

translate(input, output);
