import { z } from "zod";
import { readFile } from "fs/promises";
import { extname } from "path";
import { Tool, ToolInput, ToolResult } from "./types";

export interface FileReaderInput extends ToolInput {
  filePath: string;
}

export interface FileReaderResult {
  filename: string;
  content: string;
}

export class FileReaderTool implements Tool<FileReaderInput> {
  name = "file_reader";
  description = "Read local text files (.md, .txt, .html, etc.) and return structured content";
  
  inputSchema = z.object({
    filePath: z.string().describe("The local file path to read")
  });

  async prompt(input: FileReaderInput): Promise<string> {
    return `Reading file: ${input.filePath}`;
  }

  async* call(
    input: FileReaderInput,
    _context: { abortController: AbortController; options: { isNonInteractiveSession: boolean } }
  ): AsyncGenerator<ToolResult, void, unknown> {
    try {
      const { filePath } = input;
      const ext = extname(filePath).toLowerCase();
      
      const supportedExtensions = ['.md', '.txt', '.html', '.htm', '.json', '.js', '.ts', '.css', '.xml', '.csv'];
      if (!supportedExtensions.includes(ext)) {
        throw new Error(`Unsupported file type: ${ext}. Supported types: ${supportedExtensions.join(', ')}`);
      }

      const content = await readFile(filePath, 'utf-8');
      const filename = filePath.split('/').pop() || filePath;

      // Chunk the content to avoid context window issues
      const CHUNK_SIZE = 3000;
      const chunks: string[] = [];
      for (let i = 0; i < content.length; i += CHUNK_SIZE) {
        chunks.push(content.substring(i, i + CHUNK_SIZE));
      }

      for (let i = 0; i < chunks.length; i++) {
        const result: FileReaderResult = {
          filename: `${filename} (part ${i + 1}/${chunks.length})`,
          content: chunks[i]
        };

        yield {
          type: 'file_read',
          data: result
        };
      }
    } catch (error) {
      yield {
        type: 'error',
        data: {
          message: error instanceof Error ? error.message : 'Unknown error occurred',
          filePath: input.filePath
        }
      };
    }
  }
}