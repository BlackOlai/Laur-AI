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

## Reglas instaladas y baseline

**Medición original (2026-09-03): 395 violaciones.**
**Última medición (2026-09-03): ~300 violaciones.**

| Código | Regla | Original | Actual | Severidad |
|---|---|---|---|---|
| `E722` | except desnudo (`except:`) | 56 | **0** ✅ | error — COMPLETO |
| `F821` | nombre no definido | 4 | **0** ✅ | error (bug make_automation corregido) |
| `F401` | import no usado | 38 | **0** ✅ | error — COMPLETO |
| `F841` | variable asignada y no usada | 18 | **0** ✅ | error — COMPLETO |
| `T201` | print() directo | 147 | ~145 | warn (baseline) |
| `E701` | múltiples statements en una línea | 87 | ~58 | warn (baseline) — sin autofix seguro |
| `F541` | f-string sin placeholder | 17 | 17 | warn (baseline) |
| `PLR0915` | demasiados statements por función | 16 | 17 | warn (baseline) |
| **Total** | | **395** | **~300** | |

**Burndowns ejecutados:**
1. `E722/F821`: `except:` → `except Exception:` + handlers silenciosos loguean el error.
2. `F401`: 40 imports órfanos removidos (`ruff --fix`) + casos manuales
   (`PIL.ImageFilter`, redundancia de assets en video_explicativo).
3. `F841`: 19 variables asignadas y no usadas removidas (incl. `result = ...execute()`
   en database_manager manteniendo la llamada con efecto real).

**Queda en baseline (warn):** `E701` (cosmético, sin autofix seguro — no se toca
para no arriesgar try/except en archivos críticos), `T201`, `F541`, `PLR0915`.


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