# Repository Guidelines

## Project Structure & Module Organization

This workspace currently contains no source code, datasets, tests, or build configuration. Hidden environment directories (`.agents/`, `.codex/`, `.aws/`, and `.git/`) are not application modules; leave them unchanged.

As the project develops, group related files by purpose. Suggested directories are `src/` for processing code, `tests/` for automated checks, `data/` for election inputs and outputs, and `docs/` for methodology. These are proposed conventions, not existing directories. Document the actual layout in a README when adding the first implementation.

## Build, Test, and Development Commands

No build, test, or local run commands are currently configured. When introducing tooling, document the exact installation and execution commands in the README, including required runtime versions. Prefer reproducible scripts over undocumented manual steps. Do not assume `npm test`, `make build`, or any language-specific command is available.

## Coding Style & Naming Conventions

No language, formatter, or linter has been established. Follow the conventions of the chosen language and configure formatting alongside the first source files. Use descriptive names that identify the municipality, election year, or processing stage where relevant. Keep raw inputs separate from generated outputs and record their provenance.

## Testing Guidelines

No testing framework or coverage threshold exists. Add tests for transformations, missing values, municipality identifiers, and vote totals as those features are implemented. Use descriptive test names and small fixtures. Document how contributors run the suite.

## Commit & Pull Request Guidelines

Git history is unavailable in this workspace, so no existing commit convention can be verified. Use concise, imperative commit subjects, such as `Add municipality identifier validation`. Pull requests should explain the change, data sources affected, and validation performed; link relevant issues when available.

## Security & Data Handling

Never commit credentials or private configuration. Record source URLs, retrieval dates, and election years for imported data. Preserve original files so derived results can be reproduced.
