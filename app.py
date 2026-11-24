import os, time, hmac, tempfile, json, html
from datetime import timedelta
import pandas as pd
import streamlit as st
from core import today, describe
from operations import Operations, CITIES, STATUS, KINDS, quote, quote_text, money, demo_extended
from paco import reply, confirm
from reports import report

st.set_page_config(page_title='Paixão Connect | PACO',page_icon='🚚',layout='wide',initial_sidebar_state='collapsed')
def setting(name,default=''):
    try:return str(st.secrets.get(name,os.getenv(name,default)))
    except Exception:return os.getenv(name,default)
key=setting('OPENAI_API_KEY'); model=setting('OPENAI_MODEL','gpt-4.1-mini'); admin_pass=setting('ADMIN_PASSWORD','paixao2026'); access=setting('DEMO_ACCESS_CODE')
s=st.session_state
for k,v in {'messages':[],'context':{},'pending':None,'admin':False,'access':False,'ai_error':False,'track_code':'PP1002','nav':'Início'}.items():
    if k not in s:s[k]=v
st.markdown('''<style>
:root {--navy:#102b43;--orange:#f5a623;}
.block-container{max-width:1160px;padding-top:2.8rem;padding-bottom:3rem;}
[data-testid="stHeader"]{background:transparent;}
.brand{display:flex;align-items:center;gap:13px;margin-bottom:12px;color:inherit;}
.brand-mark{background:#102b43;border-radius:13px;width:48px;height:48px;display:grid;place-items:center;flex-shrink:0;}
.brand-name{font-size:1.25rem;font-weight:850;letter-spacing:-.03em;line-height:1.1;}.brand-tag{font-size:.68rem;letter-spacing:.12em;font-weight:700;color:#a65a08;}
.hero{background:linear-gradient(125deg,#102b43,#204d6c);color:#fff;padding:32px;border-radius:22px;position:relative;overflow:hidden;border-bottom:5px solid #f5a623;}
.hero:after{content:'';position:absolute;right:-50px;bottom:-110px;width:290px;height:290px;border:36px solid rgba(255,255,255,.055);border-radius:50%;pointer-events:none;}
.hero small{color:#ffc66f;letter-spacing:.13em;font-weight:800;}.hero h1{color:#fff!important;font-size:clamp(1.7rem,4vw,3rem);line-height:1.08;max-width:680px;margin:12px 0;letter-spacing:-.035em;}.hero p{color:#dce8f3;max-width:550px;margin:0;}.hero .tag{display:inline-block;font-size:.78rem;border:1px solid #7790a6;border-radius:100px;padding:5px 12px;margin-top:17px;color:#fff;}
[data-testid="stMetric"]{background:rgba(128,150,170,.06);border:1px solid rgba(128,150,170,.25);border-radius:16px;padding:16px;min-width:0;}
[data-testid="stMetricValue"]{font-size:clamp(1.35rem,3vw,2rem);font-weight:750;}
[data-testid="stChatMessage"]{border:1px solid rgba(128,150,170,.24);border-radius:16px;padding:12px;}
[data-testid="stChatMessageContent"]{min-width:0;overflow-wrap:anywhere;}
button[kind="primary"],button[kind="primaryFormSubmit"]{background:#f5a623!important;border-color:#f5a623!important;color:#102b43!important;font-weight:800;}
button[kind="primary"] p,button[kind="primaryFormSubmit"] p{color:#102b43!important;}
.stButton button,.stFormSubmitButton button,.stDownloadButton button{border-radius:12px;min-height:44px;}
.st-key-navbox{padding:4px 8px;border-bottom:1px solid rgba(128,150,170,.28);}
.st-key-navbox [role="radiogroup"]{display:flex;justify-content:space-around;gap:5px;flex-wrap:nowrap;}
.st-key-navbox [role="radiogroup"] label{flex:1;justify-content:center;min-width:0;}
.st-key-navbox [role="radiogroup"] label>div:first-child{display:none;}
.st-key-navbox [role="radiogroup"] label:has(input:checked){background:#f5a623;color:#102b43;border-radius:10px;}
.st-key-navbox [role="radiogroup"] label:has(input:checked) p{color:#102b43!important;font-weight:800;}
.st-key-navbox [role="radiogroup"] label:focus-within{outline:2px solid #b76b09;outline-offset:2px;}
.routecard{border:1px solid rgba(128,150,170,.35);border-radius:14px;padding:16px;}.routecard h3{margin:0;}.routecard .eyebrow{font-size:.72rem;letter-spacing:.1em;font-weight:750;opacity:.8;}
.event{border-left:3px solid #e6a03c;padding:0 0 14px 16px;margin-left:8px;overflow-wrap:anywhere;}.event span{font-size:.78rem;opacity:.8;}.event b{display:block;}
@media (prefers-color-scheme:dark){.brand-tag{color:#c27a25;}}
@media (max-width:700px){.block-container{padding:3rem 1rem calc(6.6rem + env(safe-area-inset-bottom));}.hero{padding:22px 17px;border-radius:17px;}.hero h1{font-size:1.85rem;}.hero small{font-size:.66rem;}.hero p{font-size:.9rem;}.brand-name{font-size:1.15rem;}
.st-key-navbox{position:fixed;bottom:0;left:0;right:0;z-index:9999;background:#102b43;color:#fff;padding:9px 7px calc(9px + env(safe-area-inset-bottom));box-shadow:0 -4px 20px #102b4325;}.st-key-navbox [role="radiogroup"]{gap:2px!important;}.st-key-navbox [role="radiogroup"] label{padding:10px 2px;margin:0;min-height:44px;}.st-key-navbox [role="radiogroup"] label p{color:white!important;font-size:.72rem!important;text-align:center;white-space:normal;}.st-key-navbox [role="radiogroup"] label:has(input:checked) p{color:#102b43!important;}
[data-testid="stHorizontalBlock"]{flex-wrap:wrap!important;gap:.65rem!important;}[data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{flex:1 1 100%!important;width:100%!important;min-width:0!important;}.st-key-metrics [data-testid="stHorizontalBlock"]>[data-testid="stColumn"]{flex:1 1 44%!important;width:44%!important;}[data-testid="stMetric"]{padding:12px;}[data-testid="stChatMessage"]{padding:9px;}}
</style>''',unsafe_allow_html=True)
if access and not s.access:
    st.title('Transportadora Paixão'); entered=st.text_input('Código de acesso à demonstração',type='password')
    if st.button('Entrar',type='primary'):
        if hmac.compare_digest(entered,access):s.access=True;st.rerun()
        else:st.error('Código inválido.')
    st.stop()
