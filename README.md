# Paixão Connect 4.1 — PACO discreto e Ajuda guiada

## Atualização da versão 4.0
- PACO fechado por padrão em todas as telas. O botão azul-marinho abre a janela compacta sem alterar a largura do portal. Minimizar preserva a conversa, a carga e o protocolo. Atalhos iniciais: Rastrear, Atraso, Avaria. O envio usa um botão de seta; o campo não exibe o contador de caracteres. Limite de 800 caracteres validado no envio.
- O chat abre sobre o site no computador e como painel compacto acima do menu no celular. A navegação para Ajuda minimiza o chat, sem perder os dados.
- Ajuda: escolha resolver ou acompanhar; localize a entrega com código ou telefone; selecione o motivo e confirme o envio. A busca aceita os mesmos telefones fictícios e códigos do rastreamento. A entrega atual é reaproveitada; é possível trocar de carga. Se já houver um chamado ativo para o mesmo motivo, o usuário recebe um atalho para acompanhá-lo. O protocolo selecionado fica disponível no PACO. Fotos, reagendamento, avaliação, confirmação e reabertura permanecem disponíveis quando aplicáveis.
- O controle Manage app pertence ao Streamlit Community Cloud. Aplicado CSS para ocultar elementos conhecidos da hospedagem quando estão dentro do documento e margem inferior de segurança no desktop. Não há garantia de ocultação se o controle estiver no shell externo da hospedagem. Teste também em aba anônima, sem login de proprietário. A administração continua acessível em share.streamlit.io.
- Mapas, previsão de entrega, base de dados, motivos engraçados, fretes, avaliações e gestão preservados. Gestão continua como última opção do menu Mais. Nenhuma alteração nos Secrets, dependências ou config.toml.

## Como atualizar
1. Extraia o ZIP de atualização rápida e substitua `app.py`, `paco_window.py` e `support_ui.py` na raiz do repositório, em um único commit. Os testes e README são opcionais para executar o aplicativo.
2. Clique em Commit changes. Abra o mesmo endereço do site. Se necessário, reinicie pelo painel Streamlit Cloud.
3. Em aba nova, confira que o PACO começa fechado e que abrir/minimizar não reduz a largura. Consulte PP1003; confira o mapa, depois abra PACO e pergunte a previsão sem repetir o código. Prepare uma reclamação, continue na Ajuda e confirme. Consulte o mesmo chamado e verifique que o sistema evita duplicação.
4. Na Ajuda, teste um telefone fictício com DDD, selecione uma entrega, escolha Avaria e verifique que o campo de fotos aparece. Teste um chamado com solução proposta e sua confirmação ou reabertura. Confira também no celular.

## Validação 4.1
111 testes automatizados passaram (99 anteriores, com a expectativa de abertura atualizada, e 12 adicionais). Os novos testes utilizam widgets simulados e SQLite, sem Streamlit real. A sintaxe foi compilada. Não foi possível renderizar a interface no navegador real ou executar a API; o posicionamento e a ocultação de elementos do Streamlit Cloud devem ser conferidos após a publicação. A busca por telefone continua simulada e não é autenticação de titularidade.

---

## Histórico de versões
# Paixão Connect 4.0 — PACO flutuante

## Novidades 4.0
- PACO em janela flutuante no canto inferior direito, com widgets nativos do Streamlit conectados à base e às ferramentas originais. A primeira visita abre a janela em telas com largura superior a 900 px; em telas menores, exibe apenas um botão discreto de boas-vindas em azul-marinho, que abre o atendimento ao toque. O botão permanece acessível depois de minimizar.
- Menu com três itens: Início, Ajuda e Mais. Gestão continua como última opção de Mais. O PACO não é uma página separada; os atalhos anteriores abrem a janela na página atual. Ao seguir para a Ajuda pelo chat, a janela minimiza e preserva carga, pendência e protocolo.
- Histórico, confirmação de ações, cancelamento, integração com as reclamações e carregamento durante consultas preservados. Em desktop amplo o layout reserva espaço ao lado do chat, e no celular a janela fica acima da barra inferior, com rolagem e botão Minimizar.
- Nenhuma alteração no mapa, na base, nas regras de negócio, na frase de rastreamento, nas configurações de API ou nos motivos de atraso. Não há novas dependências.

### Atualização rápida da versão 3.9
1. Faça uma cópia do repositório ou mantenha o histórico do GitHub.
2. Extraia o pacote de atualização. Substitua `app.py` e adicione `paco_window.py` na raiz do repositório, no mesmo commit. O arquivo `test_paco_window.py` é opcional para o funcionamento, mas permite reproduzir os testes. README e relatório de testes são documentação.
3. Clique em Commit changes. Abra o endereço já publicado. Se necessário, use Reboot app no Streamlit Cloud. Não altere o `config.toml`, `requirements.txt` ou Secrets se já estiver na 3.9.
4. Em uma aba nova no computador, confira a abertura automática. No celular, confira o botão de boas-vindas, toque para abrir e minimize. Teste PP1003, pergunte pelo prazo, registre um chamado e clique em Acompanhar meu chamado. Reabra a janela para conferir a conversa. Em Mais, Gestão deve aparecer por último. Teste o mapa de rastreamento depois de minimizar.

### Validação 4.0
90 testes anteriores e 9 novos testes automatizados de estado e interação com widgets simulados passaram. Sintaxe validada. O ambiente não dispõe do Streamlit e não conseguiu instalar a dependência, portanto os testes não executam o navegador real, a API real ou a renderização do mapa. A posição flutuante usa CSS de contêineres identificados por chave; deve ser conferida na versão publicada do Streamlit, especialmente no iPhone e em modo paisagem. O estado da janela e a conversa são preservados durante a sessão, não entre sessões independentes.

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
- 99 testes automatizados passaram: 90 anteriores e nove novos da janela PACO. Sintaxe compilada. Streamlit não está instalado neste ambiente; renderização em celular e API ao vivo devem ser conferidas após publicação.

## Execução local
`python -m pip install -r requirements.txt`

`python -m streamlit run app.py`

`python -m unittest discover -v`
