# Knowledge Graph Report: AgentCurator

## Overview
AgentCurator — personal AI research assistant with Chrome Extension frontend + Python FastMCP backend.

Corpus: 5 files (2 Python, 3 Markdown)
Graph: 30 nodes, 33 edges
Communities: 4
Token cost: 34,242 input

## Communities

### README & Setup
Setup, dependencies, build configuration (README.md, FastMCP, uvicorn, pnpm).

### Frontend (Manifest V3)
Chrome Extension frontend: Side Panel orchestrator, sidepanel.js, background.js, Gemini API binding.

### Backend Tools & API
Backend MCP tools: fetch_tech_news, manage_local_library, render_prefab_dashboard, CORS middleware.

### Project Architecture
Architecture docs: CLAUDE.md with constraints, deduplication logic, dynamic tool binding, iframe rendering strategy.

## God Nodes (High Connectivity)
- Python MCP Server (FastMCP)
- Tool Chaining Pattern
- sidepanel.js

## Suggested Questions
1. How do frontend and backend communicate?
2. What are the three core backend tools?
3. How does data flow through the system?

## Next Steps
Backend (main.py) complete. Frontend (Chrome Extension) not yet implemented.
