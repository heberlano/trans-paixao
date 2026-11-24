"""Guided customer and manager screens for Paixão Connect 3.0."""
from datetime import datetime, timedelta
import streamlit as st
from phone_lookup import search_delivery
import pandas as pd
from core import today, forecast_text, delay_summary
from operations import money
from resolution import TYPES, SLA, ACTIVE, classify
from tracking_feedback import tracking_result
from service_bridge import select_delivery, registered

def fmt(ts):
    if not ts:return 'Ainda não registrado'
    return datetime.fromisoformat(ts).strftime('%d/%m/%Y %H:%M' if 'T' in ts else '%d/%m/%Y')

def feedback(store,code,key,go):
    d,h,m=tracking_result(store,code)
    if not d:
        st.warning(f'**{h}**\n\n{m}');st.button('Conversar com PACO',key=key,on_click=go,args=('PACO',),use_container_width=True)
    return d

def case_card(store,t,manager=False):
    st.markdown(f"### {t['id']}")
    st.caption(f"Carga {t['code']} · {t['kind']} · Aberto em {fmt(t['created'])}")
    if t['status']=='Resolvido':st.success('Problema confirmado como resolvido pelo cliente.' if t['rating'] is not None else 'Encerrado no sistema anterior (sem confirmação registrada).')
    elif t['status']=='Aguardando confirmação':st.info('Temos uma proposta de solução. Precisamos saber se ela atende à sua necessidade.')
    else:st.info({'Aberto':'Recebemos sua solicitação. Ela está na fila de atendimento.','Em análise':'Sua solicitação está em análise.','Reaberto':'Recebemos seu pedido de nova análise.'}.get(t['status'],t['status']))
    st.markdown(f"**Prioridade:** {t['priority']} · **Meta de retorno:** {SLA[t['priority']]} h")
    st.caption(f"Prazo de primeiro retorno neste ciclo: {fmt(t['deadline'])} · {t['sla']}. Meta simulada, não prazo de entrega ou de solução.")
    if t['remaining_hours'] is not None and t['status']!='Resolvido':
        if t['remaining_hours']<0:st.warning(f"Meta de retorno ultrapassada em {abs(t['remaining_hours']):.1f} h. Sinalizado para revisão da gestão.")
        else:st.caption(f"Restam {t['remaining_hours']:.1f} h para a meta de retorno.")
    if t['requested_date']:st.write('Data solicitada: '+fmt(t['requested_date']))
    if t['proposed_date']:st.write('Nova data proposta: '+fmt(t['proposed_date'])+' (depende da confirmação do cliente).')
    if t['solution']:st.markdown('**Última atualização da equipe**');st.text(t['solution'])
    st.caption('Setor responsável: '+t['owner'])
    with st.expander('Ver histórico do atendimento'):
        for e in store.events(t['id'],t['code']):
            st.markdown('**'+e['event']+'**');st.caption(fmt(e['created'])+' · '+e['actor']);st.text(e['detail'])
    images=store.photos(t['id'],t['code'])
    if images:
        with st.expander(f'Fotos anexadas ({len(images)})'):
            for im in images:st.image(im,width=260)
    if manager:st.markdown('**Descrição enviada pelo cliente**');st.text(t['detail'])

HELP_CSS = """<style>
.st-key-help_flow{max-width:730px;margin:0 auto;}
.st-key-help_flow [data-testid="stVerticalBlock"]{gap:.55rem!important;}
.help-intro{border-radius:14px;background:linear-gradient(120deg,#102b43,#235573);color:white;padding:15px 17px;}
.help-intro small{color:#ffc66f;font-size:.67rem;font-weight:750;letter-spacing:.08em;}
.help-intro strong{display:block;font-size:1.35rem;line-height:1.2;margin:4px 0;}
.help-intro p{color:#e4edf5;margin:0;font-size:.85rem;}
.st-key-help_flow [data-testid="stRadio"] [role="radiogroup"]{gap:.4rem!important;}
.st-key-help_flow [data-testid="stRadio"] [role="radiogroup"] label{margin:0!important;padding:7px 8px;border:1px solid #dbe4ee;border-radius:9px;background:white;flex:1 1 auto;}
.st-key-help_flow [data-testid="stRadio"] [role="radiogroup"] label:has(input:checked){background:#fff4e3;border-color:#e0aa57;}
.st-key-help_flow [data-testid="stForm"]{padding:10px!important;}
.st-key-help_flow [data-testid="stCaptionContainer"] p{line-height:1.35;}
.st-key-help_search [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:minmax(0,1fr) 84px;gap:6px!important;}
.st-key-help_search [data-testid="stColumn"]{width:100%!important;min-width:0!important;flex:none!important;}
</style>"""


