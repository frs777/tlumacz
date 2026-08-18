import React, {useState} from 'react';
import {Box, Text, useApp} from 'ink';
import {MessageHistory} from './MessageHistory.js';
import {InputBox} from './InputBox.js';
import {StatusLine} from './StatusLine.js';
import {generateChatResponse, ChatMessage, ToolCallbacks} from '../utils/ai-client.js';

export interface Message {
  id: string;
  text: string;
  timestamp: Date;
  role: 'user' | 'assistant' | 'tool';
  toolName?: string;
  toolCall?: boolean;
}

export const App: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [status, setStatus] = useState<string>('');
  const [toolStatus, setToolStatus] = useState<string>('');
  const {exit} = useApp();

  const handleSubmit = async (text: string) => {
    if (text.trim()) {
      // Check for exit commands
      if (text.trim().toLowerCase() === 'exit' || text.trim().toLowerCase() === 'quit') {
        exit();
        return;
      }
      
      const userMessage: Message = {
        id: Date.now().toString(),
        text: text.trim(),
        timestamp: new Date(),
        role: 'user',
      };
      setMessages(prev => [...prev, userMessage]);
      setStatus('Sending message to AI...');
      setIsLoading(true);
      
      try {
        // Convert messages to ChatMessage format
        const chatMessages: ChatMessage[] = [...messages, userMessage].map(msg => ({
          role: msg.role as 'user' | 'assistant' | 'tool',
          content: msg.text,
        }));
        
        const callbacks: ToolCallbacks = {
          onToolCall: (toolName: string) => {
            setToolStatus(`Calling ${toolName} tool...`);
          },
          onToolResult: (toolName: string, result: any) => {
            const toolMessage: Message = {
              id: `tool-${Date.now()}`,
              text: JSON.stringify(result, null, 2),
              timestamp: new Date(),
              role: 'tool',
              toolName,
            };
            setMessages(prev => [...prev, toolMessage]);
            setToolStatus('');
          },
          onStatusChange: (status: string) => {
            setToolStatus(status);
          },
        };
        
        const response = await generateChatResponse(chatMessages, undefined, callbacks);
        
        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          text: response,
          timestamp: new Date(),
          role: 'assistant',
        };
        
        setMessages(prev => [...prev, assistantMessage]);
        setStatus('Response received');
        setTimeout(() => setStatus(''), 3000);
      } catch (error) {
        setStatus(`Error: ${error instanceof Error ? error.message : 'Failed to get response'}`);
        setTimeout(() => setStatus(''), 5000);
      } finally {
        setIsLoading(false);
        setToolStatus('');
      }
    }
  };

  return (
    <Box flexDirection="column" height="100%">
      <Box borderStyle="round" borderColor="green" paddingX={1}>
        <Text color="green" bold>
          🌍 Welcome to Translator Agent v0.4.0
        </Text>
      </Box>
      
      <MessageHistory messages={messages} />
      
      <InputBox onSubmit={handleSubmit} />
      
      <StatusLine status={status} isLoading={isLoading} toolStatus={toolStatus} />
    </Box>
  );
};