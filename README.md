# Agentic CLI

> Enterprise-grade AI development assistant with comprehensive security, audit trails, and compliance-ready workflows

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

![Agentic](images/agentic.png)

## What is Agentic CLI?

Agentic CLI is an enterprise-focused AI development assistant designed for security-conscious organizations that need reproducible, auditable, and compliant AI-assisted development workflows. Perfect for regulated industries including healthcare, finance, defense, and government.

## Why Enterprise Teams Choose Agentic CLI

- **Zero Trust Security**: Sandboxed execution with comprehensive audit trails
- **Compliance Ready**: Full activity logging for SOX, HIPAA, SOC2 requirements
- **Human Oversight**: Mandatory approval gates prevent autonomous code changes
- **Reproducible Workflows**: Structured task templates eliminate AI inconsistency
- **Air-Gap Compatible**: Local-first design works in restricted environments



## Enterprise Use Cases

### Healthcare & Life Sciences
```bash
# Generate HIPAA-compliant data processing
agentic generate "Create patient data ETL with encryption and audit logging"

# Review for compliance before deployment
agentic review --compliance-check=hipaa

# Apply with full audit trail
agentic apply --audit-id=PROJ-2025-001
```

### Financial Services
```bash
# Generate SOX-compliant financial reporting
agentic generate "Create quarterly report generator with data lineage tracking"

# Multi-level approval workflow
agentic review --approver=security-team --approver=compliance-officer

# Deploy with change tracking
agentic apply --change-request=CR-2025-Q3-15
```

### Government & Defense
```bash
# Air-gapped development environment
agentic init --template=secure-python --offline-mode

# Generate with classification handling
agentic generate "Create secure document processor" --classification=confidential

# Mandatory security review
agentic review --security-scan --penetration-test
```

## Quick Start

```bash
# Install
pipx install agentic-cli

# Initialize enterprise project
agentic init --template=enterprise-python

# Generate with audit trail
agentic generate "Create FastAPI route for user authentication"

# Security review
agentic review --security-scan

# Approved deployment
agentic apply --audit-trail
```

## Core Concepts

### Task Templates
Instead of free-form prompts, Agentic CLI uses structured task templates that define:
- Input parameters and validation
- Output file patterns and locations  
- Code quality checks and tests
- Context requirements

### Sandboxed Generation
All AI-generated code is created in `.agentic/preview/` where you can:
- Review changes before applying
- Run tests and validation
- Modify generated code
- Reject or approve changes

### Human-in-the-Loop
Every workflow includes human checkpoints:
1. **Generate**: AI creates code based on your description
2. **Review**: You examine the generated code and tests
3. **Apply**: You explicitly approve changes to your project

## Project Status

**🚧 Active Development**: Core functionality implemented with CLI framework, sandbox security, and task templates. Currently refining enterprise features and gathering feedback from security-focused organizations.

### Current Status (Q3 2025)
- [x] Core CLI framework with Click
- [x] Sandboxed execution environment
- [x] Task template system with YAML configs
- [x] Human approval workflow (generate → review → apply)
- [x] LLM provider abstraction
- [ ] Enterprise audit dashboard
- [ ] Compliance reporting features
- [ ] RBAC integration

### Enterprise Roadmap
- **Q4 2025**: Enterprise pilot program with audit/compliance features
- **Q1 2026**: RBAC, SSO integration, and compliance reporting
- **Q2 2026**: Enterprise deployment and support tier

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Gateway   │────│ Security Layer  │────│ Audit Logger    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         v                       v                       v
┌─────────────────────────────────────────────────────────────────┐
│                   Core Orchestrator                             │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────────┐ │
│  │ Agent Manager │  │Context Engine │  │ Task Registry       │ │
│  └───────────────┘  └───────────────┘  └─────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
         │                       │                       │
         v                       v                       v
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Generator Agent │    │ Reviewer Agent  │    │ LLM Providers   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Security Model

Agentic CLI implements multiple security layers:

- **Input Sanitization**: All user inputs are validated and sanitized
- **Sandboxed Execution**: Generated code cannot access your filesystem directly
- **Output Validation**: All generated code is scanned for potential issues
- **Audit Trail**: Every operation is logged for review and debugging
- **Explicit Approval**: No changes are applied without your consent

## Contributing

This project is in early development. We welcome:

- **Feedback** on the core concepts and architecture
- **Use Case Examples** to help define the MVP scope
- **Security Review** of the proposed architecture
- **Technical Discussion** on implementation approaches

## Documentation

- [Product Requirements Document (PRD)](PRD.md) - Product vision and requirements
- [Software Design Document (SDD)](SDD.md) - Technical architecture and design
- [Claude Context (CLAUDE.md)](CLAUDE.md) - AI assistant context and guidelines

## License

MIT License - see [LICENSE](LICENSE) for details.

## Frequently Asked Questions

**Q: How is this different from GitHub Copilot or Cursor?**
A: Agentic CLI is designed for enterprise environments requiring security, compliance, and audit trails. Every operation is logged, code runs in sandboxes, and nothing changes without explicit approval - perfect for regulated industries.

**Q: What compliance standards does it support?**
A: Built-in audit logging supports SOX, HIPAA, SOC2, and similar requirements. All AI interactions, code generation, and approvals are tracked with timestamps and user attribution.

**Q: Can it work in air-gapped environments?**
A: Yes. Agentic CLI works entirely locally with optional cloud LLM integration. You can use local models or restricted API endpoints that meet your security requirements.

**Q: What's the current status?**
A: Core functionality is implemented and working. We're currently onboarding enterprise pilot customers to refine compliance and audit features.

---

*"The best tools disappear into the work. They amplify intention without adding noise, extend capability without creating dependency, and serve the user's goals without imposing their own agenda."*