# Decisions

- Use one bidirectional abstraction with independent transport directions so tests exercise the same API for every mechanism.
- Use a shared anonymous mapping for the initial ring implementation; it preserves fork sharing without requiring cleanup of persistent names.
