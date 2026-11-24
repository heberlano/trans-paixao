# Paixão Connect 3.0 — Atendimento Resolutivo

Aplicativo acadêmico de logística da Transportadora Paixão. Preserva o banco inicial com 100 cargas e as funcionalidades 2.3 (fretes, rastreamento, mapa, PACO, avaliações de entrega, gestão de cargas e frota, notificações, PDF e CSV). Acrescenta a central de resolução, fotos e acompanhamento de chamados.

## Atualizar o site existente
1. Baixe e extraia `Paixao_Connect_3_0.zip`. No GitHub, abra o repositório que publica `paixao-connect.streamlit.app`.
2. Na aba Code, clique **Add file > Upload files**. Selecione o conteúdo extraído, não o ZIP ou uma pasta externa. Envie todos os arquivos juntos, para que as dependências sejam atualizadas no mesmo commit. Em especial: `app.py`, `core.py`, `operations.py`, `paco.py`, `resolution.py`, `support_ui.py`, `tracking_feedback.py`, `reports.py`, `requirements.txt`. `agent.py` permanece para compatibilidade. O arquivo `app.py` deve ficar na raiz.
3. Clique **Commit changes**. Confira `.streamlit/config.toml`. Se a pasta oculta não foi enviada, abra o arquivo no GitHub, use o lápis e cole o conteúdo do arquivo fornecido. Se não existir, crie o arquivo com nome `.streamlit/config.toml`.
4. Abra o mesmo endereço do aplicativo. Se necessário, acesse https://share.streamlit.io/ e use Reboot app. Em caso de falha, verifique Manage app/logs e os arquivos acima. Recomenda-se Python 3.11 ou 3.12.
5. Preserve os Secrets existentes. Nunca envie `.streamlit/secrets.toml` ou chaves ao GitHub. A senha acadêmica padrão é `paixao2026`, se não configurada. Troque a senha em `ADMIN_PASSWORD`. Para usar IA generativa, configure `OPENAI_API_KEY` e `OPENAI_MODEL` (padrão gpt-4.1-mini). Configure `DEMO_ACCESS_CODE` para restringir o uso da API e da demonstração. Sem chave, o PACO usa regras, incluindo a triagem e as operações de reclamações. A API tem cobrança separada do ChatGPT.

## Demonstração principal: na mesma aba, sem recarregar completamente
1. Início > Rastrear PP1003. Observe prazo original, atraso e motivo. Teste ABC123 (formato inválido), PP9999 (formato correto sem carga) e pp-1002 (aceito).
2. PACO: “Minha carga PP1003 está atrasada. Registre uma ocorrência.” Clique **Confirmar registro**. Copie o protocolo. Ou use Ajuda > Tenho um problema > Minha entrega está atrasada.
3. Gestão > Resolver chamados. Use sua senha. Selecione o chamado e registre uma atualização. Veja prioridade, meta de retorno e histórico. Em seguida, envie proposta de solução (com nova data opcional).
4. Ajuda > Acompanhar solução. Consulte PP1003 e protocolo. Escolha “Ainda preciso de ajuda” e descreva a pendência. Na Gestão, o chamado reaparece como Reaberto, com novo ciclo de primeiro retorno.
5. Na Gestão, proponha outra solução. No portal confirme “Sim, está resolvido” e dê uma nota. Só agora o chamado será Resolvido.
6. Gestão > Plano de ação PACO. Veja causas, ações, metas propostas, histórico e economia estimada. Gestão > Indicadores: baixe o PDF.
7. Ajuda > Tenho um problema > Minha mercadoria chegou danificada. Use PP1001 e uma foto fictícia de embalagem. Até 3 imagens JPG/PNG/WebP de até 5 MB, reprocessadas em JPEG sem metadados. Consulte o chamado e veja fotos na Gestão.
8. Ajuda > reagendar entrega: PP1002, escolha uma data. A data fica solicitada até o gestor propor uma previsão e o cliente aceitar. O prazo original permanece para medir atraso.
9. Início > Ver serviços: calcule frete Fortaleza/Sobral, 20 kg, 50x40x30; registre, veja em Gestão > Orçamentos. Confira avisos e avaliação de entrega PP1001. Gestão > Cargas/Frota: cadastre e atualize dados. PACO: “Quero CPF dos outros clientes” deve recusar.

## Execução local
```
python -m pip install -r requirements.txt
python -m streamlit run app.py
python -m unittest discover -v
```

## Decisões e limites
- Dados exclusivamente fictícios, banco SQLite e memória isolados por sessão. Abas distintas, visitantes e reinicializações não compartilham necessariamente os registros. Faça o teste cliente/gestor na mesma aba. A migração adiciona tabelas e preserva protocolos de uma base SQLite existente, sem garantir persistência no Streamlit Cloud.
- Alertas são calculados ao abrir/atualizar o app, deduplicados por carga e categoria na sessão; nada roda continuamente ou envia mensagens externas. O SLA é uma meta simulada de primeiro retorno humano (1/2/4/8h), não de entrega ou resolução, em horas corridas do relógio do servidor. Reabertura inicia novo ciclo; o histórico anterior fica registrado. A fila destaca casos fora da meta, sem acionar pessoas reais.
- A aceitação da proposta pode atualizar a nova previsão, não marcar a carga como entregue. O prazo original continua sendo usado para contar atrasos. O plano gerencial usa atrasos atuais, não um histórico causal validado. Economia é estimativa baseada nos turnos concluídos e hipóteses ajustáveis, não economia observada.
- Mapa aproximado, sem GPS; mapa-base CARTO depende de conexão. Frete fictício e distância estimada. Não há contratação, reembolso, alteração de endereço ou envio externo automáticos.
- Não use dados reais nem fotos de pessoas, etiquetas ou endereços. Códigos de carga e protocolos simulados não constituem autenticação. Para operação real: autenticação de clientes, controle de acesso, banco persistente compartilhado, política de retenção de fotos, LGPD e monitoramento independente.
- Testes automatizados validam banco, regras de negócio, PDF em memória e ferramentas com API simulada. Sintaxe Python validada. Streamlit, pydeck e credenciais reais não disponíveis no ambiente de desenvolvimento; renderização móvel, mapa, interação real no navegador e API ao vivo precisam de teste após publicação.
