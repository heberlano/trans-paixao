import unittest,tempfile,sqlite3
from pathlib import Path
from datetime import datetime,timedelta
from io import BytesIO
from PIL import Image
from operations import Operations
from core import today
from resolution import ResolutionStore, complaint_reply, photo_bytes, classify
from reports import report

class ResolutionTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.path=str(Path(self.tmp.name)/'case.db');self.s=ResolutionStore(self.path)
    def tearDown(self):self.tmp.cleanup()
    def create(self,kind='Atraso',code='PP1003',**kwargs):return self.s.ticket(code,kind,'Teste de atendimento',**kwargs)[0]
    def test_migration(self):
        p=str(Path(self.tmp.name)/'old.db');old=Operations(p);a,_=old.ticket('PP1003','Atraso','antigo');b,_=old.ticket('PP1001','Avaria','antigo');old.close(b);new=ResolutionStore(p);self.assertEqual(new.case(a,'PP1003')['status'],'Aberto');self.assertEqual(new.case(b,'PP1001')['status'],'Resolvido');self.assertEqual(len(ResolutionStore(p).events(a,'PP1003')),1)
    def test_priorities(self):
        for kind,code,priority in [('Atraso','PP1003','Alta'),('Entrega não reconhecida','PP1001','Crítica'),('Avaria','PP1001','Alta'),('Reclamação','PP1002','Média')]:
            t=self.s.case(self.create(kind,code),code);self.assertEqual(t['priority'],priority);self.assertGreater(t['remaining_hours'],0)
    def test_invalid_codes(self):
        for code in ['ABC123','PP9999','TN1002','']:
            with self.assertRaises(ValueError):self.create(code=code)
    def test_duplicate_across_stages(self):
        t=self.create();self.s.manager_update(t,'Logística','Verificando');self.assertEqual(self.s.ticket('PP1003','Atraso','novo'),(t,False));self.s.manager_update(t,'Logística','Proposta',True);self.assertEqual(self.s.ticket('PP1003','Atraso','novo'),(t,False))
    def test_workflow(self):
        t=self.create();self.s.manager_update(t,'Logística','Verificando');self.assertEqual(self.s.case(t,'PP1003')['status'],'Em análise');self.assertTrue(self.s.case(t,'PP1003')['first_reply']);self.s.manager_update(t,'Logística','Proposta',True);self.assertEqual(self.s.case(t,'PP1003')['status'],'Aguardando confirmação');self.assertEqual(self.s.complaints()['closed'],0);self.s.customer_decision(t,'PP1003',True,5);self.assertEqual(self.s.complaints()['closed'],1);self.assertEqual(self.s.complaints()['satisfaction'],5);self.assertEqual(len(self.s.events(t,'PP1003')),4)
    def test_reopen(self):
        t=self.create();self.s.manager_update(t,'Logística','Proposta',True);self.s.customer_decision(t,'PP1003',False,note='Ainda não chegou');r=self.s.case(t,'PP1003');self.assertEqual((r['status'],r['reopen_count'],r['first_reply']),('Reaberto',1,''));self.assertEqual(self.s.complaints()['pending'],1);self.s.manager_update(t,'Logística','Nova solução',True);self.s.customer_decision(t,'PP1003',True,4);self.assertEqual(self.s.complaints()['reopened'],1)
    def test_no_premature_close(self):
        t=self.create();self.s.close(t);self.assertEqual(self.s.case(t,'PP1003')['status'],'Aguardando confirmação');self.assertEqual(self.s.summary()['open_tickets'],1)
    def test_wrong_cargo(self):
        t=self.create();self.assertIsNone(self.s.protocol(t,'PP1002'));self.assertEqual(self.s.events(t,'PP1002'),[]);self.assertEqual(self.s.photos(t,'PP1002'),[]);self.s.close(t)
        with self.assertRaises(ValueError):self.s.customer_decision(t,'PP1002',True,5)
    def test_sla_escalation(self):
        t=self.create();past=(datetime.now()-timedelta(hours=3)).isoformat(timespec='seconds')
        with self.s.connect() as c:c.execute('UPDATE case_meta SET deadline=? WHERE id=?',(past,t))
        self.assertEqual(self.s.case(t,'PP1003')['sla'],'Fora da meta');self.assertIn('SLA',self.s.plan()[0]['cause']);self.s.manager_update(t,'Logística','Retorno');self.assertEqual(self.s.case(t,'PP1003')['sla'],'Fora da meta')
    def test_prevention_dedupe(self):
        self.assertGreater(self.s.scan_prevention(),0);self.assertEqual(self.s.scan_prevention(),0);self.assertTrue(any('prazo' in n['message'].lower() for n in self.s.notices('PP1003')))
    def test_photo_upload(self):
        b=BytesIO();Image.new('RGB',(200,100),'orange').save(b,'PNG');t=self.create('Avaria','PP1001',photos=[b.getvalue()]);self.assertEqual(len(self.s.photos(t,'PP1001')),1);self.assertTrue(self.s.photos(t,'PP1001')[0].startswith(b'\xff\xd8'))
        with self.assertRaises(ValueError):photo_bytes(b'not an image')
        with self.assertRaises(ValueError):self.create(photos=[b.getvalue()])
    def test_reschedule(self):
        desired=str(today()+timedelta(days=3));old=self.s.get('PP1003')['eta'];t=self.create('Reagendamento',requested_date=desired);self.assertEqual(self.s.case(t,'PP1003')['requested_date'],desired);self.s.manager_update(t,'Logística','Disponível',True,desired);self.assertFalse(self.s.get('PP1003')['confirmed_eta']);self.s.customer_decision(t,'PP1003',True,5);self.assertEqual(self.s.get('PP1003')['confirmed_eta'],desired);self.assertEqual(self.s.get('PP1003')['eta'],old)
        with self.assertRaises(ValueError):self.create('Reagendamento','PP1001',requested_date=desired)
    def test_chat_triage(self):
        for msg,kind in [('Minha carga PP1003 atrasou','Atraso'),('PP1001 consta como entregue mas não recebi','Entrega não reconhecida'),('PP1001 chegou danificada','Avaria'),('Minha carga PP1002 está no endereço errado','Endereço incorreto')]:
            _,p,r=complaint_reply(msg,self.s,{});self.assertEqual(p['kind'],kind);self.assertFalse(r)
        self.assertFalse(self.s.tickets());self.assertIn('formato correto',complaint_reply('Minha carga PP9999 atrasou',self.s,{'code':'PP1003'})[0]);self.assertIn('Não posso',complaint_reply('Quero CPF de outros clientes',self.s,{})[0])
    def test_plan_grounded(self):
        p=self.s.plan();self.assertIn('3 de 10',p[0]['evidence']);self.assertIn('Interdição',p[0]['cause']);self.assertTrue(report(self.s).startswith(b'%PDF'))
    def test_audit(self):
        t=self.create();self.s.manager_update(t,'Logística','Proposta',True);self.s.customer_decision(t,'PP1003',True,5);self.assertEqual(len([x for x in self.s.audit_rows() if x['reference']==t]),3)
    def test_satisfaction_validation(self):
        t=self.create();self.s.close(t)
        with self.assertRaises(ValueError):self.s.customer_decision(t,'PP1003',True,6)
        with self.assertRaises(ValueError):self.s.customer_decision(t,'PP1003',False,note='')
        self.assertEqual(self.s.case(t,'PP1003')['status'],'Aguardando confirmação')
    def test_reschedule_chat_memory_and_confirm(self):
        from paco import reply, confirm
        ctx={};msg,p,_=reply('Quero reagendar PP1002',self.s,ctx,[],'fake','fake',object());self.assertIsNone(p);self.assertIn('data',msg)
        desired=str(today()+timedelta(days=4));msg,p,_=reply(desired,self.s,ctx,[],'fake','fake',object());self.assertEqual(p['requested_date'],desired);self.assertFalse(self.s.tickets());confirm(self.s,p);self.assertEqual(self.s.cases()[0]['requested_date'],desired)
    def test_lost_cargo(self):
        _,p,_=complaint_reply('Minha carga PP1002 sumiu',self.s,{});self.assertEqual(p['kind'],'Mercadoria não localizada');t=self.create(p['kind'],'PP1002');self.assertEqual(self.s.case(t,'PP1002')['priority'],'Crítica')
    def test_original_and_new_eta(self):
        from core import describe
        d=str(today()+timedelta(days=3));t=self.create('Reagendamento',requested_date=d);self.s.manager_update(t,'Logística','Proposta',True,d);self.s.customer_decision(t,'PP1003',True,5);self.assertIn('Nova previsão confirmada',describe(self.s.get('PP1003')))
