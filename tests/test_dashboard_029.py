"""Offline generator parity, source labels and embedding safety."""
import copy
from contextlib import ExitStack
from html.parser import HTMLParser
import json
import unittest
from unittest.mock import patch
from research import dashboard_029 as dashboard
from research import manual_kraken_reversal_024 as manual


class Embedded(HTMLParser):
    def __init__(self):super().__init__();self.active=False;self.payload='';self.external=[]
    def handle_starttag(self,tag,attrs):
        attrs=dict(attrs)
        if tag=='script' and attrs.get('id')=='demo-data':self.active=True
        if tag in ('script','link','iframe','img') and (attrs.get('src') or attrs.get('href')):self.external.append(attrs)
    def handle_endtag(self,tag):
        if tag=='script':self.active=False
    def handle_data(self,text):
        if self.active:self.payload+=text


class DashboardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.result=manual.offline_demo()
    def setUp(self):
        stack=ExitStack();self.addCleanup(stack.close)
        for name in ('socket.socket','socket.getaddrinfo','socket.create_connection','urllib.request.urlopen','subprocess.Popen','subprocess.run'):
            stack.enter_context(patch(name,side_effect=AssertionError('NETWORK_OR_PROCESS_FORBIDDEN')))
    def model(self,report=None):return dashboard.view_model(self.result if report is None else report,generated_at='2026-11-06T00:00:00Z')
    def test_exact_original_rows_candidates_features_and_ranking(self):
        original=manual.operator_report(self.result);model=self.model()
        self.assertEqual(model['rows'],original['pairs']);self.assertEqual(model['candidates'],original['candidates'])
        self.assertEqual(model['source'],manual.SOURCE);self.assertEqual(model['policy'],'NO ORDERS')
        self.assertEqual(model['source_revision'],dashboard.SOURCE_REVISION)
    def test_session_stable_across_generation_times_and_no_duplicate_scan(self):
        a=self.model();b=dashboard.view_model(self.result,generated_at='2026-11-07T00:00:00Z')
        self.assertEqual(a['id'],b['id']);self.assertNotEqual(a['generated_at'],b['generated_at'])
    def test_fixture_coordinate_distinct_from_generation_clock(self):
        model=self.model();self.assertEqual(model['as_of'],1900000800)
        self.assertTrue(model['as_of_text'].startswith('2030-'));self.assertTrue(model['generated_at'].startswith('2026-'))
    def test_generated_document_is_self_contained_with_manual_same_origin_route(self):
        html=dashboard.render(self.model());parser=Embedded();parser.feed(html)
        self.assertEqual(json.loads(parser.payload),self.model());self.assertFalse(parser.external)
        self.assertIn("connect-src 'self'",html);self.assertIn("form-action 'none'",html)
        for token in ('__MODEL__','__APP__','__ENGINE__'):self.assertNotIn(token,html)
        self.assertIn('DEMO / SYNTHETIC DATA',html);self.assertIn('NO REAL ORDERS',html)
        self.assertLess(len(html.encode()),512*1024)
    def test_restore_is_local_bounded_preview_with_explicit_confirmation(self):
        html=dashboard.render(self.model())
        self.assertIn('id="restore" type="button">Restore demo journal</button>',html)
        self.assertIn('id="restore-file" type="file"',html)
        self.assertIn('id="confirm-restore"',html)
        self.assertIn('id="cancel-restore"',html)
        self.assertLess(html.index('if(file.size>P.LIMIT)'),html.index('await file.text()'))
        self.assertIn("$('restore-preview').textContent",html)
        self.assertIn('User-supplied synthetic records only.',html)
        self.assertNotIn('__RESTORE__',html)

    def test_load_demo_label_is_plain_text_without_missing_glyph(self):
        html=dashboard.render(self.model())
        self.assertIn('id="load-demo">Load demo scan</button>',html)
        self.assertNotIn('↗',html)
    def test_unsafe_text_cannot_close_embedded_json_script(self):
        model=self.model();bad='</script><script>window.stolen=true</script><img src=x onerror=alert(1)>'
        model['rows']['BTC/USD']['why_early']=bad
        html=dashboard.render(model);parser=Embedded();parser.feed(html)
        self.assertNotIn(bad,html);self.assertEqual(json.loads(parser.payload)['rows']['BTC/USD']['why_early'],bad)
    def test_unexpected_source_or_network_counter_refused(self):
        for changed in ({'source':'REAL_SOURCE'},{'requests':1}):
            original=manual.operator_report(self.result);original.update(changed)
            with patch.object(manual,'operator_report',return_value=original),self.assertRaises(ValueError):self.model()
    def test_invalid_or_missing_reference_price_is_unavailable(self):
        for value in (None,float('nan'),float('inf'),-1,True):
            original=manual.operator_report(self.result);original['pairs']['BTC/USD']['fixture_only_closed_price_usd']=value
            with patch.object(manual,'operator_report',return_value=original):model=self.model()
            self.assertIsNone(model['rows']['BTC/USD']['fixture_only_closed_price_usd'])
    def test_default_blocked_report_has_no_candidates_or_invented_values(self):
        model=self.model(manual.run_offline())
        self.assertFalse(model['candidates']);self.assertIsNone(model['as_of'])
        self.assertTrue(all(row['decision']=='BLOCKED' and row['fixture_only_closed_price_usd'] is None for row in model['rows'].values()))
    def test_generation_uses_existing_explicit_offline_demo(self):
        with patch.object(manual,'offline_demo',return_value=self.result) as demo:
            html=dashboard.generate(generated_at='2026-11-06T00:00:00Z')
        demo.assert_called_once_with();self.assertIn('Rule-based explanation',html)


if __name__=='__main__':unittest.main()
