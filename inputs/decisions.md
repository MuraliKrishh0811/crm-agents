D1 Backend language: Python
D2 Frontend: React (Vite + TypeScript)
D3 CRM store: SQLite local;
D4 Coding agent: Claude Code
D5 Ollama model: llama3.1:8b
D6 Teams agent: after the web dashboard
D7 Graph permissions: deferred for later
D8 Hosting: deferred for later

D5 CONFIRMED: machine is a MacBook Air M4 with 16 GB RAM. Use llama3.1:8b. Compare qwen3:8b against it using TR-8 later.
Keep the model name in OLLAMA_MODEL config. Keep prompts short and use a small context window.
The smoke test must include a warm-up call, because Ollama unloads idle models.
D7 DEFERRED: Graph permission set and approver are decided with IT when live access is requested.
In Phase 1, write the permission needs into docs/first_day_with_access.md as "to be confirmed". Do not scope permissions in code.
D8 DEFERRED: hosting is out of scope for Phase 1.
AUTHORITY: REQUIREMENTS.md is the source of truth. inputs/crm_scheduling_agents_project_description.txt is background only. If they differ, follow REQUIREMENTS.md.
ARCHITECTURE: docs/architecture/eraser-code.txt is the authoritative source. architecture.png is a rendered copy for human readers only.
