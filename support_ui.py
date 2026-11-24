"""Guided customer and manager screens for Paixão Connect 3.0."""
from datetime import datetime, timedelta
import streamlit as st
from lookup_ui import phone_search
import pandas as pd
from core import today
from operations import money
from resolution import TYPES, SLA, ACTIVE, classify
from tracking_feedback import tracking_result

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
    a,b=st.columns(2);a.metric('Prioridade',t['priority']);b.metric('Meta de retorno',f"{SLA[t['priority']]} h")
    st.caption(f"Prazo de primeiro retorno neste ciclo: {fmt(t['deadline'])} · {t['sla']}. Meta simulada, não prazo de entrega ou de solução.")
    if t['remaining_hours'] is not None and t['status']!='Resolvido':
        if t['remaining_hours']<0:st.warning(f"Meta de retorno ultrapassada em {abs(t['remaining_hours']):.1f} h. Sinalizado para revisão da gestão.")
        else:st.caption(f"Restam {t['remaining_hours']:.1f} h para a meta de retorno.")
    if t['requested_date']:st.write('Data solicitada: '+fmt(t['requested_date']))
    if t['proposed_date']:st.write('Nova data proposta: '+fmt(t['proposed_date'])+' (depende da confirmação do cliente).')
    if t['solution']:st.markdown('**Última atualização da equipe**');st.text(t['solution'])
    st.caption('Setor responsável: '+t['owner'])
    with st.expander('Ver histórico do atendimento',expanded=True):
        for e in store.events(t['id'],t['code']):
            st.markdown('**'+e['event']+'**');st.caption(fmt(e['created'])+' · '+e['actor']);st.text(e['detail'])
    images=store.photos(t['id'],t['code'])
    if images:
        with st.expander(f'Fotos anexadas ({len(images)})'):
            for im in images:st.image(im,width=260)
    if manager:st.markdown('**Descrição enviada pelo cliente**');st.text(t['detail'])

