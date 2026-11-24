"""Run the real support flow on a minimal widget double and SQLite store."""
import tempfile, unittest, sys, types
from pathlib import Path
from unittest.mock import patch
from resolution import ResolutionStore
from service_bridge import select_delivery, registered, open_help
try:
    import streamlit
except ImportError:
    with patch.dict(sys.modules, {'streamlit':types.ModuleType('streamlit')}):
        import support_ui as helpui
else:
    import support_ui as helpui

class State(dict):
    __getattr__=dict.__getitem__
    __setattr__=dict.__setitem__
class Rerun(Exception):pass
class UI:
    def __init__(self,s,raw='',submit='',kind=None,decision=None):
        self.s=s;self.raw=raw;self.submit=submit;self.kind=kind;self.decision=decision;self.forms=[];self.buttons={};self.output=[]
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def container(self,*args,**kwargs):return self
    def columns(self,spec,**kwargs):return [self]*(spec if isinstance(spec,int) else len(spec))
    def form(self,key,**kwargs):self.forms.append(key);return self
    def expander(self,*args,**kwargs):return self
    def markdown(self,text,**kwargs):self.output.append(text)
    caption=markdown;warning=markdown;info=markdown;success=markdown;write=markdown;text=markdown
    def text_input(self,*args,**kwargs):return self.raw
    def text_area(self,*args,**kwargs):return 'Teste'
    def select_slider(self,*args,**kwargs):return 5
    def date_input(self,*args,**kwargs):return kwargs['value']
    def file_uploader(self,*args,**kwargs):return []
    def image(self,*args,**kwargs):pass
    def selectbox(self,label,options,**kwargs):return self.kind if label=='Selecione o problema' and self.kind else self.s.get(kwargs['key'],options[0])
    def radio(self,label,options,**kwargs):return self.decision if label=='Resultado' and self.decision else self.s.get(kwargs['key'],options[0])
    def form_submit_button(self,label,**kwargs):return label==self.submit
    def button(self,label,**kwargs):self.buttons[kwargs.get('key',label)]=(kwargs.get('on_click'),kwargs.get('args',()));return False
    def callback(self,key):fn,args=self.buttons[key];fn(*args)
    def rerun(self):raise Rerun()
class HelpTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=ResolutionStore(str(Path(self.tmp.name)/'test.sqlite'));self.s=State(track_code='',context={},messages=[],pending=None,protocol_task='new')
    def tearDown(self):self.tmp.cleanup()
    def draw(self,rerun=False,**kwargs):
        ui=UI(self.s,**kwargs)
        def flash(msg):self.s['flash']=msg;raise Rerun()
        with patch.object(helpui,'st',ui):
            if rerun:
                with self.assertRaises(Rerun):helpui.customer_support(self.store,self.s,None,flash,None)
            else:helpui.customer_support(self.store,self.s,None,flash,None)
        return ui
    def test_first_screen_only_search(self):
        ui=self.draw();self.assertEqual(ui.forms,['help_find_delivery']);self.assertNotIn('help_new_PP1003_Atraso',ui.forms)
    def test_code_search_and_shared_context(self):
        self.draw(raw='pp1003',submit='Buscar',rerun=True);self.assertEqual(self.s.track_code,'PP1003');self.assertEqual(self.s.context['code'],'PP1003')
        self.assertIn('help_new_PP1003_Atraso',self.draw().forms)
    def test_phone_choice(self):
        ui=self.draw(raw='(88) 00000-0001',submit='Buscar');ui.callback('help_pick_PP1002');self.assertEqual(self.s.track_code,'PP1002');self.assertEqual(self.s.help_search_matches,[])
    def test_invalid_code_message(self):
        ui=self.draw(raw='ABC123',submit='Buscar');self.assertFalse(self.s.track_code);self.assertTrue(any('padrão' in x for x in ui.output))
    def test_create_and_follow_single_action(self):
        select_delivery(self.s,self.store,'PP1003');self.draw(kind='Atraso',submit='Confirmar e registrar chamado',rerun=True);tid=self.s.protocol_query[1];self.assertTrue(self.store.case(tid,'PP1003'));self.assertEqual(self.s.protocol_task,'lookup');self.assertEqual(self.s.context['protocol'],tid);self.assertTrue(any(tid in x for x in self.draw().output))
    def test_duplicate_offers_existing_ticket(self):
        select_delivery(self.s,self.store,'PP1003');tid,_=self.store.ticket('PP1003','Atraso','Teste');ui=self.draw(kind='Atraso');self.assertIn('help_existing',ui.buttons);ui.callback('help_existing');self.assertEqual(self.s.protocol_query,('PP1003',tid));self.assertEqual(len(self.store.cargo_tickets('PP1003')),1)
    def test_switch_delivery_drops_unrelated_protocol(self):
        tid,_=self.store.ticket('PP1003','Atraso','Teste');registered(self.s,self.store,'PP1003',tid,'Atraso');helpui.choose_help_delivery(self.store,self.s,'PP1002');self.assertEqual(self.s.protocol_query,('PP1002',''));self.assertNotIn('protocol',self.s.context);self.assertIsNone(helpui.selected_case(self.store,self.s,'PP1002',tid))
    def test_pending_avaria_from_chat(self):
        select_delivery(self.s,self.store,'PP1003');self.s.pending={'kind':'Avaria','code':'PP1003'};open_help(self.s,self.store);ui=self.draw();self.assertIn('help_new_PP1003_Avaria',ui.forms)
    def test_reopen_from_help(self):
        tid,_=self.store.ticket('PP1003','Atraso','Teste');registered(self.s,self.store,'PP1003',tid,'Atraso');self.store.manager_update(tid,'Logística','Proposta',True);self.draw(decision='Ainda preciso de ajuda',submit='Reabrir chamado',rerun=True);self.assertEqual(self.store.case(tid,'PP1003')['status'],'Reaberto')
    def test_accept_from_help(self):
        tid,_=self.store.ticket('PP1003','Atraso','Teste');registered(self.s,self.store,'PP1003',tid,'Atraso');self.store.manager_update(tid,'Logística','Proposta',True);self.draw(decision='Sim, foi resolvido',submit='Confirmar resolução',rerun=True);self.assertEqual(self.store.case(tid,'PP1003')['status'],'Resolvido')
if __name__=='__main__':unittest.main()
