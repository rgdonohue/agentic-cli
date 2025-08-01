# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is the **Agentic CLI Development Environment** - a CLI-first AI development assistant focused on secure, reproducible code generation. The project provides structured task templates, sandboxed execution, and human-in-the-loop workflows for AI-assisted development.

## Key Architecture Components

The system follows a modular architecture with these main components:

- **CLI Gateway** (`cli/`) - Command parsing and user interaction
- **Security Layer** (`security/`) - Sandboxed execution with audit trails
- **Context Engine** (`context/`) - Project context and documentation integration
- **Agent Framework** (`agents/`) - Core agents (Generator, Reviewer)
- **Task Registry** (`tasks/`) - Structured task definitions and templates
- **Documentation Index** (`docs/`) - Local project knowledge base

## Core CLI Commands

```bash
agentic init [--template=<name>]           # Project setup with templates
agentic generate <task> [--context=<path>] # Generate code/docs from task description
agentic review [--file=<path>]             # Review and validate generated content
agentic apply                              # Apply approved changes to project
agentic config [get|set] <key> [value]    # Configuration management
```

## Security Design Principles

- **Fail-Safe Defaults**: All operations are read-only unless explicitly approved
- **Sandboxed Execution**: File writes go to `.agentic/preview/` requiring user approval
- **Comprehensive Auditing**: Every action is logged, traceable, and auditable
- **Context Isolation**: Clear boundaries between user data, agent state, and external resources

## Development Workflow

All agent outputs require validation through:
1. Static analysis (mypy, ruff)
2. Security scanning
3. Test execution
4. User approval gates

The system prioritizes reproducibility, transparency, and developer control while leveraging AI capabilities.

## Task Templates

Structured task definitions provide:
- Input parameter schemas
- Output file patterns
- Validation commands
- Code templates
- Context requirements

## Agent Workflow

The system provides AI-assisted development through:
- Code generation from natural language (GeneratorAgent)
- Quality validation and review (ReviewerAgent)
- Human approval gates for all changes
- Incremental development support

## Development Approach

- MVP-first development (core generation capabilities)
- Security-by-design with sandboxed execution
- Local-first with optional cloud features
- Extensible task template system
- Community-driven task library