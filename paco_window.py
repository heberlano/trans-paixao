"""Floating PACO using native Streamlit widgets and the existing session.
No iframe, external JavaScript, new database or second conversation.
"""


def init_window(state):
    if state.get('paco_window') not in ('open', 'closed'):
        state['paco_window'] = 'closed'
    if state.get('nav') == 'PACO':  # migrate sessions from 3.9
        state['nav'] = 'Início'
        open_window(state)


def open_window(state):
    state['paco_window'] = 'open'


def close_window(state):
    state['paco_window'] = 'closed'


def reset_conversation(state, sync, store):
    state['messages'] = []
    state['context'] = {}
    state['pending'] = None
    sync(state, store)


CSS = '''<style>
/* 4.1 — only a small launcher until explicitly opened. Never resize the page. */
.st-key-navbox [data-testid="stHorizontalBlock"]{grid-template-columns:repeat(3,minmax(0,1fr))!important;}
/* Community Cloud decorations when rendered inside the app. The hosting shell
   can also render its management control outside this document. */
[data-testid="stAppViewerBadge"], [data-testid="stAppViewerBadgeContainer"],
[data-testid="stAppManageButton"], [class*="viewerBadge_container"], [class*="viewerBadge_link"]{display:none!important;}
.st-key-paco_panel_open{
 position:fixed!important;right:22px;bottom:58px;z-index:1100!important;
 width:344px!important;max-width:calc(100vw - 28px)!important;
 max-height:calc(100dvh - 76px);box-sizing:border-box;overflow-y:auto!important;
 overscroll-behavior:contain;background:#fff!important;color:#102b43!important;
 border:1px solid #dbe4ee;border-radius:18px;padding:10px!important;
 box-shadow:0 12px 36px #102b4330,0 2px 6px #102b4310;color-scheme:light;scrollbar-width:thin;
}
.st-key-paco_panel_open,.st-key-paco_panel_open [data-testid="stVerticalBlock"]{gap:.4rem!important;}
.st-key-paco_header{background:linear-gradient(125deg,#102b43,#235573);border-radius:11px;padding:8px 10px!important;}
.st-key-paco_header [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:minmax(0,1fr) 38px;gap:5px!important;align-items:center;}
.st-key-paco_panel_open [data-testid="stColumn"]{width:100%!important;min-width:0!important;flex:none!important;}
.paco-brand{display:flex;gap:8px;align-items:center;}.paco-brand-icon{width:32px;height:32px;flex:none;border-radius:9px;background:#ffffff15;display:grid;place-items:center;color:#ffc66f;}
.paco-brand strong{display:block;color:white;font-size:.95rem;line-height:1.15;}.paco-brand small{color:#dce8f3;font-size:.69rem;display:block;margin-top:2px;}
.st-key-paco_header button[kind="secondary"]{background:#ffffff10!important;color:#fff!important;border:0!important;border-radius:9px!important;padding:2px!important;min-height:38px!important;}
.st-key-paco_header button[kind="secondary"] p,.st-key-paco_header button span{color:#fff!important;}
.st-key-paco_messages [data-testid="stChatMessage"]{border:0!important;background:#fff!important;border-radius:10px;padding:6px!important;gap:7px!important;}
.st-key-paco_messages [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]){background:#edf4fa!important;}
.st-key-paco_messages [data-testid="stChatMessageContent"] p,.st-key-paco_messages [data-testid="stChatMessageContent"] li{font-size:.86rem;line-height:1.38;overflow-wrap:anywhere;}
.st-key-paco_messages [data-testid="stChatMessageContent"] p:last-child{margin-bottom:0;}
.st-key-paco_messages [data-testid="stChatMessageAvatar"]{width:24px;height:24px;flex-shrink:0;}
.st-key-paco_messages [data-testid="stChatMessageContent"] ul{padding-left:1.15rem;margin:.25rem 0;}
.st-key-paco_choices [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr));gap:4px!important;}
.st-key-paco_choices button{padding:4px!important;min-height:36px!important;border-radius:18px!important;}.st-key-paco_choices button p{font-size:.75rem!important;}
.st-key-paco_composer [data-testid="stForm"]{border:0!important;padding:0!important;}
.st-key-paco_composer [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:minmax(0,1fr) 44px;align-items:end;gap:6px!important;}
.st-key-paco_composer button{min-height:44px!important;padding:4px!important;border-radius:10px!important;}.st-key-paco_composer input{font-size:16px!important;}
.st-key-paco_composer [data-baseweb="input"]:focus-within{border-color:#235573!important;box-shadow:none!important;}
.st-key-paco_confirm [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:1fr 1fr;gap:6px!important;}
.st-key-paco_confirm button p,.st-key-paco_actions button p{font-size:.78rem!important;}.st-key-paco_confirm button,.st-key-paco_actions button{min-height:36px!important;padding:5px!important;}
.st-key-paco_panel_open [data-testid="stCaptionContainer"] p{font-size:.73rem!important;line-height:1.25;}
.st-key-paco_panel_open [data-testid="stAlert"] p{font-size:.8rem!important;}
.st-key-paco_panel_open [data-testid="stExpander"]{border:0!important;}
.st-key-paco_panel_open [data-testid="stExpander"] summary{min-height:30px!important;padding:3px!important;}
.st-key-paco_launcher_closed{position:fixed!important;bottom:58px;right:22px;z-index:1100!important;width:auto!important;max-width:calc(100vw - 32px)!important;}
.st-key-paco_launcher_closed button{background:#153a56!important;border:1px solid #153a56!important;color:#fff!important;border-radius:30px!important;min-height:48px!important;padding:9px 16px!important;box-shadow:0 5px 18px #102b4330!important;}
.st-key-paco_launcher_closed button p,.st-key-paco_launcher_closed button span{color:#fff!important;font-size:.85rem;font-weight:700;}
@media(min-width:701px){.block-container{padding-bottom:5rem!important;}}
@media(max-width:700px){
 .st-key-paco_panel_open{left:8px!important;right:8px!important;bottom:calc(77px + env(safe-area-inset-bottom,0px))!important;width:auto!important;max-width:none!important;max-height:calc(100dvh - 92px - env(safe-area-inset-bottom,0px));padding:10px!important;border-radius:18px 18px 12px 12px;animation:pacoSheet .18s ease-out;}
 .st-key-paco_launcher_closed{right:12px;bottom:calc(77px + env(safe-area-inset-bottom,0px))!important;}
 .st-key-paco_launcher_closed button{min-height:44px!important;padding:6px 12px!important;}
 .block-container{padding-bottom:calc(8.7rem + env(safe-area-inset-bottom,0px))!important;}
}
@keyframes pacoSheet{from{transform:translateY(12px);opacity:.6}to{transform:translateY(0);opacity:1}}
@media(prefers-reduced-motion:reduce){.st-key-paco_panel_open{animation:none!important;}}
@media(max-height:500px){.st-key-paco_panel_open{max-height:calc(100dvh - 92px);}}
</style>'''

