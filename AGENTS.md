# Spelling Coach Development Instructions

## Mission

Help Derek design, build, test, review, and document the
Reading and Spelling Coach.

This is also a learning project. Explain important work in
clear, plain language.

Existing project decisions, documentation, and approved code
must be respected.

## Current Development Phase

- Design, code, and automated testing may begin now.
- Do not deploy the completed system to the old computer yet.
- Deployment waits until the graphics card and server are ready.
- Derek must approve deployment.
- Design the software now for the future local AI server.
- Avoid choices that would require rebuilding the application
  when the GPU is installed.

## Human Approval Rules

- Work on one small, clearly defined task at a time.
- Explain the proposed task before changing important code.
- State which files are expected to change.
- Do not merge anything into the main branch without Derek's
  explicit approval.
- Do not deploy, delete major files, change repository settings,
  or perform destructive actions without explicit approval.
- Do not overwrite existing work without explaining why.
- Stop and ask when requirements are unclear or conflicting.

## Review and Learning Requirements

After completing a task, report:

1. What was changed.
2. Which files were changed.
3. Why each change was needed.
4. How the important code works.
5. Which tests were run.
6. Whether every test passed.
7. Any errors, risks, or unfinished work.
8. What decision Derek needs to make next.

Use clear explanations suitable for someone learning Python,
software development, Git, testing, and cybersecurity.

## Architecture Requirements

Keep major parts separate whenever practical:

- User interface
- Spelling and reading lesson logic
- Word and lesson data
- User progress storage
- Text-to-speech
- Speech recognition
- AI coaching
- AI model provider
- Authentication
- Logging
- Backups
- Administrative controls

The AI system must use a replaceable provider layer.

It should eventually support:

- A temporary cloud model
- A small CPU-based local model
- A future GPU-powered local model
- Ollama or another compatible local model server

Changing the AI provider should not require rebuilding the
whole application.

## Coding Requirements

- Prefer readable, beginner-friendly Python.
- Use clear variable and function names.
- Keep functions focused on one responsibility.
- Add type hints where they improve understanding.
- Add comments only when they explain something important.
- Avoid unnecessary packages and complicated frameworks.
- Preserve backward compatibility unless a change is approved.
- Add or update tests whenever behavior changes.
- Run existing tests before declaring a task complete.
- Never hide a failed test.

## Accessibility Requirements

Accessibility is a core feature, not an optional extra.

The application should support:

- Dyslexia-friendly layouts
- Clear language
- Adjustable text size and spacing
- Simple navigation
- Keyboard access
- Read-aloud controls
- Repeat-word controls
- Slower pronunciation
- Encouraging correction messages
- Minimal screen clutter
- Clear progress information

## Security and Privacy Requirements

- Never place passwords, API keys, tokens, or private credentials
  in the repository.
- Never use real student records as test data.
- Validate untrusted input.
- Use limited permissions.
- Protect saved progress and account information.
- Keep secrets in environment variables or approved secret stores.
- Do not expose the future server directly to the internet without
  an approved security plan.
- Report security concerns instead of silently ignoring them.

## Git and Deployment Rules

- Keep the main branch stable.
- Use a separate branch for development work.
- Make small, understandable changes.
- Do not push or merge local work without approval.
- Do not deploy to the old server until the hardware, operating
  system, AI runtime, backups, and recovery plan are ready.
