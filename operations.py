"""Extended business tools. All data and prices are simulated."""
from tracking_feedback import chat_tracking_check
from core import Store, canonical, today, now, normalize, codes, describe, forbidden, REFUSAL, demo_reply
from datetime import date, datetime, timedelta
from collections import Counter, defaultdict
import math, re, secrets

CITIES={'Fortaleza':(-38.5267,-3.7319),'Sobral':(-40.3497,-3.688),'Itapajé':(-39.583,-3.686),'Tianguá':(-40.991,-3.729),'Crateús':(-40.677,-5.178),'Teresina':(-42.803,-5.089),'Juazeiro do Norte':(-39.315,-7.213),'Iguatu':(-39.298,-6.359),'Natal':(-35.209,-5.795),'Parnaíba':(-41.777,-2.905),'Recife':(-34.877,-8.047)}
STATUS=['Aguardando coleta','Em trânsito','Saiu para entrega','Entregue','Atrasada']
KINDS=['Atraso','Prioridade','Reclamação','Entrega não reconhecida','Avaria']

def money(n): return f'R$ {n:,.2f}'.replace(',','X').replace('.',',').replace('X','.')
def city(s):
    return next((c for c in CITIES if normalize(c)==normalize(s.strip())),None)
def quote(origin,destination,weight,length,width,height,service='Econômica'):
    a,b=city(origin),city(destination)
    if not a or not b or a==b: raise ValueError('Escolha duas cidades diferentes da lista atendida.')
    vals=list(map(float,[weight,length,width,height]))
    if not all(math.isfinite(v) and 0<v<=10000 for v in vals): raise ValueError('Peso e dimensões devem ser positivos e até 10.000.')
    if service not in ['Econômica','Expressa']: raise ValueError('Modalidade inválida.')
    lon1,lat1=map(math.radians,CITIES[a]); lon2,lat2=map(math.radians,CITIES[b]); h=math.sin((lat2-lat1)/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    km=round(6371*2*math.asin(min(1,math.sqrt(h)))*1.25)
    cub=round(vals[1]*vals[2]*vals[3]/1e6*300,2); charge=max(vals[0],cub)
    total=round((25+km*.12+charge*1.15)*(1.45 if service=='Expressa' else 1),2)
    return dict(origin=a,destination=b,weight=vals[0],length=vals[1],width=vals[2],height=vals[3],service=service,km=km,cubed=cub,charge=charge,total=total,days=max(1,math.ceil(km/(550 if service=='Expressa' else 300)))+int(service=='Econômica'))

def quote_text(q):
    return f"**Cotação simulada: {money(q['total'])}**\n\n{q['origin']} → {q['destination']} · {q['service']}\n\nDistância estimada: {q['km']} km | Peso tarifável: {q['charge']} kg | Prazo estimado: {q['days']} dia(s). Sem validade comercial."

class Operations(Store):
    def __init__(self,path):
        super().__init__(path)
        with self.connect() as c:
            c.executescript('''CREATE TABLE IF NOT EXISTS fleet(id TEXT PRIMARY KEY, label TEXT, driver TEXT, capacity REAL, status TEXT);
            CREATE TABLE IF NOT EXISTS assignments(code TEXT PRIMARY KEY, vehicle TEXT);
            CREATE TABLE IF NOT EXISTS quotes(id TEXT PRIMARY KEY, origin TEXT,destination TEXT,weight REAL,length REAL,width REAL,height REAL,service TEXT,total REAL,created TEXT);
            CREATE TABLE IF NOT EXISTS ratings(code TEXT PRIMARY KEY, score INTEGER, created TEXT);
            CREATE TABLE IF NOT EXISTS notices(id INTEGER PRIMARY KEY, code TEXT, message TEXT, created TEXT);''')
            c.execute('BEGIN IMMEDIATE')
            if not c.execute('SELECT 1 FROM fleet LIMIT 1').fetchone():
                c.executemany('INSERT INTO fleet VALUES(?,?,?,?,?)',[(f'V{i:03}',f'Caminhão {i:02}',f'Motorista fictício {i:02}',cap,stat) for i,(cap,stat) in enumerate([(8000,'Disponível'),(12000,'Em rota'),(6000,'Manutenção'),(10000,'Em rota'),(3500,'Disponível')],1)])
                c.executemany('INSERT OR IGNORE INTO assignments VALUES(?,?)',[(f'PP{i}',f'V{(i%5)+1:03}') for i in range(1002,1101) if i%3==0])
    def ticket(self,code,kind,detail):
        if kind!='Avaria': return super().ticket(code,kind,detail)
        code=canonical(code)
        if not self.get(code): raise ValueError('Carga inexistente')
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE'); r=c.execute("SELECT id FROM tickets WHERE code=? AND kind=? AND status='Aberto'",(code,kind)).fetchone()
            if r:return r[0],False
            tid='OC-'+secrets.token_hex(3).upper(); c.execute('INSERT INTO tickets VALUES(?,?,?,?,?,?)',(tid,code,kind,detail[:300],'Aberto',now())); return tid,True
    def protocol(self,tid,code):
        with self.connect() as c:r=c.execute('SELECT id,code,kind,status,created FROM tickets WHERE id=? AND code=?',(tid.strip().upper(),canonical(code))).fetchone()
        return dict(r) if r else None
    def cargo_tickets(self,code): return [{k:t[k] for k in ('id','code','kind','status','created')} for t in self.tickets() if t['code']==canonical(code)]
    def close(self,tid):
        ok=super().close(tid)
        if ok:
            t=next(t for t in self.tickets() if t['id']==tid); self.notify(t['code'],f'Protocolo {tid} resolvido.')
        return ok
    def notify(self,code,msg):
        with self.connect() as c:c.execute('INSERT INTO notices(code,message,created) VALUES(?,?,?)',(code,msg,now()))
    def notices(self,code):
        d=self.get(code)
        if not d:return []
        with self.connect() as c:out=[dict(r) for r in c.execute('SELECT message,created FROM notices WHERE code=? ORDER BY id DESC',(d['code'],))]
        out.append({'message':f"Última situação: {d['status']} · {d['location']}",'created':d['updated']})
        if d['days_late']:out.insert(0,{'message':f"Prazo original vencido há {d['days_late']} dia(s). {d['reason']}",'created':now()})
        return out
    def create_cargo(self,origin,destination,eta,vehicle=''):
        if origin not in CITIES or destination not in CITIES or origin==destination:raise ValueError('Origem e destino inválidos.')
        if date.fromisoformat(str(eta))<today():raise ValueError('Prazo inicial não pode estar vencido.')
        if vehicle and not any(v['id']==vehicle and v['status']!='Manutenção' for v in self.fleet()):raise ValueError('Veículo indisponível.')
        with self.connect() as c:
            c.execute('BEGIN IMMEDIATE'); used={r[0] for r in c.execute('SELECT code FROM cargo')}; n=next((n for n in range(1101,10000) if f'PP{n}' not in used),10000)
            if n>9999:raise ValueError('Limite de códigos atingido.')
            code=f'PP{n}'; ts=now(); c.execute('INSERT INTO cargo VALUES(?,?,?,?,?,?,?,?)',(code,origin,destination,origin,STATUS[0],str(eta),'',ts)); c.execute('INSERT INTO history VALUES(?,?,?)',(code,f'Cadastro · {origin}',ts))
            if vehicle:c.execute('INSERT INTO assignments VALUES(?,?)',(code,vehicle))
        self.notify(code,'Carga cadastrada.'); return code
    def update_cargo(self,code,location,status,reason=''):
        d=self.get(code)
        if not d or location not in CITIES or status not in STATUS:raise ValueError('Dados inválidos.')
        if d['status']=='Entregue':raise ValueError('Carga entregue não pode ser alterada nesta demonstração.')
        if status=='Entregue' and location!=d['destination']:raise ValueError('Entrega deve ocorrer no destino.')
        if status=='Atrasada' and not reason.strip():raise ValueError('Informe o motivo do atraso.')
        if d['days_late'] and status!='Entregue':status='Atrasada'; reason=reason.strip() or d['reason']
        ts=now()
        with self.connect() as c:
            c.execute('UPDATE cargo SET location=?,status=?,reason=?,updated=? WHERE code=?',(location,status,reason[:150] if status=='Atrasada' else '',ts,d['code'])); c.execute('INSERT INTO history VALUES(?,?,?)',(d['code'],f'{status} · {location}'+(f' · {reason[:150]}' if status=='Atrasada' else ''),ts))
        self.notify(d['code'],f'{status} · {location}')
    def fleet(self):
        with self.connect() as c:return [dict(r) for r in c.execute('SELECT * FROM fleet ORDER BY id')]
    def save_vehicle(self,vid,label,driver,capacity,status):
        if status not in ['Disponível','Em rota','Manutenção'] or not re.fullmatch(r'V\d{3}',vid) or not label.strip() or not driver.strip() or not math.isfinite(capacity) or not 0<capacity<=100000:raise ValueError('Dados de veículo inválidos.')
        with self.connect() as c:c.execute('INSERT INTO fleet VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET label=excluded.label,driver=excluded.driver,capacity=excluded.capacity,status=excluded.status',(vid,label[:60],driver[:60],capacity,status))
    def assign(self,code,vid):
        d=self.get(code)
        if not d or d['status']=='Entregue' or not any(v['id']==vid and v['status']!='Manutenção' for v in self.fleet()):raise ValueError('Carga ou veículo indisponível.')
        with self.connect() as c:c.execute('INSERT OR REPLACE INTO assignments VALUES(?,?)',(d['code'],vid))
    def assignments(self):
        with self.connect() as c:return [dict(r) for r in c.execute('SELECT * FROM assignments ORDER BY code')]
    def save_quote(self,q):
        q=quote(**{k:q[k] for k in ['origin','destination','weight','length','width','height','service']}); qid='CT-'+secrets.token_hex(3).upper()
        with self.connect() as c:c.execute('INSERT INTO quotes VALUES(?,?,?,?,?,?,?,?,?,?)',(qid,q['origin'],q['destination'],q['weight'],q['length'],q['width'],q['height'],q['service'],q['total'],now()))
        return qid
    def quotes(self):
        with self.connect() as c:return [dict(r) for r in c.execute('SELECT * FROM quotes ORDER BY created DESC')]
    def rate(self,code,score):
        d=self.get(code)
        if not d or d['status']!='Entregue' or score not in range(1,6):raise ValueError('Avaliação permitida apenas para carga entregue, de 1 a 5.')
        with self.connect() as c:c.execute('INSERT INTO ratings VALUES(?,?,?) ON CONFLICT(code) DO UPDATE SET score=excluded.score,created=excluded.created',(d['code'],score,now()))
    def extended(self):
        m=self.summary(); rows=self.all(); routes=defaultdict(lambda:[0,0]); delivered_days=Counter()
        for d in rows:
            r=f"{d['origin']} → {d['destination']}"; routes[r][0]+=1; routes[r][1]+=d['status']=='Atrasada'
            if d['status']=='Entregue':delivered_days[d['updated'][:10]]+=1
        with self.connect() as c:n,avg=c.execute('SELECT COUNT(*),AVG(score) FROM ratings').fetchone()
        m.update(routes=[dict(route=k,total=v[0],late=v[1],rate=round(v[1]/v[0]*100,1)) for k,v in routes.items()],ratings=n,satisfaction=round(avg,2) if n else None,quotes=len(self.quotes()),quoted_total=round(sum(q['total'] for q in self.quotes()),2),fleet=len(self.fleet()),delivered_days=dict(delivered_days)); return m
    def alerts(self):
        rows=self.all(); a=[]; late=[d for d in rows if d['status']=='Atrasada']; risk=[d for d in rows if d['status'] in STATUS[:2] and 0<=(date.fromisoformat(d['eta'])-today()).days<=1]
        if late:a.append(('Alta',f'{len(late)} cargas atrasadas','Priorizar revisão de ocorrências e prazos.'))
        if risk:a.append(('Atenção',f'{len(risk)} cargas próximas do prazo','Verificar movimentações e capacidade antes do vencimento.'))
        old=[t for t in self.tickets() if t['status']=='Aberto' and datetime.now()-datetime.fromisoformat(t['created'])>timedelta(hours=24)]
        if old:a.append(('Alta',f'{len(old)} protocolos abertos há mais de 24h','Encaminhar para revisão do gestor.'))
        vehicles=[v for v in self.fleet() if v['status']=='Manutenção']; maintenance={v['id'] for v in vehicles}; active={d['code'] for d in rows if d['status']!='Entregue'}
        conflicts=[x for x in self.assignments() if x['vehicle'] in maintenance and x['code'] in active]
        if conflicts:a.append(('Alta',f'{len(conflicts)} cargas ativas ligadas a veículo em manutenção','Reavaliar a alocação de frota.'))
        groups=Counter(d['destination'] for d in rows if d['status']=='Aguardando coleta')
        for dest,n in groups.items():
            if n>=2:a.append(('Oportunidade',f'{n} cargas aguardam coleta para {dest}','Avaliar consolidação, capacidade e prazos.'))
        return a

def demo_extended(text,store,ctx):
    s=normalize(text)
    if forbidden(text):return REFUSAL,None,False
    feedback=chat_tracking_check(text,store,ctx)
    if feedback:return feedback
    ms=codes(text)
    if len(set(ms))>1:return 'Consulte uma carga por vez.',None,False
    if ms:ctx['code']='PP'+ms[0]
    code=ctx.get('code','')
    if re.search(r'frete|cotacao|orcamento|quanto custa',s):
        # Explicit complete quote examples; no inferred dimensions.
        cities=sorted([(s.find(normalize(c)),c) for c in CITIES if normalize(c) in s]); w=re.search(r'(\d+(?:[,.]\d+)?)\s*kg',s); dim=re.search(r'(\d+(?:[,.]\d+)?)\s*[x×]\s*(\d+(?:[,.]\d+)?)\s*[x×]\s*(\d+(?:[,.]\d+)?)',s)
        if len(cities)==2 and w and dim:
            try:
                q=quote(cities[0][1],cities[1][1],float(w[1].replace(',','.')),*[float(x.replace(',','.')) for x in dim.groups()], 'Expressa' if 'express' in s else 'Econômica');ctx['quote']=q;return quote_text(q)+'\n\nPosso registrar a cotação se você solicitar.',None,True
            except ValueError as e:return str(e),None,False
        if ctx.get('quote') and re.search('registr|contrat|salv',s):return quote_text(ctx['quote'])+'\n\nConfirme a solicitação.',{'action':'quote','quote':ctx['quote']},False
        return 'Informe origem, destino, peso em kg e dimensões em cm (C x L x A). Ex.: frete Fortaleza para Sobral 20 kg 50x40x30.',None,False
    if ctx.get('quote') and re.search(r'contrat|registrar (?:essa|a) cotacao',s):return 'Confirme o registro da cotação simulada.',{'action':'quote','quote':ctx['quote']},False
    if 'protocolo' in s:
        if not store.get(code):return 'Informe o código da carga para consultar os protocolos.',None,False
        tid=re.search(r'\bOC-[A-F0-9]{6}\b',text.upper()); rows=[store.protocol(tid[0],code)] if tid else store.cargo_tickets(code);rows=[r for r in rows if r]
        return ('\n\n'.join(f"**{r['id']}** · {r['kind']} · {r['status']}" for r in rows) or 'Nenhum protocolo encontrado para essa carga.'),None,True
    if re.search(r'notific|alerta',s) and store.get(code):return '\n\n'.join(r['message'] for r in store.notices(code)),None,True
    if re.search(r'avaria|danific|quebrad',s) and store.get(code):return 'Preparei uma ocorrência de avaria. Confirme para registrar.',{'code':code,'kind':'Avaria'},False
    if re.search(r'avali|satisfacao',s) and store.get(code):
        score=re.search(r'\b([1-5])\b',s)
        if store.get(code)['status']!='Entregue':return 'A avaliação está disponível após a entrega.',None,False
        if score:return 'Confirme a avaliação.',{'action':'rating','code':code,'score':int(score[1])},False
        return 'Informe uma nota de 1 a 5.',None,False
    return demo_reply(text,store,ctx)
