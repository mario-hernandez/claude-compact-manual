#!/usr/bin/env python3
"""compact-manual: comprime la sesión Claude Code actual al portapapeles."""

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

PROJECTS_ROOT = Path.home() / ".claude" / "projects"
BACKUPS_DIR = Path.home() / ".claude" / "compact-backups"
BACKUPS_KEEP = 20
MAX_TEXT_BLOCK = 100_000

SKIP_TYPES = {
    "permission-mode", "file-history-snapshot", "attachment",
    "last-prompt", "queue-operation", "system", "progress",
    "summary", "agentId",
}

SYSTEM_REMINDER_RX = re.compile(r"<system-reminder>.*?</system-reminder>", re.DOTALL)
LOCAL_CMD_RX = re.compile(r"<local-command-(?:stdout|stderr|caveat)>.*?</local-command-(?:stdout|stderr|caveat)>", re.DOTALL)
COMMAND_WRAP_RX = re.compile(r"<command-(?:name|message|args)>.*?</command-(?:name|message|args)>", re.DOTALL)
USAGE_BLOCK_RX = re.compile(r"<usage>.*?</usage>", re.DOTALL)
AGENT_ID_LINE_RX = re.compile(r"^\s*agentId:\s*[a-f0-9]+.*$", re.MULTILINE)
UUID_RX = re.compile(r"\b([0-9a-f]{8})-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b", re.I)
OMIT_LINES_RX = re.compile(r"\[\.\.\.\s*(\d+)\s*líneas omitidas\s*\.\.\.\]")
OMIT_ERR_RX = re.compile(r"\[errores preservados\]")
ERROR_RX = re.compile(
    r"^\s*(?:Traceback\b|ERROR:|FATAL\b|panic:|\w+(?:Error|Exception):|FAIL(?:ED)?\b|BUILD FAILED|✗)",
    re.MULTILINE,
)

LIMITS = {
    "conservative": {
        "Read":      (3000, "summary_long"),
        "Bash":      (2500, "head_tail"),
        "Grep":      (1800, "head"),
        "Glob":      (1500, "head"),
        "Edit":      (600,  "summary"),
        "Write":     (200,  "summary"),
        "MultiEdit": (800,  "summary"),
        "WebFetch":  (2500, "head_tail"),
        "WebSearch": (1800, "head"),
        "Agent":     (3500, "head_tail"),
        "Task":      (3500, "head_tail"),
        "TodoWrite": (400,  "summary"),
        "NotebookEdit": (600, "summary"),
        "default":   (2000, "head_tail"),
    },
    "aggressive": {
        "Read":      (800,  "summary_long"),
        "Bash":      (700,  "head_tail"),
        "Grep":      (500,  "head"),
        "Glob":      (400,  "head"),
        "Edit":      (150,  "summary"),
        "Write":     (100,  "summary"),
        "MultiEdit": (200,  "summary"),
        "WebFetch":  (800,  "head_tail"),
        "WebSearch": (500,  "head"),
        "Agent":     (1500, "head_tail"),
        "Task":      (1500, "head_tail"),
        "TodoWrite": (120,  "summary"),
        "NotebookEdit": (150, "summary"),
        "default":   (600,  "head_tail"),
    },
}

NO_DEDUPE_CMDS = (
    "date", "ls", "pwd", "ps", "top", "df", "du", "who", "w", "uptime",
    "git status", "git log", "git diff", "git branch",
    "curl", "wget",
    "docker ps", "docker logs", "docker stats", "docker inspect",
    "kubectl get", "kubectl describe", "kubectl logs",
    "tail", "watch", "iostat", "vmstat", "netstat", "lsof",
    "python -c", "node -e", "ruby -e", "perl -e",
    "npm test", "pytest", "jest", "go test", "cargo test",
    "xcodebuild", "make", "cmake",
    "gh pr view", "gh run", "gh issue",
    "rg", "find", "grep",
    "brew list", "pip list", "npm list",
)


def current_project_dir():
    encoded = str(Path.cwd()).replace("/", "-")
    candidate = PROJECTS_ROOT / encoded
    if candidate.is_dir():
        return candidate
    return None


def find_current_session():
    project = current_project_dir()
    candidates = []
    fallback_used = False
    if project is not None:
        candidates = [p for p in project.glob("*.jsonl") if p.is_file()]
    if not candidates and PROJECTS_ROOT.is_dir():
        fallback_used = True
        for sub in PROJECTS_ROOT.iterdir():
            if sub.is_dir():
                candidates.extend(p for p in sub.glob("*.jsonl") if p.is_file())
    if not candidates:
        return None, [], fallback_used
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    now = time.time()
    recent = [p for p in candidates if now - p.stat().st_mtime < 900 and p.stat().st_size > 5000]
    return candidates[0], recent, fallback_used


