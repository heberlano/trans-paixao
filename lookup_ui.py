import streamlit as st
from phone_lookup import EXAMPLES, lookup

def examples(store):
    with st.expander('Ver exemplos de rastreamento e telefone'):
        st.caption('Use os códigos e telefones de exemplo abaixo. Outros telefones fictícios com DDD também geram entregas de exemplo. Não informe dados pessoais reais.')
        for number,ids in EXAMPLES:
            rows=[d for code in ids if (d:=store.get(code))]
            st.markdown('**'+number+'**')
            for d in rows:st.caption(f"{d['code']} · {d['status']} · {d['origin']} → {d['destination']}")

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
        st.caption("Experimente (88) 00000-1234 ou outro telefone fictício com DDD.")
