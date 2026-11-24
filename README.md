# Paixão Connect 3.9 — Portal do cliente

Equilíbrio entre o visual da versão 3.5 e a navegação compacta da 3.6. Banner curto azul-marinho com ilustração de caminhão, detalhes em laranja, busca em um campo, quatro itens no menu, central de ajuda discreta e mapa sempre visível depois da consulta. Sem balão laranja do PACO ou lista pública de exemplos.

## Novidades 3.9
- Identidade institucional própria, inspirada na organização de serviços de portais de logística: cabeçalho, banner original em SVG, busca compacta e dois atalhos funcionais para cotação e avisos. Menu inferior com quatro opções no celular. Gestão permanece ao final de Mais.
- Sem dependência de imagens ou arquivos externos para o banner. Preservados mapa, prazos, integração PACO/Ajuda e frase de busca aprovada.
- Se já estiver na 3.8, substitua `app.py`, `lookup_ui.py` e `.streamlit/config.toml`. Os demais módulos não foram modificados.

## Novidades 3.8
- Atraso até hoje, tempo restante previsto e atraso total previsto são calculados em dias corridos, mantendo o prazo original. Exemplo: prazo original 22/11, hoje 24/11, previsão 27/11: 2 dias decorridos, 3 restantes, 5 de atraso total previsto.
- PACO, Ajuda e rastreamento compartilham a carga selecionada na sessão. Um chamado preparado pode continuar na Ajuda (inclusive avaria com fotos); o registro confirmado é consultável nos dois canais. Chamados duplicados continuam bloqueados.
- Gestão é a última opção em Mais, após frete, avisos e avaliação.
- Teste: busque PP1003, abra PACO e pergunte a previsão sem repetir o código; peça uma reclamação, continue na Ajuda, confirme o registro e volte ao PACO para perguntar o andamento do chamado.

## Etapas do transporte
Aguardando coleta; objeto coletado na origem; objeto recebido na sede da transportadora; em separação; em trânsito; objeto recebido na unidade de destino; saiu para entrega; entregue. Há também tentativa de entrega sem sucesso e registro de atraso. O atraso é exibido separadamente da etapa física, inclusive quando o gestor atualiza a movimentação de uma carga vencida. O histórico dos novos registros contém apenas movimentações simuladas já ocorridas, com datas e locais. Bases anteriores são lidas sem excluir registros; para cargas antigas que só informavam “Atrasada”, a etapa inicial de referência é “Em trânsito”. Não são adicionados eventos retroativos a bases antigas.

Códigos adicionais para testar em sessão nova: PP1067 (coletada), PP1068 (na sede), PP1069 (separação), PP1070 (unidade de destino), PP1071 (saiu para entrega), PP1072 (tentativa sem sucesso). PP1003 continua atrasada pelo Flamengo e PP1006 pelo jiu-jítsu. As cargas geradas por telefone também têm histórico detalhado.

Se já utiliza a versão 3.7, envie os arquivos do pacote de atualização rápida para a raiz do repositório. O pacote completo também está disponível. Os arquivos de teste e documentação são opcionais para execução, mas acompanham o código para verificação.

## Nova previsão
Toda carga atrasada recebe uma nova data estimada fictícia, inclusive as criadas por telefone. O cálculo determinístico usa o último registro, o prazo original e um intervalo de 1 a 3 dias conforme o código; ao chegar à data estimada, avança para a próxima janela. Uma nova previsão confirmada pelo gestor e aceita pelo cliente prevalece enquanto vigente. O prazo original não é alterado. A nova data aparece no rastreio, PACO, avisos e gestão. Não é garantia comercial.

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
1. Início ou Rastreio > campo de código ou telefone > `(88) 00000-0001` > selecionar PP1003.
2. PACO > “Não sei meu código de rastreio” > informar o telefone de exemplo > “PP1003 está atrasada” > confirmar registro.
3. Ajuda > Tenho um problema > escolher motivo na lista compacta > buscar pelo telefone > selecionar carga > registrar solicitação. Gestão > Resolver chamados > propor solução; Ajuda > Acompanhar solução > confirmar/reabrir.
4. Consultar `(88) 00000-1234` e selecionar a carga atrasada; em uma sessão nova, o motivo será a comemoração do Flamengo. Repetir a consulta e conferir que os códigos não mudam. Consultar outro telefone fictício, por exemplo `(85) 00000-5678`, para o cenário do jiu-jítsu. Testar PP9999, ABC123 e um telefone curto.
5. Códigos fixos: PP1003 Flamengo, PP1006 avó no jiu-jítsu, PP1093 bode na estrada, PP1094 café e futebol, PP1099 GPS e galinheiro, PP1100 festa de aniversário. Os motivos são inteiramente fictícios.

## Limites técnicos
- SQLite isolado por sessão; utilize a mesma aba para o fluxo cliente/gestor. Não é uma base de produção. Não há autenticação de titularidade do telefone, GPS, contatos externos, notificações em segundo plano ou persistência garantida após reinício. Fretes e SLA são estimativas de referência. Para uso comercial, implementar autenticação, controle de acesso, proteção de dados e integração de rastreio real.
- A API é opcional e usa os Secrets existentes. Sem API, o atendimento funciona por regras. A consulta de telefone é local nos dois modos.
- 90 testes automatizados passaram: 81 anteriores e nove novos de prazos e integração PACO/Ajuda. Sintaxe compilada. Streamlit não está instalado neste ambiente; renderização em celular e API ao vivo devem ser conferidas após publicação.

## Execução local
`python -m pip install -r requirements.txt`

`python -m streamlit run app.py`

`python -m unittest discover -v`
