"""Floating PACO using native Streamlit widgets and the existing session.
No iframe, external JavaScript, new database or second conversation.
"""


def init_window(state):
    if state.get('paco_window') not in ('auto', 'open', 'closed'):
        state['paco_window'] = 'auto'
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
/* 4.0: native floating PACO, independent of navigation */
.st-key-navbox [data-testid="stHorizontalBlock"]{grid-template-columns:repeat(3,minmax(0,1fr))!important;}
.st-key-paco_panel_auto,.st-key-paco_panel_open{
 position:fixed!important;right:20px;bottom:20px;z-index:1100!important;
 width:370px!important;max-width:calc(100vw - 28px)!important;max-height:calc(100vh - 40px);max-height:calc(100dvh - 40px);
 box-sizing:border-box;overflow-y:auto!important;overscroll-behavior:contain;
 background:#fff!important;color:#102b43!important;border:1px solid #dbe4ee;border-radius:18px;
 padding:12px!important;box-shadow:0 14px 60px #102b433d,0 2px 9px #102b431a;
 color-scheme:light;scrollbar-width:thin;
}
.st-key-paco_panel_auto,.st-key-paco_panel_open,.st-key-paco_panel_auto [data-testid="stVerticalBlock"],.st-key-paco_panel_open [data-testid="stVerticalBlock"]{gap:.45rem!important;}
.st-key-paco_header{background:linear-gradient(125deg,#102b43,#235573);border-radius:12px;padding:10px 11px!important;}
.st-key-paco_header [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:minmax(0,1fr) auto;gap:6px!important;align-items:center;}
.st-key-paco_header [data-testid="stColumn"]{width:100%!important;min-width:0!important;flex:none!important;}
.paco-brand{display:flex;gap:9px;align-items:center;}.paco-brand-icon{width:36px;height:36px;flex:none;border-radius:11px;background:#ffffff16;display:grid;place-items:center;color:#ffc66f;}
.paco-brand strong{display:block;color:white;font-size:1rem;line-height:1.15;letter-spacing:.03em;}.paco-brand small{color:#dce8f3;font-size:.68rem;line-height:1.2;display:block;margin-top:3px;}
.st-key-paco_header button[kind="secondary"]{background:#ffffff12!important;color:#fff!important;border:1px solid #ffffff45!important;border-radius:9px!important;padding:4px 8px!important;min-height:40px!important;}
.st-key-paco_header button[kind="secondary"] p{color:#fff!important;font-size:.73rem!important;}
.st-key-paco_messages [data-testid="stChatMessage"]{border:0!important;background:#f0f4f8!important;border-radius:11px;padding:8px!important;gap:7px!important;}
.st-key-paco_messages [data-testid="stChatMessage"]:has([data-testid="stChatMessageAvatarUser"]){background:#e5eef8!important;}
.st-key-paco_messages [data-testid="stChatMessageContent"] p,.st-key-paco_messages [data-testid="stChatMessageContent"] li{font-size:.85rem;line-height:1.4;}
.st-key-paco_messages [data-testid="stChatMessageContent"] p:last-child{margin-bottom:0;}
.st-key-paco_messages [data-testid="stChatMessageAvatar"]{width:26px;height:26px;flex-shrink:0;}
.st-key-paco_choices [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:repeat(3,minmax(0,1fr));gap:4px!important;}
.st-key-paco_choices [data-testid="stColumn"],.st-key-paco_composer [data-testid="stColumn"],.st-key-paco_confirm [data-testid="stColumn"]{width:100%!important;min-width:0!important;flex:none!important;}
.st-key-paco_choices button{padding:4px!important;min-height:40px!important;border-radius:10px!important;}.st-key-paco_choices button p{font-size:.75rem!important;}
.st-key-paco_composer [data-testid="stForm"]{border:0!important;padding:0!important;}
.st-key-paco_composer [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:minmax(0,1fr) auto;align-items:end;gap:6px!important;}
.st-key-paco_composer button{min-height:44px!important;padding:7px 10px!important;border-radius:10px!important;}.st-key-paco_composer input{font-size:16px!important;}
.st-key-paco_confirm [data-testid="stHorizontalBlock"]{display:grid!important;grid-template-columns:1fr 1fr;gap:6px!important;}
.st-key-paco_confirm button p,.st-key-paco_actions button p{font-size:.8rem!important;}.st-key-paco_confirm button,.st-key-paco_actions button{min-height:42px!important;padding:6px!important;}
.st-key-paco_panel_auto [data-testid="stCaptionContainer"] p,.st-key-paco_panel_open [data-testid="stCaptionContainer"] p{font-size:.73rem!important;line-height:1.25;}
.st-key-paco_panel_auto [data-testid="stAlert"] p,.st-key-paco_panel_open [data-testid="stAlert"] p{font-size:.8rem!important;}
.st-key-paco_launcher_auto,.st-key-paco_launcher_closed{position:fixed!important;bottom:20px;right:20px;z-index:1100!important;width:auto!important;max-width:calc(100vw - 32px)!important;}
.st-key-paco_launcher_auto{display:none!important;}
.st-key-paco_launcher_auto button,.st-key-paco_launcher_closed button{background:#153a56!important;border:1px solid #153a56!important;color:#fff!important;border-radius:30px!important;min-height:52px!important;padding:9px 17px!important;box-shadow:0 6px 24px #102b433b!important;}
.st-key-paco_launcher_auto button p,.st-key-paco_launcher_closed button p{color:#fff!important;font-size:.83rem;font-weight:700;}
.st-key-paco_launcher_auto button{animation:pacoWelcome .35s ease-out both;}
@keyframes pacoWelcome{from{transform:translateY(7px);opacity:.25}to{transform:translateY(0);opacity:1}}
@media(prefers-reduced-motion:reduce){.st-key-paco_launcher_auto button{animation:none!important;}}
/* Reserve desktop workspace beside the chat; avoid obscuring the map. */
@media(min-width:1050px){
 [data-testid="stMain"]:has(.st-key-paco_panel_auto) .block-container,[data-testid="stMain"]:has(.st-key-paco_panel_open) .block-container{max-width:min(920px,calc(100% - 408px))!important;margin-right:408px!important;}
}
@media(max-width:900px){
 .st-key-paco_panel_auto{display:none!important;}.st-key-paco_launcher_auto{display:flex!important;}
}
@media(max-width:700px){
 .st-key-paco_panel_open{left:8px!important;right:8px!important;bottom:calc(70px + env(safe-area-inset-bottom,0px))!important;width:auto!important;max-width:none!important;max-height:calc(100vh - 86px);max-height:calc(100dvh - 86px - env(safe-area-inset-bottom,0px));padding:10px!important;border-radius:15px;}
 .st-key-paco_launcher_auto,.st-key-paco_launcher_closed{right:12px;bottom:calc(70px + env(safe-area-inset-bottom,0px))!important;}
 .st-key-paco_launcher_auto button,.st-key-paco_launcher_closed button{min-height:46px!important;padding:7px 13px!important;}
 .block-container{padding-bottom:calc(8.6rem + env(safe-area-inset-bottom,0px))!important;}
}
@media(max-height:500px){.st-key-paco_panel_open,.st-key-paco_panel_auto{max-height:calc(100dvh - 84px);}}
</style>'''

HEADER = '''<div class="paco-brand"><div class="paco-brand-icon"><svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4" y="7" width="16" height="13" rx="4"/><path d="M12 3v4M2 12v4M22 12v4M9 13h.01M15 13h.01M9 17h6"/></svg></div><div><strong>PACO</strong><small>Assistente virtual · Transportadora Paixão</small></div></div>'''


def render_window(st, state, store, answer, confirm_action, go_help, sync):
    """Draw actual Python-backed widgets, with one conversation per session."""
    mode = state['paco_window']
    if mode in ('auto', 'closed'):
        with st.container(key='paco_launcher_'+mode):
            st.button('PACO · Posso ajudar?' if mode == 'auto' else 'PACO',
                      icon=':material/chat:', key='paco_open_button',
                      on_click=open_window, args=(state,), help='Abrir atendimento PACO')
    if mode == 'closed':
        return
    with st.container(key='paco_panel_'+mode):
        with st.container(key='paco_header'):
            a,b = st.columns([3,1], gap='small', vertical_alignment='center')
            a.markdown(HEADER, unsafe_allow_html=True)
            b.button('Minimizar', key='paco_minimize', on_click=close_window,
                     args=(state,), help='Minimizar sem apagar a conversa')
        if state.get('ai_error'):
            st.caption('O atendimento automático está disponível enquanto a IA não responde.')
        with st.container(height=245 if state['messages'] else 128, border=False, key='paco_messages'):
            if not state['messages']:
                with st.chat_message('assistant', avatar='🚚'):
                    st.markdown('Olá! Sou o **PACO**, da Transportadora Paixão. 👋\n\nPrecisa localizar sua mercadoria ou resolver um problema com sua entrega?')
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
                    ('Chamado','Quero acompanhar uma reclamação.')]):
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
                st.caption('Entrega em atendimento: '+code)
                if state.get('pending') and state['pending'].get('kind'):
                    st.button('Continuar na Central de ajuda',key='chat_to_help_pending',on_click=go_help,use_container_width=True)
                elif state.get('protocol_query',('', ''))[0]==code and state['protocol_query'][1]:
                    st.button('Acompanhar meu chamado',key='chat_to_help_case',on_click=go_help,args=(state['protocol_query'][1],),use_container_width=True)
                else:
                    st.button('Abrir ou acompanhar chamado',key='chat_to_help',on_click=go_help,use_container_width=True)
        with st.container(key='paco_composer'):
            with st.form('chat',clear_on_submit=True,border=False):
                a,b=st.columns([4,1],gap='small',vertical_alignment='bottom')
                text=a.text_input('Sua mensagem',placeholder='Digite sua mensagem…',label_visibility='collapsed',max_chars=800)
                submit=b.form_submit_button('Enviar',type='primary',use_container_width=True)
            if submit and text.strip():
                open_window(state)
                with st.spinner('PACO consultando…'):
                    answer(text.strip())
                st.rerun()
        if state['messages']:
            with st.expander('Opções da conversa'):
                if st.button('Limpar conversa',key='paco_clear',help='Apaga a conversa, não os chamados registrados'):
                    reset_conversation(state,sync,store)
                    open_window(state)
                    st.rerun()
