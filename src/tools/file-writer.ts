import { z } from "zod";
import { writeFile } from "fs/promises";
import { Tool, ToolInput, ToolResult } from "./types";

export interface FileWriterInput extends ToolInput {
  filePath: string;
  content: string;
}

export interface FileWriterResult {
  filePath: string;
  status: 'success';
}

export class FileWriterTool implements Tool<FileWriterInput> {
  name = "file_writer";
  description = "Write text content to a local file. Use this to save translations or reports.";
  
  inputSchema = z.object({
    filePath: z.string().describe("The local file path to write to"),
    content: z.string().describe("The text content to write to the file")
  });

  async prompt(input: FileWriterInput): Promise<string> {
    return `Writing content to file: ${input.filePath}`;
  }

  async* call(
    input: FileWriterInput,
    _context: { abortController: AbortController; options: { isNonInteractiveSession: boolean } }
  ): AsyncGenerator<ToolResult, void, unknown> {
    try {
      const { filePath, content } = input;
      
      await writeFile(filePath, content, 'utf-8');

      const result: FileWriterResult = {
        filePath,
        status: 'success'
      };

      yield {
        type: 'file_written',
        data: result
      };
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