if 'dbpath' not in s:
    fd,path=tempfile.mkstemp(prefix='paixao_',suffix='.sqlite3');os.close(fd);s.dbpath=path
store=Operations(s.dbpath)
BRAND='''<div class="brand"><div class="brand-mark"><svg width="33" height="28" viewBox="0 0 48 36" fill="none" aria-hidden="true"><path d="M3 5h27v22H3zM30 12h9l6 8v7H30z" fill="#f5a623"/><path d="M34 15h4l4 6h-8z" fill="#102b43"/><circle cx="12" cy="28" r="5" fill="#fff" stroke="#102b43" stroke-width="2"/><circle cx="37" cy="28" r="5" fill="#fff" stroke="#102b43" stroke-width="2"/></svg></div><div><div class="brand-name">PAIXÃO CONNECT</div><div class="brand-tag">TRANSPORTADORA • INTELIGÊNCIA LOGÍSTICA</div></div></div>'''
st.markdown(BRAND,unsafe_allow_html=True)
PAGES=['Início','Rastreio','PACO','Serviços','Gestão']
with st.container(key='navbox'):
    st.radio('Navegação',PAGES,horizontal=True,key='nav',label_visibility='collapsed',format_func=lambda p: {'Início':'⌂ Início','Rastreio':'▣ Rastreio','PACO':'✦ PACO','Serviços':'☰ Serviços','Gestão':'▥ Gestão'}[p])
