# Reference sources (authoritative, in priority order)

| Topic                                 | URL                                                                        | Pinned version / notes                                                                            |
| ------------------------------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- |
| Microsoft Agent Framework docs        | https://learn.microsoft.com/en-us/agent-framework/                         | Start here.                                                                                       |
| Microsoft Agent Framework repo        | https://github.com/microsoft/agent-framework                               | agent-framework 1.22.0, agent-framework-openai 1.17.0, agent-framework-ollama 1.0.0b261015 (beta) |
| Agent Framework Foundry client (PyPI) | https://pypi.org/project/agent-framework-foundry/                          | agent-framework-foundry 1.15.0                                                                    |
| Azure Identity (PyPI)                 | https://pypi.org/project/azure-identity/                                   | azure-identity 1.26.0                                                                             |
| Agent Framework Python changelog      | https://github.com/microsoft/agent-framework/blob/main/python/CHANGELOG.md | Read the raw file. Focus on entries for the packages we use.                                      |
| Azure AI Foundry / Azure OpenAI       | https://learn.microsoft.com/en-us/azure/foundry/                           | Old URL redirects here.                                                                           |
| Microsoft Graph                       | https://learn.microsoft.com/en-us/graph/                                   | msgraph-sdk 1.64.0. All Graph code UNVERIFIED.                                                    |
| Ollama docs                           | https://docs.ollama.com                                                    |                                                                                                   |
| Ollama repo                           | https://github.com/ollama/ollama                                           |                                                                                                   |
| Ollama Python client                  | https://github.com/ollama/ollama-python                                    | ollama 0.6.3. Use the raw README for verbatim snippets.                                           |
| Claude Code settings                  | https://code.claude.com/docs/en/settings                                   | Old docs.claude.com URL redirects here.                                                           |
| Taste skill (UI quality)              | https://github.com/Leonxlnx/taste-skill                                    | v2.0.0, commit f624f37. Reference only.                                                           |
| Graphify (context management)         | https://github.com/Graphify-Labs/graphify                                  | graphifyy 0.9.91 (PyPI, double y). No GitHub releases. Reference only.                            |
| pytest (PyPI)                         | https://pypi.org/project/pytest/                                           | pytest 9.1.1 (test-only dependency)                                                               |
| pytest docs                           | https://docs.pytest.org/en/latest/                                         |                                                                                                   |

Rules:

- Official docs win over blogs, samples and forums.
- If a page cannot be fetched, report it and stop on that item. Do not substitute memory.
- Record the date each source was read.
- Pin exact versions (no ranges). Do not upgrade without a reason recorded in decisions.md.

Install note: do not install the agent-framework meta-package. It pulls in agent-framework-ollama, which requires ollama<0.5.4. Install the exact set: agent-framework-core 1.22.0, agent-framework-foundry 1.15.0, agent-framework-openai 1.17.0, azure-identity 1.26.0, ollama 0.6.3, msgraph-sdk 1.64.0.

Test-only: pytest 9.1.1. Not part of the runtime install set.
