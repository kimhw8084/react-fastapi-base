# Working with Codex or another implementation agent

The repository is the instruction source. No particular model or effort is required. A configured executor should use actual local commands and the feature example, not reconstruct prior chat history.

A feature task should identify user behavior, permissions, data invariants, edge cases and non-goals. Read the related recipe and work-items module. Use ordinary feature code for business decisions and platform services for transport/state/transactions/audit. Add tests before changing a common contract.

Example task:

> Add a cost-center field to work items, optional at first. Preserve existing records. Validate a maximum length on the server, regenerate the API contract, expose it through the feature definition and export/import version policy, and test migration of an existing database. Do not edit shared grid/modal geometry. Run relevant tests and the authoritative gate; report blocked checks honestly.

Do not advertise `generate workspace`—that command is not implemented. `create` creates an application; `upgrade-plan` is dry-run only. Full framework coding-agent evaluation has not been run. Tests of generators are not evidence that a particular model completes arbitrary features correctly.

The current SysGrid AGENTS.md control-room restriction remains applicable to SysGrid. This new template's agent instructions do not override it. The delivered scripts execute deterministic setup/testing/generation; they never call an LLM or autonomous agent.