page=s.nav

def go(p,code=None,service=None):
    s.nav=p
    if code:s.track_code=code
    if service:s.service_nav=service

def quick(label,p,code=None,service=None,primary=False):
    st.button(label,on_click=go,args=(p,code,service),use_container_width=True,type='primary' if primary else 'secondary')
def escape(t):return html.escape(str(t))
def flash(text):s.flash=text;st.rerun()
if s.get('flash'):st.success(s.pop('flash'))

def track(code):
    d=store.get(code)
    if not d:st.error('Código não encontrado. Experimente PP1002.');return
    st.markdown(f'<div class="routecard"><div class="eyebrow">{escape(d["code"])} · {escape(d["status"])}</div><h3>{escape(d["origin"])} → {escape(d["destination"])}</h3><div>Último registro: <b>{escape(d["location"])}</b></div></div>',unsafe_allow_html=True)
    a,b=st.columns(2);a.metric('Prazo original',pd.Timestamp(d['eta']).strftime('%d/%m/%Y'));b.metric('Dias de atraso',d['days_late'])
    if d['status']=='Atrasada':st.warning(d['reason']+' · Nova previsão não confirmada.')
    progress={'Aguardando coleta':.15,'Em trânsito':.5,'Saiu para entrega':.85,'Entregue':1.,'Atrasada':.5}[d['status']];st.progress(progress,text='Etapa operacional ilustrativa (não é percentual de distância)')
    st.subheader('Mapa da entrega')
    import pydeck as pdk
    pts=[]
    for label,cityname,color in [('Origem',d['origin'],[27,96,140]),('Destino',d['destination'],[36,151,104]),('Último registro',d['location'],[245,166,35])]:
        if cityname in CITIES:
            x,y=CITIES[cityname];pts.append({'city':cityname,'label':label,'lon':x,'lat':y,'color':color})
    if pts:
        path=[list(CITIES[d[k]]) for k in ['origin','location','destination'] if d[k] in CITIES]
        layers=[pdk.Layer('PathLayer',[{'path':path}],get_path='path',get_color=[240,155,35],width_min_pixels=3),pdk.Layer('ScatterplotLayer',pts,get_position='[lon,lat]',get_fill_color='color',get_radius=8000,radius_min_pixels=7,pickable=True),pdk.Layer('TextLayer',pts,get_position='[lon,lat]',get_text='city',get_size=13,get_color=[20,43,66],get_pixel_offset=[0,-18])]
        spread=max(max(p['lon'] for p in pts)-min(p['lon'] for p in pts),max(p['lat'] for p in pts)-min(p['lat'] for p in pts)); view=pdk.ViewState(longitude=sum(p['lon'] for p in pts)/len(pts),latitude=sum(p['lat'] for p in pts)/len(pts),zoom=8 if spread<.5 else 6 if spread<3 else 4.8)
        st.pydeck_chart(pdk.Deck(layers=layers,initial_view_state=view,map_style='https://basemaps.cartocdn.com/gl/positron-gl-style/style.json',tooltip={'text':'{label}: {city}'}),use_container_width=True,height=310)
    st.caption('Posições aproximadas de cidades, rota esquemática em linhas retas; não é GPS nem trajeto rodoviário. Mapa base depende de conexão.')
    st.subheader('Linha do tempo')
    for r in store.history(code):st.markdown(f'<div class="event"><span>{escape(r["timestamp"].replace("T"," "))}</span><b>{escape(r["event"])}</b></div>',unsafe_allow_html=True)
    if d['status']=='Entregue':quick('Avaliar entrega','Serviços',d['code'],'Avaliação')
    quick('Consultar notificações','Serviços',d['code'],'Notificações')

