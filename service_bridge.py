"""Shared customer context across tracking, PACO and Help (session only)."""
from tracking_feedback import tracking_result


def select_delivery(state, store, code):
    d, _, _ = tracking_result(store, code)
    if not d:
        return False
    code = d['code']
    ctx = state.setdefault('context', {})
    if ctx.get('code') != code:
        ctx.pop('reschedule_code', None)
        ctx.pop('protocol', None)
        pending = state.get('pending')
        if pending and pending.get('code') and pending['code'] != code:
            state['pending'] = None
    ctx['code'] = code
    ctx.pop('phone_codes', None)
    ctx.pop('waiting_phone', None)
    state['track_code'] = code
    if state.get('protocol_query', ('',''))[0] != code:
        state['protocol_query'] = (code, '')
        ctx.pop('protocol',None)
        state['help_refresh'] = True
    return True


def sync_chat_delivery(state, store):
    code = state.get('context', {}).get('code')
    if code:
        select_delivery(state, store, code)
    else:
        state['track_code'] = ''
        state.pop('protocol_query', None)
        state['context'].pop('protocol',None)
        state['protocol_task']='new'
        state['help_refresh']=True


def open_help(state, store, code=None, protocol=None, kind=None):
    code = code or state.get('context', {}).get('code')
    if not code or not select_delivery(state, store, code):
        state['protocol_task'] = 'new'
        state['help_refresh'] = True
        return
    code = state['track_code']
    pending = state.get('pending') or {}
    if protocol is None and not kind and pending.get('kind') and pending.get('code') == code:
        kind = pending['kind']
    if protocol is None and not kind:
        active=[t for t in store.cargo_tickets(code) if t['status']!='Resolvido']
        if active:protocol=active[0]['id'] if len(active)==1 else ''
    if protocol is not None:
        state['protocol_query'] = (code, protocol)
        state['protocol_task'] = 'lookup'
    else:
        state['case_kind'] = kind or ('Atraso' if store.get(code)['status']=='Atrasada' else 'Reclamação')
        state['protocol_task'] = 'new'
    state['help_refresh'] = True


def registered(state, store, code, tid, kind):
    select_delivery(state, store, code)
    state['protocol_query'] = (code, tid)
    state['protocol_task'] = 'lookup'
    state['help_refresh'] = True
    pending = state.get('pending') or {}
    if pending.get('code') == code and pending.get('kind') == kind:
        state['pending'] = None
    state.setdefault('context', {})['protocol'] = tid


def chat_protocol_text(store, code, tid=''):
    rows = [store.protocol(tid, code)] if tid else store.cargo_tickets(code)
    rows = [r for r in rows if r]
    if not rows:
        return 'Ainda não encontramos chamados para essa consulta. Confira o protocolo ou abra uma solicitação na Central de ajuda.'
    return '\n\n'.join(f"**{r['id']}** · {r['kind']} · {r['status']}" + (f"\n\nÚltima atualização: {r['solution']}" if r.get('solution') else '') for r in rows) + '\n\nVocê pode acompanhar o histórico e confirmar a solução na Central de ajuda.'
