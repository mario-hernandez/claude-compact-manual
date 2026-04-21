# Security Policy

## Reporting

If you find a security issue, please report it privately via [GitHub Security Advisories](https://github.com/mario-hernandez/claude-compact-manual/security/advisories/new) instead of opening a public issue.

## Scope

This is a local CLI tool. It:
- Reads JSONL files from `~/.claude/projects/`
- Writes backups to `~/.claude/compact-backups/`
- Uses `pbcopy`/`pbpaste` to interact with the clipboard
- Makes **zero network requests**

Out of scope: issues that require an attacker to already have local write access to your home directory.

## Privacy note

Compacted transcripts may contain sensitive data (API keys, tokens, personal info) if those appeared in your conversation. The tool does **not** redact secrets — this is deliberate, because secrets are often legitimate context (e.g. debugging a script that uses them). Review backups in `~/.claude/compact-backups/` before sharing.

If you want to strip backups, simply `rm -rf ~/.claude/compact-backups/` — the tool creates them on demand.