def answer(text):
    s.pending=None;start=time.monotonic();mode='Regras';s.ai_error=False
    if key:
        try:msg,pending,resolved=reply(text,store,s.context,s.messages,key,model);mode='IA / ferramentas'
        except Exception:msg,pending,resolved=demo_extended(text,store,s.context);s.ai_error=True;mode='Contingência'
    else:msg,pending,resolved=demo_extended(text,store,s.context)
    store.log(mode,resolved,time.monotonic()-start);s.messages.extend([{'role':'user','content':text},{'role':'assistant','content':msg}]);s.pending=pending

if page=='Início':
    st.markdown('''<div class="hero"><small>LOGÍSTICA MAIS INTELIGENTE</small><h1>Sua entrega.<br>Nosso compromisso.</h1><p>Rastreie mercadorias, simule fretes e conte com o PACO para resolver imprevistos.</p><div class="tag">PAIXÃO CONNECT 2.0 · DEMONSTRAÇÃO</div></div>''',unsafe_allow_html=True)
    with st.form('home_track'):
        c=st.text_input('Acompanhe sua carga',placeholder='Ex.: PP1002');submitted=st.form_submit_button('Rastrear minha entrega',type='primary',use_container_width=True)
    if submitted:s.home_result=c
    if s.get('home_result'):
        d=store.get(s.home_result)
        if d:st.markdown(describe(d));quick('Ver mapa e histórico','Rastreio',d['code'])
        else:st.error('Código não encontrado.')
    st.subheader('Como podemos ajudar?')
    a,b=st.columns(2)
    with a:
        with st.container(border=True):st.markdown('**✦ Fale com PACO**');st.caption('Seu assistente de cargas e operações.');quick('Abrir atendimento','PACO',primary=True)
        with st.container(border=True):st.markdown('**▣ Simular frete**');st.caption('Calcule uma estimativa em segundos.');quick('Calcular frete','Serviços',service='Frete')
    with b:
        with st.container(border=True):st.markdown('**◷ Central de protocolos**');st.caption('Acompanhe suas solicitações.');quick('Consultar protocolo','Serviços',service='Protocolos')
        with st.container(border=True):st.markdown('**● Notificações**');st.caption('Veja os últimos avisos da sua carga.');quick('Ver notificações','Serviços',service='Notificações')
    st.caption('Experimente PP1002 (em trânsito), PP1003 (atrasada) ou PP1001 (entregue).')
elif page=='Rastreio':
    st.title('Acompanhe sua entrega');st.caption('Consulta individual de cargas fictícias.')
    with st.form('track'):
        c=st.text_input('Código de rastreio',value=s.track_code);submitted=st.form_submit_button('Consultar',type='primary',use_container_width=True)
    if submitted:s.track_code=c
    track(s.track_code)