def clean_wrappers(text):
    text = SYSTEM_REMINDER_RX.sub("", text)
    text = LOCAL_CMD_RX.sub("", text)
    text = COMMAND_WRAP_RX.sub("", text)
    return text.strip()


def post_compress(text):
    text = USAGE_BLOCK_RX.sub("", text)
    text = AGENT_ID_LINE_RX.sub("", text)
    text = UUID_RX.sub(r"\1…", text)
    text = OMIT_LINES_RX.sub(r"⋯\1", text)
    text = OMIT_ERR_RX.sub("⚠", text)
    text = re.sub(r"→ \(vacío\)", "→ ∅", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def truncate_lines(text, head_n, tail_n, preserve_errors=True):
    lines = text.splitlines()
    total = len(lines)
    if total <= head_n + tail_n:
        return text

    head = lines[:head_n]
    tail = lines[-tail_n:] if tail_n else []
    errors = []
    if preserve_errors:
        middle = lines[head_n : total - tail_n]
        window = set()
        for i, ln in enumerate(middle, start=head_n):
            if ERROR_RX.search(ln):
                for j in range(max(0, i - 1), min(total, i + 3)):
                    window.add(j)
        errors = [lines[j] for j in sorted(window) if lines[j] not in head and lines[j] not in tail]

    removed = total - head_n - tail_n
    parts = ["\n".join(head)]
    if removed > 0:
        parts.append(f"    [... {removed} líneas omitidas ...]")
    if tail:
        parts.append("\n".join(tail))
    out = "\n".join(parts)
    if errors:
        out += "\n    [errores preservados]\n" + "\n".join(dict.fromkeys(errors[:10]))
    return out


def format_tool_use(tool_name, inp):
    if not isinstance(inp, dict):
        return f"[{tool_name}]"
    fp = inp.get("file_path") or "?"
    if tool_name == "Read":
        return f"[Read {fp}]"
    if tool_name == "Bash":
        cmd = inp.get("command") or "?"
        if len(cmd) > 500:
            cmd = cmd[:500] + "…"
        return f"$ {cmd}"
    if tool_name == "Grep":
        pat = (inp.get("pattern") or "?")[:100]
        path = inp.get("path") or inp.get("glob") or ""
        return f"[Grep {pat}{' in '+path if path else ''}]"
    if tool_name == "Glob":
        return f"[Glob {inp.get('pattern') or '?'}]"
    if tool_name == "Edit":
        return f"[Edit {fp}]"
    if tool_name == "MultiEdit":
        n = len(inp.get("edits") or [])
        return f"[MultiEdit {fp} ×{n}]"
    if tool_name == "Write":
        return f"[Write {fp}]"
    if tool_name == "WebFetch":
        return f"[WebFetch {inp.get('url') or '?'}]"
    if tool_name == "WebSearch":
        q = (inp.get("query") or "?")[:100]
        return f"[WebSearch {q}]"
    if tool_name in ("Agent", "Task"):
        desc = inp.get("description") or inp.get("subagent_type") or (inp.get("prompt") or "")[:100]
        return f"[Agent: {(desc or '?')[:120]}]"
    if tool_name == "TodoWrite":
        todos = inp.get("todos") or []
        return f"[TodoWrite ×{len(todos)}]"
    return f"[{tool_name}]"


def stringify_result_content(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        out = []
        for b in content:
            if not isinstance(b, dict):
                out.append(str(b))
                continue
            t = b.get("type")
            if t == "text":
                out.append(b.get("text", ""))
            elif t == "image":
                out.append("[image omitted]")
            elif t == "document":
                src = b.get("source")
                if isinstance(src, dict):
                    out.append(f"[document: {src.get('media_type', 'unknown')}]")
                else:
                    out.append("[document]")
            else:
                txt = b.get("text")
                if txt:
                    out.append(txt)
                else:
                    out.append(f"[{t or 'block'}]")
        return "\n".join(x for x in out if x)
    if isinstance(content, dict):
        try:
            return json.dumps(content, ensure_ascii=False)
        except (TypeError, ValueError):
            return str(content)
    return str(content) if content is not None else ""


def format_tool_result(tool_name, content, mode, preserve_code):
    text = stringify_result_content(content).strip()
    if not text:
        return "  → (vacío)"

    limits_map = LIMITS[mode]
    if preserve_code and tool_name in ("Read", "Edit", "MultiEdit", "Write"):
        max_chars, strategy = limits_map.get(tool_name, limits_map["default"])
        max_chars = max_chars * 8
    else:
        max_chars, strategy = limits_map.get(tool_name, limits_map["default"])

    if len(text) <= max_chars:
        indented = "\n".join("    " + ln for ln in text.splitlines())
        return f"  →\n{indented}"

    if strategy == "summary":
        n_lines = text.count("\n") + 1
        return f"  → [{n_lines} líneas / {len(text):,} chars omitidos]"

    if strategy == "summary_long":
        n_lines = text.count("\n") + 1
        head = "\n".join(text.splitlines()[:5])
        head_indented = "\n".join("    " + ln for ln in head.splitlines())
        return f"  → [{n_lines} líneas / {len(text):,} chars, primeras 5:]\n{head_indented}"

    preserve = tool_name in ("Bash", "Agent", "Task")
    if strategy == "head":
        truncated = truncate_lines(text, 30, 0, preserve_errors=preserve)
    else:
        truncated = truncate_lines(text, 20, 10, preserve_errors=preserve)
    indented = "\n".join("    " + ln for ln in truncated.splitlines())
    return f"  →\n{indented}"


def iter_messages(jsonl_path, skip_tail_seconds=2):
    cutoff = time.time() - skip_tail_seconds
    raw = []
    with open(jsonl_path, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.strip():
                raw.append(line)
    if len(raw) > 1 and jsonl_path.stat().st_mtime > cutoff:
        raw = raw[:-1]
    for line in raw:
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if msg.get("type") in SKIP_TYPES:
            continue
        yield msg


def should_dedupe(tool_name, args):
    if tool_name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
        return False
    if tool_name == "Bash":
        cmd = (args.get("command") or "").strip().lower()
        for p in NO_DEDUPE_CMDS:
            if cmd == p or cmd.startswith(p + " ") or cmd.startswith(p + "\t"):
                return False
    return True


def truncate_text_block(txt, limit=MAX_TEXT_BLOCK):
    if len(txt) <= limit:
        return txt
    return txt[: limit // 2] + f"\n[... {len(txt) - limit} chars omitidos en text block ...]\n" + txt[-limit // 2 :]


def build_transcript(jsonl_path, mode, preserve_code, dedupe=True, raw=False):
    lines = []
    stats = {"turns": 0, "tools": {}, "user_msgs": 0, "assistant_msgs": 0, "deduped": 0, "skipped_lines": 0}
    tool_id_to_name = {}
    tool_id_to_args = {}
    seen_calls = {}

    for msg in iter_messages(jsonl_path):
        mtype = msg.get("type")
        if mtype not in ("user", "assistant"):
            continue
        message = msg.get("message") or {}
        role = message.get("role")
        if role and role not in ("user", "assistant"):
            continue
        content = message.get("content")
        if content is None:
            continue

        if isinstance(content, str):
            txt = clean_wrappers(content)
            if txt:
                if not raw:
                    txt = truncate_text_block(txt)
                lines.append(f"U: {txt}")
                stats["turns"] += 1
                stats["user_msgs"] += 1
            continue

        if not isinstance(content, list):
            continue

        for b in content:
            if not isinstance(b, dict):
                continue
            btype = b.get("type")

            if btype == "text":
                txt = clean_wrappers(b.get("text") or "")
                if not txt:
                    continue
                if not raw:
                    txt = truncate_text_block(txt)
                prefix = "U" if mtype == "user" else "A"
                lines.append(f"{prefix}: {txt}")
                stats["turns"] += 1
                if mtype == "user":
                    stats["user_msgs"] += 1
                else:
                    stats["assistant_msgs"] += 1

            elif btype == "tool_use":
                tname = b.get("name") or "?"
                tid = b.get("id") or ""
                targs = b.get("input") or {}
                tool_id_to_name[tid] = tname
                tool_id_to_args[tid] = targs
                lines.append(f"  {format_tool_use(tname, targs)}")
                stats["tools"][tname] = stats["tools"].get(tname, 0) + 1

            elif btype == "tool_result":
                tid = b.get("tool_use_id") or ""
                tname = tool_id_to_name.get(tid, "default")
                targs = tool_id_to_args.get(tid) or {}
                raw_content = stringify_result_content(b.get("content", ""))
                if raw:
                    indented = "\n".join("    " + ln for ln in raw_content.splitlines())
                    lines.append(f"  →\n{indented}" if indented else "  → ∅")
                    continue
                if dedupe and should_dedupe(tname, targs) and len(raw_content) > 200:
                    key_path = targs.get("file_path") or targs.get("command") or targs.get("pattern") or targs.get("url") or ""
                    if key_path:
                        dkey = (tname, key_path)
                        content_hash = hashlib.sha1(raw_content.encode("utf-8", "ignore")).hexdigest()[:12]
                        prev = seen_calls.get(dkey)
                        if prev and prev == content_hash:
                            label = key_path.rsplit("/", 1)[-1] if "/" in key_path else key_path[:60]
                            lines.append(f"  → [same output as previous {tname} of {label} · unchanged]")
                            stats["deduped"] += 1
                            continue
                        seen_calls[dkey] = content_hash
                lines.append(format_tool_result(tname, b.get("content", ""), mode, preserve_code))

            elif btype == "thinking":
                continue

    return "\n".join(lines), stats


def rotate_backups():
    if not BACKUPS_DIR.exists():
        return
    for pattern in ("*.md", "clipboard-pre-*.txt"):
        files = sorted(BACKUPS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
        for old in files[BACKUPS_KEEP:]:
            try:
                old.unlink()
            except OSError as e:
                print(f"[warn] no pude borrar backup antiguo {old}: {e}", file=sys.stderr)


def backup_clipboard():
    try:
        r = subprocess.run(["pbpaste"], capture_output=True, timeout=5)
        if r.returncode == 0 and r.stdout:
            BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d-%H%M%S")
            path = BACKUPS_DIR / f"clipboard-pre-{ts}.txt"
            path.write_bytes(r.stdout)
            return path
    except (subprocess.SubprocessError, FileNotFoundError, OSError):
        pass
    return None


def copy_to_clipboard(text):
    try:
        subprocess.run(["pbcopy"], input=text.encode("utf-8"), check=True, timeout=10)
        return True, None
    except (subprocess.SubprocessError, FileNotFoundError) as e:
        return False, str(e)


def warn_multi_session(recent, chosen):
    if len(recent) <= 1:
        return
    print(f"\n⚠ Detectadas {len(recent)} sesiones activas en los últimos 15 min:", file=sys.stderr)
    for p in recent:
        age = int(time.time() - p.stat().st_mtime)
        marker = " ← elegida" if p == chosen else ""
        print(f"    {p.stem[:8]}  {p.stat().st_size:>10,} B  hace {age:>4}s{marker}", file=sys.stderr)
    print("    Si no es la correcta, usa --session <path>\n", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(description="Comprimir sesión Claude Code al portapapeles")
    parser.add_argument("mode", nargs="?", default="conservative",
                        choices=["conservative", "aggressive", "auto"])
    parser.add_argument("--preserve-code", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--session", help="Path a un JSONL específico (default: más reciente)")
    parser.add_argument("--no-backup", action="store_true")
    parser.add_argument("--no-clipboard-backup", action="store_true")
    parser.add_argument("--no-dedupe", action="store_true",
                        help="Desactiva dedup de tool_results idénticos")
    parser.add_argument("--raw", action="store_true",
                        help="Modo ultra-literal: sin truncar, sin dedupe, sin post_compress. Solo elimina ruido del harness.")
    args = parser.parse_args()

    recent_candidates = []
    fallback_used = False
    if args.session:
        jsonl_path = Path(args.session).expanduser().resolve()
    else:
        jsonl_path, recent_candidates, fallback_used = find_current_session()

    if not jsonl_path or not jsonl_path.exists() or not jsonl_path.is_file():
        print(f"[ERROR] No se encontró JSONL de sesión actual (cwd={Path.cwd()}, buscando en {PROJECTS_ROOT})", file=sys.stderr)
        sys.exit(1)

    try:
        with open(jsonl_path, "rb") as _f:
            magic = _f.read(2)
        if magic == b"\x1f\x8b":
            print(f"[ERROR] El archivo parece gzip, no JSONL: {jsonl_path}", file=sys.stderr)
            sys.exit(1)
    except PermissionError:
        print(f"[ERROR] Sin permiso de lectura: {jsonl_path}", file=sys.stderr)
        sys.exit(1)
    except OSError as e:
        print(f"[ERROR] No pude abrir {jsonl_path}: {e}", file=sys.stderr)
        sys.exit(1)

    if fallback_used:
        print(f"⚠ cwd={Path.cwd()} no tiene JSONLs en {PROJECTS_ROOT}. Usando sesión más reciente global: {jsonl_path.stem[:8]}", file=sys.stderr)
    if recent_candidates:
        warn_multi_session(recent_candidates, jsonl_path)

    original_size = jsonl_path.stat().st_size

    mode = args.mode
    if mode == "auto":
        if original_size < 80_000:
            print(f"[SKIP] Sesión pequeña ({original_size:,} bytes). No vale compactar. Usa 'conservative' si insistes.")
            sys.exit(0)
        mode = "aggressive" if original_size > 1_500_000 else "conservative"
        print(f"[auto] modo elegido: {mode}")

    transcript, stats = build_transcript(
        jsonl_path, mode=mode, preserve_code=args.preserve_code,
        dedupe=not args.no_dedupe, raw=args.raw,
    )
    if not args.raw:
        transcript = post_compress(transcript)
    transcript = transcript.encode("utf-8", "replace").decode("utf-8", "replace")

    session_id = jsonl_path.stem
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    header = (
        f"## Session digest — {now} · {session_id[:8]} · mode={mode}\n"
        f"(Reanudación de conversación previa. Transcript comprimido de {stats['turns']} turnos.\n"
        f" Leyenda: U=user, A=assistant, `[Tool args]` = llamada, `→` = resultado.\n"
        f" `[same output as previous ... · unchanged]` = tool_result idéntico al anterior omitido.\n"
        f" JSONL original preservado en {jsonl_path})\n\n"
    )
    full = header + transcript

    compressed_size = len(full)
    ratio_raw = compressed_size / original_size if original_size else 1.0
    ratio = min(ratio_raw, 9.999)
    tokens_per_char = 1 / 3.0
    saved_tokens = int(max(0, (original_size - compressed_size)) * tokens_per_char)
    compressed_tokens = int(compressed_size * tokens_per_char)
    original_tokens = int(original_size * tokens_per_char)

    backup_path = None
    if not args.no_backup and not args.dry_run:
        try:
            BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d-%H%M%S-%f")[:-3]
            mode_label = "raw" if args.raw else mode
            backup_path = BACKUPS_DIR / f"{ts}-{session_id[:8]}-{mode_label}.md"
            backup_path.write_text(full, encoding="utf-8")
            rotate_backups()
        except OSError as e:
            print(f"[warn] no pude guardar backup en {BACKUPS_DIR}: {e}", file=sys.stderr)
            backup_path = None

    clip_backup_path = None
    if not args.dry_run and not args.no_clipboard_backup:
        clip_backup_path = backup_clipboard()

    copied = False
    copy_err = None
    if not args.dry_run:
        copied, copy_err = copy_to_clipboard(full)

    tools_summary = ", ".join(f"{k}×{v}" for k, v in sorted(stats["tools"].items(), key=lambda x: -x[1])[:10])

    print()
    print(f"  /compact-manual ({mode})   {jsonl_path.name}")
    print(f"  ─────────────────────────────────────────────────────────────")
    print(f"  Original:    {original_size:>10,} bytes  (~{original_tokens:>7,} tokens)")
    print(f"  Comprimido:  {compressed_size:>10,} chars  (~{compressed_tokens:>7,} tokens)")
    print(f"  Ratio:       {ratio*100:>10.1f}%        →   ahorro ~{saved_tokens:,} tokens")
    print(f"  Turnos:      {stats['turns']:>10}   (user {stats['user_msgs']} / assistant {stats['assistant_msgs']})")
    print(f"  Tools:       {tools_summary or '—'}")
    if stats.get("deduped"):
        print(f"  Dedup:       {stats['deduped']} tool_results duplicados colapsados a referencia")
    if backup_path:
        print(f"  Backup:      {backup_path}")
    if clip_backup_path:
        print(f"  Clipboard previo guardado en: {clip_backup_path}")
    print()

    if args.dry_run:
        print("  [DRY-RUN] No se copió al portapapeles ni se guardó backup.")
        print()
        preview = full[:1500]
        print("--- Preview (primeros 1500 chars) ---")
        print(preview)
        if len(full) > 3000:
            print("\n--- Preview (últimos 800 chars) ---")
            print(full[-800:])
        return

    if copied:
        print(f"  ✓ Copiado al portapapeles ({compressed_size:,} chars)")
        print()
        print(f"  Siguiente paso — sesión limpia con el transcript como único contexto:")
        print(f"    1.  /clear       ← crea sesión nueva (JSONL limpio)")
        print(f"    2.  Cmd+V        ← pegar transcript")
        print(f"    3.  Enter        ← enviar")
        if backup_path:
            print()
            print(f"  Si pierdes el portapapeles antes de pegar:  pbcopy < {backup_path}")
    else:
        print(f"  ✗ pbcopy falló: {copy_err}")
        if backup_path:
            print(f"    Copia manualmente con:  pbcopy < {backup_path}")


if __name__ == "__main__":
    main()