def customer_support(store,s,go,flash,choose):
    st.markdown('<div class="support-hero"><div class="eyebrow">CUIDAMOS DA SUA ENTREGA</div><h2>Vamos resolver juntos.</h2><p>Conte o que aconteceu. Você poderá acompanhar cada atualização por aqui.</p></div>',unsafe_allow_html=True)
    task=choose('protocol_task',[('new','Tenho um problema','support_agent'),('lookup','Acompanhar solução','search')],'protocol_menu')
    if task=='new':
        st.subheader('1. O que aconteceu com sua entrega?')
        if s.get('case_kind') not in TYPES:s.case_kind='Atraso'
        kind=st.selectbox('Escolha o motivo',list(TYPES),index=list(TYPES).index(s.case_kind),format_func=lambda k:TYPES[k][0],key='compact_problem_choice')
        s.case_kind=kind
        st.caption(TYPES[kind][1])
        st.subheader('2. Identifique sua carga')
        def select_case_code(code):
            s.track_code=code;s['case_code_'+kind]=code
        phone_search(store,'new_case_phone',select_case_code)
        with st.form('new_case_'+kind):
            code=st.text_input('Código de rastreamento',value=s.track_code,key='case_code_'+kind,help='PP seguido de quatro números. Exemplo: PP1003.')
            st.markdown('**3. Conte mais sobre o ocorrido**')
            detail=st.text_area('Descrição (opcional)',placeholder='Ex.: Preciso saber quando minha mercadoria chegará.',max_chars=300)
            desired=st.date_input('Qual data você prefere?',value=today()+timedelta(days=1),min_value=today()) if kind=='Reagendamento' else ''
            files=st.file_uploader('Fotos da embalagem ou produto (opcional)',type=['jpg','jpeg','png','webp'],accept_multiple_files=True,help='Até 3 imagens, cada uma com no máximo 5 MB. Use fotos fictícias, sem pessoas, etiquetas ou dados pessoais.') if kind=='Avaria' else []
            st.caption('O pedido será encaminhado à fila de atendimento simulada. Não é um contato real nem uma garantia de nova data.')
            ok=st.checkbox('Confirmo o registro desta solicitação');submit=st.form_submit_button('Registrar e acompanhar',type='primary',use_container_width=True)
        if submit:
            d=feedback(store,code,'case_help_new',go)
            if d and not ok:st.warning('Marque a confirmação acima para que possamos registrar sua solicitação.')
            elif d:
                try:
                    if len(files)>3 or any(f.size>5*1024*1024 for f in files):raise ValueError('Envie até três imagens de 5 MB cada.')
                    tid,new=store.ticket(d['code'],kind,detail or 'Solicitação pelo portal.',str(desired),[f.getvalue() for f in files]);s.track_code=d['code'];s.protocol_query=(d['code'],tid);s.protocol_task='lookup';flash(('Recebemos sua solicitação! Acompanhe as próximas etapas: ' if new else 'Já existe uma solicitação ativa para este problema. Vamos mostrar o andamento: ')+tid)
                except ValueError as e:st.warning(str(e))
    else:
        st.subheader('Acompanhe cada etapa da solução');st.caption('Informe seu código de rastreio. Se tiver o protocolo, use-o para encontrar uma solicitação específica.')
        def select_lookup_code(code):
            s.track_code=code;s.protocol_query=(code,'');s['lookup_code']=code;s['lookup_tid']=''
        phone_search(store,'case_lookup_phone',select_lookup_code)
        with st.form('case_lookup'):
            previous=s.get('protocol_query',(s.track_code,''));code=st.text_input('Código da carga',value=previous[0],key='lookup_code');tid=st.text_input('Protocolo (opcional)',value=previous[1],key='lookup_tid',placeholder='OC-XXXXXX');sub=st.form_submit_button('Consultar atendimento',type='primary',use_container_width=True)
        if sub:s.protocol_query=(code,tid)
        if not s.get('protocol_query'):return
        code,tid=s.protocol_query;d=feedback(store,code,'case_help_lookup',go)
        if not d:return
        cases=[store.case(tid,d['code'])] if tid.strip() else [x for x in store.cases() if x['code']==d['code']];cases=[x for x in cases if x]
        if not cases:st.info('Ainda não encontramos chamados nessa consulta. Confira os códigos ou selecione Tenho um problema para registrar uma solicitação.');return
        for t in cases:
            with st.container(border=True):
                case_card(store,t)
                if t['status']=='Aguardando confirmação':
                    st.subheader('A solução atende à sua necessidade?')
                    with st.form('decision_'+t['id']):
                        decision=st.radio('Escolha uma opção',['Sim, está resolvido','Ainda preciso de ajuda']);score=st.select_slider('Nota para o atendimento (se resolvido)',options=[1,2,3,4,5],value=5);note=st.text_area('O que ainda precisamos resolver? (se não resolvido)',max_chars=300);sub=st.form_submit_button('Enviar minha resposta',type='primary')
                    if sub:
                        try:
                            accept=decision.startswith('Sim');store.customer_decision(t['id'],d['code'],accept,score,note);flash('Agradecemos sua confirmação e avaliação!' if accept else 'Sentimos muito. Seu chamado foi reaberto para nova análise.')
                        except ValueError as e:st.warning(str(e))
                elif t['rating']:st.caption(f'Você avaliou o atendimento com {t["rating"]}/5. Obrigado!')

def manager_cases(store,flash):
    st.subheader('Fila de atendimento');st.caption('Priorize chamados críticos e fora do prazo. A solução só será encerrada após a confirmação do cliente.')
    m=store.complaints()
    with st.container(key='metrics_complaints'):
        for items in [[('Recebidos',m['total']),('Pendentes',m['pending'])],[('Resolvidos',m['closed']),('Fora da meta',m['breached'])],[('Taxa de resolução',f"{m['rate']}%" if m['rate'] is not None else '—'),('Satisfação',f"{m['satisfaction']}/5" if m['satisfaction'] is not None else '—')],[('Tempo médio de resolução',f"{m['mean_hours']} h" if m['mean_hours'] is not None else '—'),('Reaberturas',m['reopened'])]]:
            for col,(label,value) in zip(st.columns(2),items):col.metric(label,value)
    st.caption('Fora da meta inclui retornos tardios. O prazo medido é de primeiro retorno no ciclo atual. Tempo médio considera chamados confirmados pelo cliente.')
    if m['kinds']:st.bar_chart(pd.DataFrame.from_dict(m['kinds'],orient='index',columns=['Chamados']),horizontal=True,color='#b76b09')
    else:st.info('Nenhuma reclamação registrada. Abra uma solicitação pelo portal ou PACO para iniciar o atendimento.')
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
