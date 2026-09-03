# Laura A.I. - Laura V2

Este repositorio passa a considerar `LauraV2.py` como a versao principal e oficial do assistente.

O objetivo atual do projeto e manter uma experiencia local para Windows com:

- ativacao por voz
- resposta falada
- sistema modular de `skills`
- HUD/widget desktop
- automacoes locais e tarefas agendadas

Arquivos e fluxos antigos continuam no repositorio apenas como referencia ou legado, mas nao sao mais a base oficial de uso.

## Versao Oficial

- Entrada principal da logica: `LauraV2.py`
- Launcher recomendado: `main_launcher.py`
- Atalho de execucao: `run_laura_v2.bat`

Se a ideia for usar apenas a versao atual, trate `LauraV2.py` como a fonte de verdade para comportamento, dependencias e futuras refatoracoes.

## O Que O Laura V2 Faz

- escuta o usuario via microfone
- reconhece a palavra de ativacao "Laura"
- responde usando modelo de IA configurado no `.env`
- fala as respostas usando `edge-tts`
- executa habilidades carregadas dinamicamente da pasta `skills`
- acompanha agenda e tarefas em background
- recebe mensagens do widget/HUD por arquivo local
- atualiza status em arquivos JSON para integracao com a interface desktop

## Arquitetura Atual

### Nucleo

- `LauraV2.py`: loop principal, voz, IA, status, agendamentos e integracao com skills
- `config.py`: leitura das variaveis de ambiente e validacao basica das chaves
- `core/skill_manager.py`: carregamento dinamico e roteamento de skills
- `core/file_processor.py`: extracao de texto de arquivos suportados

### Interface Desktop

- `main_launcher.py`: sobe o nucleo e abre a HUD via `pywebview`
- `frontend/widget.html`: interface visual do modo desktop
- `status.json`: estado atual do assistente
- `widget_data.json`: dados auxiliares do widget
- `input.txt`: canal simples de entrada usado pela interface

### Skills

As habilidades ficam na pasta `skills/`. Cada skill deve expor:

```python
KEYWORDS = ["palavra-chave", "outra ativacao"]

def execute(query, say, takeCommand, context=None):
    ...
    return True
```

O carregamento e feito automaticamente na inicializacao.

## Requisitos

- Windows
- Python 3.12
- microfone configurado no sistema
- conexao com internet para IA, TTS e servicos externos

## Dependencias Principais

As dependencias Python estao em `requirements.txt`. Entre as mais importantes para o fluxo atual:

- `openai`
- `python-dotenv`
- `SpeechRecognition`
- `edge-tts`
- `pygame`
- `pycaw`
- `comtypes`
- `pyautogui`
- `fastapi` e `uvicorn` permanecem no repositorio, mas nao sao o foco desta versao

## Configuracao

Crie ou atualize o arquivo `.env` na raiz do projeto.

Variaveis mais relevantes para o `LauraV2.py`:

```env
GROQ_API_KEY=
GROQ_MODEL_NAME=llama-3.3-70b-versatile

OPENROUTER_API_KEY=
OPENROUTER_MODEL_NAME=openai/gpt-oss-120b:free

YOUTUBE_API_KEY=
WEATHER_API_KEY=
NEWS_API_KEY=

LAURA_AUTH_CODE=
```

Observacoes:

- O `LauraV2.py` esta configurado hoje para usar Groq como cliente principal.
- O `config.py` ainda mantem compatibilidade com OpenRouter e configuracoes antigas.
- Pelo menos uma chave de IA valida deve estar presente para o assistente responder.

## Como Executar

### Opcao recomendada

Execute:

```powershell
python main_launcher.py
```

Ou, no Windows:

```powershell
.\run_laura_v2.bat
```

### Execucao direta do nucleo

Se quiser rodar sem a HUD:

```powershell
python LauraV2.py
```

## Fluxo Basico de Uso

1. Inicie o sistema.
2. Aguarde a saudacao inicial.
3. Fale "Laura" seguido do comando.
4. Se necessario, o assistente fara perguntas complementares.
5. As skills podem executar acoes locais, consultas externas ou automacoes.

## Estrutura Resumida

```text
.
|-- LauraV2.py
|-- main_launcher.py
|-- run_laura_v2.bat
|-- config.py
|-- requirements.txt
|-- core/
|   |-- skill_manager.py
|   `-- file_processor.py
|-- skills/
|-- frontend/
|   `-- widget.html
|-- status.json
|-- agenda.json
|-- scheduled_tasks.json
|-- widget_data.json
`-- input.txt
```

## Arquivos Legados Ou Secundarios

Os fluxos antigos foram agrupados na pasta `legacy/` e nao definem mais a versao oficial:

- `legacy/voice-v1/`: versao anterior baseada em `Laura.py`
- `legacy/web-stack/`: backend FastAPI antigo, deploy serverless e UI React antiga

Eles podem ser mantidos temporariamente por compatibilidade, testes antigos ou referencia de implementacao. A recomendacao e evitar novas funcionalidades nesses fluxos enquanto a consolidacao da versao oficial nao for concluida.

## Estado Atual Do Repositorio

Este README foi atualizado para refletir a decisao de consolidar o projeto em torno do `LauraV2.py`.

Proximos passos naturais dessa limpeza:

- revisar scripts antigos
- revisar nomes e referencias internas ainda herdadas de "Laura"
- reduzir dependencias que pertencem apenas a versoes descontinuadas
- documentar melhor as skills nativas

## Licenca

Este projeto utiliza a licenca MIT. Consulte o arquivo `LICENSE`.
