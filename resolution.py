"""PACO 3.0: auditable complaint workflow, with customer confirmation."""
from operations import Operations, KINDS, money
from core import today, now, normalize, forbidden, REFUSAL, delivery_estimate, forecast_text, describe
from tracking_feedback import tracking_result, chat_tracking_check
from phone_lookup import chat_phone, HELP
from delay_scenarios import install, SCENARIOS
from datetime import datetime, timedelta, date
from collections import Counter
from io import BytesIO
import secrets, re

TYPES = {
 'Atraso': ('Minha entrega está atrasada','Sentimos muito pela demora. Vamos conferir o prazo e o motivo registrado.'),
 'Não recebida': ('Não recebi minha mercadoria','Entendemos sua preocupação. Vamos solicitar uma verificação da entrega.'),
 'Mercadoria não localizada': ('Não conseguem localizar minha mercadoria','Entendemos a preocupação. Vamos sinalizar uma investigação prioritária da localização.'),
 'Avaria': ('Minha mercadoria chegou danificada','Sentimos muito pelo ocorrido. Você pode anexar fotos da embalagem ou do produto para ajudar na análise.'),
 'Endereço incorreto': ('Minha carga está no endereço errado','Vamos pedir à equipe que verifique a rota. Não alteraremos o endereço automaticamente.'),
 'Entrega não reconhecida': ('Consta como entregue, mas não recebi','Entendemos a gravidade. Vamos solicitar a conferência do comprovante de recebimento.'),
 'Reagendamento': ('Preciso reagendar a entrega','Vamos registrar a data desejada para avaliação da logística. A mudança não é automática.'),
 'Prioridade': ('Preciso de prioridade','Entendemos a urgência. Vamos encaminhar sua solicitação para análise, sem prometer antecipação.'),
 'Reclamação': ('Tenho outro problema','Sentimos muito pela dificuldade. Conte o que aconteceu para que possamos encaminhar a análise.')}
ACTIVE=('Aberto','Em análise','Aguardando confirmação','Reaberto')
SLA={'Baixa':8,'Média':4,'Alta':2,'Crítica':1}

def classify(kind,cargo):
    if kind in ('Mercadoria não localizada','Entrega não reconhecida') or (kind=='Não recebida' and cargo['status']=='Entregue'):return 'Crítica'
    if kind in ('Avaria','Endereço incorreto','Não recebida'):return 'Alta'
    if kind in ('Atraso','Prioridade'):return 'Alta' if cargo['days_late']>=2 or kind=='Prioridade' else 'Média'
    return 'Baixa' if kind=='Reagendamento' else 'Média'

def photo_bytes(data):
    from PIL import Image, ImageOps
    if not data or len(data)>5*1024*1024:raise ValueError('Escolha uma imagem de até 5 MB.')
    try:
        with Image.open(BytesIO(data)) as im:
            if im.format not in ('JPEG','PNG','WEBP') or im.width*im.height>20_000_000:raise ValueError('Formato ou resolução não aceitos.')
            im=ImageOps.exif_transpose(im).convert('RGB');im.thumbnail((1600,1600)); out=BytesIO();im.save(out,format='JPEG',quality=82);return out.getvalue()
    except Exception as e:raise ValueError('Não conseguimos ler a foto. Use JPG, PNG ou WebP de até 5 MB.') from e