def lookup_help_delivery(store,s):
    """Unified search; retain only result codes, not the phone entered."""
    with st.container(key='help_search'):
        with st.form('help_find_delivery',clear_on_submit=True,border=False):
            a,b=st.columns([4,1],gap='small',vertical_alignment='bottom')
            raw=a.text_input('Código ou telefone cadastrado com DDD',placeholder='Ex.: PP1002 ou telefone com DDD',label_visibility='collapsed',max_chars=40)
            submitted=b.form_submit_button('Buscar',type='primary',use_container_width=True)
        if submitted:
            rows,title,error=search_delivery(store,raw)
            s['help_search_matches']=[d['code'] for d in rows]
            s['help_search_error']=(title,error) if error else None
            if len(rows)==1:
                choose_help_delivery(store,s,rows[0]['code']);st.rerun()
        if s.get('help_search_error'):
            title,error=s['help_search_error'];st.warning(f'**{title}**\n\n{error}')
        codes=s.get('help_search_matches',[])
        if codes:
            st.caption('Selecione a entrega para a qual precisa de ajuda:')
            for code in codes:
                d=store.get(code)
                if d:st.button(f"{code} · {d['destination']} · {d['status']}",key='help_pick_'+code,on_click=choose_help_delivery,args=(store,s,code),use_container_width=True)


def choose_help_delivery(store,s,code):
    if not select_delivery(s,store,code):return False
    s['help_search_matches']=[];s['help_search_error']=None
    # Preserve a valid existing protocol, but never carry it across deliveries.
    current=s.get('protocol_query',('',''))
    if current[0]!=code:s['protocol_query']=(code,'')
    return True


def selected_case(store,s,code,tid):
    """Keep the selected protocol shared with PACO and reject unrelated IDs."""
    t=store.case(tid,code)
    if t:
        s['protocol_query']=(code,t['id']);s.setdefault('context',{})['protocol']=t['id']
    return t


