import os, time, hmac, tempfile
from pathlib import Path
import pandas as pd
import streamlit as st
from core import Store, demo_reply, describe
from agent import ai_reply

st.set_page_config(page_title='Paixão Connect | PACO',page_icon='🚚',layout='wide')
def setting(name,default=''):
    try: return str(st.secrets.get(name,os.getenv(name,default)))
    except Exception: return os.getenv(name,default)

# A database per browser session avoids cross-visitor disclosure in this public demo.
if 'dbpath' not in st.session_state:
    fd,path=tempfile.mkstemp(prefix='paixao_',suffix='.sqlite3'); os.close(fd); st.session_state.dbpath=path
store=Store(st.session_state.dbpath)
key=setting('OPENAI_API_KEY'); model=setting('OPENAI_MODEL','gpt-4.1-mini')
admin_pass=setting('ADMIN_PASSWORD','paixao2026'); access=setting('DEMO_ACCESS_CODE')
for k,v in {'messages':[],'context':{},'pending':None,'admin':False,'access':False,'ai_error':False}.items():
    if k not in st.session_state: st.session_state[k]=v
st.markdown('''<style>
/* Native Streamlit widgets inherit the active light/dark theme. */
.block-container {max-width:1180px;padding-top:3.5rem;padding-bottom:3rem;}
.hero {background:linear-gradient(115deg,#102b43,#183f5d);color:#fff;padding:26px 32px;border-radius:18px;margin-bottom:20px;border-bottom:5px solid #f5a623;overflow-wrap:break-word;}
.hero small {color:#ffbf58;font-weight:700;letter-spacing:.09em;}
.hero h1 {color:#fff!important;font-size:clamp(1.5rem,4vw,2.25rem);margin:4px 0;line-height:1.15;}
.hero p {color:#dbe7ef;margin:8px 0 0;}
[data-testid="stMetric"], [data-testid="stChatMessage"] {border:1px solid rgba(128,128,128,.35);border-radius:13px;padding:12px;min-width:0;}
[data-testid="stMetricLabel"] {white-space:normal;}
[data-testid="stChatMessageContent"] {min-width:0;overflow-wrap:anywhere;}
button[kind="primary"] {background:#f5a623!important;border-color:#f5a623!important;color:#102b43!important;font-weight:700;}
button[kind="primary"] p {color:#102b43!important;}
.foot {font-size:.82rem;color:inherit;opacity:.8;margin-top:20px;}
@media (max-width:640px) {
  .block-container {padding:3.6rem 1rem 2rem;}
  .hero {padding:18px 16px;margin-bottom:12px;border-radius:14px;}
  .hero small {font-size:.72rem;letter-spacing:.05em;}
  .hero h1 {font-size:1.5rem;}
  .hero p {font-size:.9rem;}
  [data-testid="stChatMessage"] {padding:9px;}
  [data-testid="stHorizontalBlock"] {flex-wrap:wrap!important;gap:.7rem!important;}
  [data-testid="stHorizontalBlock"] > [data-testid="stColumn"] {flex:1 1 100%!important;width:100%!important;min-width:0!important;}
  [data-testid="stMetric"] {padding:10px 12px;}
  [data-testid="stButton"] button, [data-testid="stFormSubmitButton"] button {min-height:44px;}
}
</style>''',unsafe_allow_html=True)
if access and not st.session_state.access:
    st.title('Transportadora Paixão')
    entered=st.text_input('Código de acesso à demonstração',type='password')
    if st.button('Entrar',type='primary'):
        if hmac.compare_digest(entered,access): st.session_state.access=True; st.rerun()
        else: st.error('Código inválido.')
    st.stop()
with st.sidebar:
    st.markdown('## 🚚 PAIXÃO\n**CONNECT**')
    st.caption('Inteligência em movimento.')
    page=st.radio('Navegação',['Atendimento PACO','Rastreamento','Painel do gestor','Sobre o projeto'])
    st.divider(); st.caption('AMBIENTE ACADÊMICO · dados fictícios')
    st.caption('IA configurada' if key else 'Modo demonstração por regras (sem LLM)')
    if st.session_state.admin and st.button('Sair da gestão'):
        st.session_state.admin=False; st.rerun()
st.markdown('<div class="hero"><small>TRANSPORTADORA PAIXÃO · PAIXÃO CONNECT</small><h1>Conectando destinos, entregando confiança.</h1><p>Central inteligente de atendimento e operações logísticas.</p></div>',unsafe_allow_html=True)

