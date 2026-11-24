"""Banco de dados e regras de negócio do PACO. Dados exclusivamente fictícios."""
import sqlite3, re, unicodedata, secrets
from datetime import date, timedelta, datetime
from collections import Counter
from contextlib import contextmanager

ROUTES = [('Fortaleza','Sobral'),('Sobral','Tianguá'),('Sobral','Crateús'),('Fortaleza','Juazeiro do Norte'),('Sobral','Teresina'),('Fortaleza','Natal'),('Sobral','Parnaíba'),('Fortaleza','Recife')]
REASONS = ['Manutenção do veículo']*4 + ['Interdição na rota']*3 + ['Falha operacional']*2 + ['Condições climáticas']

STAGES = ['Aguardando coleta','Objeto coletado na origem','Objeto recebido na sede da transportadora','Em separação na transportadora','Em trânsito','Objeto recebido na unidade de destino','Saiu para entrega','Entregue']
EXCEPTION_STAGE = 'Tentativa de entrega sem sucesso'
STAGE_LABELS = {'Em trânsito':'Objeto em trânsito','Saiu para entrega':'Objeto saiu para entrega','Entregue':'Objeto entregue'}

def stage_label(stage): return STAGE_LABELS.get(stage,stage)

def stage_index(stage):
    return 6 if stage==EXCEPTION_STAGE else STAGES.index(stage) if stage in STAGES else 0

def seed_movements(c,code,origin,dest,location,status,reason,ts):
    """Simulated completed milestones, not future movements."""
    stage='Em trânsito' if status=='Atrasada' else status
    c.execute('INSERT OR REPLACE INTO cargo_stage VALUES(?,?)',(code,stage))
    idx=stage_index(stage)
    end=datetime.fromisoformat(ts)
    for i in range(idx + int(stage==EXCEPTION_STAGE)):
        milestone=STAGES[i]
        city=origin if i<4 else location if i==4 and idx==5 else dest if i>=5 else origin
        stamp=(end-timedelta(hours=8*(idx-i+int(stage==EXCEPTION_STAGE)))).isoformat(timespec='seconds')
        c.execute('INSERT INTO history VALUES(?,?,?)',(code,stage_label(milestone)+' · '+city,stamp))
    event=stage_label(stage)+' · '+location
    if reason:event+=' · '+reason
    c.execute('INSERT INTO history VALUES(?,?,?)',(code,event,ts))

def normalize(s):
    return ''.join(c for c in unicodedata.normalize('NFD',s.lower()) if unicodedata.category(c)!='Mn')

def codes(s):
    return re.findall(r'\b(?:PP|TN|TP)\s*[- ]?\s*(\d{4})\b',s,re.I)

def canonical(s):
    m=re.fullmatch(r'(?:PP|TN|TP)\s*[- ]?\s*(\d{4})',s.strip(),re.I)
    return 'PP'+m.group(1) if m else ''

def today(): return date.today()

def now(): return datetime.now().isoformat(timespec='seconds')