def customer_support(store,s,go,flash,choose):
    st.markdown(HELP_CSS,unsafe_allow_html=True)
    with st.container(key='help_flow'):
        st.markdown('<div class="help-intro"><small>CENTRAL DE ATENDIMENTO</small><strong>Vamos resolver juntos.</strong><p>Conte o que aconteceu ou acompanhe uma solicitação.</p></div>',unsafe_allow_html=True)
        if s.pop('help_refresh',False):
            if s.get('case_kind') in TYPES:s['help_kind_v41']=s['case_kind']
            s['help_action_v41']=s.get('protocol_task','new')
        if s.get('protocol_task') not in ('new','lookup'):s['protocol_task']='new'
        if s.get('help_action_v41')!=s['protocol_task']:s['help_action_v41']=s['protocol_task']
        def task_changed():s['protocol_task']=s['help_action_v41']
        task=st.radio('O que você precisa?', ['new','lookup'],format_func=lambda x:'Resolver um problema' if x=='new' else 'Acompanhar chamado',horizontal=True,key='help_action_v41',on_change=task_changed,label_visibility='collapsed')
        st.markdown('**1 · Localize sua entrega**')
        d=store.get(s.get('track_code','')) if s.get('track_code') else None
        if d:
            with st.container(border=True):
                st.markdown(f"**{d['code']} · {d['status']}**")
                st.caption(f"{d['origin']} → {d['destination']} · {d['stage_label']}")
                forecast=forecast_text(d)
                if forecast:st.caption(forecast)
            with st.expander('Trocar de entrega',expanded=bool(s.get('help_search_matches') or s.get('help_search_error'))):
                lookup_help_delivery(store,s)
        else:
            st.caption('Informe seu código de rastreamento (ex.: PP1002) ou o telefone cadastrado com DDD.')
            lookup_help_delivery(store,s)
            st.caption('Se preferir, o PACO também pode ajudar a localizar sua carga.')
            return
        code=d['code']
        if task=='new':
            st.markdown('**2 · O que aconteceu?**')
            if s.get('case_kind') not in TYPES:s['case_kind']='Atraso' if d['status']=='Atrasada' else 'Reclamação'
            if s.get('help_kind_v41') not in TYPES:s['help_kind_v41']=s['case_kind']
            kind=st.selectbox('Selecione o problema',list(TYPES),format_func=lambda k:TYPES[k][0],key='help_kind_v41',label_visibility='collapsed')
            s['case_kind']=kind
            st.caption(TYPES[kind][1])
            if kind=='Atraso' and d['status']=='Atrasada':
                st.caption(f"Motivo registrado: {d['reason']}. {delay_summary(d)}.")
            active=[t for t in store.cargo_tickets(code) if t['kind']==kind and t['status'] in ACTIVE]
            if active:
                existing=active[0]['id']
                st.info('Já existe um chamado em andamento para esse problema. Não é necessário abrir outro.')
                def follow():
                    selected_case(store,s,code,existing);s['protocol_task']='lookup';s['help_refresh']=True
                st.button('Acompanhar chamado '+existing,key='help_existing',on_click=follow,type='primary',use_container_width=True)
                return
            st.markdown('**3 · Envie sua solicitação**')
            with st.form('help_new_'+code+'_'+kind,border=False):
                detail=st.text_area('Conte mais (opcional)',placeholder='Se desejar, descreva o que ocorreu.',max_chars=300,height=80)
                pending=s.get('pending') or {};preferred=today()+timedelta(days=1)
                if kind=='Reagendamento' and pending.get('code')==code and pending.get('requested_date'):
                    preferred=max(today(),datetime.fromisoformat(pending['requested_date']).date())
                desired=st.date_input('Data desejada',value=preferred,min_value=today()) if kind=='Reagendamento' else ''
                files=st.file_uploader('Anexar fotos (opcional)',type=['jpg','jpeg','png','webp'],accept_multiple_files=True,help='Até 3 imagens de 5 MB. Não envie dados pessoais.') if kind=='Avaria' else []
                st.caption('Ao registrar, você confirma o envio à equipe responsável. Acompanhe a resposta pelo protocolo.')
                submit=st.form_submit_button('Confirmar e registrar chamado',type='primary',use_container_width=True)
            if submit:
                try:
                    if len(files)>3 or any(f.size>5*1024*1024 for f in files):raise ValueError('Envie até três imagens de 5 MB cada.')
                    tid,new=store.ticket(code,kind,detail or 'Solicitação pelo portal.',str(desired),[f.getvalue() for f in files]);registered(s,store,code,tid,kind)
                    s.messages.append({'role':'assistant','content':f'Chamado {tid} · {kind} · carga {code}. Você pode acompanhar o andamento aqui ou na Central de ajuda.'})
                    flash(('Recebemos sua solicitação! Protocolo: ' if new else 'Já existe uma solicitação ativa. Protocolo: ')+tid)
                except ValueError as e:st.warning(str(e))
        else:
            st.markdown('**2 · Acompanhe seu chamado**')
            cases=[t for t in store.cases() if t['code']==code]
            if not cases:
                st.info('Não encontramos chamados para esta entrega. Se algo não saiu como esperado, selecione Resolver um problema acima.')
                return
            ids=[t['id'] for t in cases];target=s.get('protocol_query',('',''))[1];widget='help_case_v41_'+code
            if s.get(widget) not in ids or (target in ids and s.get(widget)!=target):s[widget]=target if target in ids else ids[0]
            def protocol_changed():selected_case(store,s,code,s[widget])
            if len(cases)>1:
                tid=st.selectbox('Escolha o chamado',ids,format_func=lambda x:next(f"{t['kind']} · {t['status']} · {x}" for t in cases if t['id']==x),key=widget,on_change=protocol_changed)
            else:tid=ids[0]
            t=selected_case(store,s,code,tid)
            if not t:return
            with st.container(border=True):
                st.markdown(f"**{t['kind']} · {t['status']}**")
                st.caption(f"Protocolo {t['id']} · Aberto em {fmt(t['created'])}")
                if t['status']=='Resolvido':st.success('Seu atendimento está encerrado. Obrigado pela confiança!' if t['rating'] is not None else 'Atendimento encerrado no sistema.')
                elif t['status']=='Aguardando confirmação':st.info('Temos uma proposta de solução. Confira abaixo e diga se ela resolveu o problema.')
                else:
                    st.write({'Aberto':'Recebemos sua solicitação. Nossa equipe vai analisar o caso.','Em análise':'Nossa equipe está verificando o ocorrido.','Reaberto':'Vamos analisar novamente sua solicitação.'}.get(t['status'],t['status']))
                if t['solution']:st.markdown('**Última atualização**');st.text(t['solution'])
                if t['requested_date']:st.caption('Data solicitada: '+fmt(t['requested_date']))
                if t['proposed_date']:st.write('Nova data proposta: '+fmt(t['proposed_date'])+' (aguardando confirmação).')
                if t['status'] in ('Aberto','Em análise','Reaberto') and not t['first_reply']:
                    st.caption('Previsão de primeiro retorno: '+fmt(t['deadline'])+' (meta, não garantia de solução).')
                    if t['sla']=='Fora da meta':st.warning('A meta de retorno foi ultrapassada. O caso está sinalizado para revisão.')
                with st.expander('Histórico e detalhes'):
                    st.caption(f"Prioridade: {t['priority']} · Setor: {t['owner']} · {t['sla']}")
                    for e in store.events(tid,code):
                        st.markdown('**'+e['event']+'**');st.caption(fmt(e['created'])+' · '+e['actor']);st.text(e['detail'])
                    for im in store.photos(tid,code):st.image(im,width=260)
                if t['status']=='Aguardando confirmação':
                    st.markdown('**A solução resolveu seu problema?**')
                    decision=st.radio('Resultado',['Sim, foi resolvido','Ainda preciso de ajuda'],key='help_decision_'+tid,label_visibility='collapsed')
                    accept=decision.startswith('Sim')
                    with st.form('help_decision_form_'+tid,border=False):
                        score=st.select_slider('Como avalia o atendimento?',options=[1,2,3,4,5],value=5) if accept else 5
                        note=st.text_area('O que ainda precisamos resolver?',max_chars=300) if not accept else ''
                        sub=st.form_submit_button('Confirmar resolução' if accept else 'Reabrir chamado',type='primary',use_container_width=True)
                    if sub:
                        try:store.customer_decision(tid,code,accept,score,note);flash('Agradecemos sua confirmação e avaliação!' if accept else 'Sentimos muito. Seu chamado foi reaberto para nova análise.')
                        except ValueError as e:st.warning(str(e))
                elif t['rating']:st.caption(f'Você avaliou o atendimento com {t["rating"]}/5. Obrigado!')

