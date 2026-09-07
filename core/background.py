"""Tareas de segundo plano de la Laura (extraído de Laura.py — refactor prompt 09).

Monitorea Clima/Mercado para el widget y tareas de producción del Google
Calendar, en bucle cada 15 minutos. Recibe dependencias explícitas en vez
de depender de globals de Laura.py.
"""
import time

INTERVAL_SECONDS = 900  # 15 minutos


def background_tasks(client, model_to_use, say, takeCommand, skill_manager):
    """Bucle de monitorización en segundo plano (Climate/Market/Calendar)."""
    print("[Background] Iniciando tareas de monitoramiento (Clima/Mercado/Calendar)...")
    try:
        from skills.info_services import update_widget_cache
    except Exception as e:
        print(f"[Background Error] Fallo al importar info_services: {e}")
        return

    while True:
        try:
            print("[Background] Buscando actualizaciones de Clima y Mercado...")
            data = update_widget_cache()
            if data:
                print(f"[Background] Éxito: Datos actualizados a {data.get('updated')}")
            else:
                print("[Background Warning] update_widget_cache devolvió vacío.")
        except Exception as e:
            print(f"[Background Error] Error en la ejecución: {e}")

        # Verifica tareas de producción en el Google Calendar
        try:
            from skills.google_calendar import check_production_tasks
            print("[Background] Verificando tareas de producción en el Google Calendar...")
            check_production_tasks(client, model_to_use, say, takeCommand, skill_manager)
        except ImportError:
            pass  # Bibliotecas de Google no instaladas — se ignora silenciosamente
        except Exception as e:
            print(f"[Background] Error al verificar Google Calendar: {e}")

        time.sleep(INTERVAL_SECONDS)