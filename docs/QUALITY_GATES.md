# Quality Gates de la Laura — Baseline

> Fuente: prompt **08-eslint-quality-gates-install.md** del vibe-coding-toolkit,
> adaptado a Python con **Ruff**. Principio: el gate nace con la severidad que
> la medición indica — regla sin violaciones en `error`, con violaciones en
> `warn` + baseline. **Aquí no se corrige nada; solo se instala y se mide.**

## Comandos

```powershell
pip install ruff                 # linter (ya en requirements: ruff>=0.12.7)
ruff check .                     # corre el gate
ruff check . --fix               # corrige solo lo automático y seguro
ruff check . --statistics        # conteo por regla (baseline)
```

## Reglas instaladas y baseline (medido 2026-09-03)

| Código | Regla | Violaciones | Severidad propuesta |
|---|---|---|---|
| `T201` | print() directo | 147 | warn (baseline) — se baja con burndown |
| `E701` | múltiples statements en una línea | 87 | warn (baseline) |
| `E722` | except desnudo (`except:`) | 56 | warn (baseline) |
| `F401` | import no usado | 38 | warn (baseline) |
| `F841` | variable asignada y no usada | 18 | warn (baseline) |
| `F541` | f-string sin placeholder | 17 | warn (baseline) |
| `PLR0915` | demasiados statements por función | 16 | warn (baseline) |
| `E401` | varios imports en una línea | 4 | warn (baseline) |
| `E402` | import fuera del top | 4 | warn (baseline) |
| `F821` | nombre no definido | 4 | error (0 en core/laura) => a medium |
| `E741` | nombre ambiguo | 2 | warn |
| `E702` | ; en una línea | 1 | warn |
| `F811` | redefinido sin uso | 1 | warn |
| **Total** | | **395** | |

`F821` (nombre no definido) marca 4 pero todos en skills legadas no cargadas —
no rompen el flujo principal. Se revisan en burndown.

## Teto de tamaño por archivo (baseline > 350 líneas)

`pyproject.toml` usa `PLR0915` como proxy de tamaño; el techo real medido:

| Líneas | Archivo |
|---|---|
| 1108 | `skills/video_explicativo.py` |
| 582 | `skills/visual_assets.py` |
| 415 | `Laura.py` |
| 409 | `skills/video_explicativo_assets.py` |
| 405 | `skills/google_calendar.py` |
| 395 | `skills/file_manager.py` |

Son los 6 candidatos del refactor (**prompt 09-file-size-refactor.md**) — se
dividen por responsabilidad, 1 archivo por commit, con `py_compile` como
smoke test entre cada uno. `Laura.py` es el único de `core/`/raíz: es la
prioridad (kernel + chat + orquestración + helpers).

## Decisiones de severidad aplicadas en `pyproject.toml`

- `T20` en `skills/*` → ignorada (baseline en warn implícito): las skills
  hablan y loguean; se limpian en burndown, no ahora.
- `T20`/`F401` en `test_*.py` → ignoradas (los tests no son producción).
- Core nuevo (`core/state.py`, `core/skill_protocol.py`) **debe pasar en
  error**: son las piezas que la Laura va a auto-extender (Fase 5).

## Estado

- [x] Ruff instalado
- [x] `pyproject.toml` con gates
- [x] Baseline medido (395 violaciones)
- [x] Lista de archivos > 350 líneas
- [ ] Refactor de los 6 (prompt 09) — PRÓXIMO
- [ ] Burndown de reglas warn → error (prompt 02) — después