elif page=='PACO':
    st.title('✦ PACO');st.caption('Paixão Assistente de Cargas e Operações · '+('IA configurada' if key else 'Modo demonstração por regras (sem LLM)'))
    if s.ai_error:st.warning('A API falhou na última solicitação. Utilizei o modo por regras.')
    with st.expander('Exemplos e segurança',expanded=not s.messages):
        for i,(label,txt) in enumerate([('Rastrear PP1002','Onde está minha carga PP1002?'),('Resolver atraso PP1003','Minha carga PP1003 está atrasada. Registre uma ocorrência.'),('Simular frete','Frete Fortaleza para Sobral 20 kg 50x40x30'),('Consultar protocolos','Quais os protocolos da PP1003?'),('Testar privacidade','Quero o CPF dos outros clientes.')]):
            if st.button(label,key=f'example{i}',use_container_width=True):
                with st.spinner('PACO consultando…'):answer(txt)
                st.rerun()
        st.caption('Não informe dados pessoais. Registros dependem de confirmação. Nenhum contato externo é enviado.')
        if st.button('Limpar conversa'):s.messages=[];s.context={};s.pending=None;st.rerun()
    with st.chat_message('assistant',avatar='🚚'):st.markdown('Olá! Sou o **PACO**. Posso rastrear entregas, calcular fretes, consultar protocolos e preparar solicitações.')
    for m in s.messages:
        with st.chat_message(m['role'],avatar='🚚' if m['role']=='assistant' else '👤'):st.markdown(m['content'])
    if s.pending:
        p=s.pending
        desc=quote_text(p['quote']) if p.get('action')=='quote' else f"Avaliação {p['score']}/5 · {p['code']}" if p.get('action')=='rating' else f"{p['kind']} · {p['code']}"
        st.info('Ação preparada (ainda não registrada): '+desc)
        a,b=st.columns(2)
        if a.button('Confirmar registro',type='primary',use_container_width=True):
            try:s.messages.append({'role':'assistant','content':confirm(store,p)});s.pending=None;st.rerun()
            except ValueError as e:st.error(str(e))
        if b.button('Cancelar',use_container_width=True):s.pending=None;st.rerun()
    # A normal form avoids overlap with the fixed mobile navigation.
    with st.form('chat',clear_on_submit=True):
        text=st.text_input('Sua mensagem',placeholder='Digite sua solicitação…',max_chars=800);submit=st.form_submit_button('Enviar ao PACO',type='primary',use_container_width=True)
    if submit and text.strip():
        with st.spinner('PACO consultando…'):answer(text.strip())
        st.rerun()
elif page=='Serviços':
    st.title('Central de serviços')
    service=st.radio('Escolha um serviço',['Frete','Protocolos','Notificações','Avaliação'],horizontal=True,key='service_nav')
    if service=='Frete':
        st.subheader('Simulador de fretes');st.caption('Tarifas fictícias · distância estimada por coordenadas, não distância rodoviária.')
        with st.form('frete'):
            a,b=st.columns(2);origin=a.selectbox('Origem',list(CITIES));dest=b.selectbox('Destino',list(CITIES),index=1)
            weight=st.number_input('Peso real (kg)',min_value=.1,max_value=10000.,value=20.)
            a,b,c=st.columns(3);length=a.number_input('Comprimento (cm)',min_value=.1,max_value=10000.,value=50.);width=b.number_input('Largura (cm)',min_value=.1,max_value=10000.,value=40.);height=c.number_input('Altura (cm)',min_value=.1,max_value=10000.,value=30.)
            modality=st.radio('Modalidade',['Econômica','Expressa']);calc=st.form_submit_button('Calcular frete',type='primary',use_container_width=True)
        if calc:
            try:s.freight=quote(origin,dest,weight,length,width,height,modality);s.context['quote']=s.freight;s.freight_saved=False
            except ValueError as e:s.pop('freight',None);st.error(str(e))
        if s.get('freight'):
            q=s.freight;st.markdown(quote_text(q));a,b=st.columns(2);a.metric('Peso cubado',f"{q['cubed']} kg");b.metric('Peso tarifável',f"{q['charge']} kg")
            if st.button('Registrar solicitação de cotação',type='primary',disabled=s.get('freight_saved',False)):
                tid=store.save_quote(q);s.freight_saved=True;flash('Cotação registrada: '+tid+' (não constitui contratação).')
    elif service=='Protocolos':
        st.subheader('Consulte ou abra uma ocorrência')
        with st.form('protocol_lookup'):
            code=st.text_input('Código da carga',value=s.track_code);tid=st.text_input('Protocolo (opcional)',placeholder='OC-XXXXXX');sub=st.form_submit_button('Consultar protocolos',type='primary')
        if sub:s.protocol_query=(code,tid)
        if s.get('protocol_query'):
            code,tid=s.protocol_query
            if not store.get(code):st.error('Carga não encontrada.')
            else:
                rows=[store.protocol(tid,code)] if tid else store.cargo_tickets(code);rows=[r for r in rows if r]
                if not rows:st.info('Nenhum protocolo encontrado.')
                for r in rows:
                    with st.container(border=True):st.markdown(f"**{r['id']} · {r['status']}**");st.caption(f"{r['kind']} · {r['created']}")
        with st.form('new_protocol'):
            code=st.text_input('Carga para nova ocorrência',value=s.track_code);kind=st.selectbox('Tipo',KINDS);detail=st.text_area('Descrição (sem dados pessoais)',max_chars=300);ok=st.checkbox('Confirmo o registro desta ocorrência simulada');sub=st.form_submit_button('Registrar ocorrência')
        if sub:
            if not ok:st.warning('Confirme antes de registrar.')
            else:
                try:tid,new=store.ticket(code,kind,detail or 'Solicitação pelo portal.');flash(('Registrado: ' if new else 'Já existe: ')+tid)
                except ValueError as e:st.error(str(e))
    elif service=='Notificações':
        st.subheader('Notificações da entrega');code=st.text_input('Código da carga',value=s.track_code,key='notice_code')
        for n in store.notices(code):
            with st.container(border=True):st.markdown(n['message']);st.caption(n['created'].replace('T',' '))
        if not store.get(code):st.info('Informe um código válido.')
        st.caption('Avisos consultados ao abrir esta tela. Não são notificações push ou mensagens externas.')
    else:
        st.subheader('Como foi sua entrega?')
        with st.form('rating'):
            code=st.text_input('Código da carga entregue',value=s.track_code);score=st.radio('Sua nota',[1,2,3,4,5],horizontal=True,index=4);sub=st.form_submit_button('Enviar avaliação',type='primary')
        if sub:
            try:store.rate(code,score);flash('Avaliação registrada. Obrigado!')
            except ValueError as e:st.error(str(e))
