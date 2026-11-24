"""Geração local de entregas fictícias. Não consulta contatos reais."""
import re, hmac, hashlib, secrets
from datetime import timedelta
from delay_scenarios import SCENARIOS
from core import normalize, forbidden, REFUSAL, describe, today, now, ROUTES, seed_movements

EXAMPLES = [('(88) 00000-0001',('PP1002','PP1003')),('(85) 00000-0002',('PP1001','PP1004')),('(88) 00000-0003',('PP1005','PP1006')),('(86) 00000-0004',('PP1093','PP1094')),('(85) 00000-0005',('PP1064','PP1065')),('(88) 00000-0006',('PP1099','PP1100')),('(85) 00000-0007',('PP1010','PP1020')),('(86) 00000-0008',('PP1050','PP1080'))]
HELP='Sem problema! Se você não tem o código de rastreamento, informe o telefone com DDD vinculado à compra. Neste ambiente de simulação, use um telefone fictício com DDD, como (88) 00000-1234. Se não houver associação, criaremos entregas de exemplo para você testar.'
PHONE_PATTERN=r'(?<![\w\d])(?:\+55[ .-]*)?\(?\d{2}\)?[ .-]*\d{4,5}[ .-]*\d{4}(?![\w\d])'

def phone_key(raw):
    raw=str(raw or '').strip()
    if not re.fullmatch(PHONE_PATTERN,raw):return ''
    digits=re.sub(r'\D','',raw)
    if raw.startswith('+55'):digits=digits[2:]
    return digits if len(digits) in (10,11) and digits[0]!='0' else ''

def lookup(store,raw):
    p=phone_key(raw)
    if not p:return [],'Confira o telefone informado. Precisamos do DDD e do número, como (88) 00000-0001.'
    for number,ids in EXAMPLES:
        if p==phone_key(number):
            rows=[d for code in ids if (d:=store.get(code))]
            if rows:return rows,''
    # Os números digitados não são armazenados nem enviados a serviços externos.
    # Uma chave por base permite encontrar o mesmo par de cargas dentro da sessão.
    with store.connect() as c:
        c.execute('BEGIN IMMEDIATE')
        c.execute('CREATE TABLE IF NOT EXISTS demo_settings(name TEXT PRIMARY KEY,value TEXT)')
        c.execute('CREATE TABLE IF NOT EXISTS demo_phone_cargo(phone_digest TEXT,code TEXT UNIQUE,PRIMARY KEY(phone_digest,code))')
        c.execute("INSERT OR IGNORE INTO demo_settings VALUES('phone_secret',?)",(secrets.token_hex(32),))
        key=c.execute("SELECT value FROM demo_settings WHERE name='phone_secret'").fetchone()[0]
        digest=hmac.new(bytes.fromhex(key),p.encode(),hashlib.sha256).hexdigest()
        ids=[r[0] for r in c.execute('SELECT code FROM demo_phone_cargo WHERE phone_digest=? ORDER BY code',(digest,))]
        if not ids:
            used={r[0] for r in c.execute('SELECT code FROM cargo')}
            ids=[f'PP{n}' for n in range(2000,9000) if f'PP{n}' not in used][:2]
            if len(ids)!=2:return [],'O limite de entregas de exemplo foi atingido nesta sessão. Consulte um código existente.'
            ordinal=c.execute('SELECT COUNT(DISTINCT phone_digest) FROM demo_phone_cargo').fetchone()[0]
            t=today();ts=now()
            for j,code in enumerate(ids):
                origin,dest=ROUTES[(ordinal+j)%len(ROUTES)]
                status='Atrasada' if j==0 else 'Em trânsito'
                reason=SCENARIOS[ordinal%len(SCENARIOS)][0] if j==0 else ''
                eta=(t+timedelta(days=-2 if j==0 else 2)).isoformat()
                c.execute('INSERT INTO cargo VALUES(?,?,?,?,?,?,?,?)',(code,origin,dest,origin,status,eta,reason,ts))
                seed_movements(c,code,origin,dest,origin,status,reason,ts)
                c.execute('INSERT INTO demo_phone_cargo VALUES(?,?)',(digest,code))
    return [store.get(code) for code in ids],''

