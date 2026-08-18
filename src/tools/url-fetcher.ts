import { z } from "zod";
import TurndownService from "turndown";
import { Tool, ToolInput, ToolResult } from "./types";

export interface UrlFetcherInput extends ToolInput {
  url: string;
}

export interface UrlFetcherResult {
  url: string;
  content: string;
  title: string;
}

export class UrlFetcherTool implements Tool<UrlFetcherInput> {
  name = "url_fetcher";
  description = "Fetch content from HTTP(S) URLs and convert HTML to Markdown";
  
  inputSchema = z.object({
    url: z.string().url().describe("The HTTP(S) URL to fetch content from")
  });

  private turndownService: any;

  constructor() {
    this.turndownService = new TurndownService({
      headingStyle: 'atx',
      codeBlockStyle: 'fenced'
    });
  }

  async prompt(input: UrlFetcherInput): Promise<string> {
    return `Fetching content from URL: ${input.url}`;
  }

  async* call(
    input: UrlFetcherInput,
    context: { abortController: AbortController; options: { isNonInteractiveSession: boolean } }
  ): AsyncGenerator<ToolResult, void, unknown> {
    try {
      const { url } = input;
      
      // Validate URL format
      if (!url.startsWith('http://') && !url.startsWith('https://')) {
        throw new Error('URL must start with http:// or https://');
      }

      const response = await fetch(url, {
        signal: context.abortController.signal,
        headers: {
          'User-Agent': 'Mozilla/5.0 (compatible; TranslatorAgent/1.0)'
        }
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const contentType = response.headers.get('content-type') || '';
      if (!contentType.includes('text/html')) {
        throw new Error(`Content type '${contentType}' is not supported. Only HTML content can be processed.`);
      }

      const html = await response.text();
      
      // Extract title from HTML
      const titleMatch = html.match(/<title[^>]*>([^<]+)<\/title>/i);
      const title = titleMatch ? titleMatch[1].trim() : new URL(url).hostname;

      // Convert HTML to Markdown
      const markdown = this.turndownService.turndown(html);

      const result: UrlFetcherResult = {
        url,
        content: markdown,
        title
      };

      yield {
        type: 'url_fetched',
        data: result
      };
    } catch (error) {
      yield {
        type: 'error',
        data: {
          message: error instanceof Error ? error.message : 'Unknown error occurred',
          url: input.url
        }
      };
    }
  }
}