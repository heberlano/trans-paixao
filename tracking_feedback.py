"""Consistent customer-facing tracking validation for the portal and PACO."""
import re
import unicodedata

FORMAT = 'Desculpe, mas o código informado não corresponde ao padrão de rastreamento utilizado pela Transportadora Paixão. Nossos códigos começam com as letras PP, seguidas de quatro números (ex.: PP1002). Confira o código no comprovante de envio e tente novamente. Se não souber o código, use a busca pelo telefone com DDD vinculado à compra. O PACO está à disposição para ajudar!'
MISSING = 'Sentimos muito! O código informado está no formato correto, mas não conseguimos localizar uma entrega vinculada a ele em nosso sistema. Pode ter ocorrido um erro de digitação ou a carga ainda não ter sido cadastrada. Confira o código no comprovante de envio e tente novamente. Se não souber o código, procure a entrega pelo telefone com DDD vinculado à compra. Estamos à disposição para orientar você.'
EMPTY = 'Precisamos do seu código para localizar a entrega. Digite o código de rastreamento informado no momento do envio da mercadoria. Ele começa com PP, seguido de quatro números. Exemplo: PP1002.'
MULTIPLE = 'Para ajudar você com segurança, vamos consultar uma entrega por vez. Qual código deseja consultar primeiro?'

def tracking_result(store, raw):
    """Return (cargo, heading, message). Strict public PP format; allow spaces/hyphen/case."""
    raw = str(raw or '').strip()
    if not raw:
        return None, 'Informe seu código de rastreamento', EMPTY
    m = re.fullmatch(r'PP\s*-?\s*([0-9]{4})', raw, re.I)
    if not m:
        return None, 'Vamos conferir seu código de rastreamento?', FORMAT
    cargo = store.get('PP' + m[1])
    if not cargo:
        return None, 'Ainda não localizamos sua entrega', MISSING
    return cargo, '', ''

def chat_tracking_check(text, store, ctx):
    """Return a deterministic reply on bad explicit codes, before memory or LLM tools.
    Do not confuse order protocols, quotes, dimensions or ratings with tracking codes.
    """
    raw = text.strip()
    norm = ''.join(c for c in unicodedata.normalize('NFD', raw.lower()) if unicodedata.category(c) != 'Mn')
    tracking_intent = bool(re.search(r'\b(rastre\w*|carga|entrega|mercadoria|codigo|pedido)\b', norm))
    quote_intent = bool(re.search(r'\b(frete|cotacao|orcamento|quanto custa)\b', norm))
    # PP and common alphanumeric code-like strings; reject tokens with extra suffixes.
    candidates = re.findall(r'(?<![\w])PP(?:\s*-\s*|\s+)?[0-9][A-Za-z0-9_-]*\b', raw, re.I)
    candidates += re.findall(r'(?<![\w])(?:TN|TP)\s*-?\s*[0-9][A-Za-z0-9_-]*\b', raw, re.I)
    if (tracking_intent and not quote_intent) or re.fullmatch(r'[A-Za-z]{1,12}[- ]?[0-9]+[A-Za-z0-9_-]*', raw):
        for m in re.finditer(r'(?<![\w])([A-Za-z]{1,12})-?([0-9]+[A-Za-z0-9_-]*)\b', raw):
            if m[1].upper() not in ('PP','OC','CT','V') and not re.fullmatch(r'x[0-9]+', m[0], re.I):
                candidates.append(m[0])
    # A bare number is only a tracking attempt if not part of a quote/rating.
    if re.fullmatch(r'[0-9]{4,}', raw): candidates.append(raw)
    if not candidates and tracking_intent and not quote_intent:
        m = re.search(r'\b(?:codigo(?:\s+de\s+rastreio)?|rastreio|rastrear|carga|pedido)\s*(?:e\s+|: ?|#)?\s*([0-9]+[A-Za-z0-9_-]*|pp(?:-[A-Za-z0-9]+|[A-Za-z]+)?)\b', norm)
        if m: candidates.append(m[1])
    if not candidates and tracking_intent and not quote_intent:
        m = re.search(r'(?i:\b(?:c[oó]digo(?: de rastreio)?|rastreio|carga)\s*(?:[:#]\s*|(?:é|e)\s+))([A-Z]{2,12})\b', raw)
        if m: candidates.append(m[1])
    if not candidates and re.fullmatch(r'PP(?:[- ]?[A-Za-z]+)?', raw, re.I): candidates.append(raw)
    # Distinct codes only; a malformed explicit attempt must not reuse the previous cargo.
    if candidates:
        checked = [tracking_result(store, x) for x in candidates]
        errors = [x for x in checked if x[0] is None]
        if errors:
            ctx.pop('code', None)
            return errors[0][2], None, False
        unique = {x[0]['code'] for x in checked}
        if len(unique) > 1:
            ctx.pop('code', None)
            return MULTIPLE, None, False
        ctx['code'] = next(iter(unique))
    return None