class ResolutionStore(Operations):
    def __init__(self,path):
        super().__init__(path)
        with self.connect() as c:
            c.executescript('''CREATE TABLE IF NOT EXISTS case_meta(id TEXT PRIMARY KEY, priority TEXT, deadline TEXT, first_reply TEXT, cycle_start TEXT, owner TEXT, requested_date TEXT, proposed_date TEXT, solution TEXT, closed TEXT, rating INTEGER, reopen_count INTEGER DEFAULT 0);
            CREATE TABLE IF NOT EXISTS case_events(seq INTEGER PRIMARY KEY, id TEXT, event TEXT, detail TEXT, actor TEXT, created TEXT);
            CREATE TABLE IF NOT EXISTS case_photos(seq INTEGER PRIMARY KEY, id TEXT, image BLOB);
            CREATE TABLE IF NOT EXISTS audit(seq INTEGER PRIMARY KEY, actor TEXT, action TEXT, reference TEXT, result TEXT, created TEXT);
            CREATE TABLE IF NOT EXISTS prevention(code TEXT, category TEXT, PRIMARY KEY(code,category));
            CREATE TABLE IF NOT EXISTS confirmed_eta(code TEXT PRIMARY KEY, eta TEXT);''')
            for t in c.execute('SELECT * FROM tickets WHERE id NOT IN (SELECT id FROM case_meta)').fetchall():
                self._init_case(c,dict(t),classify(t['kind'],self.get(t['code'])), '', 'Migração')
        install(self)
    def _event(self,c,tid,event,detail,actor):
        c.execute('INSERT INTO case_events(id,event,detail,actor,created) VALUES(?,?,?,?,?)',(tid,event,detail[:700],actor,now()))
    def _audit(self,c,actor,action,ref,result):
        c.execute('INSERT INTO audit(actor,action,reference,result,created) VALUES(?,?,?,?,?)',(actor,action,ref,result[:300],now()))
    def audit(self,actor,action,ref='',result=''):
        with self.connect() as c:self._audit(c,actor,action,ref,result)
    def audit_rows(self):
        with self.connect() as c:return [dict(r) for r in c.execute('SELECT actor,action,reference,result,created FROM audit ORDER BY seq DESC')]
    def _notice(self,c,code,msg):c.execute('INSERT INTO notices(code,message,created) VALUES(?,?,?)',(code,msg,now()))
    def _init_case(self,c,t,priority,requested,actor):
        ts=t['created']; due=(datetime.fromisoformat(ts)+timedelta(hours=SLA[priority])).isoformat(timespec='seconds')
        c.execute('INSERT INTO case_meta(id,priority,deadline,first_reply,cycle_start,owner,requested_date,proposed_date,solution,closed,rating) VALUES(?,?,?,?,?,?,?,?,?,?,?)',(t['id'],priority,due,'',ts,'Logística',requested,'','',ts if t['status']=='Resolvido' else '',None))
        self._event(c,t['id'],'Solicitação recebida','Encaminhada à fila de logística nesta sessão.',actor)
    def ticket(self,code,kind,detail,requested_date='',photos=(),actor='Cliente'):
        d,_,msg=tracking_result(self,code)
        if not d:raise ValueError(msg)
        if kind not in TYPES:raise ValueError('Escolha um tipo de problema.')
        if kind=='Reagendamento':
            if d['status']=='Entregue':raise ValueError('A carga já foi entregue e não pode ser reagendada.')
            try:valid=date.fromisoformat(str(requested_date))>=today()
            except ValueError:valid=False
            if not valid:raise ValueError('Informe uma data desejada a partir de hoje.')
        else:requested_date=''
        if len(photos)>3:raise ValueError('Envie até três fotos por chamado.')
        if photos and kind!='Avaria':raise ValueError('Fotos disponíveis somente para avarias.')
        imgs=[photo_bytes(p) for p in photos]; code=d['code']; priority=classify(kind,d)
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            r=c.execute("SELECT id FROM tickets WHERE code=? AND kind=? AND status!='Resolvido'",(code,kind)).fetchone()
            if r:return r[0],False
            tid='OC-'+secrets.token_hex(3).upper(); ts=now()
            c.execute('INSERT INTO tickets VALUES(?,?,?,?,?,?)',(tid,code,kind,str(detail)[:300],'Aberto',ts))
            self._init_case(c,dict(id=tid,created=ts,status='Aberto'),priority,str(requested_date),actor)
            for img in imgs:c.execute('INSERT INTO case_photos(id,image) VALUES(?,?)',(tid,img))
            self._notice(c,code,f'Solicitação {tid} recebida. Acompanhe o retorno na central de ajuda.')
            self._audit(c,actor,'Registrar chamado',tid,f'{kind} · {priority}')
        return tid,True
    def cases(self):
        with self.connect() as c:rows=[dict(r) for r in c.execute('SELECT t.*, m.priority,m.deadline,m.first_reply,m.cycle_start,m.owner,m.requested_date,m.proposed_date,m.solution,m.closed,m.rating,m.reopen_count FROM tickets t JOIN case_meta m ON t.id=m.id ORDER BY t.created DESC')]
        for t in rows:
            deadline=datetime.fromisoformat(t['deadline']); responded=bool(t['first_reply']); breach=(datetime.fromisoformat(t['first_reply'])>deadline) if responded else (datetime.now()>deadline and t['status']!='Resolvido')
            t['sla']= 'Fora da meta' if breach else 'Respondido no prazo' if responded else 'Sem retorno registrado' if t['status']=='Resolvido' else 'Aguardando retorno'
            t['remaining_hours']=round((deadline-datetime.now()).total_seconds()/3600,2) if not responded else None
        return rows
    def case(self,tid,code):
        d,_,_=tracking_result(self,code)
        if not d:return None
        return next((x for x in self.cases() if x['id']==str(tid).strip().upper() and x['code']==d['code']),None)
    def protocol(self,tid,code):
        t=self.case(tid,code);return {k:t[k] for k in ('id','code','kind','status','created','priority','deadline','sla','solution','proposed_date')} if t else None
    def cargo_tickets(self,code):
        d,_,_=tracking_result(self,code)
        return [{k:t[k] for k in ('id','code','kind','status','created','priority','deadline','sla','solution','proposed_date')} for t in self.cases() if d and t['code']==d['code']]
    def events(self,tid,code):
        if not self.case(tid,code):return []
        with self.connect() as c:return [dict(r) for r in c.execute('SELECT event,detail,actor,created FROM case_events WHERE id=? ORDER BY seq',(tid.upper(),))]
    def photos(self,tid,code):
        if not self.case(tid,code):return []
        with self.connect() as c:return [r[0] for r in c.execute('SELECT image FROM case_photos WHERE id=?',(tid.upper(),))]
    def get(self,code):
        d=super().get(code)
        if d:
            with self.connect() as c:
                # During initial migration the table may not yet exist.
                if c.execute("SELECT 1 FROM sqlite_master WHERE name='confirmed_eta'").fetchone():
                    r=c.execute('SELECT eta FROM confirmed_eta WHERE code=?',(d['code'],)).fetchone();d['confirmed_eta']=r[0] if r else ''
            d.setdefault('confirmed_eta','')
            d['estimated_eta']=delivery_estimate(d)
        return d
    def manager_update(self,tid,owner,note,propose=False,new_date=''):
        t=next((x for x in self.cases() if x['id']==tid),None)
        if not t or t['status'] not in ('Aberto','Em análise','Reaberto'):raise ValueError('Escolha um chamado em aberto ou em análise.')
        if not note.strip() or not owner.strip():raise ValueError('Informe o setor responsável e uma atualização clara.')
        if new_date:
            if not propose or self.get(t['code'])['status']=='Entregue' or date.fromisoformat(str(new_date))<today():raise ValueError('A nova data exige proposta de solução, carga ativa e data a partir de hoje.')
        status='Aguardando confirmação' if propose else 'Em análise'; ts=now()
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            if c.execute('UPDATE tickets SET status=? WHERE id=? AND status=?',(status,tid,t['status'])).rowcount!=1:raise ValueError('O chamado mudou. Atualize a tela.')
            c.execute("UPDATE case_meta SET owner=?,first_reply=CASE WHEN first_reply='' THEN ? ELSE first_reply END,solution=?,proposed_date=? WHERE id=?",(owner[:80],ts,note[:700],str(new_date),tid))
            self._event(c,tid,'Solução proposta' if propose else 'Equipe em análise',note,'Gestor')
            self._notice(c,t['code'],f'{tid}: {status}. Consulte a central de ajuda.')
            self._audit(c,'Gestor','Atualizar chamado',tid,status)
    def customer_decision(self,tid,code,accepted,score=None,note=''):
        t=self.case(tid,code)
        if not t or t['status']!='Aguardando confirmação':raise ValueError('Não há solução aguardando sua confirmação.')
        if accepted and score not in range(1,6):raise ValueError('Escolha uma nota de 1 a 5.')
        if not accepted and not note.strip():raise ValueError('Conte o que ainda falta resolver.')
        ts=now(); status='Resolvido' if accepted else 'Reaberto'
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            if c.execute("UPDATE tickets SET status=? WHERE id=? AND status='Aguardando confirmação'",(status,t['id'])).rowcount!=1:raise ValueError('A solicitação já foi atualizada.')
            if accepted:
                c.execute('UPDATE case_meta SET closed=?,rating=? WHERE id=?',(ts,score,t['id']))
                if t['proposed_date'] and self.get(t['code'])['status']!='Entregue':
                    c.execute('INSERT INTO confirmed_eta VALUES(?,?) ON CONFLICT(code) DO UPDATE SET eta=excluded.eta',(t['code'],t['proposed_date']))
                    c.execute('INSERT INTO history VALUES(?,?,?)',(t['code'],'Nova previsão confirmada: '+t['proposed_date'],ts))
            else:
                due=(datetime.fromisoformat(ts)+timedelta(hours=SLA[t['priority']])).isoformat(timespec='seconds')
                c.execute("UPDATE case_meta SET reopen_count=reopen_count+1,first_reply='',deadline=?,cycle_start=?,proposed_date='',closed='',rating=NULL WHERE id=?",(due,ts,t['id']))
            self._event(c,t['id'],'Cliente confirmou a solução' if accepted else 'Cliente pediu nova análise', 'Nota: '+str(score) if accepted else note,'Cliente')
            self._notice(c,t['code'],f'{t["id"]}: {status}.')
            self._audit(c,'Cliente','Confirmar solução' if accepted else 'Reabrir chamado',t['id'],status)
    def close(self,tid):
        # Never bypass customer confirmation in the V3 store.
        self.manager_update(tid,'Logística','A equipe concluiu a análise. Confirme se o problema foi resolvido.',True);return True
    def scan_prevention(self):
        rows=self.all(); made=0
        with self.connect() as c:
            for d in rows:
                if d['status']=='Entregue':continue
                days=(date.fromisoformat(d['confirmed_eta'] or d['eta'])-today()).days
                if days<0:category='atraso'; msg='Identificamos que o prazo da sua carga passou. Pedimos desculpas. Consulte o rastreamento ou solicite uma análise.'
                elif days<=1 and d['status']!='Saiu para entrega':category='risco';msg='O prazo da sua entrega está próximo e a carga ainda não saiu para entrega. Existe possibilidade de atraso. Acompanhe por aqui.'
                else:continue
                if c.execute('INSERT OR IGNORE INTO prevention VALUES(?,?)',(d['code'],category)).rowcount:
                    self._notice(c,d['code'],msg);self._audit(c,'PACO','Alerta preventivo',d['code'],category);made+=1
        return made
    def summary(self):
        m=super().summary();m['open_tickets']=sum(t['status'] in ACTIVE for t in self.tickets());return m
    def complaints(self):
        rows=self.cases();closed=[t for t in rows if t['status']=='Resolvido']; rated=[t['rating'] for t in closed if t['rating'] is not None]; replies=[t for t in rows if t['first_reply']]; times=[(datetime.fromisoformat(t['closed'])-datetime.fromisoformat(t['created'])).total_seconds()/3600 for t in closed if t['closed'] and t['rating'] is not None]
        return dict(total=len(rows),closed=len(closed),pending=len(rows)-len(closed),breached=sum(t['sla']=='Fora da meta' for t in rows),rate=round(100*len(closed)/len(rows),1) if rows else None,mean_hours=round(sum(times)/len(times),2) if times else None,satisfaction=round(sum(rated)/len(rated),2) if rated else None,reopened=sum(t['reopen_count'] for t in rows),sla_rate=round(100*sum(t['sla']=='Respondido no prazo' for t in replies)/len(replies),1) if replies else None,kinds=dict(Counter(t['kind'] for t in rows)))
    def plan(self):
        m=self.extended(); out=[];total=sum(m['reasons'].values()); actions={'Manutenção do veículo':'Revisar histórico de falhas e programar manutenção preventiva.','Interdição na rota':'Revisar rotas alternativas e margens de prazo.','Falha operacional':'Mapear etapas de coleta e expedição; conferir responsáveis.','Condições climáticas':'Revisar previsões e margens de segurança, sem comprometer a segurança da viagem.'}
        actions.update(dict(SCENARIOS))
        for reason,n in sorted(m['reasons'].items(),key=lambda x:-x[1]):out.append(dict(cause=reason,evidence=f'{n} de {total} atrasos atuais ({100*n/max(total,1):.1f}%)',action=actions.get(reason,'Investigar a causa antes de definir ações.'),owner='Gestão logística',target='Reavaliar em 30 dias; meta proposta: reduzir a ocorrência em 25%.'))
        overdue=[t for t in self.cases() if t['sla']=='Fora da meta' and t['status'] in ACTIVE]
        if overdue:out.insert(0,dict(cause='SLA fora da meta',evidence=f'{len(overdue)} chamados pendentes fora da meta de retorno',action='Revisar fila e priorizar casos críticos.',owner='Atendimento',target='Revisar hoje.'))
        return out
    def alerts(self):
        a=super().alerts(); pending=[t for t in self.cases() if t['status'] in ACTIVE and t['sla']=='Fora da meta']
        if pending:a.insert(0,('Crítica',f'{len(pending)} chamados fora da meta de primeiro retorno','Escalonar para revisão do gestor.'))
        return a

