import unittest,tempfile
from pathlib import Path
from datetime import date,timedelta
from unittest.mock import patch
from core import delay_metrics,delay_summary,describe,today
from service_bridge import select_delivery,open_help,registered,sync_chat_delivery
from resolution import ResolutionStore,complaint_reply
from phone_lookup import lookup

class SharedServiceTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=ResolutionStore(str(Path(self.tmp.name)/'data.sqlite'));self.state={'context':{},'pending':None,'messages':[]}
    def tearDown(self):self.tmp.cleanup()
    def test_dates_example(self):
        with patch('core.today',return_value=date(2026,11,24)):
            d={'status':'Atrasada','eta':'2026-11-22','estimated_eta':'2026-11-27'}
            self.assertEqual(delay_metrics(d),{'elapsed':2,'remaining':3,'total':5});self.assertIn('Atraso total previsto: 5 dias',delay_summary(d))
    def test_confirmed_precedence(self):
        with patch('core.today',return_value=date(2026,11,24)):
            d={'status':'Atrasada','eta':'2026-11-22','estimated_eta':'2026-11-27','confirmed_eta':'2026-11-29'}
            self.assertEqual(delay_metrics(d),{'elapsed':2,'remaining':5,'total':7})
    def test_track_to_chat(self):
        self.assertTrue(select_delivery(self.state,self.store,'PP1003'));msg,p,ok=complaint_reply('Qual a nova previsão?',self.store,self.state['context']);self.assertTrue(ok);self.assertIn('PP1003',msg);self.assertIn('Atraso total previsto',msg)
    def test_pending_to_help(self):
        select_delivery(self.state,self.store,'PP1003');_,p,_=complaint_reply('Minha mercadoria chegou danificada',self.store,self.state['context']);self.state['pending']=p;open_help(self.state,self.store);self.assertEqual(self.state['case_kind'],'Avaria');self.assertEqual(self.state['track_code'],'PP1003');self.assertEqual(self.state['pending'],p)
    def test_help_registration_to_chat(self):
        tid,_=self.store.ticket('PP1003','Atraso','Teste');registered(self.state,self.store,'PP1003',tid,'Atraso');msg,_,ok=complaint_reply('Qual o andamento do meu chamado?',self.store,self.state['context']);self.assertTrue(ok);self.assertIn(tid,msg);open_help(self.state,self.store);self.assertEqual(self.state['protocol_query'],('PP1003',tid));self.assertEqual(self.state['protocol_task'],'lookup')
    def test_change_cargo_clears_pending(self):
        select_delivery(self.state,self.store,'PP1003');self.state['pending']={'code':'PP1003','kind':'Atraso'};self.state['context']['protocol']='OC-AAAAAA';select_delivery(self.state,self.store,'PP1002');self.assertIsNone(self.state['pending']);self.assertNotIn('protocol',self.state['context']);self.assertEqual(self.state['protocol_query'],('PP1002',''))
    def test_phone_generated(self):
        rows,_=lookup(self.store,'(88) 00000-1234');select_delivery(self.state,self.store,rows[0]['code']);self.assertIn('Atraso total previsto',describe(rows[0]));self.assertEqual(self.state['context']['code'],rows[0]['code'])
    def test_invalid_chat_clears_selection(self):
        select_delivery(self.state,self.store,'PP1003');complaint_reply('PP9999',self.store,self.state['context']);sync_chat_delivery(self.state,self.store);self.assertEqual(self.state['track_code'],'');self.assertNotIn('protocol_query',self.state)
    def test_duplicate_from_shared_context(self):
        tid,_=self.store.ticket('PP1003','Atraso','Teste');registered(self.state,self.store,'PP1003',tid,'Atraso');again,new=self.store.ticket('PP1003','Atraso','PACO');self.assertFalse(new);self.assertEqual(tid,again)