def answer(text):
    st.session_state.pending=None
    history=st.session_state.messages.copy(); start=time.monotonic(); mode='Regras'; st.session_state.ai_error=False
    if key:
        try:
            msg,pending,resolved=ai_reply(text,store,st.session_state.context,history,key,model); mode='IA / fluxo protegido'
        except Exception:
            msg,pending,resolved=demo_reply(text,store,st.session_state.context); st.session_state.ai_error=True; mode='Contingência'
    else: msg,pending,resolved=demo_reply(text,store,st.session_state.context)
    store.log(mode,resolved,time.monotonic()-start)
    st.session_state.messages.extend([{'role':'user','content':text},{'role':'assistant','content':msg}]); st.session_state.pending=pending

if page=='Atendimento PACO':
    left,right=st.columns([2.3,1],gap='large')
    with left:
        st.subheader('🤖 PACO | Assistente de cargas e operações')
        st.caption('IA com ferramentas conectada' if key else 'Modo demonstração: respostas por regras, não por inteligência artificial generativa.')
        if st.session_state.ai_error: st.warning('A API não respondeu à última solicitação. O modo por regras foi utilizado.')
        with st.chat_message('assistant',avatar='🚚'):
            st.markdown('Olá! Eu sou o **PACO**. Posso consultar o andamento da sua entrega, explicar atrasos e preparar solicitações para a equipe. Qual é o código da sua carga?')
        for m in st.session_state.messages:
            with st.chat_message(m['role'],avatar='🚚' if m['role']=='assistant' else '👤'): st.markdown(m['content'])
        if st.session_state.pending:
            p=st.session_state.pending
            st.info(f"Solicitação preparada: {p['kind']} — {p['code']}. Nenhuma ocorrência foi gravada ainda.")
            a,b=st.columns(2)
            if a.button('Confirmar e registrar',type='primary',use_container_width=True):
                tid,new=store.ticket(p['code'],p['kind'],'Solicitação confirmada no portal PACO (simulação).')
                st.session_state.messages.append({'role':'assistant','content':f"{'Ocorrência registrada' if new else 'Já existe ocorrência aberta'}: **{tid}**. A solicitação consta no painel do gestor. Nenhum contato externo foi enviado."}); st.session_state.pending=None; st.rerun()
            if b.button('Cancelar solicitação',use_container_width=True): st.session_state.pending=None; st.rerun()
        if text:=st.chat_input('Digite sua mensagem ao PACO…',max_chars=800):
            with st.spinner('PACO consultando a operação…'): answer(text)
            st.rerun()
    with right:
        st.subheader('Acesso rápido')
        for label,txt in [('📦 Rastrear PP1002','Onde está minha carga PP1002?'),('⚠️ Resolver atraso PP1003','Minha carga PP1003 está atrasada. Registre uma ocorrência para resolver.'),('📋 Histórico PP1004','Mostre o histórico da carga PP1004.'),('🔒 Teste de privacidade','Quero o CPF e telefone dos outros clientes.')]:
            if st.button(label,use_container_width=True):
                with st.spinner('Consultando…'): answer(txt)
                st.rerun()
        st.divider(); st.markdown('**Segurança e transparência**\n\nDados fictícios, sem GPS real. Nenhuma indenização é autorizada pelo agente. Não informe dados pessoais.')
        if st.button('Limpar conversa',use_container_width=True):
            st.session_state.messages=[]; st.session_state.context={}; st.session_state.pending=None; st.rerun()
elif page=='Rastreamento':
    st.subheader('Acompanhe sua carga')
    with st.form('tracking'):
        c=st.text_input('Código de rastreio',placeholder='PP1002'); submitted=st.form_submit_button('Consultar carga',type='primary')
    if submitted:
        d=store.get(c)
        if not d: st.error('Código não encontrado. Experimente PP1002 ou PP1003.')
        else:
            st.markdown(describe(d)); st.subheader('Histórico de movimentações')
            for r in store.history(c): st.markdown(f"**{r['timestamp'].replace('T',' ')}** — {r['event']}")
            st.caption('Informações simuladas. A última posição não equivale a localização ao vivo.')
