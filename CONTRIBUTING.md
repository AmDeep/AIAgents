# Contributing

Keep examples deterministic, local-only and small enough to understand in one sitting. Prefer standard-library implementations so the safety properties remain inspectable.

Before opening a change:

1. Add or update tests for success, invalid input and relevant failure paths.
2. Run `python -m pytest` and `python -m compileall -q examples`.
3. Update the example README with changed behavior and sample output.
4. Confirm no secrets, generated caches or machine-specific paths are included.

Do not make an example imply that a prompt is an authorization boundary or that a subprocess timeout alone is a complete security sandbox.
