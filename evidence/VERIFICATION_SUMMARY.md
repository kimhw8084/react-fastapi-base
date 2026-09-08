# Executed verification — 2026-09-06

Release: **NOT_CERTIFIED**. Code gates: **not all clear**. Full 68-domain scope: **not complete**.

| Check | Observed result |
|---|---|
| Backend pytest suite | 103 passed |
| Application generation / upgrade planning | 6 passed |
| Pure TypeScript runtime / transport logic under Node | 10 passed |
| Native Node static server | 8 passed |
| Real localhost Uvicorn / HTTP workflow | 19 checks passed |
| Architecture source checks | Passed |
| Generated OpenAPI / TypeScript drift check | Passed |
| TypeScript syntax parsing | 25 source files parsed; NOT a full typecheck |
| React strict typecheck, component tests, Vite build | BLOCKED: dependency installation and reviewed frontend lock absent |
| Built-application Playwright / accessibility | BLOCKED |
| Python and npm advisory clearance | BLOCKED |
| Company identity, storage, native publisher and persistence | Not exercised; BLOCKED |
| Full SysGrid migration / visual-behavioral parity | Not implemented or certified |

The 103 + 6 + 10 + 8 test counts are distinct executed suites. The 19 HTTP checks are a separate smoke harness. Do not reinterpret these counts as production coverage or a complete security/accessibility certification. Source hashes bind 107 implementation/test/config files to this run. No company data was used. See verification.json and the individual logs for the exact commands.
