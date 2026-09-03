import os
import json
import asyncio
import threading
from contextlib import AsyncExitStack
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_CONFIG_PATH = os.path.join(BASE_DIR, "mcp_servers.json")

class MCPManager:
    def __init__(self):
        self.sessions = {}
        self.openai_tools = []
        self._loop = asyncio.new_event_loop()
        self._exit_stack = AsyncExitStack()
        self._ready_event = threading.Event()
        
        # Inicia a thread que manterá o event loop e as conexões de I/O abertas
        self._thread = threading.Thread(target=self._start_async_loop, daemon=True)
        self._thread.start()
        
        # Espera um pouco pela inicialização para garantir que as tools estejam prontas
        self._ready_event.wait(timeout=10)

    def _start_async_loop(self):
        asyncio.set_event_loop(self._loop)
        self._loop.run_until_complete(self._init_servers())
        self._loop.run_forever()

    async def _init_servers(self):
        if not os.path.exists(MCP_CONFIG_PATH):
            self._ready_event.set()
            return
            
        with open(MCP_CONFIG_PATH, "r", encoding="utf-8") as f:
            try:
                config = json.load(f)
                servers = config.get("mcpServers", {})
            except Exception:
                servers = {}

        for name, conf in servers.items():
            try:
                # Pegar variáveis de ambiente se existirem
                env = os.environ.copy()
                if "env" in conf:
                    env.update(conf["env"])

                server_params = StdioServerParameters(
                    command=conf["command"],
                    args=conf.get("args", []),
                    env=env
                )
                
                stdio_transport = await self._exit_stack.enter_async_context(stdio_client(server_params))
                read, write = stdio_transport
                session = await self._exit_stack.enter_async_context(ClientSession(read, write))
                
                await session.initialize()
                self.sessions[name] = session
                
                # Buscar tools disponíveis
                response = await session.list_tools()
                for tool in response.tools:
                    # Traduzir as ferramentas para o Schema esperado pelo OpenAI/Groq
                    self.openai_tools.append({
                        "type": "function",
                        "function": {
                            "name": f"{name}__{tool.name}",
                            "description": tool.description or f"Tool {tool.name} of {name}",
                            "parameters": tool.inputSchema
                        }
                    })
                print(f"[MCPManager] Servidor '{name}' inicializado. Ferramentas carregadas.")
            except Exception as e:
                print(f"[MCPManager] Erro ao iniciar servidor '{name}': {e}")
                
        self._ready_event.set()

    def get_tools(self):
        """Retorna as ferramentas mapeadas no formato da OpenAI."""
        return self.openai_tools

    def call_tool(self, name, args):
        """Executa a ferramenta remotamente no servidor MCP, de forma síncrona."""
        if "__" not in name:
            return f"Erro: Nome da ferramenta inválido '{name}'. Deve seguir o padrão 'servidor__ferramenta'."
            
        server_name, tool_name = name.split("__", 1)
        if server_name not in self.sessions:
            return f"Erro: Servidor MCP '{server_name}' não encontrado."
            
        # Executa a corrotina de forma thread-safe
        future = asyncio.run_coroutine_threadsafe(
            self._async_call_tool(server_name, tool_name, args),
            self._loop
        )
        try:
            return future.result(timeout=30)
        except Exception as e:
            return f"Erro ao executar ferramenta: {e}"

    async def _async_call_tool(self, server_name, tool_name, args):
        session = self.sessions[server_name]
        try:
            # Chama a tool via MCP SDK v1.x
            result = await session.call_tool(tool_name, arguments=args)
            
            # Formatar a saída como texto simples para o LLM
            output = ""
            if hasattr(result, 'content'):
                for content in result.content:
                    if content.type == "text":
                        output += content.text + "\n"
            return output.strip() if output else "Ação concluída com sucesso (sem saída de texto)."
        except Exception as e:
            return f"Erro interno da ferramenta: {e}"
