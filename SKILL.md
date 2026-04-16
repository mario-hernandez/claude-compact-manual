---
name: compact-manual
description: "Comprime la sesión Claude Code actual al portapapeles para hacer rewind+paste manual. Alternativa a /compact que NO resume con LLM sino que extrae el diálogo literal truncando solo outputs de tools. Usar cuando el usuario diga 'compacta la sesión', 'compact manual', 'limpia el contexto', o invoque /compact-manual."
argument-hint: "[conservative|aggressive|auto|--raw] [--preserve-code] [--dry-run] [--no-dedupe]"
allowed-tools: Bash
metadata:
  author: mario-hernandez
  version: 1.1
---

## Qué hace

Lee el JSONL de la sesión actual (`~/.claude/projects/-Users-mario/*.jsonl`, el más reciente), extrae el diálogo user/assistant, trunca tool_results verbosos (con preservación regex de errores completos), formatea como markdown transcript, copia al portapapeles con `pbcopy` y guarda backup en `~/.claude/compact-backups/`.

Luego el usuario ejecuta **`/clear`** (crea sesión nueva con JSONL limpio — la anterior queda archivada) y pega con `Cmd+V` para empezar con el transcript comprimido como único contexto.

## Cómo ejecutarla

Ejecutar el script con Bash, **pasando los argumentos del usuario con `$ARGUMENTS`**:

```bash
python3 ~/.claude/skills/compact-manual/scripts/compact.py $ARGUMENTS
```

Si el usuario no pasó args, `$ARGUMENTS` queda vacío y el script corre en modo `conservative` por defecto.

### Argumentos

| Arg | Efecto |
|-----|--------|
| (ninguno) | Modo **conservative** (default). Trunca tool_results >2-3KB, conserva diálogo literal |
| `aggressive` | Trunca tool_results muy corto (~600 chars), ideal >1.5MB sesión |
| `auto` | Elige `aggressive` si sesión >1.5MB, `conservative` si <1.5MB, skip si <80KB |
| `--raw` | **Modo ultra-literal**: sin truncar, sin dedup, sin post_compress. Solo elimina wrappers del harness (`<system-reminder>`, etc). Ratio ~9-15% pero fidelidad total. Úsalo cuando quieras preservar TODO sin decisiones automáticas |
| `--preserve-code` | Nunca trunca agresivamente Read/Edit/Write (multiplica sus límites ×8) |
| `--no-dedupe` | Desactiva dedup de tool_results idénticos |
| `--dry-run` | Preview + stats sin copiar ni guardar backup |
| `--session <path>` | Procesa un JSONL específico (default: más reciente en proyecto actual) |
| `--no-backup` | No guarda backup (normalmente sí guarda, retiene últimos 20) |
| `--no-clipboard-backup` | No guarda el clipboard anterior antes de sobrescribir |

### Ejemplos de invocación

```bash
python3 ~/.claude/skills/compact-manual/scripts/compact.py                # default: conservative
python3 ~/.claude/skills/compact-manual/scripts/compact.py aggressive
python3 ~/.claude/skills/compact-manual/scripts/compact.py auto
python3 ~/.claude/skills/compact-manual/scripts/compact.py --raw           # ultra-fidelidad
python3 ~/.claude/skills/compact-manual/scripts/compact.py --dry-run
python3 ~/.claude/skills/compact-manual/scripts/compact.py aggressive --preserve-code
```

## Qué informar al usuario después

1. **Ratio de compresión** (original/comprimido, tokens ahorrados estimados)
2. **Path del backup** guardado
3. **Confirmación** de que está en el portapapeles
4. **Instrucciones finales claras**:
   - `/clear` (crea sesión nueva con JSONL limpio — la actual queda accesible via `/resume`)
   - `Cmd+V` para pegar el transcript
   - Enter para enviar

Importante: **NO sugerir ESC ESC** — en Claude Code eso es rewind de file edits (checkpoints de archivos), NO rewind de conversación. La forma correcta de empezar con contexto limpio es `/clear`.

## Principios de diseño

- **No usa LLM para comprimir** → determinista, sin pérdida arbitraria. Tú eliges qué perder.
- **Preserva diálogo literal** (user + assistant text) → el tejido narrativo queda intacto.
- **Solo trunca tool_results** (donde está el 85% del peso según análisis empírico).
- **Preserva errores completos** (regex matches en Bash/Task con contexto ±3 líneas).
- **Backup automático** en `~/.claude/compact-backups/` (retiene 20 últimos).
- **Ratios observados**: 4-5% en sesiones grandes (>1MB), 10-15% en sesiones medianas.

## Flow completo (para guiar al usuario)

```
1. /compact-manual       ← skill procesa JSONL, transcript al portapapeles + backup
2. /clear                ← sesión nueva con JSONL limpio (anterior archivada en /resume)
3. Cmd+V                 ← pegar transcript comprimido
4. Enter                 ← enviar, seguir trabajando con contexto comprimido
```

**Por qué `/clear` y no ESC ESC**: en Claude Code, ESC ESC revierte _ediciones de archivos_ (checkpoints locales), no la conversación. `/clear` sí crea una sesión completamente nueva con su propio JSONL, que es lo que queremos para que el próximo `/compact-manual` no procese la conversación vieja redundantemente.
