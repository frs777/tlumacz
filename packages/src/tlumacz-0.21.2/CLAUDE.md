# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Translator Agent** - an AI-powered intelligent translation CLI tool that supports text, file, and web page translation. The project is built with TypeScript, React, and Ink to provide an interactive terminal interface.

## Project Status

**IMPORTANT**: This project is currently in initial development phase. The repository contains only documentation files in `/docs/` directory. The entire application needs to be built from scratch according to the specifications.

## Development Commands

Once the project is set up, use these commands:

```bash
npm run dev      # Run the CLI in development mode using tsx
npm run build    # Build production CLI  
npm start        # Run the built CLI
npx tsx src/cli.tsx  # Direct TypeScript execution
```

## Architecture Guidelines

### Core Technologies
- **Runtime**: Node.js v20+
- **Language**: TypeScript
- **UI Framework**: React + Ink (for terminal UI)
- **AI Integration**: ai sdk (for translation functionality)

### Expected Project Structure
```
src/
├── cli.tsx           # Main CLI entry point
├── components/       # React/Ink UI components
│   ├── App.tsx      # Main application component
│   ├── MessageHistory.tsx
│   ├── InputBox.tsx
│   └── StatusLine.tsx
├── services/        # Core business logic
│   ├── translator.ts
│   └── ai-client.ts
├── utils/           # Utility functions
└── types/           # TypeScript type definitions
```

### UI Layout Requirements
1. **Welcome Message** - Display at the top on startup
2. **Message History** - Central scrollable area showing conversation
3. **Input Box** - Bottom area for user input
4. **Status Line** - Below input box for errors/status messages

### Key Features to Implement
- Automatic input type detection (text/file/URL)
- Interactive terminal interface with React + Ink
- Command system for various operations
- Configuration support (default language, vocabulary, themes)
- Support for multiple input sources

## Development Workflow

1. **After Each Feature**: Run `npm run dev` to ensure functionality
2. **Update Changelog**: Maintain changelog for all feature updates
3. **Git Commits**: Include original prompt/requirements in commit messages

## Important Reminders

- The project needs full initialization including package.json, tsconfig.json, and all source files
- Focus on creating a functional CLI with proper error handling
- Ensure the terminal UI is responsive and user-friendly
- Implement proper TypeScript types throughout the codebase
- Use `npm i <package>` to install package
- Always run `npm run dev` to test if it works
- Always bump version after you finish
- Alwasy commit you changes after you finish

## Testing Approach

Once the project is set up, implement:
- Unit tests for translation services
- Integration tests for CLI commands
- UI component testing with React Testing Library adapted for Ink

## Configuration

The application should support configuration for:
- Default target language
- Custom vocabulary/glossaries
- UI themes
- API settings for the AI SDK

## Command System

Implement a command system that supports:
- Direct text translation
- File translation (with path input)
- URL translation (fetch and translate web content)
- Configuration commands
- Help and documentation commands