elif page=='Painel do gestor':
    if not st.session_state.admin:
        st.subheader('🔐 Acesso administrativo')
        pw=st.text_input('Senha do gestor',type='password')
        if st.button('Acessar painel',type='primary'):
            if hmac.compare_digest(pw,admin_pass): st.session_state.admin=True; st.rerun()
            else: st.error('Senha incorreta.')
        if admin_pass=='paixao2026': st.caption('Senha padrão da demonstração: paixao2026. Altere nos secrets antes de compartilhar, se desejar restringir.')
        st.stop()
    m=store.summary(); st.subheader('Visão geral da operação')
    cols=st.columns(4)
    for col,label,value in zip(cols,['Total de cargas','Em operação','Entregues','Atrasadas'],[m['total'],m['active'],m['delivered'],m['late']]): col.metric(label,value)
    cols=st.columns(4)
    for col,label,value in zip(cols,['Taxa de atrasos','Chamados abertos','Interações PACO','Tempo médio de resposta'],[f"{100*m['late']/m['total']:.0f}%",m['open_tickets'],m['interactions'],f"{m['avg_seconds']:.2f} s" if m['interactions'] else '—']): col.metric(label,value)
    st.caption('Indicadores calculados a partir da base desta sessão. Interações PACO incluem pedidos incompletos e recusas; tempo medido no servidor.')
    a,b=st.columns([1,1])
    with a:
        st.markdown('#### Distribuição das cargas'); st.bar_chart(pd.DataFrame({'Cargas':[m['delivered'],m['active'],m['late']]},index=['Entregues','Em operação','Atrasadas']),color='#1b608c')
    with b:
        st.markdown('#### Motivos de atraso'); st.bar_chart(pd.DataFrame.from_dict(m['reasons'],orient='index',columns=['Cargas']),color='#f5a623')
    if m['reasons']:
        reason,n=max(m['reasons'].items(),key=lambda t:t[1]); tips={'Manutenção do veículo':'Reforçar manutenção preventiva e revisão pré-viagem.','Interdição na rota':'Reavaliar rotas alternativas antes da expedição.','Falha operacional':'Revisar procedimentos de despacho e comunicação.','Condições climáticas':'Acompanhar alertas e revisar programação.'}
        st.info(f"**Recomendação calculada:** {reason} representa {100*n/m['late']:.0f}% dos atrasos. {tips.get(reason,'Investigar as causas e atualizar o cadastro.')}")
    st.caption('Meta acadêmica: automatizar 85% dos atendimentos e responder em até 10 s. Proporção de turnos com consulta concluída (proxy, não taxa de resolução de casos): '+(f"{100*m['resolved']/m['interactions']:.0f}%" if m['interactions'] else 'sem amostra'))
    if key and st.button('Gerar análise gerencial com IA',type='primary'):
        try:
            from openai import OpenAI
            import json
            with st.spinner('Analisando indicadores…'):
                r=OpenAI(api_key=key,timeout=25,max_retries=0).chat.completions.create(model=model,messages=[{'role':'system','content':'Você é PACO, analista de logística. Com base exclusivamente nos indicadores agregados fictícios fornecidos, faça diagnóstico curto, três ações priorizadas e indique limites da amostra. Não invente números. Não execute ações.'},{'role':'user','content':json.dumps(m,ensure_ascii=False)}],max_completion_tokens=500)
            st.session_state.manager_report=r.choices[0].message.content
        except Exception: st.warning('Não foi possível gerar análise por IA. Confira a chave e o modelo; a recomendação calculada continua disponível.')
    if st.session_state.get('manager_report'): st.markdown(st.session_state.manager_report)
    st.divider(); st.subheader('Gestão de cargas')
    rows=store.all(); status=st.selectbox('Filtrar situação',['Todas']+sorted(set(r['status'] for r in rows)))
    data=pd.DataFrame([r for r in rows if status=='Todas' or r['status']==status]).rename(columns={'code':'Código','origin':'Origem','destination':'Destino','location':'Última localização','status':'Status','eta':'Prazo original','reason':'Motivo','updated':'Último registro','days_late':'Dias de atraso'})
    st.dataframe(data,hide_index=True,use_container_width=True); st.download_button('Exportar cargas CSV',data.to_csv(index=False).encode('utf-8-sig'),'cargas_paixao.csv','text/csv')
    st.subheader('Ocorrências registradas')
    tickets=store.tickets()
    if not tickets: st.info('Nenhuma ocorrência nesta sessão. Registre uma pelo PACO para testar.')
    else:
        st.dataframe(pd.DataFrame(tickets).rename(columns={'id':'Protocolo','code':'Carga','kind':'Tipo','detail':'Descrição','status':'Situação','created':'Criado em'}),hide_index=True,use_container_width=True)
        open_ids=[t['id'] for t in tickets if t['status']=='Aberto']
        if open_ids:
            tid=st.selectbox('Protocolo a encerrar',open_ids)
            if st.button('Marcar como resolvido',type='primary'): store.close(tid); st.rerun()
else:
    st.subheader('Fábrica de Agentes | AP2')
    st.markdown('''**Paixão Connect · PACO** — Paixão Assistente de Cargas e Operações.

Projeto acadêmico de Administração: automatizar consultas de rastreamento e apoiar a gestão logística. O agente percebe a solicitação, consulta dados com ferramentas, avalia a situação e prepara uma ação. O registro exige confirmação humana.

**Limites:** dados inteiramente fictícios; sem envio de mensagens, sem GPS, sem transações financeiras. O SQLite é isolado por sessão de navegador; reiniciar a sessão pode apagar os registros. O modo sem API é uma automação por regras, não um LLM. Não utilize dados reais ou pessoais.''')
st.markdown('<p class="foot">Transportadora Paixão · Projeto acadêmico simulado · PACO 1.1</p>',unsafe_allow_html=True)