def manager_cases(store,flash):
    st.subheader('Fila de atendimento');st.caption('Priorize chamados críticos e fora do prazo. A solução só será encerrada após a confirmação do cliente.')
    m=store.complaints()
    with st.container(key='metrics_complaints'):
        for col,(label,value) in zip(st.columns(2),[('Pendentes',m['pending']),('Fora da meta',m['breached'])]):col.metric(label,value)
        with st.expander('Indicadores e motivos das reclamações'):
            for items in [[('Recebidos',m['total']),('Resolvidos',m['closed'])],[('Taxa de resolução',f"{m['rate']}%" if m['rate'] is not None else '—'),('Satisfação',f"{m['satisfaction']}/5" if m['satisfaction'] is not None else '—')],[('Tempo médio de resolução',f"{m['mean_hours']} h" if m['mean_hours'] is not None else '—'),('Reaberturas',m['reopened'])]]:
                for col,(label,value) in zip(st.columns(2),items):col.metric(label,value)
            st.caption('Fora da meta inclui retornos tardios. O prazo medido é de primeiro retorno no ciclo atual. Tempo médio considera chamados confirmados pelo cliente.')
            if m['kinds']:st.bar_chart(pd.DataFrame.from_dict(m['kinds'],orient='index',columns=['Chamados']),horizontal=True,color='#b76b09')
    if not m['total']:st.info('Nenhuma reclamação registrada. Abra uma solicitação pelo portal ou PACO para iniciar o atendimento.')
    rows=store.cases(); filter_status=st.radio('Mostrar',['Pendentes','Todos','Resolvidos'],horizontal=True);rows=[t for t in rows if filter_status=='Todos' or (filter_status=='Pendentes' and t['status'] in ACTIVE) or (filter_status=='Resolvidos' and t['status']=='Resolvido')]
    rows.sort(key=lambda t:(t['status']=='Resolvido', t['sla']!='Fora da meta',SLA[t['priority']],t['created']))
    if not rows:return
    selected=st.selectbox('Escolha um chamado',[t['id'] for t in rows],format_func=lambda id:next(f"{t['priority']} · {t['code']} · {t['kind']} · {id}" for t in rows if t['id']==id));t=next(x for x in rows if x['id']==selected)
    with st.container(border=True):case_card(store,t,True)
    if t['status'] not in ('Aberto','Em análise','Reaberto'):
        st.caption('Aguardando confirmação do cliente ou atendimento já encerrado.');return
    st.subheader('Registrar retorno ou propor solução')
    with st.form('manager_case_'+selected):
        owner=st.selectbox('Setor responsável',['Logística','Atendimento','Frota','Qualidade']);note=st.text_area('Atualização ao cliente',placeholder='Explique o que foi verificado e o próximo passo.',max_chars=700);propose=st.checkbox('Enviar proposta de solução para confirmação do cliente');include_date=st.checkbox('Incluir nova previsão de entrega (opcional)',disabled=store.get(t['code'])['status']=='Entregue');new_date=st.date_input('Nova previsão proposta',min_value=today(),value=today()+timedelta(days=1));sub=st.form_submit_button('Salvar atualização',type='primary')
    if sub:
        try:store.manager_update(selected,owner,note,propose,str(new_date) if include_date else '');flash('Atualização registrada. O cliente poderá consultar o andamento.')
        except ValueError as e:st.warning(str(e))

