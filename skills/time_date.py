import datetime

KEYWORDS = ["que dia é hoje", "qual a data", "que horas são", "que dia é", "dia de hoje", "horário atual"]

def execute(query, say, takeCommand, context=None):
    now = datetime.datetime.now()
    # Formata a data: Sexta-feira, 01 de Maio de 2026
    dias_semana = ["Segunda-feira", "Terça-feira", "Quarta-feira", "Quinta-feira", "Sexta-feira", "Sábado", "Domingo"]
    dia_semana = dias_semana[now.weekday()]
    data_extensa = now.strftime("%d/%m/%Y")
    hora_atual = now.strftime("%H:%M")
    
    if "hora" in query.lower() or "horário" in query.lower():
        say(f"Senhor, agora são exatamente {hora_atual}.")
    else:
        say(f"Hoje é {dia_semana}, dia {data_extensa}. Agora são {hora_atual}.")
    
    return True
