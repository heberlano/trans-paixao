"""Test native widget wiring with a Streamlit double; no browser or API needed."""
import tempfile
import unittest
from pathlib import Path
from paco_window import init_window, open_window, close_window, render_window
from service_bridge import select_delivery, sync_chat_delivery, open_help, registered
from resolution import ResolutionStore, complaint_reply


class Rerun(Exception):
    pass


class FakeUI:
    def __init__(self, click=None, text=''):
        self.click=click; self.text=text; self.buttons={}; self.containers=[]; self.output=[]
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def container(self,**kwargs):
        self.containers.append(kwargs.get('key'));return self
    def columns(self,spec,**kwargs):return [self]*(spec if isinstance(spec,int) else len(spec))
    def button(self,label,**kwargs):
        key=kwargs.get('key',label);self.buttons[key]=(kwargs.get('on_click'),kwargs.get('args',()))
        return self.click==key and not kwargs.get('on_click')
    def callback(self,key):
        fn,args=self.buttons[key];fn(*args)
    def markdown(self,text,**kwargs):self.output.append(text)
    caption=markdown;info=markdown;error=markdown;warning=markdown
    def chat_message(self,*args,**kwargs):return self
    def spinner(self,*args,**kwargs):return self
    def expander(self,*args,**kwargs):return self
    def form(self,*args,**kwargs):return self
    def text_input(self,*args,**kwargs):return self.text
    def form_submit_button(self,*args,**kwargs):return self.click=='submit'
    def rerun(self):raise Rerun()


class WindowTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.store=ResolutionStore(str(Path(self.tmp.name)/'data.sqlite'))
        self.state={'nav':'Início','context':{},'messages':[],'pending':None}
        init_window(self.state)
        open_window(self.state)
    def tearDown(self):self.tmp.cleanup()
    def answer(self,text):
        msg,pending,_=complaint_reply(text,self.store,self.state['context'])
        self.state['messages'] += [{'role':'user','content':text},{'role':'assistant','content':msg}]
        self.state['pending']=pending
        sync_chat_delivery(self.state,self.store)
    def confirm(self,p):
        tid,_=self.store.ticket(p['code'],p['kind'],'Teste PACO',actor='PACO')
        registered(self.state,self.store,p['code'],tid,p['kind'])
        self.state['messages'].append({'role':'assistant','content':tid})
        self.state['pending']=None
    def help(self,protocol=None):
        open_help(self.state,self.store,protocol=protocol)
        self.state['nav']='Ajuda';close_window(self.state)
    def draw(self,click=None,text='',rerun=False):
        ui=FakeUI(click,text)
        if rerun:
            with self.assertRaises(Rerun):render_window(ui,self.state,self.store,self.answer,self.confirm,self.help,sync_chat_delivery)
        else:render_window(ui,self.state,self.store,self.answer,self.confirm,self.help,sync_chat_delivery)
        return ui
    def test_initial_closed_and_explicit_launcher(self):
        self.state.pop('paco_window');init_window(self.state)
        ui=self.draw();self.assertEqual(self.state['paco_window'],'closed');self.assertNotIn('paco_panel_open',ui.containers);self.assertIn('paco_launcher_closed',ui.containers)
        self.assertNotIn('paco_suggestion_0',ui.buttons)
        ui.callback('paco_open_button');self.assertIn('paco_suggestion_0',self.draw().buttons)
    def test_legacy_auto_migrates_closed(self):
        self.state['paco_window']='auto';init_window(self.state);self.assertEqual(self.state['paco_window'],'closed')
    def test_reject_long_message_without_calling_agent(self):
        ui=self.draw('submit','x'*801);self.assertEqual(self.state['messages'],[]);self.assertTrue(any('800 caracteres' in x for x in ui.output))
    def test_migrate_old_paco_page(self):
        self.state['nav']='PACO';init_window(self.state)
        self.assertEqual(self.state['nav'],'Início');self.assertEqual(self.state['paco_window'],'open')
    def test_minimize_and_reopen_keep_context(self):
        select_delivery(self.state,self.store,'PP1003');self.answer('Qual a nova previsão?')
        old=list(self.state['messages']);self.draw().callback('paco_minimize')
        ui=self.draw();self.assertNotIn('paco_panel_closed',ui.containers);ui.callback('paco_open_button')
        self.assertEqual(self.state['messages'],old);self.assertEqual(self.state['context']['code'],'PP1003')
        self.assertIn('paco_panel_open',self.draw().containers)
    def test_send_keeps_current_page_and_uses_selected_cargo(self):
        self.state['nav']='Rastreio';select_delivery(self.state,self.store,'PP1003')
        self.draw('submit','Qual a nova previsão?',rerun=True)
        self.assertEqual(self.state['nav'],'Rastreio');self.assertEqual(self.state['paco_window'],'open')
        self.assertIn('PP1003',self.state['messages'][-1]['content'])
    def test_quick_action(self):
        select_delivery(self.state,self.store,'PP1003');self.draw('paco_suggestion_1',rerun=True)
        self.assertEqual(self.state['paco_window'],'open');self.assertTrue(self.state['messages'])
    def test_confirm_and_help_share_real_protocol(self):
        select_delivery(self.state,self.store,'PP1003')
        self.draw('submit','Minha carga está atrasada. Registre uma reclamação.',rerun=True)
        self.assertTrue(self.state['pending']);self.draw('paco_confirm_button',rerun=True)
        tid=self.state['protocol_query'][1];self.assertTrue(self.store.case(tid,'PP1003'))
        self.draw().callback('chat_to_help_case');self.assertEqual(self.state['nav'],'Ajuda');self.assertEqual(self.state['paco_window'],'closed');self.assertEqual(self.state['protocol_query'],('PP1003',tid))
    def test_cancel_does_not_register(self):
        select_delivery(self.state,self.store,'PP1003');self.state['pending']={'kind':'Atraso','code':'PP1003'}
        self.draw('paco_cancel_button',rerun=True);self.assertIsNone(self.state['pending']);self.assertFalse(self.store.cargo_tickets('PP1003'))
    def test_pending_avaria_handoff(self):
        select_delivery(self.state,self.store,'PP1003');self.state['pending']={'kind':'Avaria','code':'PP1003'}
        self.draw().callback('chat_to_help_pending');self.assertEqual(self.state['case_kind'],'Avaria');self.assertEqual(self.state['paco_window'],'closed');self.assertTrue(self.state['pending'])
    def test_clear_is_explicit(self):
        select_delivery(self.state,self.store,'PP1003');self.answer('Qual a nova previsão?')
        self.draw('paco_clear',rerun=True);self.assertEqual(self.state['messages'],[]);self.assertEqual(self.state['context'],{});self.assertIsNone(self.state['pending'])

if __name__=='__main__':unittest.main()
