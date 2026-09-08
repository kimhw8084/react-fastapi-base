# Theme and branding

Use ./dev create with --theme operations, clarity or minimal for an independent application. Change product identity in backend/app/config/application.json and optional browser title/defaultTheme in runtime-config.json. Theme variables belong in frontend/src/theme/tokens.css. The runtime title override takes precedence; deleting that override lets the backend name apply.

Do not hardcode domain colors in shared components. Add semantic variables for a new visual concern. Check contrast, focus visibility, zoom and all states, not only the default screenshot. Existing tests prove generated themes do not modify core files; real visual/a11y proof is still required for every theme. Logo/alternate shell support is not yet a complete runtime-only configuration system.