def complaint_reply(text,store,ctx):
    """Deterministic triage before optional LLM, with explicit confirmation."""
    s=normalize(text)
    phone=chat_phone(text,store,ctx)
    if phone is not None:return phone
    # Address complaints are safe; never allow private-data or financial requests.
    cleaned=re.sub(r'(endereco errado|endereco incorreto|endereco diferente)', '',s)
    if forbidden(cleaned):return REFUSAL,None,False
    feedback=chat_tracking_check(text,store,ctx)
    if feedback:return feedback
    if re.search(r'frete|cotacao|orcamento|quanto custa|avali|notific|alerta',s):return None
    code=ctx.get('code','');d=store.get(code) if code else None
    if re.search(r'previsao|quando.*(?:cheg|entreg)|qual.*(?:data|prazo)|nova data',s) and not re.search(r'reagend|remarc|regist|abrir|reclam|resolv|soluc|priori|urgente',s):
        if not d:return 'Informe o código da entrega para que eu possa verificar a previsão. '+HELP,None,False
        return describe(d),None,True
    if re.search(r'reagend|remarc',s) or (ctx.get('reschedule_code')==code and re.search(r'\b\d{4}-\d{2}-\d{2}\b',text)):kind='Reagendamento'
    elif re.search(r'avaria|danific|quebrad|amassad',s):kind='Avaria'
    elif re.search(r'endereco errado|endereco incorreto|endereco diferente',s):kind='Endereço incorreto'
    elif re.search(r'extravi|sumiu|nao localiz',s):kind='Mercadoria não localizada'
    elif re.search(r'nao recebi|nao chegou|nao reconhe',s):kind='Entrega não reconhecida' if d and d['status']=='Entregue' else 'Não recebida'
    elif re.search(r'priori|urgente|urgencia',s):kind='Prioridade'
    elif re.search(r'atras|reclam|ocorrencia|chamado|resolv|soluc',s) and not re.search(r'consult|acompan|qual.*protocolo|status.*chamado|qual.*motivo|por que|porque|quantos dias',s):kind='Atraso' if ('atras' in s or d and d['days_late']) else 'Reclamação'
    else:return None
    if not d:return 'Sinto muito pela dificuldade. Informe o código de rastreio (ex.: PP1003). '+HELP,None,False
    requested=''
    if kind=='Reagendamento':
        if d['status']=='Entregue':return 'Essa carga já consta como entregue. Se houver um problema, podemos abrir uma reclamação.',None,False
        match=re.search(r'\b\d{4}-\d{2}-\d{2}\b',text)
        if not match:
            ctx['reschedule_code']=code
            return 'Informe a data desejada no formato AAAA-MM-DD ou use a Central de ajuda para escolher no calendário. A data será avaliada pela equipe.',None,False
        try:valid=date.fromisoformat(match[0])>=today()
        except ValueError:valid=False
        if not valid:return 'Escolha uma data válida a partir de hoje.',None,False
        requested=match[0];ctx.pop('reschedule_code',None)
    priority=classify(kind,d); msg=TYPES[kind][1]+f'\n\n**{code}** · {d["status"]}. Último registro: {d["location"]}.'
    if d['days_late']:msg+=f' Prazo original vencido há {d["days_late"]} dia(s). Motivo registrado: {d["reason"]}.'
    forecast=forecast_text(d)
    if forecast:msg+='\n\n**'+forecast+'**'
    msg+=f'\n\nPreparei um chamado de **{kind}**, prioridade **{priority}**, com meta de primeiro retorno de {SLA[priority]} h na simulação. Confirme abaixo para registrar. Isso não garante a resolução nesse prazo.'
    if kind=='Avaria':msg+=' Você também pode abrir o chamado na Central de ajuda e anexar fotos.'
    return msg,dict(code=code,kind=kind,requested_date=requested),False
