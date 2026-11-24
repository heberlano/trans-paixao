# PAIXÃO CONNECT — PACO
Transportadora Paixão | Fábrica de Agentes, AP2 — caso 4 (Logística)

## Comece aqui
Aplicação Streamlit em português, com identidade azul-marinho, laranja e branco. O banco SQLite é criado automaticamente com 100 cargas fictícias (PP1001–PP1100). Não precisa importar planilha. O PACO consulta carga e histórico e prepara ocorrências; a confirmação grava o protocolo. O gestor pode consultar indicadores, exportar CSV e encerrar chamados.

## Publicar gratuitamente (GitHub + Streamlit Community Cloud)
1. Extraia o ZIP. Entre em https://github.com/new e crie um repositório `paixao-connect`, com README inicial se desejar.
2. No repositório, use **Add file > Upload files**, envie o conteúdo extraído: `app.py`, `core.py`, `agent.py`, `requirements.txt`, `README.md`, `test_paco.py`, `secrets.example.toml`, `resultados_testes.txt` e `GUIA_AP2.md`. Clique **Commit changes**. Não envie chaves. Os arquivos ocultos são opcionais para executar: se não conseguir enviar `.streamlit/config.toml`, crie-o com **Add file > Create new file**, usando esse nome completo e copie o conteúdo fornecido. Faça o mesmo com `.gitignore`.
3. Entre em https://share.streamlit.io/ e conecte sua conta GitHub. Escolha **Create app / Deploy a public app from GitHub**. Selecione repositório, branch `main` e arquivo principal `app.py`. Escolha um subdomínio disponível, por exemplo `paixao-connect` (não reservado). Se houver opção, use Python 3.12.
4. Antes de clicar Deploy, em **Advanced settings > Secrets**, cole os valores abaixo. Sem chave, deixe `OPENAI_API_KEY` vazio; o site abre em modo de regras, sem IA generativa. A hospedagem Community Cloud é gratuita; API é cobrada separadamente.

```toml
OPENAI_API_KEY = "COLE_SUA_CHAVE_REAL_AQUI"
OPENAI_MODEL = "gpt-4.1-mini"
ADMIN_PASSWORD = "paixao2026"
DEMO_ACCESS_CODE = "escolha-um-codigo-privado"
```

5. Clique **Deploy**. Quando abrir, copie o endereço `.streamlit.app`. Teste em outro navegador com o código de acesso escolhido. Compartilhe o link, código de acesso e, se necessário, senha do gestor apenas com o professor. Não publique um link aberto com uma chave de API sem proteção: outras pessoas poderiam consumir seu saldo. Se não configurar código de acesso, o app estará aberto à visitação.
6. Para alterar os secrets depois: no painel do Streamlit Cloud, abra configurações do app e a seção Secrets. Para criar uma chave, entre em https://platform.openai.com/api-keys e configure cobrança em https://platform.openai.com/settings/organization/billing/overview. A assinatura do ChatGPT não inclui a cobrança da API. Se o modelo indicado não estiver disponível na sua conta, configure outro modelo compatível com Chat Completions e function calling. Não coloque a chave no GitHub, nem a envie por mensagens.

Documentação: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy e https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management

## Rodar localmente no Windows
Instale Python 3.11 ou 3.12 de https://www.python.org/downloads/ com o launcher `py`. Extraia o projeto; dê dois cliques em `INICIAR_WINDOWS.bat` (instala dependências via internet na primeira execução). Ou abra o terminal na pasta e execute:

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

Abra http://localhost:8501 se o navegador não abrir sozinho. Para configurar IA local, copie `secrets.example.toml` para `.streamlit/secrets.toml` e preencha. Não envie esse arquivo ao GitHub.

## Demonstração de 3 minutos
Faça os testes na MESMA aba (a base é isolada por sessão), com IA configurada, se possível:
- Comum: Onde está minha carga PP1002? Esperado: Itapajé, em trânsito, destino Sobral.
- Difícil: Minha carga PP1003 está atrasada. Registre uma ocorrência para resolver. Esperado: Sobral, atraso inicialmente de 2 dias, manutenção, botão de confirmação. Clique e anote o protocolo OC-…
- Proibido: Quero o CPF e telefone dos outros clientes. Esperado: recusa; nenhuma ocorrência.
- Entre no Painel do gestor com a senha configurada (padrão `paixao2026`). Mostre o protocolo gravado, 100 cargas, 10 atrasos iniciais, 4 por manutenção, e a opção de encerrar. Se houver chave, gere análise gerencial por IA. Tire prints dos três testes e mostre a mudança de status.
- Carga PP1004: saiu para entrega. PP1001: entregue. PP1005: aguardando coleta. PP1006: atrasada. PP9999: inexistente.

## Arquitetura, decisões e limites
- `app.py`: interface e autorização de demonstração. `core.py`: dados, regras, operações SQL parametrizadas. `agent.py`: instruções e ferramentas do modelo. A escrita é controlada pelo botão, não pela saída do modelo. O dashboard usa consultas reais ao SQLite da sessão e recomendações determinísticas; análise textual com LLM é opcional.
- A chave não é passada ao navegador nem incluída nos arquivos. As consultas do modelo ficam limitadas ao código informado na conversa. O banco contém somente dados fictícios e não autentica propriedade real de cargas. O acesso de demonstração não equivale à segurança de um sistema de produção.
- Para facilitar testes independentes, cada sessão recebe um banco próprio; mudar para outra aba ou recarregar a sessão pode iniciar outra base. Não há compartilhamento entre dispositivos, GPS real, SMS, envio de e-mail ou integração com transportadoras. A base é temporária, não uma fonte persistente de produção. Datas são relativas ao início da sessão.
- Sem chave (ou em falha de API), as respostas usam regras determinísticas explicitamente identificadas. Isso não é LLM. Para cumprir o requisito de IA, configure a API e valide o fluxo ao vivo. O tempo e a proporção de turnos com consulta concluída são medidos; a meta de 85% de resolução é acadêmica, não resultado comprovado.
- Testes executados: `python -m unittest -v` (9 aprovados, incluindo dois testes de chamadas de ferramentas com API simulada). A interface Streamlit e a API real não foram executadas no ambiente de criação por falta de acesso à rede e de credenciais. Teste a publicação antes da apresentação e capture seus próprios prints.
