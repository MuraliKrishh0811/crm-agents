# CRM Agents project

Read REQUIREMENTS.md and inputs/decisions.md before any planning or coding.
Hard rules: R1-R12 in REQUIREMENTS.md.

- Never open, print or search any .env file yourself. The app's own settings loader may read it when tests run (see R7).
- All code is real. Never stub agents, providers or API calls. Never hardcode responses.
- Local mode (Ollama, .eml files, mock calendar) is the working system in Phase 1.
- Always make a plan first and wait for approval. Work in small slices; run tests after each.
- Verify Microsoft Graph, Agent Framework, Azure OpenAI and Ollama details against current docs.
  Never rely on memory. Mark anything unverified.
- Never commit. The owner commits after tests and the smoke test pass. Show git status and propose a message.