def search_delivery(store,raw):
    """One search field: identify phone or tracking code without retaining raw input."""
    from tracking_feedback import tracking_result
    raw=str(raw or '').strip()
    if not raw:
        return [],'Como podemos localizar sua entrega?','Informe o código de rastreio ou, se não souber, um telefone fictício com DDD.'
    if phone_key(raw) or (re.fullmatch(r'[\d\s()+.-]+',raw) and (len(re.sub(r'\D','',raw))>=5 or raw.startswith(('(', '+')))):
        rows,error=lookup(store,raw)
        return rows,('Vamos conferir seu telefone?' if error else ''),error
    cargo,heading,message=tracking_result(store,raw)
    return ([cargo] if cargo else []),heading,message

def redact(text):
    return re.sub(PHONE_PATTERN,'[telefone informado]',text)

def chat_phone(text,store,ctx):
    s=normalize(text)
    matches=re.findall(PHONE_PATTERN,text)
    missing=bool(re.search(r'(nao (?:sei|tenho|lembro|encontro|achei|recebi)|perdi|esqueci|sem)\s+(?:qual e )?(?:o |meu |um )?(?:codigo|rastreio|numero de rastreio)',s))
    by_phone=bool(re.search(r'(?:pelo|por|com|via) (?:meu |o )?telefone|(?:meu|o) (?:telefone|celular) (?:e|:) |telefone com ddd|buscar.*telefone|consultar.*telefone',s))
    waiting=ctx.get('waiting_phone',False)
    candidates=ctx.get('phone_codes',[])
    selection=re.fullmatch(r'(?:a |o |quero (?:a |o )?)?(primeira|primeiro|segunda|segundo|1|2)(?: entrega| carga)?[.!]?',s.strip())
    if candidates and selection:
        i=0 if selection[1] in ('primeira','primeiro','1') else 1
        if i<len(candidates):
            ctx['code']=candidates[i];ctx.pop('phone_codes',None)
            d=store.get(ctx['code'])
            return describe(d)+'\n\nSe quiser, posso preparar um chamado para a equipe analisar.',None,True
    if not (matches or missing or by_phone or waiting):return None
    # Refuse other sensitive requests, even when a number is included.
    cleaned=re.sub(r'\b(?:telefone|celular)\b','',s)
    if forbidden(cleaned) or re.search(r'terceir|outros? clientes|outras? pessoas|lista|todos|todas|de quem|dono|titular|qual.*telefone|informe.*telefone|me (?:de|diga|mostre).*telefone',s):
        return REFUSAL,None,False
    if matches:
        ctx.pop('code',None);ctx.pop('reschedule_code',None);ctx.pop('phone_codes',None);ctx['waiting_phone']=False
        if len(matches)!=1:return 'Vamos consultar um telefone por vez. Qual deles você deseja usar?',None,False
        rows,err=lookup(store,matches[0])
        if err:ctx['waiting_phone']=True;return err,None,False
        ctx['phone_codes']=[d['code'] for d in rows]
        if len(rows)==1:ctx['code']=rows[0]['code']
        return 'Localizei '+str(len(rows))+' entrega(s) fictícia(s) vinculada(s) a esse telefone nesta simulação.\n\n'+'\n'.join(f"- **{d['code']}** — {d['origin']} → {d['destination']} · {d['status']}" for d in rows)+'\n\nQual dessas entregas você deseja consultar ou solicitar ajuda? Envie o código correspondente (ou diga primeira ou segunda).',None,True
    if waiting and re.search(r'\bPP\s*-?\s*\d{4}\b',text,re.I):ctx.pop('waiting_phone',None);return None
    if waiting and not (missing or by_phone) and not re.fullmatch(r'[\d\s()+.-]+',text):ctx.pop('waiting_phone',None);return None
    ctx.pop('code',None);ctx.pop('reschedule_code',None);ctx.pop('phone_codes',None);ctx['waiting_phone']=True
    return HELP,None,False
