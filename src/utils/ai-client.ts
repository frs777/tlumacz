import { createOpenAI } from "@ai-sdk/openai";
import { generateText, LanguageModel, Message } from "ai";
import dotenv from "dotenv";

dotenv.config();

export const openai = createOpenAI({
  baseURL: process.env.OPENAI_BASE_URL,
  apiKey: process.env.OPENAI_API_KEY,
});

export const getLanguageModel = (modelName?: string): LanguageModel => {
  const model = modelName ?? (process.env.MODEL_NAME || "qwen2.5-coder:7b");
  return openai(model);
};

export interface ChatMessage {
  role: "user" | "assistant" | "tool";
  content: string;
}

export interface ToolCallbacks {
  onToolCall?: (toolName: string, args: any) => void;
  onToolResult?: (toolName: string, result: any) => void;
  onStatusChange?: (status: string) => void;
}

export async function generateChatResponse(
  messages: ChatMessage[],
  modelName?: string,
  _callbacks?: ToolCallbacks
): Promise<string> {
  const model = getLanguageModel(modelName);
  
  // Map ChatMessage to ai-sdk Message (which requires an 'id')
  // Map tool role to assistant, as generateText might not support tool role directly in this context
  const aiMessages: Message[] = messages.map((m, index) => ({
    id: index.toString(),
    role: (m.role === 'tool' ? 'assistant' : m.role) as 'user' | 'assistant' | 'system',
    content: m.content,
  }));

  let result = await generateText({
    model,
    system: `You are a professional technical translator and system assistant. 
Translate provided text into Polish.`,
    messages: aiMessages,
  });

  return result.text;
}