class Store:
    def __init__(self,path):
        self.path=path
        with self.connect() as c:
            c.executescript('''CREATE TABLE IF NOT EXISTS cargo(code TEXT PRIMARY KEY, origin TEXT, destination TEXT, location TEXT, status TEXT, eta TEXT, reason TEXT, updated TEXT);
            CREATE TABLE IF NOT EXISTS history(code TEXT, event TEXT, timestamp TEXT);
            CREATE TABLE IF NOT EXISTS cargo_stage(code TEXT PRIMARY KEY, stage TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS tickets(id TEXT PRIMARY KEY, code TEXT, kind TEXT, detail TEXT, status TEXT, created TEXT);
            CREATE TABLE IF NOT EXISTS interactions(id INTEGER PRIMARY KEY, mode TEXT, resolved INTEGER, seconds REAL, created TEXT);''')
            c.execute('BEGIN IMMEDIATE')
            if not c.execute('SELECT 1 FROM cargo LIMIT 1').fetchone(): self.seed(c)
    @contextmanager
    def connect(self):
        c=sqlite3.connect(self.path,timeout=15); c.row_factory=sqlite3.Row
        try:
            with c: yield c
        finally: c.close()
    def seed(self,c):
        t=today()
        special={1:('Fortaleza','Fortaleza','Fortaleza','Entregue'),2:('Fortaleza','Sobral','Itapajé','Em trânsito'),3:('Fortaleza','Tianguá','Sobral','Atrasada'),4:('Sobral','Crateús','Crateús','Saiu para entrega'),5:('Sobral','Teresina','Sobral','Aguardando coleta'),6:('Fortaleza','Juazeiro do Norte','Iguatu','Atrasada')}
        remaining=['Entregue']*57+['Em trânsito']*29+['Atrasada']*8
        # 58 entregues, 32 em trânsito/saída/coleta, 10 atrasadas.
        j=0
        for i in range(1,101):
            code=f'PP{1000+i}'
            if i in special: origin,dest,loc,status=special[i]
            else:
                origin,dest=ROUTES[(i-1)%len(ROUTES)]; status=remaining[i-7]; loc=dest if status=='Entregue' else origin
                extra={67:STAGES[1],68:STAGES[2],69:STAGES[3],70:STAGES[5],71:STAGES[6],72:EXCEPTION_STAGE,73:STAGES[1],74:STAGES[2],75:STAGES[3],76:STAGES[5]}
                if status=='Em trânsito' and i in extra:
                    status=extra[i];loc=dest if stage_index(status)>=5 else origin
            delta=-2 if status=='Atrasada' else -1 if status=='Entregue' else 0 if status=='Saiu para entrega' else 1+(i%4)
            eta=(t+timedelta(days=delta)).isoformat()
            reason=REASONS[j] if status=='Atrasada' else ''; j+=int(status=='Atrasada')
            updated=now(); c.execute('INSERT INTO cargo VALUES(?,?,?,?,?,?,?,?)',(code,origin,dest,loc,status,eta,reason,updated))
            seed_movements(c,code,origin,dest,loc,status,reason,updated)
    def get(self,code):
        with self.connect() as c:
            r=c.execute('SELECT * FROM cargo WHERE code=?',(canonical(code),)).fetchone()
            if not r:return None
            phase=c.execute('SELECT stage FROM cargo_stage WHERE code=?',(r['code'],)).fetchone()
        d=dict(r); d['stage']=phase[0] if phase else ('Em trânsito' if d['status']=='Atrasada' else d['status']); d['stage_label']=stage_label(d['stage']); d['days_late']=0 if d['status']=='Entregue' else max(0,(today()-date.fromisoformat(d['eta'])).days)
        if d['days_late']>0: d['status']='Atrasada'; d['reason']=d['reason'] or 'Motivo ainda não registrado'
        return d
    def all(self):
        with self.connect() as c: ids=[r[0] for r in c.execute('SELECT code FROM cargo ORDER BY code')]
        return [self.get(i) for i in ids]
    def history(self,code):
        with self.connect() as c: return [dict(r) for r in c.execute('SELECT event,timestamp FROM history WHERE code=? ORDER BY timestamp',(canonical(code),))]
    def ticket(self,code,kind,detail):
        code=canonical(code); detail=detail.strip()[:300]
        if not self.get(code): raise ValueError('Carga inexistente')
        if kind not in ('Atraso','Prioridade','Reclamação','Entrega não reconhecida'): raise ValueError('Tipo inválido')
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE')
            r=c.execute("SELECT id FROM tickets WHERE code=? AND kind=? AND status='Aberto'",(code,kind)).fetchone()
            if r: return r[0],False
            tid='OC-'+secrets.token_hex(3).upper()
            c.execute('INSERT INTO tickets VALUES(?,?,?,?,?,?)',(tid,code,kind,detail,'Aberto',now()))
            return tid,True
    def tickets(self):
        with self.connect() as c: return [dict(r) for r in c.execute('SELECT * FROM tickets ORDER BY created DESC')]
    def close(self,tid):
        with self.connect() as c: return c.execute("UPDATE tickets SET status='Resolvido' WHERE id=? AND status='Aberto'",(tid,)).rowcount==1
    def log(self,mode,resolved,seconds):
        with self.connect() as c: c.execute('INSERT INTO interactions(mode,resolved,seconds,created) VALUES(?,?,?,?)',(mode,int(resolved),seconds,now()))
    def summary(self):
        rows=self.all(); counts=Counter(r['status'] for r in rows); late=[r for r in rows if r['status']=='Atrasada']; reasons=Counter(r['reason'] for r in late)
        with self.connect() as c:
            n,res,avg=c.execute('SELECT COUNT(*),COALESCE(SUM(resolved),0),COALESCE(AVG(seconds),0) FROM interactions').fetchone()
        return {'total':len(rows),'delivered':counts['Entregue'],'active':len(rows)-counts['Entregue']-len(late),'late':len(late),'reasons':dict(reasons),'open_tickets':sum(t['status']=='Aberto' for t in self.tickets()),'interactions':n,'resolved':res,'avg_seconds':round(avg,2)}

