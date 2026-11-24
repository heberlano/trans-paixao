import tempfile, unittest
from pathlib import Path
from datetime import date,timedelta
from unittest.mock import patch
from core import today, describe, forecast_text
from resolution import ResolutionStore, complaint_reply
from phone_lookup import lookup
from paco import reply

class ForecastTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.s=ResolutionStore(str(Path(self.tmp.name)/'db.sqlite'))
    def tearDown(self):self.tmp.cleanup()
    def test_all_delayed_have_future_estimate(self):
        for d in self.s.all():
            if d['status']=='Atrasada':
                self.assertGreater(date.fromisoformat(d['estimated_eta']),today());self.assertIn('Nova previsão estimada',describe(d));self.assertLess(date.fromisoformat(d['eta']),today())
            else:self.assertFalse(d['estimated_eta'])
    def test_phone_generated_and_stable(self):
        rows,_=lookup(self.s,'(88) 00000-1234');d=rows[0];self.assertIn('Flamengo',d['reason']);self.assertTrue(d['estimated_eta']);self.assertEqual(d['estimated_eta'],lookup(self.s,'(88) 00000-1234')[0][0]['estimated_eta'])
    def test_chat_forecast_not_complaint(self):
        d=self.s.get('PP1003');msg,p,ok=reply('Qual a nova previsão da carga PP1003 atrasada?',self.s,{},[],'fake','fake',object());self.assertTrue(ok);self.assertIsNone(p);self.assertIn(date.fromisoformat(d['estimated_eta']).strftime('%d/%m/%Y'),msg)
    def test_complaint_and_notice_forecast(self):
        msg,p,_=complaint_reply('PP1003 está atrasada, registre chamado',self.s,{});self.assertEqual(p['kind'],'Atraso');self.assertIn('Nova previsão estimada',msg);self.assertTrue(any('Nova previsão estimada' in n['message'] for n in self.s.notices('PP1003')))
    def test_confirmation_precedence_and_original(self):
        old=self.s.get('PP1003')['eta'];t,_=self.s.ticket('PP1003','Atraso','Teste');new=str(today()+timedelta(days=5));self.s.manager_update(t,'Logística','Nova data',True,new);self.s.customer_decision(t,'PP1003',True,5);d=self.s.get('PP1003');self.assertEqual(d['eta'],old);self.assertFalse(d['estimated_eta']);self.assertIn('Nova previsão confirmada',forecast_text(d));self.assertNotIn('estimada',forecast_text(d))
    def test_expired_confirmed_and_estimate(self):
        t,_=self.s.ticket('PP1003','Atraso','Teste');new=today()+timedelta(days=1);self.s.manager_update(t,'Logística','Nova data',True,str(new));self.s.customer_decision(t,'PP1003',True,5)
        future=new+timedelta(days=1)
        with patch('core.today',return_value=future):
            d=self.s.get('PP1003');self.assertGreater(date.fromisoformat(d['estimated_eta']),future);self.assertIn('Previsão anterior vencida',forecast_text(d))
    def test_delivered_no_prediction(self):
        self.s.update_cargo('PP1003','Tianguá','Entregue','');self.assertFalse(forecast_text(self.s.get('PP1003')))
