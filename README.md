<div align="center">

<img src="docs/images/hero.png" alt="compact-manual hero" width="100%"/>

# compact-manual

**Tu `/compact` sin los daños colaterales del LLM.**

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.8%2B-yellow.svg)
![Platform](https://img.shields.io/badge/platform-macOS-lightgrey.svg)
![Status](https://img.shields.io/badge/status-stable-brightgreen.svg)

</div>

Comprime sesiones de Claude Code de forma **determinista** extrayendo el diálogo literal del JSONL y truncando los `tool_results` verbosos — sin invocar un LLM que reinterprete, resuma o pierda matices. Pensado para quienes usan Claude Code a diario y quieren vaciar contexto sin perder el hilo real de la conversación. Ratios típicos: **4–10%** del tamaño original (hasta 22× en sesiones grandes).

## TL;DR

```bash
git clone https://github.com/mario-hernandez/compact-manual-ti2wr.git
cd compact-manual-ti2wr
mkdir -p ~/.claude/skills/compact-manual/scripts
cp SKILL.md ~/.claude/skills/compact-manual/
cp scripts/compact.py ~/.claude/skills/compact-manual/scripts/
chmod +x ~/.claude/skills/compact-manual/scripts/compact.py
```

Luego en Claude Code:

```
/compact-manual       ← comprime sesión al portapapeles
/clear                ← sesión nueva limpia
Cmd+V + Enter         ← continúas con el contexto comprimido
```

## ¿Por qué existe?

El `/compact` nativo resume tu sesión usando un LLM: pierde código exacto, inventa paráfrasis y a veces simplifica decisiones críticas que tomaste hace 200 mensajes. **compact-manual** no resume: **recorta**. Lee tu JSONL real, conserva cada palabra que escribiste tú y cada palabra que escribió Claude, y solo trunca los bloques ruidosos (outputs de `ls -la`, lecturas de archivos enormes, builds verbosos). Determinista, auditable, sin alucinaciones.

---

<div align="center">

<img src="docs/images/workflow.png" alt="Workflow de 4 pasos: compactar, limpiar, pegar, continuar" width="100%"/>

*Los 4 pasos del workflow completo*

</div>

---

## 🚀 Quickstart (5 minutos)

¿Primera vez creando una skill custom de Claude Code? Tranqui, esto es más fácil de lo que parece. En 5 minutos tienes `compact-manual` funcionando.

### 📋 Requisitos

- macOS (probado en Sonoma y Sequoia)
- Claude Code instalado y funcionando
- Python 3 (viene preinstalado en macOS moderno)

### Instalación paso a paso

```bash
# 1. Clonar el repo
git clone https://github.com/mario-hernandez/compact-manual-ti2wr.git
cd compact-manual-ti2wr

# 2. Copiar la skill a tu directorio Claude
mkdir -p ~/.claude/skills/compact-manual/scripts
cp SKILL.md ~/.claude/skills/compact-manual/
cp scripts/compact.py ~/.claude/skills/compact-manual/scripts/
chmod +x ~/.claude/skills/compact-manual/scripts/compact.py

# 3. Listo. Abre Claude Code y escribe /compact-manual
```

Eso es todo. No hay dependencias externas que instalar, no hay API keys que configurar, no hay `npm install` que falle a las 2am.

### ✂️ Tu primera ejecución

Escribe `/compact-manual` en cualquier sesión larga de Claude Code. Verás algo así:

```
/compact-manual (conservative)   199e85b2-8c9c-45d9-b057-480edeb7e79a.jsonl
─────────────────────────────────────────────────────────────
Original:     1,268,565 bytes  (~422,855 tokens)
Comprimido:     110,246 chars  (~ 36,748 tokens)
Ratio:              8.7%        →   ahorro ~386,106 tokens
Turnos:              41   (user 12 / assistant 29)
Tools:       Agent×33, Edit×14, Bash×11, ...

✓ Copiado al portapapeles (110,246 chars)

Siguiente paso — sesión limpia con el transcript como único contexto:
  1.  /clear       ← crea sesión nueva (JSONL limpio)
  2.  Cmd+V        ← pegar transcript
  3.  Enter        ← enviar
```

Lo que ves: el script leyó el JSONL de tu sesión actual, extrajo lo esencial (turnos, decisiones, archivos tocados) y te lo copió al portapapeles. Un 8-9% del tamaño original. Medio millón de tokens convertidos en unos 37 mil.

### ✨ Los 3 pasos que siguen (muy importante)

1. **`/clear`** — crea una sesión completamente nueva con un JSONL limpio. **No uses `ESC ESC`**: eso es rewind de archivos (vuelve atrás a un punto del disco), no rewind de conversación. Queremos una sesión fresca, no un viaje en el tiempo.
2. **`Cmd+V`** — pegas el transcript comprimido que ya tienes en el portapapeles.
3. **`Enter`** — envías. Claude arranca con todo el contexto de la sesión anterior, pero sin el peso muerto de tool_results gigantes, screenshots en base64, ni logs de 20.000 líneas.

Resultado: sigues trabajando donde lo dejaste, pero con un 90% menos de contexto consumido.

### 🎯 Cuándo usarlo

Señales claras de que toca compactar:

- Cuando el CLI avisa `context used: >70%`
- Cuando notas que Claude empieza a olvidar detalles del inicio de la sesión
- Cuando una sesión de debugging ha explotado en tool_results (builds fallidos, greps enormes, outputs de tests)

Regla práctica: si estás pensando "ojalá pudiera seguir pero sin perder lo que ya hemos hecho" — es el momento.

---

## 📖 Guía completa de uso

`/compact-manual` extrae la conversación JSONL en curso, la comprime a un resumen narrativo fiel, y lo deja en el portapapeles listo para pegar en una sesión nueva.

### Los 5 modos

| Modo | Cuándo usar | Ratio típico | Pérdida |
|------|-------------|--------------|---------|
| `conservative` (default) | Sesión normal 300KB–1.5MB | ~10% | Solo trunca `tool_results` grandes |
| `aggressive` | Sesión >1.5MB crítica | ~4–5% | Trunca `tool_results` muy corto |
| `auto` | Cuando dudas del tamaño | Adaptativo | Depende del peso del JSONL |
| `--raw` | Quiero fidelidad TOTAL | ~10–15% | Solo quita wrappers del harness, nada más |
| `--preserve-code` | Muchas ediciones de código | +80% sobre conservative | No trunca Read/Edit/Write |

### Flags disponibles

- **`conservative`** — Modo por defecto. Equilibrio entre ratio y fidelidad.
- **`aggressive`** — Compresión agresiva para sesiones enormes.
- **`auto`** — Elige modo según el tamaño del JSONL detectado.
- **`--raw`** — Mínima intervención: quita únicamente el ruido del harness.
- **`--preserve-code`** — Nunca trunca resultados de Read/Edit/Write (código íntegro).
- **`--dry-run`** — Calcula y muestra el resultado sin escribir backup ni copiar al portapapeles.
- **`--session <path>`** — Procesa un JSONL concreto (útil para sesiones pasadas).
- **`--no-backup`** — No guarda copia en `~/.claude/compact-backups/`.
- **`--no-clipboard-backup`** — No salva el contenido previo del portapapeles.
- **`--no-dedupe`** — Desactiva la eliminación de tool_calls duplicados consecutivos.

### Ejemplos reales

```bash
/compact-manual                              # default conservative
/compact-manual aggressive                   # sesión grande
/compact-manual --raw                        # máxima fidelidad
/compact-manual aggressive --preserve-code   # comprime pero conserva código
/compact-manual --dry-run                    # preview sin tocar nada
/compact-manual --session /path/to/old.jsonl # compactar sesión vieja
```

Se pueden combinar: `/compact-manual auto --preserve-code --no-backup`.

### ¿Qué preserva y qué trunca?

| Categoría | Tratamiento |
|-----------|-------------|
| **Preserva íntegro** | User prompts literales, texto del assistant, decisiones tomadas, conclusiones, errores completos (`Traceback`, `FAIL`, stack traces) con su contexto circundante |
| **Trunca con cabeza+cola** | Outputs de Read (>3KB), Bash (>2.5KB), Agent reports (>3.5KB) — conserva las primeras N y últimas M líneas, con marcador `[... N líneas omitidas ...]` en medio |
| **Descarta** | `thinking` blocks, `file-history-snapshots`, `system-reminders` inyectados por el harness, acorta UUIDs a 8 chars |

En modo `--raw` solo se aplica la tercera categoría (descarte de ruido), nunca se trunca.

### Backups

Toda ejecución (salvo `--no-backup`) deja dos archivos en disco:

- **`~/.claude/compact-backups/YYYYMMDD-HHMMSS-xxxx-{mode}.md`** — el resumen compactado en markdown. Se retienen los **últimos 20**, el resto se rota automáticamente.
- **`~/.claude/compact-backups/clipboard-pre-YYYYMMDD-HHMMSS.txt`** — el contenido previo de tu portapapeles, por si estabas copiando algo importante antes de lanzar la skill.

Para recuperar un backup:

```bash
ls -lt ~/.claude/compact-backups/ | head -20
cat ~/.claude/compact-backups/20260416-143022-a3f9-conservative.md | pbcopy
```

### Recomendaciones rápidas

- **Primera vez**: prueba siempre con `--dry-run` para ver el ratio antes de comprometerte.
- **Sesiones con mucho código**: combina `conservative --preserve-code` para mantener diffs y archivos leídos.
- **Sesiones con errores que estás debugeando**: usa `--raw`; los Traceback completos son críticos y no merece la pena arriesgar truncado.
- **Revisitar trabajo antiguo**: `--session` apunta al JSONL en `~/.claude/projects/…` y compacta sin afectar la sesión actual.

---

<div align="center">

<img src="docs/images/compression-viz.png" alt="Visualización de compresión: 6.4MB a 289KB, 22x" width="100%"/>

*Visualización real: sesión de debugging de 6.4 MB comprimida a 289 KB (ratio 4.5%, 22× más pequeño)*

</div>

---

## 📊 Benchmarks & métricas

Datos reales medidos sobre sesiones de producción. Todas las mediciones se tomaron en un Mac M2 Pro con Python 3.12.

### Compresión por tamaño de sesión

| Tamaño sesión | Turnos | Tools | conservative | aggressive | --raw | Notas |
|---|---|---|---|---|---|---|
| 61 MB | 69 | 131 | — | ~8% | — | JSONL gigante con chrome-devtools, 160ms |
| 27 MB | 773 | 671 | ~6% | ~4% | — | Sesión larga de desarrollo |
| 6.4 MB | 217 | 283 | 4.5% | 4.2% | 9.5% | Debugging intensivo |
| 8.1 MB | 356 | 348 | ~8% | ~5% | — | Muchos Reads/Edits |
| 1.5 MB | 44 | 116 | 9.1% | 7.9% | — | Sesión desarrollo skill |
| 1.1 MB | 31 | 61 | ~8% | — | — | Sesión normal |
| <80 KB | — | — | skip | skip | skip | Auto no compacta |

Cuanto más grande la sesión, mejor comprime: las sesiones largas acumulan más tool_results duplicados y outputs verbosos que el algoritmo detecta y deduplica.

### Performance

| Tamaño input | Tiempo total | RSS pico | Python peak |
|---|---|---|---|
| 1 MB | ~50ms | 23 MB | 0.6 MB |
| 10 MB | ~100ms | 40 MB | 4 MB |
| 50 MB | ~150ms | 100 MB | 20 MB |
| 100 MB (proyectado) | ~300ms | ~200 MB | — |

Escalado cuasi-lineal. Incluso sesiones de 60 MB se procesan en menos de 200ms.

### Desglose del peso de una sesión típica

| Categoría | % del peso | Strategy |
|---|---|---|
| Tool results (Read, Bash, Grep, Agent outputs) | **85%** | Truncate head+tail |
| User prompts | 3% | Preservar literal |
| Assistant text | 7% | Preservar literal |
| Thinking blocks | 2% | Descartar completo |
| Metadata (file-history, permission-mode, progress) | 3% | Descartar completo |

**El 85% del peso son tool_results**. Por eso el ratio agresivo del 4% es alcanzable sin tocar una sola línea del diálogo humano-LLM.

### Tokenización real

El tokenizer BPE de Claude tiene ratio promedio **~3 chars/token** en transcripts técnicos (no 4, como suele asumirse). Nuestro stat usa 3. Ejemplo real:

- Sesión 6.4 MB = ~2.1 millones tokens originales
- Comprimida a 289 KB = ~96k tokens
- **Ahorro: ~2 millones tokens** (~$20 en créditos si fuera API puro)

### Qué preserva 100%

Medido sobre sesión real de 6.4 MB:

- **User prompts**: 100% verbatim (0 truncados)
- **Assistant text blocks**: 100% verbatim
- **Comandos Bash** hasta 500 chars (>500 se truncan con `…`)
- **Errores** (Traceback, FAIL, BUILD FAILED, etc.): 100% verbatim + 3 líneas de contexto

### Qué pierde

- **Read de archivos** >3KB (conservative) o >800 bytes (aggressive) → solo primeras 5 líneas
- **Bash outputs** >2.5KB → head 20 + tail 10 + errores preservados
- **Agent/Task reports** >3.5KB → head 20 + tail 10 (pierde middle)
- **UUIDs completos** → primeros 8 chars + `…`
- **`<usage>` blocks** de agentes (tokens input/output)
- **Tool_results duplicados** → dedup los referencia con `[same as previous...]`

### Limitaciones honestas

- El modo `aggressive` puede perder contexto intermedio en outputs grandes. Si necesitas el middle de un Bash largo, usa `conservative` o `--raw`.
- Archivos binarios en Read (imágenes, PDFs) se truncan agresivamente: el algoritmo está pensado para texto.
- Los ratios asumen sesiones técnicas (dev, debugging). Sesiones con mucha prosa natural comprimen peor (~15-20%) porque hay menos tool_results.

---

## 🧠 Filosofía: por qué NO usar /compact nativo

### El problema con `/compact` nativo

El `/compact` que viene con Claude Code usa un LLM (el propio Claude) para resumir la conversación. Es elegante en teoría, pero implica que un modelo decide qué "no es importante" y lo descarta. Esa decisión es arbitraria por naturaleza: se basa en heurísticas del modelo, no en reglas que tú puedas inspeccionar o ajustar. El resultado típico es que pierdes justo el detalle que necesitabas diez turnos después — ese path exacto, ese stack trace, ese valor de variable que el resumen consideró "ruido".

Además, cuesta tokens. Estás pagando input + output para que Claude resuma su propio trabajo, en una sesión que de por sí ya ha consumido contexto. Y lo más incómodo: no puedes auditar qué se descartó. El resumen es opaco — una caja negra que te devuelve texto fluido sin marcar dónde hubo pérdida.

### La filosofía de `compact-manual`

- **Determinismo**: mismas reglas siempre, mismo output dado el mismo JSONL. Si algo desaparece, puedes saber exactamente por qué regla. Nada de "el modelo decidió".
- **Fidelidad del diálogo**: los user prompts se conservan literales y los assistant texts verbatim. Nada se "interpreta" ni se parafrasea — el hilo narrativo queda intacto.
- **Honestidad sobre la pérdida**: cuando trunca, lo dice explícitamente con marcadores como `[45 líneas omitidas]` o `[same as previous Read of X]`. Sabes qué se perdió y dónde.
- **Trade-off explícito**: usa `--raw` si no quieres perder nada, `aggressive` si prefieres ratio mínimo. La decisión es tuya, no del modelo.

### Comparativa side-by-side

| Aspecto | `/compact` nativo | `compact-manual` |
|---|---|---|
| Motor | LLM (Claude) | Reglas deterministas |
| Coste | Tokens (input + output del resumen) | Gratis (local) |
| Velocidad | Depende de tamaño + latencia API | <200ms siempre |
| Fidelidad diálogo | "Interpretado" | Literal |
| Auditable | No (caja negra) | Sí (código Python legible) |
| Control | Un solo modo | 4 modos + 6 flags |
| Ratio compresión | Variable, no predecible | 4-15% según modo |
| Privacidad | Envía todo a Anthropic | 100% local |
| Dependencias | Claude Code + API | Claude Code + python3 stdlib |

### Cuándo SÍ usar `/compact` nativo

Seamos honestos: hay casos donde el nativo gana.

- Cuando quieres un resumen **narrativo** pensado para que lo lea un humano.
- Cuando **no te importa el detalle técnico** — solo el hilo general de lo que se habló.
- Cuando la sesión es **conversacional pura**, sin muchos `tool_uses` ni output de comandos.

### Cuándo SÍ usar `compact-manual`

- **Sesiones de coding/debugging**: mucho tool output que comprimir, mucho ruido que filtrar.
- **Iteraciones largas sobre el mismo archivo**: aquí el dedup brilla — un Read repetido 12 veces se convierte en una entrada.
- Quieres conservar el **hilo narrativo** sin que un LLM lo parafraseé.
- Te importa **el ratio y el coste** — y que sean predecibles.
- Quieres **auditar** qué se descartó y por qué.

### Una anécdota real

En una sesión de debugging con 217 turnos y 283 `tool_uses`, `compact-manual aggressive` comprimió 6.4MB a 274KB — un ratio del 4.2%. El 85% del peso original eran `tool_results` de Read y Bash, ninguno relevante para el siguiente turno. Preservó los 54 user prompts literales y los 163 assistant texts completos. El `/compact` nativo habría resumido todo en unas 2000 palabras narrativas — útiles para contarle a otro humano qué pasó, inútiles para retomar el debug en el punto exacto.

La elección depende de qué valoras: resumen humano vs. continuidad técnica.

---

## ⚙️ Power user & edge cases

Esta sección desgrana el comportamiento interno de `compact-manual` para quien quiera auditar, extender o confiar en él para pipelines serios. Todo lo que aparece aquí está implementado, no es roadmap.

### 1. Comportamiento avanzado del algoritmo

**Detección de sesión activa.** El algoritmo resuelve la sesión actual por tres vías encadenadas: primero intenta mapear `cwd()` a `~/.claude/projects/<encoded>/` (el encoding reemplaza `/` por `-`); si el directorio no existe, cae a la sesión global más reciente por `mtime`. Si detecta dos o más `.jsonl` modificados en los últimos 15 minutos, emite un **warning por stderr** con el listado de candidatos y elige el más reciente, pero te avisa para que lo verifiques con `--session`.

**Skip de última línea.** Antes de parsear, comprueba el `mtime` del JSONL. Si la última línea fue escrita hace **menos de 2 segundos**, se descarta: evita leer un objeto JSON a medio flush mientras la sesión viva sigue escribiendo. Esto no aplica a archivos de una sola línea.

**Truncación por tool.** Cada tool se trata con una estrategia específica:
- `Bash` → **head+tail** (primeras 40 líneas + últimas 20, con marcador `⋯N líneas omitidas`)
- `Grep` → **head_only** (normalmente ya viene filtrado)
- `Write` / `Edit` → **summary** (diff sintético)
- `Read` → **summary_long** si >3 KB (`N líneas totales, primeras 5 mostradas`)

**Preservación de errores.** Regex sobre contenido de tool_results buscando `Traceback`, `FAIL`, `panic`, `ERROR:`. Captura con contexto ±3 líneas. Si la sección errónea cae en el "middle" descartado por head+tail, **se re-inyecta al final** del bloque truncado con prefijo `[errores preservados]`.

**Dedup.** Clave compuesta `(tool_name, key_path) + SHA1-12` del contenido normalizado. Dos `Read` del mismo archivo con idéntico output colapsan al primero; el resto queda como `[same as previous Read of X · unchanged]`.

**Post-compress.** Pasada final sobre el texto ya ensamblado: UUIDs → 8 chars, `<usage>…</usage>` eliminados, prefijos `agentId:` strippeados, sustituciones Unicode (`⋯N`, `∅` para empty output, `⚠` para warnings).

### 2. Edge cases que maneja

- **JSONL de 1 línea** → no aplica `skip_tail` (dejaría el archivo vacío).
- **Archivos gzip** detectados por magic bytes (`1f 8b`) → error limpio.
- **`PermissionError`** → mensaje amigable, sin stacktrace crudo.
- **Document blocks** (PDFs base64 embebidos) → `[document: application/pdf]` en vez de dump.
- **Surrogates Unicode inválidos** → saneados con `errors='replace'` antes de `pbcopy`.
- **`BACKUPS_DIR` readonly** → warn por stderr y continúa; no crashea.
- **Multi-sesión ambiguo** → warning + listado de candidatos.

### 3. Flags combinables raros

- **`--raw --no-dedupe`** → cero transformaciones. Útil para forensics.
- **`--dry-run --session <old-uuid>`** → audita una sesión vieja sin tocar el portapapeles.
- **`aggressive --preserve-code`** → ratio bajo pero sin perder código.

---

## 🏗️ Arquitectura

Esta sección documenta la estructura interna para contributors o auditores que quieran extender el código. El script es pequeño (~500 LOC) y deliberadamente simple.

### Estructura del repo

```
compact-manual-ti2wr/
├── README.md                  # este archivo
├── SKILL.md                   # frontmatter + documentación de la skill
├── scripts/
│   └── compact.py             # lógica principal (~500 LOC stdlib only)
├── docs/
│   └── images/                # diagramas pedagógicos
├── LICENSE                    # MIT
└── .gitignore
```

No hay `requirements.txt`, `setup.py` ni `pyproject.toml`. El script es un único archivo ejecutable; funciona con cualquier Python 3.8+ que traiga macOS por defecto.

### Pipeline conceptual

```
JSONL sesión            ┌─────────────────────┐
~/.claude/projects/ ──→ │ find_current_session│ ──→ Path al JSONL activo
                        └─────────────────────┘
                                   ↓
                        ┌─────────────────────┐
                        │   iter_messages()   │ ──→ generator de msgs (skip ruido)
                        └─────────────────────┘
                                   ↓
                        ┌─────────────────────┐
                        │  build_transcript() │ ──→ truncación + dedup por tool
                        └─────────────────────┘
                                   ↓
                        ┌─────────────────────┐
                        │   post_compress()   │ ──→ UUID collapse, unicode subs
                        └─────────────────────┘
                                   ↓
                        ┌────────┐   ┌────────┐
                        │ pbcopy │   │ backup │ ──→ .md + clipboard-pre-*.txt
                        └────────┘   └────────┘
```

### Funciones clave

| Función | Responsabilidad | LOC |
|---|---|---|
| `current_project_dir()` | Encodea cwd a `-Users-mario-xxx` | 5 |
| `find_current_session()` | Detecta JSONL activo + multi-session warn | 15 |
| `iter_messages()` | Generator JSONL con skip_tail + SKIP_TYPES | 20 |
| `clean_wrappers()` | Strip harness tags | 5 |
| `post_compress()` | UUID truncate, unicode subs | 10 |
| `truncate_lines()` | head+tail con regex-preserved errors | 25 |
| `format_tool_use()` | Renderiza `[Read /path]`, `$ bash`, etc | 30 |
| `format_tool_result()` | Aplica strategy (summary/head/head_tail) | 35 |
| `stringify_result_content()` | Maneja str/list/dict/image/document | 25 |
| `should_dedupe()` | Decide si Bash es time-sensitive | 8 |
| `build_transcript()` | Loop principal + state | 75 |
| `rotate_backups()` | Mantiene últimos 20 | 10 |
| `backup_clipboard()` | pbpaste → archivo timestamped | 12 |
| `main()` | CLI, orquestación, stats, output | 110 |

### Decisiones de diseño clave

- **stdlib only**: sin `pip install`. Usa solo `argparse`, `hashlib`, `json`, `re`, `subprocess`, `pathlib`, `datetime`.
- **Markdown transcript > JSON/YAML**: medido empíricamente, JSON añade +10% tokens por boilerplate.
- **Python > bash**: JSONL estructurado + strings grandes + `pbcopy` = Python gana en claridad.
- **Dedup por key-path, no line-hash**: detecta "mismo Read unchanged" sin false positives.
- **Errors preservados con regex**: cheap, deterministic, sin false negatives críticos.

### Cómo contribuir

1. **Fork** el repo y clona localmente.
2. Haz tus cambios en `scripts/compact.py`.
3. **Testea con JSONLs reales** de `~/.claude/projects/-Users-mario/*.jsonl`.
4. Ejecuta con `--dry-run` para no ensuciar el portapapeles durante iteración.
5. Prueba los modos (`conservative`, `aggressive`, `auto`, `--raw`).
6. Un PR con **tests adversariales** sería bienvenido.

### Filosofía del código

**"Boring Python"**: sin clases innecesarias, sin metaprogramación. Funciones cortas, variables claras, happy path primero. Si hay elección entre "elegante" y "obvio", gana obvio. 450 LOC es suficiente. Tests formales no existen (uso personal), pero todas las funciones están escritas para ser testeables.

---

## ❓ FAQ & Troubleshooting

### FAQ

**1. ¿Por qué no usar simplemente `/compact`?**
Porque `/compact` delega a un LLM que resume la sesión de forma arbitraria. `compact-manual` es determinista: tú ves exactamente qué entra en el digest.

**2. ¿Es seguro pegar el transcript en una sesión nueva?**
Sí. Claude parsea los marcadores `U:` / `A:` / `[Tool]` / `→` como historia literal.

**3. ¿Funciona en Linux/Windows?**
No. Depende de `pbcopy`/`pbpaste`, exclusivos de macOS.

**4. ¿Puede perder información crítica?**
Descarta `tool_results` verbosos (>3KB) pero preserva todo el diálogo y los errores. Usa `--raw` para cero pérdidas.

**5. ¿Qué pasa si ejecuto `/compact-manual` dos veces sin pegar?**
La segunda sobrescribe el portapapeles, pero los backups `.md` persisten en disco.

**6. ¿Dónde están los backups?**
En `~/.claude/compact-backups/`. Se rotan los últimos 20.

**7. ¿Puedo recuperar una sesión compactada?**
Sí. El JSONL original **nunca** se modifica. Reanúdala con `claude --resume <session-id>`.

**8. ¿Los secretos se redactan?**
**No**, decisión deliberada: los secretos pueden ser contexto legítimo. Si te preocupa, usa `--no-backup`.

**9. ¿Funciona con sesiones de cualquier tamaño?**
Sí. Testado hasta 61MB. Performance lineal, <200ms.

**10. ¿Cómo se compara con `/compact` nativo?**
Ratios parecidos, pero con control total y cero coste. Ver tabla en sección Filosofía.

### Troubleshooting

**`"No se encontró JSONL de sesión actual"`**
- **Causa:** tu `cwd` no está bajo `~/.claude/projects/-...`.
- **Fix:** ejecuta desde el directorio donde arrancó Claude Code, o pasa `--session <path>`.

**`"pbcopy falló"`**
- **Causa:** Linux/Windows/SSH sin display.
- **Fix:** usa `--dry-run` y copia manualmente del backup `.md`.

**`"Ratio inesperadamente alto (90%+)"`**
- **Causa:** sesión muy pequeña o ya compactada antes.
- **Fix:** normal. La skill no inventa compresión donde no hay redundancia.

**`"El transcript pegado confunde a Claude"`**
- **Causa:** interpretado como nueva conversación.
- **Fix:** el header ya incluye leyenda. Si sigue confuso, añade: *"este es un digest de una sesión previa, trátalo como historia"*.

**`"Script crashea con PermissionError o IsADirectoryError"`**
- **Causa:** `--session` apunta a directorio o archivo sin permisos.
- **Fix:** desde v1.1 se captura con mensaje limpio. Actualiza con `git pull`.

### Debugging tips

- **`--dry-run`** — muestra stats y preview sin tocar nada.
- **`--session <uuid>.jsonl`** — procesa una sesión antigua específica.
- **`--raw`** — si dudas de qué se está truncando, esta flag te devuelve el transcript completo.

---

## 🗺️ Roadmap

Ideas que podrían venir (sin compromiso):

- **`--chunked`** para sesiones >200KB: genera un TOC + chunks que Claude carga on-demand vía Read tool (ratio -70% inicial).
- **`--llm-summarize-old`**: modo híbrido con Haiku para resumir turnos antiguos (~$0.02/compact, opt-in).
- **Auto-detect de `CLAUDE_SESSION_ID`** si Claude Code lo expone como env var.
- **`--preserve-conclusions`**: conservar bullets y tablas del middle en Agent reports.
- **Linux/Windows support** vía `xclip` / `clip.exe` — solo si alguien lo pide.

## 🤝 Contribuir

Issues y PRs bienvenidos en GitHub. El código es ~500 LOC, **stdlib only**, fácil de leer en una tarde.

- Para testear: usa tus propios JSONLs en `~/.claude/projects/...` con `--dry-run`.
- Los cambios deben mantener la filosofía del proyecto: **determinismo sin LLM**. Si una feature requiere API, debería ser opt-in y estar justificada.

## 📚 Recursos relacionados

- [Claude Code docs](https://docs.claude.com/en/docs/claude-code/overview)
- [Claude Code Hooks](https://docs.claude.com/en/docs/claude-code/hooks) — un `PreCompact` hook podría disparar esta skill automáticamente.
- [Anthropic Token Counting API](https://platform.claude.com/docs/en/build-with-claude/token-counting)

## 🙏 Créditos

- **Idea original:** Mario Hernández — de un workflow manual con Sublime Text que pedía a gritos automatización.
- **Implementación:** construida con Claude Code v2.1+, iterando con pools de agentes paralelos.
- **Testing:** 9 agentes en 2 rondas encontraron y corrigieron ~20 bugs antes del release.

## ⚠️ Disclaimer

Herramienta personal hecha pública. Diseñada para **macOS + Claude Code v2.x**. Si el schema del JSONL de Claude Code cambia, el script podría romperse sin aviso. Sin garantías, sin soporte oficial — es software "funciona en mi Mac".

## 📜 Licencia

MIT License. Ver [LICENSE](LICENSE).

## ⭐ Si te sirvió

Dale star al repo. Es la señal más simple de que la herramienta vale. Si veo que la usa más gente, probablemente siga iterando.
