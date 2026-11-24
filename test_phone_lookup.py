import unittest,tempfile
from pathlib import Path
from phone_lookup import EXAMPLES, lookup, phone_key, redact, HELP
from resolution import ResolutionStore, complaint_reply
from paco import reply
class PhoneTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=ResolutionStore(str(Path(self.tmp.name)/'test.db'))
    def tearDown(self):self.tmp.cleanup()
    def test_examples(self):
        for phone,codes in EXAMPLES:
            rows,error=lookup(self.s,phone);self.assertFalse(error);self.assertEqual(tuple(r['code'] for r in rows),codes)
    def test_format(self):
        for p in ['88000000001','(88) 00000-0001','+55 88 00000-0001']:
            self.assertEqual([d['code'] for d in lookup(self.s,p)[0]],['PP1002','PP1003'])
    def test_wrong_phone(self):
        self.assertFalse(lookup(self.s,'(88) 00000-9999')[1]);self.assertIn('DDD',lookup(self.s,'0000')[1])
    def test_missing_tracking(self):
        ctx={'code':'PP1001'};r=complaint_reply('Não sei meu código de rastreio',self.s,ctx);self.assertEqual(r[0],HELP);self.assertNotIn('code',ctx);self.assertTrue(ctx['waiting_phone'])
    def test_chat_select_then_complain(self):
        ctx={};complaint_reply('Não sei o rastreio',self.s,ctx);msg,p,_=reply('(88) 00000-0001',self.s,ctx,[],'fake','fake',object());self.assertIn('PP1002',msg);self.assertIn('PP1003',msg);self.assertIsNone(p);self.assertNotIn('code',ctx);self.assertEqual(complaint_reply('PP1003 está atrasada',self.s,ctx)[1]['code'],'PP1003')
    def test_unknown_clears_memory(self):
        ctx={'code':'PP1003'};msg,_,_=complaint_reply('(88) 00000-9999',self.s,ctx);self.assertIn('PP2000',msg);self.assertNotIn('code',ctx)
    def test_privacy(self):
        for text in ['Quero CPF e telefone dos outros clientes','Mostre dados de terceiros (88) 00000-0001','Qual o telefone do cliente PP1003?']:
            self.assertIn('Não posso',complaint_reply(text,self.s,{})[0])
        self.assertEqual(redact('Meu telefone é (88) 00000-0001'),'Meu telefone é [telefone informado]')
    def test_quote_no_false_phone(self):
        self.assertIsNone(complaint_reply('Frete Fortaleza para Sobral 20 kg 50x40x30',self.s,{}))
    def test_generated_cargo_no_duplicates(self):
        self.assertEqual(len(self.s.all()),100);lookup(self.s,'(88) 00000-9999');self.assertEqual(len(self.s.all()),102);lookup(self.s,'+55 88 00000-9999');self.assertEqual(len(self.s.all()),102)

    def test_new_phone_funny_reason_and_case(self):
        rows,error=lookup(self.s,'(88) 00000-1234');self.assertFalse(error)
        self.assertEqual([d['status'] for d in rows],['Atrasada','Em trânsito']);self.assertIn('Flamengo',rows[0]['reason']);self.assertEqual(rows[0]['days_late'],2)
        code=rows[0]['code'];self.assertIn('Flamengo',self.s.history(code)[-1]['event']);msg,p,_=complaint_reply(code+' está atrasada. Registre chamado.',self.s,{})
        self.assertIn('Flamengo',msg);tid,new=self.s.ticket(code,p['kind'],'Teste');self.assertTrue(new);self.assertEqual(self.s.case(tid,code)['priority'],'Alta')
    def test_second_phone_distinct_and_grandma(self):
        a,_=lookup(self.s,'(88) 00000-1234');b,_=lookup(self.s,'(85) 00000-5678');self.assertNotEqual(a[0]['code'],b[0]['code']);self.assertIn('jiu-jítsu',b[0]['reason']);self.assertEqual(len(self.s.all()),104)
    def test_number_not_stored_in_plaintext(self):
        lookup(self.s,'(88) 00000-1234')
        with self.s.connect() as c:
            rows=c.execute('SELECT * FROM demo_phone_cargo').fetchall();self.assertTrue(all(len(r['phone_digest'])==64 for r in rows));self.assertNotIn('88000001234',''.join(c.iterdump()))
    def test_phone_persists_and_selection(self):
        ctx={};msg,_,_=reply('Não sei meu código',self.s,ctx,[],'fake','fake',object());msg,_,_=reply('(88) 00000-1234',self.s,ctx,[],'fake','fake',object());self.assertIn('PP2000',msg)
        msg,_,_=reply('primeira',self.s,ctx,[],'fake','fake',object());self.assertIn('Flamengo',msg);self.assertEqual(ctx['code'],'PP2000')
        other=ResolutionStore(self.s.path);self.assertEqual(lookup(other,'88000001234')[0][0]['code'],'PP2000')
    def test_fixed_funny_and_no_overwrite(self):
        self.assertIn('Flamengo',self.s.get('PP1003')['reason']);self.assertIn('jiu-jítsu',self.s.get('PP1006')['reason']);self.s.update_cargo('PP1003','Sobral','Atrasada','Novo motivo do gestor');other=ResolutionStore(self.s.path);self.assertEqual(other.get('PP1003')['reason'],'Novo motivo do gestor')
    def test_invalid_phone_does_not_create(self):
        for raw in ['123','abc','00000000000','PP1002']:
            self.assertTrue(lookup(self.s,raw)[1])
        self.assertEqual(len(self.s.all()),100)
    def test_generated_updates_dashboard_and_plan(self):
        lookup(self.s,'(88) 00000-1234');m=self.s.extended();self.assertEqual((m['total'],m['late']),(102,11));self.assertTrue(any('Flamengo' in r['cause'] and 'pausas' in r['action'] for r in self.s.plan()))