HEADER = '''<div class="paco-brand"><div class="paco-brand-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="7" width="16" height="13" rx="4"/><path d="M12 3v4M2 12v4M22 12v4M9 13h.01M15 13h.01M9 17h6"/></svg></div><div><strong>PACO</strong><small>Assistente de entregas</small></div></div>'''


def render_window(st, state, store, answer, confirm_action, go_help, sync):
    """Draw actual Python-backed widgets, with one conversation per session."""
    mode = state['paco_window']
    if mode != 'open':
        with st.container(key='paco_launcher_closed'):
            st.button('PACO',
                      icon=':material/chat:', key='paco_open_button',
                      on_click=open_window, args=(state,), help='Abrir atendimento PACO')
        return
    with st.container(key='paco_panel_'+mode):
        with st.container(key='paco_header'):
            a,b = st.columns([3,1], gap='small', vertical_alignment='center')
            a.markdown(HEADER, unsafe_allow_html=True)
            b.button('−', key='paco_minimize', on_click=close_window,
                     args=(state,), help='Minimizar sem apagar a conversa')
        if state.get('ai_error'):
            st.caption('O atendimento automático está disponível enquanto a IA não responde.')
        with st.container(height=218 if state['messages'] else 86, border=False, key='paco_messages'):
            if not state['messages']:
                with st.chat_message('assistant', avatar='🚚'):
                    st.markdown('Olá! Sou o **PACO**. Posso ajudar com sua entrega?')
            else:
                for m in state['messages']:
                    with st.chat_message(m['role'], avatar='🚚' if m['role']=='assistant' else '👤'):
                        st.markdown(m['content'])
        if not state['messages']:
            with st.container(key='paco_choices'):
                cols = st.columns(3, gap='small')
                for i,(label,prompt) in enumerate([
                    ('Rastrear','Onde está minha carga?'),
                    ('Atraso','Minha entrega está atrasada.'),
                    ('Avaria','Minha mercadoria chegou danificada.')]):
                    if cols[i].button(label,key='paco_suggestion_'+str(i),use_container_width=True,help=prompt):
                        open_window(state)
                        with st.spinner('PACO consultando…'):
                            answer(prompt)
                        st.rerun()
        if state.get('pending'):
            with st.container(key='paco_confirm'):
                from operations import quote_text
                p=state['pending']
                desc=quote_text(p['quote']) if p.get('action')=='quote' else f"Avaliação {p['score']}/5 · {p['code']}" if p.get('action')=='rating' else f"{p['kind']} · {p['code']}"
                st.info('Ação preparada (ainda não registrada): '+desc)
                a,b=st.columns(2,gap='small')
                if a.button('Confirmar registro',type='primary',key='paco_confirm_button',use_container_width=True):
                    try:
                        confirm_action(p)
                        open_window(state)
                        st.rerun()
                    except ValueError as e:
                        st.error(str(e))
                if b.button('Cancelar',key='paco_cancel_button',use_container_width=True):
                    state['pending']=None
                    open_window(state)
                    st.rerun()
        code=state.get('context',{}).get('code')
        if code:
            with st.container(key='paco_actions'):
                st.caption('Entrega: '+code)
                if state.get('pending') and state['pending'].get('kind'):
                    st.button('Continuar na Central de ajuda',key='chat_to_help_pending',on_click=go_help,use_container_width=True)
                elif state.get('protocol_query',('', ''))[0]==code and state['protocol_query'][1]:
                    st.button('Acompanhar meu chamado',key='chat_to_help_case',on_click=go_help,args=(state['protocol_query'][1],),use_container_width=True)
                else:
                    st.button('Preciso de ajuda com esta entrega',key='chat_to_help',on_click=go_help,use_container_width=True)
        with st.container(key='paco_composer'):
            with st.form('chat',clear_on_submit=True,border=False):
                a,b=st.columns([4,1],gap='small',vertical_alignment='bottom')
                text=a.text_input('Sua mensagem',placeholder='Digite sua mensagem…',label_visibility='collapsed')
                submit=b.form_submit_button('➤',help='Enviar mensagem',type='primary',use_container_width=True)
            if submit and len(text.strip())>800:
                st.warning('Envie uma mensagem de até 800 caracteres, por favor.')
            elif submit and text.strip():
                open_window(state)
                with st.spinner('PACO consultando…'):
                    answer(text.strip())
                st.rerun()
        if state['messages']:
            with st.expander('Conversa'):
                if st.button('Limpar conversa',key='paco_clear',help='Apaga a conversa, não os chamados registrados'):
                    reset_conversation(state,sync,store)
                    open_window(state)
                    st.rerun()