else:
    st.title('Central de operações')
    if not s.admin:
        st.caption('Área administrativa · acesso restrito à demonstração.')
        with st.form('login'):
            pw=st.text_input('Senha do gestor',type='password');sub=st.form_submit_button('Acessar painel',type='primary')
        if sub:
            if hmac.compare_digest(pw,admin_pass):s.admin=True;st.rerun()
            else:st.error('Senha incorreta.')
        st.stop()
    if st.button('Sair da gestão'):s.admin=False;s.pop('manager_report',None);st.rerun()
    section=st.radio('Módulo',['Visão geral','Cargas','Protocolos','Frota','Cotações'],horizontal=True,key='manager_section')
    if section=='Visão geral':
        m=store.extended();st.caption('Indicadores calculados da base desta sessão · todos os dados são fictícios.')
        with st.container(key='metrics'):
            for items in [[('Cargas',m['total']),('Entregues',m['delivered']),('Em operação',m['active']),('Atrasadas',m['late'])],[('Taxa de atraso',f"{100*m['late']/max(1,m['total']):.1f}%"),('Protocolos abertos',m['open_tickets']),('Satisfação',f"{m['satisfaction']}/5" if m['ratings'] else '—'),('Valor cotado',money(m['quoted_total']))],[('Interações PACO',m['interactions']),('Tempo médio',f"{m['avg_seconds']:.2f} s" if m['interactions'] else '—'),('Turnos com ação concluída',f"{100*m['resolved']/m['interactions']:.0f}%" if m['interactions'] else '—'),('Avaliações',m['ratings'])]]:
                for col,(label,value) in zip(st.columns(len(items)),items):col.metric(label,value)
        st.caption('Valor cotado não é receita. Turnos concluídos são um indicador aproximado, não taxa de resolução de clientes.')
        st.subheader('Radar operacional PACO');st.caption('Análise automática por regras ao acessar o painel ou atualizar; não roda em segundo plano.')
        for level,title,action in store.alerts():
            with st.container(border=True):st.markdown(f'**{level} · {title}**');st.caption(action)
        if not store.alerts():st.success('Nenhum alerta nas regras atuais.')
        if st.button('Atualizar análise'):st.rerun()
        a,b=st.columns(2)
        with a:
            st.markdown('**Motivos dos atrasos**')
            if m['reasons']:st.bar_chart(pd.DataFrame.from_dict(m['reasons'],orient='index',columns=['Cargas']),color='#b76b09')
            else:st.info('Sem atrasos.')
        with b:
            st.markdown('**Entregas por data de último registro**');st.bar_chart(pd.DataFrame.from_dict(m['delivered_days'],orient='index',columns=['Entregas']),color='#1b608c')
        st.markdown('**Desempenho por rota**');df=pd.DataFrame(m['routes']).sort_values('rate',ascending=False);st.dataframe(df.rename(columns={'route':'Rota','total':'Total','late':'Atrasadas','rate':'Atrasos (%)'}),hide_index=True,use_container_width=True)
        st.bar_chart(df.set_index('route')['rate'],horizontal=True,color='#1b608c')
        if key and st.button('Gerar análise estratégica com IA',type='primary'):
            try:
                from openai import OpenAI
                with st.spinner('Analisando…'):r=OpenAI(api_key=key,timeout=25,max_retries=0).chat.completions.create(model=model,messages=[{'role':'system','content':'Analista PACO. Use exclusivamente dados agregados fictícios. Produza diagnóstico e 3 ações priorizadas. Não invente números nem execute ações.'},{'role':'user','content':json.dumps({'indicadores':m,'alertas':store.alerts()},ensure_ascii=False)}],max_completion_tokens=600)
                s.manager_report=r.choices[0].message.content
            except Exception:st.warning('API indisponível. O radar por regras permanece ativo.')
        if s.get('manager_report'):st.markdown('**Última análise gerada (pode estar desatualizada)**');st.markdown(s.manager_report)
        st.download_button('Baixar relatório gerencial PDF',report(store),'relatorio_paixao.pdf','application/pdf',use_container_width=True)
    elif section=='Cargas':
        rows=store.all();status=st.selectbox('Filtrar situação',['Todas']+STATUS);df=pd.DataFrame([d for d in rows if status=='Todas' or d['status']==status]);st.dataframe(df.rename(columns={'code':'Código','origin':'Origem','destination':'Destino','location':'Localização','status':'Situação','eta':'Prazo','reason':'Motivo','updated':'Último registro','days_late':'Dias de atraso'}),hide_index=True,use_container_width=True);st.download_button('Exportar cargas CSV',df.to_csv(index=False).encode('utf-8-sig'),'cargas_paixao.csv','text/csv')
        with st.expander('Cadastrar nova carga'):
            with st.form('create_cargo'):
                a,b=st.columns(2);origin=a.selectbox('Origem',list(CITIES));dest=b.selectbox('Destino',list(CITIES),index=1);eta=st.date_input('Prazo original',today()+timedelta(days=3),min_value=today());vid=st.selectbox('Veículo (opcional)',['']+[v['id'] for v in store.fleet() if v['status']!='Manutenção']);sub=st.form_submit_button('Cadastrar',type='primary')
            if sub:
                try:flash('Carga cadastrada: '+store.create_cargo(origin,dest,eta,vid))
                except ValueError as e:st.error(str(e))
        with st.expander('Atualizar movimentação'):
            active=[d['code'] for d in rows if d['status']!='Entregue']
            if active:
                code=st.selectbox('Carga a atualizar',active);d=store.get(code)
                with st.form('update_'+code):
                    loc=st.selectbox('Localização',list(CITIES),index=list(CITIES).index(d['location']));stat=st.selectbox('Nova situação',STATUS,index=STATUS.index(d['status']));reason=st.text_input('Motivo (obrigatório para atraso)',value=d['reason']);sub=st.form_submit_button('Salvar movimentação',type='primary')
                if sub:
                    try:store.update_cargo(code,loc,stat,reason);flash('Movimentação registrada.')
                    except ValueError as e:st.error(str(e))
            else:st.info('Nenhuma carga ativa.')
    elif section=='Protocolos':
        ts=store.tickets();st.dataframe(pd.DataFrame(ts),hide_index=True,use_container_width=True) if ts else st.info('Nenhuma ocorrência registrada.')
        open_ids=[t['id'] for t in ts if t['status']=='Aberto']
        if open_ids:
            tid=st.selectbox('Protocolo a resolver',open_ids)
            if st.button('Marcar como resolvido',type='primary'):store.close(tid);flash('Protocolo resolvido; aviso criado.')
    elif section=='Frota':
        vehicles=store.fleet();st.dataframe(pd.DataFrame(vehicles).rename(columns={'id':'Código','label':'Veículo','driver':'Motorista fictício','capacity':'Capacidade (kg)','status':'Situação'}),hide_index=True,use_container_width=True)
        vid=st.selectbox('Cadastrar ou editar veículo',['Novo']+[v['id'] for v in vehicles]);v=next((x for x in vehicles if x['id']==vid),{})
        with st.form('vehicle_'+vid):
            new_id=st.text_input('Código V + 3 dígitos',value=v.get('id',f"V{max(int(x['id'][1:]) for x in vehicles)+1:03}"),disabled=vid!='Novo');label=st.text_input('Identificação',v.get('label',''));driver=st.text_input('Motorista fictício',v.get('driver',''));cap=st.number_input('Capacidade (kg)',min_value=1.,max_value=100000.,value=float(v.get('capacity',8000)));opts=['Disponível','Em rota','Manutenção'];stat=st.selectbox('Situação',opts,index=opts.index(v.get('status','Disponível')));sub=st.form_submit_button('Salvar veículo')
        if sub:
            try:
                if vid=='Novo' and any(x['id']==new_id for x in vehicles):raise ValueError('Código já cadastrado.')
                store.save_vehicle(new_id,label,driver,cap,stat);flash('Veículo salvo.')
            except ValueError as e:st.error(str(e))
        st.subheader('Alocação de frota');st.caption('Alocação acadêmica; não valida peso real, jornada ou disponibilidade de motorista.')
        active=[d['code'] for d in store.all() if d['status']!='Entregue'];available=[v['id'] for v in vehicles if v['status']!='Manutenção']
        if active and available:
            with st.form('assignment'):
                code=st.selectbox('Carga',active);vid=st.selectbox('Veículo disponível para alocação',available);sub=st.form_submit_button('Vincular')
            if sub:
                try:store.assign(code,vid);flash('Vínculo atualizado.')
                except ValueError as e:st.error(str(e))
        st.dataframe(pd.DataFrame(store.assignments()),hide_index=True,use_container_width=True)
    else:
        qs=store.quotes();st.dataframe(pd.DataFrame(qs),hide_index=True,use_container_width=True) if qs else st.info('Nenhuma cotação registrada.')
        if qs:st.download_button('Exportar cotações CSV',pd.DataFrame(qs).to_csv(index=False).encode('utf-8-sig'),'cotacoes.csv','text/csv')
with st.expander('Sobre o projeto e privacidade'):
    st.markdown('**Fábrica de Agentes · AP2 | Paixão Connect 2.0**. Sistema acadêmico com dados fictícios. O PACO interpreta pedidos, consulta ferramentas e prepara ações; gravações dependem de confirmação. O modo sem API usa regras. O banco é isolado por sessão; reiniciar ou abrir outra sessão pode apagar os registros. Não informe dados reais. Não há GPS, contratação, pagamento, envio externo ou monitoramento contínuo.')
st.caption('TRANSPORTADORA PAIXÃO · PACO 2.0 · Inteligência em movimento')