def intelligence(store):
    st.subheader('PACO · Plano de melhoria');st.caption('Recomendações calculadas a partir dos atrasos atuais e da fila. O gestor deve avaliar e aprovar antes de agir.')
    if st.button('Executar análise e registrar no histórico',type='primary',use_container_width=True):
        store.scan_prevention();store.audit('PACO','Gerar plano','Operação',f'{len(store.plan())} recomendações');st.success('Análise registrada no histórico.')
    plans=store.plan()
    for i,p in enumerate(plans,1):
        with st.container(border=True):
            st.markdown(f"**{i}. {p['cause']}**");st.caption(p['evidence']);st.write(p['action']);st.caption('Responsável sugerido: '+p['owner']+' · '+p['target'])
    if not plans:st.info('Não há atrasos ou chamados fora da meta para analisar agora.')
    m=store.summary();st.subheader('Economia potencial no atendimento');st.caption('Simulação: turnos com consulta concluída não equivalem a clientes ou ligações evitadas. Ajuste as hipóteses abaixo.')
    a,b=st.columns(2);mins=a.number_input('Minutos de trabalho manual por consulta',min_value=0.,max_value=120.,value=5.);cost=b.number_input('Custo por hora de trabalho (R$)',min_value=0.,max_value=1000.,value=25.);hours=m['resolved']*mins/60
    a,b=st.columns(2);a.metric('Horas potenciais poupadas',f'{hours:.2f} h');b.metric('Economia estimada',money(hours*cost));st.caption(f"{m['resolved']} turnos concluídos × {mins:g} minutos × custo/hora. Não desconta custos da IA; não mede economia real.")
    st.subheader('Histórico de ações do agente');logs=store.audit_rows()
    if logs:
        st.dataframe(pd.DataFrame(logs).rename(columns={'actor':'Responsável','action':'Ação','reference':'Referência','result':'Resultado','created':'Horário'}),hide_index=True,use_container_width=True);st.download_button('Exportar histórico CSV',pd.DataFrame(logs).to_csv(index=False).encode('utf-8-sig'),'historico_paco.csv','text/csv')
    else:st.info('As ações do PACO aparecerão aqui conforme forem executadas.')