def delivery_estimate(d):
    """Deterministic fictional forecast, preserving the original deadline.
    A confirmed future date overrides it; an expired estimate advances only
    on reaching its date. No real operational data is used.
    """
    if d['status']!='Atrasada':return ''
    if d.get('confirmed_eta') and date.fromisoformat(d['confirmed_eta'])>=today():return ''
    interval=1+int(d['code'][2:])%3
    anchor=max(date.fromisoformat(d['eta']),date.fromisoformat(d['updated'][:10]))
    if d.get('confirmed_eta'):anchor=max(anchor,date.fromisoformat(d['confirmed_eta']))
    elapsed=max(0,(today()-anchor).days)
    return (anchor+timedelta(days=interval*(elapsed//interval+1))).isoformat()

def forecast_text(d):
    """One shared customer-facing forecast for all surfaces."""
    if d['status']=='Entregue':return ''
    confirmed=d.get('confirmed_eta','')
    estimate=d.get('estimated_eta') or delivery_estimate(d)
    if confirmed and date.fromisoformat(confirmed)>=today():
        return 'Nova previsão confirmada: '+date.fromisoformat(confirmed).strftime('%d/%m/%Y')
    if estimate:
        previous=('Previsão anterior vencida: '+date.fromisoformat(confirmed).strftime('%d/%m/%Y')+'. ' if confirmed else '')
        return previous+'Nova previsão estimada: '+date.fromisoformat(estimate).strftime('%d/%m/%Y')+' (estimativa simulada, sujeita à confirmação da logística).'
    return ''

def delay_metrics(d):
    """Calendar days elapsed and projected, measured from the original date."""
    if d['status'] != 'Atrasada':return {}
    original=date.fromisoformat(d['eta'])
    current=today()
    confirmed=d.get('confirmed_eta','')
    forecast=confirmed if confirmed and date.fromisoformat(confirmed)>=current else (d.get('estimated_eta') or delivery_estimate(d))
    result={'elapsed':max(0,(current-original).days)}
    if forecast:
        end=date.fromisoformat(forecast)
        result.update(remaining=max(0,(end-current).days),total=max(0,(end-original).days))
    return result


def day_label(n):return f"{n} dia" if n==1 else f"{n} dias"


def delay_summary(d):
    m=delay_metrics(d)
    if not m:return ''
    text='Atraso até hoje: '+day_label(m['elapsed'])
    if 'total' in m:text+=' · Tempo restante previsto: '+day_label(m['remaining'])+' · Atraso total previsto: '+day_label(m['total'])
    return text


def describe(d):
    eta=date.fromisoformat(d['eta']).strftime('%d/%m/%Y')
    msg=f"**Carga {d['code']} — {d['status']}**\n\n- Rota: {d['origin']} → {d['destination']}\n- Etapa do transporte: {d.get('stage_label',d['status'])}\n- Última localização registrada: {d['location']}\n- Prazo original: {eta}"
    if d['status']=='Atrasada': msg+=f"\n- {delay_summary(d)}. Motivo: {d['reason']}."
    forecast=forecast_text(d)
    if forecast:msg+='\n- '+forecast
    if d['status']=='Atrasada':msg+='\n\nSentimos muito pela demora. Posso preparar uma ocorrência para a equipe avaliar.'
    return msg

def forbidden(text):
    s=normalize(text)
    return bool(re.search(r'\b(cpf|cnpj|telefone|endereco|senha|dados pessoais|lista de clientes|todos os clientes|todos os pedidos|todas as cargas|indeniz\w*|reembols\w*|estorn\w*|ignore as regras|api key|chave de api)\b',s))

REFUSAL='Não posso divulgar dados privados, fornecer credenciais ou autorizar pagamentos/indenizações. A equipe humana pode avaliar solicitações financeiras ou sensíveis. Posso ajudar com o rastreio ou registrar uma ocorrência operacional.'

def demo_reply(text,store,context):
    s=normalize(text)
    if forbidden(text): return REFUSAL,None,False
    matches=codes(text)
    if len(set(matches))>1: return 'Consulte uma carga por vez, por favor.',None,False
    if matches: context['code']='PP'+matches[0]
    code=context.get('code',''); d=store.get(code) if code else None
    if not d:
        if code: return f'Não encontrei a carga {code}. Confira o código e tente novamente.',None,False
        return 'Olá! Sou o PACO. Informe seu código de rastreio (por exemplo, PP1002) para consultar a entrega ou registrar uma ocorrência. Se não souber o código, informe o telefone com DDD vinculado à compra, usando um número de exemplo.',None,False
    kind=None
    if re.search(r'nao recebi|nao chegou.*entregue|nao reconhe',s) and d['status']=='Entregue': kind='Entrega não reconhecida'
    elif re.search(r'priori|urgente|urgencia|agiliza',s): kind='Prioridade'
    elif re.search(r'abr[ia]|regist|chamado|ocorrencia|reclam|resolv|soluc|sim\b|pode',s): kind='Atraso' if d['days_late'] else 'Reclamação'
    if kind:
        return describe(d)+f'\n\nPreparei uma solicitação de **{kind}**. Confirme no botão abaixo para registrá-la.',{'code':code,'kind':kind},False
    if 'historico' in s or 'movimenta' in s:
        return describe(d)+'\n\n**Histórico:**\n'+'\n'.join('- '+r['event'] for r in store.history(code)),None,True
    return describe(d),None,True
