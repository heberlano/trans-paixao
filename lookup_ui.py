import streamlit as st
from phone_lookup import lookup, search_delivery


def compact_search(store,key,on_select,on_clear=None):
    """Compact search for home/tracking; use callback for a chosen cargo."""
    s=st.session_state
    with st.container(key=key+'_compact'):
        with st.form(key+'_search',clear_on_submit=True,border=False):
            st.markdown('**Rastrear entrega**')
            a,b=st.columns([3,1],gap='small',vertical_alignment='bottom')
            raw=a.text_input('Código ou telefone com DDD',placeholder='Código ou telefone com DDD',label_visibility='collapsed',max_chars=40)
            submit=b.form_submit_button('Buscar',type='primary',use_container_width=True)
        st.caption('Use um código ou telefone de exemplo com DDD.')
        if submit:
            if on_clear:on_clear()
            rows,heading,error=search_delivery(store,raw)
            s[key+'_matches']=[d['code'] for d in rows]
            s[key+'_error']=(heading,error) if error else None
            if len(rows)==1:
                s[key+'_matches']=[]
                on_select(rows[0]['code'])
                st.rerun()
        error=s.get(key+'_error')
        if error:st.warning('**'+error[0]+'**\n\n'+error[1])
        codes=s.get(key+'_matches',[])
        if codes:
            st.caption('Entregas localizadas. Escolha a que deseja acompanhar:')
            def select(code):
                s[key+'_matches']=[];s[key+'_error']=None
                on_select(code)
            for code in codes:
                d=store.get(code)
                if d:
                    st.button(f"{code} · {d['status']} — {d['destination']}",key=key+'_choice_'+code,on_click=select,args=(code,),use_container_width=True)

def phone_search(store,key,on_select):
    with st.expander('Não sei meu código de rastreio'):
        st.caption('Informe o telefone fictício com DDD. Se não estiver cadastrado, criaremos duas entregas de exemplo nesta sessão. Não use dados reais.')
        with st.form(key+'_phone',clear_on_submit=True):
            raw=st.text_input('Telefone com DDD',placeholder='(88) 00000-0001',max_chars=24)
            submit=st.form_submit_button('Encontrar minhas entregas',use_container_width=True)
        if submit:
            rows,error=lookup(store,raw)
            st.session_state[key+'_matches']=[d['code'] for d in rows]
            st.session_state[key+'_error']=error
        if st.session_state.get(key+'_error'):st.warning(st.session_state[key+'_error'])
        if st.session_state.get(key+'_matches'):st.success('Entregas de exemplo localizadas! Escolha uma para acompanhar ou solicitar ajuda.')
        for code in st.session_state.get(key+'_matches',[]):
            d=store.get(code)
            if d:
                st.caption(f"{code} · {d['status']} · {d['origin']} → {d['destination']}")
                st.button('Selecionar '+code,key=key+'_select_'+code,on_click=on_select,args=(code,),use_container_width=True)
