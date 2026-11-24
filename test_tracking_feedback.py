import unittest, tempfile
from pathlib import Path
from operations import Operations, demo_extended
from paco import reply
from tracking_feedback import tracking_result, FORMAT, MISSING, EMPTY

class TrackingFeedbackTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.store=Operations(str(Path(self.tmp.name)/'test.sqlite3'))
    def tearDown(self): self.tmp.cleanup()
    def test_formats(self):
        for code in ['PP1002','pp1002','PP 1002','PP-1002',' pp - 1002 ']:
            self.assertEqual(tracking_result(self.store,code)[0]['code'],'PP1002')
        for code in ['ABC123','PP100','PP10022','TN1002','1234','PP1002A']:
            self.assertEqual(tracking_result(self.store,code)[2],FORMAT)
        self.assertEqual(tracking_result(self.store,'PP9999')[2],MISSING)
        self.assertEqual(tracking_result(self.store,' ')[2],EMPTY)
    def test_demo_invalid_memory(self):
        for text,expected in [('Onde está minha carga ABC123?',FORMAT),('PP123',FORMAT),('TN 1002',FORMAT),('Código: ABC',FORMAT),('PP9999',MISSING),('Quero abrir chamado PP9999',MISSING),('PP1002A',FORMAT)]:
            ctx={'code':'PP1002'}
            self.assertEqual(demo_extended(text,self.store,ctx),(expected,None,False),text)
            self.assertNotIn('code',ctx)
    def test_ai_invalid_before_api(self):
        for text,expected in [('PP9999',MISSING),('Minha carga ABC123',FORMAT)]:
            ctx={'code':'PP1002'}
            self.assertEqual(reply(text,self.store,ctx,[],'fake','fake',object()),(expected,None,False));self.assertNotIn('code',ctx)
    def test_valid_and_followup(self):
        ctx={};self.assertIn('Itapajé',demo_extended('Onde está pp-1002?',self.store,ctx)[0]);self.assertIn('Itapajé',demo_extended('Qual a localização?',self.store,ctx)[0])
    def test_nontracking(self):
        self.assertIn('R$',demo_extended('Quanto custa o frete de uma carga 20 kg Fortaleza Sobral 50x40x30',self.store,{})[0]);self.assertEqual(demo_extended('Quero avaliar PP1001 nota 5',self.store,{})[1]['score'],5)
    def test_new_cargo(self):
        from datetime import timedelta
        from core import today
        code=self.store.create_cargo('Fortaleza','Sobral',today()+timedelta(days=2));self.assertEqual(tracking_result(self.store,code)[0]['code'],code)
