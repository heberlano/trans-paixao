# Paixão Connect 2.0 | PACO

## Atualizar o site existente (GitHub + Streamlit Community Cloud)
1. Baixe e extraia o ZIP. Abra o mesmo repositório que publica `paixao-connect.streamlit.app`.
2. Na aba Code, clique Add file > Upload files. Envie **todos os arquivos da pasta extraída**, não o ZIP fechado nem uma pasta externa. `app.py` deve ficar na raiz. Confirme que `operations.py`, `paco.py` e `reports.py` foram adicionados e que `app.py` e `requirements.txt` foram substituídos. Os arquivos `core.py` e `agent.py` mantêm compatibilidade com a primeira versão. Os testes antigos continuam disponíveis.
3. Clique Commit changes. Se o upload não incluiu `.streamlit/config.toml`, abra esse arquivo pelo GitHub e use o lápis Edit this file. Substitua o conteúdo pelo config.toml fornecido. Se ainda não existir, use Add file > Create new file e informe `.streamlit/config.toml` como nome.
4. O Streamlit detecta mudanças automaticamente. Abra o mesmo endereço do site. Se não atualizar, acesse https://share.streamlit.io/ e use Reboot app. Em caso de erro, confira os logs e o caminho `app.py`.
5. Os Secrets já configurados permanecem no Streamlit. Não faça upload de uma chave real. Exemplo:

```toml
ADMIN_PASSWORD = "substitua-por-uma-senha-forte"
# OPENAI_API_KEY = "sua-chave" # configure nos Secrets, nunca no GitHub
OPENAI_MODEL = "gpt-4.1-mini"
# DEMO_ACCESS_CODE = "codigo-privado-para-o-professor"
```

Se não configurar a senha, a senha acadêmica padrão continua `paixao2026`. Recomendamos trocar. Sem chave de API, o modo por regras continua funcionando; com chave válida e modelo disponível, PACO usa chamadas de ferramentas. A API tem cobrança separada do ChatGPT. Recomendamos limite de uso e acesso restrito quando a chave estiver ativa.

## Teste rápido no mesmo navegador
- Início > Rastrear PP1002 > Ver mapa e histórico.
- PACO: "Minha carga PP1003 está atrasada. Registre uma ocorrência." Clique Confirmar registro. Copie o protocolo.
- Serviços > Protocolos: consulte PP1003 ou PP1003 + protocolo. Gestão > Protocolos: encerre. Serviços > Notificações: confira PP1003.
- Serviços > Frete: Fortaleza, Sobral, 20 kg, 50 x 40 x 30 cm. Calcule e registre. Gestão > Cotações: veja o registro. PACO também aceita "Frete Fortaleza para Sobral 20 kg 50x40x30" e depois "Quero registrar essa cotação".
- Gestão > Cargas: cadastre uma carga. Atualize a movimentação. Consulte o código novo (PP1101 em base inicial) no Rastreio.
- Serviços > Avaliação: use PP1001 e uma nota de 1 a 5. Veja o indicador na Gestão.
- Gestão > Frota: cadastre/edite veículo e motorista fictício, vincule carga ativa a veículo. Radar sinaliza alocações ligadas à manutenção.
- Gestão > Visão geral: confira indicadores, radar e exporte PDF. Se a API estiver configurada, teste a análise estratégica.
- PACO: "Quero o CPF dos outros clientes" deve recusar. Teste também no celular o contraste e o menu inferior.

## Execução local (opcional)
Python 3.11 ou 3.12 recomendado. Em terminal na pasta do projeto:

```
python -m pip install -r requirements.txt
python -m streamlit run app.py
python -m unittest -v test_paco test_v2
```

## Limites e decisões de projeto
- Projeto acadêmico, 100 cargas iniciais fictícias; não inserir dados reais. Códigos PP1001 a PP1100 mantidos. Banco SQLite e memória da conversa por sessão; abas/visitantes distintos não compartilham a base. Reabrir/reiniciar o app pode reinicializar os dados. A migração adiciona tabelas sem apagar uma base anterior existente.
- Mapa com coordenadas aproximadas de cidades e linhas esquemáticas, não GPS ou roteamento rodoviário. O mapa-base CARTO depende de conexão. O frete usa distância em linha reta x 1,25 e tarifa fictícia. Não é contratação. Valor cotado não é receita.
- Radar roda ao abrir/atualizar painel, sem tarefas de fundo. Notificações são internas ao app, sem push, WhatsApp, SMS ou e-mail. A alocação de frota não valida peso por veículo, jornada ou disponibilidade individual de motoristas.
- Avaliações por carga entregue, uma nota atualizável por carga. Protocolos e notificações acessíveis por código na base fictícia. Para produção real seria necessário autenticação de clientes, banco persistente, controle de acesso individual e revisão de LGPD/segurança.
- LLM em API externa não testado com chave real neste ambiente. Os testes de ferramentas usam cliente simulado. A interface Streamlit e mapa precisam de validação visual após publicação, incluindo CSS responsivo em diferentes aparelhos.
