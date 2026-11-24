import tempfile, unittest
from pathlib import Path
from datetime import timedelta
from core import STAGES, EXCEPTION_STAGE, today, describe, stage_index
from resolution import ResolutionStore, complaint_reply
from operations import STATUS
from phone_lookup import lookup

class StageTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.s=ResolutionStore(str(Path(self.tmp.name)/'db.sqlite'))
    def tearDown(self):self.tmp.cleanup()
    def test_seed_variety(self):
        self.assertEqual({d['stage'] for d in self.s.all()},set(STAGES+[EXCEPTION_STAGE]))
        self.assertEqual(self.s.summary()['late'],10)
    def test_full_delivered_timeline(self):
        h=self.s.history('PP1001');self.assertEqual(len(h),8);self.assertTrue(h[-1]['event'].startswith('Objeto entregue'));self.assertEqual([r['timestamp'] for r in h],sorted(r['timestamp'] for r in h))
    def test_no_future_history(self):
        d=self.s.get('PP1068');h=self.s.history(d['code']);self.assertEqual(d['stage'],STAGES[2]);self.assertEqual(len(h),3);self.assertFalse(any('saiu para entrega' in x['event'].lower() for x in h))
    def test_delay_and_stage_independent(self):
        self.s.update_cargo('PP1003','Sobral',STAGES[2]);d=self.s.get('PP1003');self.assertEqual(d['stage'],STAGES[2]);self.assertEqual(d['status'],'Atrasada');self.assertIn('Flamengo',d['reason']);self.assertTrue(d['estimated_eta']);self.assertIn(STAGES[2],describe(d));self.assertIn(STAGES[2],complaint_reply('PP1003 está atrasada. Registre chamado.',self.s,{})[0]);self.assertIn(STAGES[2],self.s.notices('PP1003')[1]['message'])
    def test_active_updates_and_exception(self):
        code=self.s.create_cargo('Fortaleza','Sobral',today()+timedelta(days=2));self.assertEqual(self.s.get(code)['stage'],STAGES[0]);
        for stage in STATUS:
            if stage in ('Entregue','Atrasada'):continue
            self.s.update_cargo(code,'Sobral',stage);self.assertEqual(self.s.get(code)['stage'],stage)
        self.s.update_cargo(code,'Sobral','Entregue');self.assertEqual(stage_index(self.s.get(code)['stage']),7)
    def test_phone_history(self):
        rows,_=lookup(self.s,'(88) 00000-4321');self.assertEqual(rows[0]['stage'],'Em trânsito');self.assertIn(STAGES[1],self.s.history(rows[0]['code'])[1]['event']);self.assertIn('Flamengo',self.s.history(rows[0]['code'])[-1]['event'])
    def test_legacy_without_stage_table(self):
        with self.s.connect() as c:c.execute('DROP TABLE cargo_stage')
        migrated=ResolutionStore(self.s.path);self.assertEqual(migrated.get('PP1002')['stage'],'Em trânsito');self.assertEqual(migrated.get('PP1003')['status'],'Atrasada');self.assertEqual(migrated.get('PP1003')['stage'],'Em trânsito')
    def test_attempt_follows_departure(self):
        h=self.s.history('PP1072');self.assertIn('Objeto saiu para entrega',h[-2]['event']);self.assertIn(EXCEPTION_STAGE,h[-1]['event']);self.assertLess(h[-2]['timestamp'],h[-1]['timestamp'])
