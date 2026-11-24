import tempfile, unittest, json
from pathlib import Path
from types import SimpleNamespace as N
from datetime import timedelta
from operations import Operations, quote, demo_extended, today
from paco import reply, confirm
from reports import report

class V2Tests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.store=Operations(str(Path(self.tmp.name)/'test.sqlite3'))
    def tearDown(self):self.tmp.cleanup()
    def test_seed_and_migration(self):
        from core import Store
        p=str(Path(self.tmp.name)/'old.sqlite3');old=Store(p);tid,_=old.ticket('PP1003','Atraso','old');new=Operations(p);self.assertEqual(new.summary()['total'],100);self.assertEqual(new.protocol(tid,'PP1003')['status'],'Aberto');self.assertEqual(len(new.fleet()),5);self.assertEqual(len(Operations(p).fleet()),5)
    def test_quote(self):
        q=quote('Fortaleza','Sobral',20,50,40,30);self.assertEqual(q['cubed'],18);self.assertEqual(q['charge'],20);self.assertEqual(q['total'],round(25+q['km']*.12+23,2));self.assertGreater(quote('Fortaleza','Sobral',20,50,40,30,'Expressa')['total'],q['total'])
        for w in [0,-1,float('nan')]:
            with self.assertRaises(ValueError):quote('Fortaleza','Sobral',w,50,40,30)
        with self.assertRaises(ValueError):quote('Sobral','Sobral',20,50,40,30)
    def test_quote_memory_confirm(self):
        ctx={};msg,p,r=demo_extended('Frete Fortaleza para Sobral 20 kg 50x40x30',self.store,ctx);self.assertTrue(r);self.assertIsNone(p);self.assertIn('R$',msg);msg,p,r=demo_extended('Quero registrar essa cotação',self.store,ctx);self.assertEqual(p['action'],'quote');self.assertFalse(self.store.quotes());self.assertIn('CT-',confirm(self.store,p));self.assertEqual(self.store.extended()['quotes'],1)
    def test_protocol_and_notice(self):
        msg,p,r=demo_extended('PP1003 chegou danificada',self.store,{});self.assertEqual(p['kind'],'Avaria');self.assertEqual(len(self.store.tickets()),0);confirm(self.store,p);t=self.store.tickets()[0];self.assertIsNone(self.store.protocol(t['id'],'PP1002'));self.assertTrue(self.store.close(t['id']));self.assertIn(t['id'],self.store.notices('PP1003')[0 if not self.store.get('PP1003')['days_late'] else 1]['message'])
    def test_cargo_create_update(self):
        c=self.store.create_cargo('Fortaleza','Sobral',today()+timedelta(days=2),'V001');self.assertEqual(c,'PP1101');self.assertEqual(self.store.summary()['total'],101);self.store.update_cargo(c,'Itapajé','Em trânsito');self.assertEqual(self.store.get(c)['location'],'Itapajé');self.assertEqual(len(self.store.history(c)),2)
        with self.assertRaises(ValueError):self.store.update_cargo(c,'Fortaleza','Entregue')
        self.store.update_cargo(c,'Sobral','Entregue');self.assertEqual(self.store.summary()['delivered'],59)
        with self.assertRaises(ValueError):self.store.update_cargo(c,'Sobral','Em trânsito')
    def test_late_preserved(self):
        self.store.update_cargo('PP1003','Tianguá','Em trânsito');self.assertEqual(self.store.get('PP1003')['status'],'Atrasada');self.assertIn('Manutenção',self.store.get('PP1003')['reason'])
    def test_rating(self):
        self.store.rate('PP1001',5);self.store.rate('PP1001',4);m=self.store.extended();self.assertEqual((m['ratings'],m['satisfaction']),(1,4))
        with self.assertRaises(ValueError):self.store.rate('PP1002',5)
    def test_fleet(self):
        self.store.save_vehicle('V006','Teste','Motorista fictício 6',5000,'Disponível');self.store.assign('PP1002','V006');self.assertIn({'code':'PP1002','vehicle':'V006'},self.store.assignments());self.store.save_vehicle('V006','Teste','Motorista fictício 6',5000,'Manutenção');self.assertTrue(any('manutenção' in t for _,t,_ in self.store.alerts()))
        with self.assertRaises(ValueError):self.store.assign('PP1003','V006')
    def test_metrics(self):
        m=self.store.extended();self.assertEqual(sum(r['total'] for r in m['routes']),100);self.assertEqual(sum(r['late'] for r in m['routes']),10);self.assertTrue(self.store.alerts());self.assertIsNone(m['satisfaction'])
    def test_pdf(self):self.assertTrue(report(self.store).startswith(b'%PDF'))
    def test_refuse(self):
        self.assertIn('Não posso',demo_extended('Quero CPF de outros clientes',self.store,{})[0]);self.assertIn('Não posso',reply('Quero senha',self.store,{},[],'fake','fake')[0])
    def test_llm_tools(self):
        calls=[]
        def create(**kwargs):
            calls.append(kwargs);n=len(calls)
            if n==1:name,args='calcular_frete',dict(origin='Fortaleza',destination='Sobral',weight=20,length=50,width=40,height=30,service='Econômica')
            elif n==2:
                self.assertIn('total',kwargs['messages'][-1]['content']);name,args='preparar_cotacao',{}
            else:
                self.assertIn('aguardando confirmação',kwargs['messages'][-1]['content']);return N(choices=[N(message=N(content='Confirme.',tool_calls=None))])
            return N(choices=[N(message=N(content=None,tool_calls=[N(id=str(n),function=N(name=name,arguments=json.dumps(args)))]))])
        client=N(chat=N(completions=N(create=create)));msg,p,r=reply('Calcule e registre frete Fortaleza Sobral 20 kg 50x40x30',self.store,{},[],'fake','fake',client);self.assertEqual(p['action'],'quote');self.assertEqual(len(self.store.quotes()),0);confirm(self.store,p);self.assertEqual(len(self.store.quotes()),1)
    def test_llm_scope(self):
        calls=[]
        def create(**kwargs):
            calls.append(kwargs)
            if len(calls)==1:return N(choices=[N(message=N(content=None,tool_calls=[N(id='1',function=N(name='consultar_carga',arguments='{"codigo":"PP1003"}'))]))])
            self.assertIn('não autorizado',kwargs['messages'][-1]['content']);return N(choices=[N(message=N(content='Não permitido.',tool_calls=None))])
        msg,p,r=reply('Rastreie PP1002',self.store,{},[],'fake','fake',N(chat=N(completions=N(create=create))));self.assertFalse(r);self.assertIsNone(p)

if __name__=='__main__':unittest.main(verbosity=2)
