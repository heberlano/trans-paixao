# Paixão Connect 3.3 — Atendimento e cenários de entrega

Atualização da versão 3.2. Preserva as 100 cargas iniciais, PACO, gestão, fretes, fotos, relatórios, reclamações, SLA e confirmação da resolução. Mantém as opções compactas de reclamação e gera duas cargas fictícias para cada telefone de formato válido que ainda não tenha associação. A primeira carga atrasada de uma nova associação usa o cenário Flamengo; a segunda associação usa o cenário da avó no jiu-jítsu. Os próximos motivos se alternam.

## Atualização no GitHub
1. Extraia o ZIP e envie todos os arquivos na raiz do repositório existente (não envie o ZIP). Inclua o novo `delay_scenarios.py`, `phone_lookup.py` e `lookup_ui.py`, além de `app.py`, `support_ui.py`, `resolution.py`, `paco.py`, `core.py`, `agent.py`, `reports.py` e `tracking_feedback.py`.
2. Salve em Commit changes. Confira `.streamlit/config.toml`; se não foi enviada, copie manualmente o arquivo para a pasta `.streamlit`. Preserve os Secrets já configurados. Não publique chaves.
3. Abra o endereço existente; use Reboot app no Streamlit Cloud se necessário. Se quiser retirar a documentação antiga do repositório, exclua `GUIA_AP2.md` manualmente, pois o upload não exclui arquivos antigos.

## Exemplos de consulta
- `(88) 00000-0001`: PP1002 e PP1003.
- `(85) 00000-0002`: PP1001 e PP1004.
- `(88) 00000-0003`: PP1005 e PP1006.
- `(86) 00000-0004`: PP1093 e PP1094.
- `(85) 00000-0005`: PP1064 e PP1065.
- `(88) 00000-0006`: PP1099 e PP1100.
- `(85) 00000-0007`: PP1010 e PP1020.
- `(86) 00000-0008`: PP1050 e PP1080.

Os números são intencionalmente fictícios, não discáveis; não use dados reais. A consulta preserva as oito associações originais. Um telefone de formato válido ainda não associado recebe duas cargas novas: uma atrasada e outra em trânsito. Repetir o telefone (inclusive com +55) recupera as mesmas cargas dentro da sessão. O número completo não é gravado no banco: utiliza-se uma chave derivada (HMAC) local; não se trata de autenticação de titularidade. O PACO pede o telefone se o cliente não souber seu código e solicita a escolha de uma das cargas encontradas. Os telefones digitados em formato reconhecido são tratados localmente e ocultados do histórico do chat.

## Teste
1. Início ou Rastreio > Não sei meu código de rastreio > `(88) 00000-0001` > selecionar PP1003.
2. PACO > “Não sei meu código de rastreio” > informar o telefone de exemplo > “PP1003 está atrasada” > confirmar registro.
3. Ajuda > Tenho um problema > escolher motivo na lista compacta > buscar pelo telefone > selecionar carga > registrar solicitação. Gestão > Resolver chamados > propor solução; Ajuda > Acompanhar solução > confirmar/reabrir.
4. Consultar `(88) 00000-1234` e selecionar a carga atrasada; em uma sessão nova, o motivo será a comemoração do Flamengo. Repetir a consulta e conferir que os códigos não mudam. Consultar outro telefone fictício, por exemplo `(85) 00000-5678`, para o cenário do jiu-jítsu. Testar PP9999, ABC123 e um telefone curto.
5. Códigos fixos: PP1003 Flamengo, PP1006 avó no jiu-jítsu, PP1093 bode na estrada, PP1094 café e futebol, PP1099 GPS e galinheiro, PP1100 festa de aniversário. Os motivos são inteiramente fictícios.

## Limites técnicos
- SQLite isolado por sessão; utilize a mesma aba para o fluxo cliente/gestor. Não é uma base de produção. Não há autenticação de titularidade do telefone, GPS, contatos externos, notificações em segundo plano ou persistência garantida após reinício. Fretes e SLA são estimativas de referência. Para uso comercial, implementar autenticação, controle de acesso, proteção de dados e integração de rastreio real.
- A API é opcional e usa os Secrets existentes. Sem API, o atendimento funciona por regras. A consulta de telefone é local nos dois modos.
- 63 testes automatizados passaram (56 anteriores, com expectativas atualizadas para a nova regra, e 7 novos). Sintaxe compilada. Streamlit não está instalado neste ambiente; renderização em celular e API ao vivo devem ser conferidas após publicação.

## Execução local
`python -m pip install -r requirements.txt`

`python -m streamlit run app.py`

`python -m unittest discover -v`
