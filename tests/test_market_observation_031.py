"""Invented Binance-shaped fixtures only; no sockets or provider requests."""
import contextlib
import copy
import importlib
import io
import json
import threading
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from urllib.error import HTTPError
from research import market_observation_031 as m

NOW=1900000800000
NOW=NOW-NOW%m.HOUR+1000

def rows():
    end=NOW-NOW%m.HOUR
    return [[end-(29-i)*m.HOUR,'100','102','99','101','10',end-(29-i)*m.HOUR+m.HOUR-1,'1010',2,'5','505','0'] for i in range(30)]

def raw(value=None):return json.dumps(rows() if value is None else value).encode()


class MarketTests(unittest.TestCase):
    def test_import_and_default_do_not_fetch_or_start_server(self):
        with patch('urllib.request.OpenerDirector.open',side_effect=AssertionError('network')),patch.object(m,'ThreadingHTTPServer',side_effect=AssertionError('server')):
            importlib.reload(m)
            with patch('sys.argv',['market']),contextlib.redirect_stdout(io.StringIO()) as out:m.main()
            self.assertIn('no server or market requests',out.getvalue())

    def test_valid_close_only_exact_pair_and_no_reversal(self):
        out=m.parse(raw(),NOW)
        self.assertEqual(out['pair'],'BTC/USDT');self.assertEqual(out['quote'],'USDT')
        self.assertEqual(out['completed_count'],29);self.assertEqual(out['latest_completed_close'],'101')
        self.assertEqual(out['status'],'OBSERVE_ONLY');self.assertIsNone(out['current_executable_quote'])
        self.assertNotIn('volume',out);self.assertNotIn('candidates',out)
        self.assertEqual(out['clock'],'LOCAL_SYSTEM_UTC_UNVERIFIED_B4_NO_GO')

    def test_unfinished_candle_excluded_from_close_observation(self):
        value=rows();a=m.parse(raw(value),NOW);value[-1][4]='102';b=m.parse(raw(value),NOW)
        self.assertEqual(a,b)

    def test_invalid_schema_and_values(self):
        mutations=[lambda r:r[2].append(0),lambda r:r[2].__setitem__(0,r[1][0]),lambda r:r[2].__setitem__(0,r[2][0]+m.HOUR),lambda r:r[2].__setitem__(4,'NaN'),lambda r:r[2].__setitem__(4,'0'),lambda r:r[2].__setitem__(5,'-1'),lambda r:r[2].__setitem__(4,'999'),lambda r:r[2].__setitem__(8,True),lambda r:r[2].__setitem__(6,r[2][6]+1),lambda r:r[2].__setitem__(5,'0'),lambda r:r[2].__setitem__(9,'11'),lambda r:r[2].__setitem__(11,'unknown')]
        for mutate in mutations:
            with self.subTest(mutate=mutate):
                value=rows();mutate(value)
                with self.assertRaises(ValueError):m.parse(raw(value),NOW)

    def test_oversize_nonfinite_short_stale_future(self):
        for value in (b'x'*(m.BODY_LIMIT+1),b'NaN',b'{"x":1,"x":2}',raw(rows()[:21])):
            with self.assertRaises((ValueError,UnicodeError)):m.parse(value,NOW)
        with self.assertRaises(ValueError):m.parse(raw(),NOW+2*m.HOUR)
        with self.assertRaises(ValueError):m.parse(raw(),NOW-2*m.HOUR)

    def test_fixed_transport_one_request_timeout_byte_cap(self):
        class Response(io.BytesIO):
            status=200;headers={'Content-Type':'application/json'}
            def geturl(self):return m.URL
        class Opener:
            calls=[]
            def open(self,request,timeout):
                self.calls.append((request,timeout));return Response(raw())
        opener=Opener();out=m.fetch_once(opener,lambda:NOW/1000)
        self.assertEqual(len(opener.calls),1);self.assertEqual(opener.calls[0][0].full_url,m.URL)
        self.assertEqual(opener.calls[0][1],12);self.assertEqual(out['pair'],'BTC/USDT')
        with self.assertRaises(ValueError):m.NoRedirect().redirect_request(None,None,302,'',{},'https://other')

    def test_provider_error_no_retry(self):
        opener=SimpleNamespace(open=unittest.mock.Mock(side_effect=HTTPError(m.URL,429,'rate limit',{},None)))
        with self.assertRaises(HTTPError):m.fetch_once(opener)
        self.assertEqual(opener.open.call_count,1)

    def test_service_rate_limit_errors_and_concurrent_refresh(self):
        calls=[];entered=threading.Event();release=threading.Event()
        def fetch():calls.append(1);entered.set();release.wait(1);return {'status':'OBSERVE_ONLY'}
        service=m.Service(fetch,lambda:100)
        thread=threading.Thread(target=service.refresh);thread.start();self.assertTrue(entered.wait(1))
        self.assertEqual(service.refresh()[0],409);release.set();thread.join()
        self.assertEqual(service.refresh()[0],429);self.assertEqual(len(calls),1)
        failed=m.Service(lambda:(_ for _ in ()).throw(ValueError('Provider HTTP 451')),lambda:100)
        self.assertEqual(failed.refresh(),(502,{'error':'Provider HTTP 451'}));self.assertEqual(failed.refresh()[0],429)

    def request(self,method='POST',path='/api/market-read',headers=None,body=b'{}'):
        from email.message import Message
        handler=m.handler('offline html',m.Service(lambda:m.parse(raw(),NOW)))
        instance=object.__new__(handler);instance.server=SimpleNamespace(server_port=8765)
        instance.path=path;instance.headers=Message()
        for k,v in (headers if headers is not None else [('Host','127.0.0.1:8765'),('Origin','http://127.0.0.1:8765'),('Content-Length','2'),('Content-Type','application/json')]):instance.headers[k]=v
        instance.rfile=io.BytesIO(body);result=[];instance.send=lambda *args:result.append(args)
        getattr(instance,'do_'+method)();return result[0]

    def test_fixed_route_origin_host_body_and_no_get_fetch(self):
        self.assertEqual(self.request()[0],200)
        self.assertEqual(self.request('GET','/')[0],200)
        self.assertEqual(self.request('GET')[0],404)
        self.assertEqual(self.request(path='/api/market-read?symbol=ETHUSDT')[0],404)
        self.assertEqual(self.request(body=b'[]')[0],400)
        for headers in ([('Host','evil'),('Origin','http://evil')],[('Host','127.0.0.1:8765')],[('Host','127.0.0.1:8765'),('Origin','null')]):
            self.assertEqual(self.request(headers=headers)[0],403)
        headers=[('Host','127.0.0.1:8765'),('Origin','http://127.0.0.1:8765'),('Content-Length','2'),('Content-Length','2'),('Content-Type','application/json')]
        self.assertEqual(self.request(headers=headers)[0],400)

    def test_retry_after_hold_and_no_automatic_retry(self):
        error=HTTPError(m.URL,429,'rate limit',{'Retry-After':'1200'},None)
        self.assertEqual(m.retry_delay(error),1200)
        self.assertEqual(m.retry_delay(HTTPError(m.URL,429,'rate limit',{'Retry-After':'172800'},None)),172800)
        self.assertEqual(m.retry_delay(HTTPError(m.URL,429,'rate limit',{'Retry-After':'unknown'},None)),10**15)
        clock=[100];calls=[]
        def refused():
            calls.append(1);raise m.ProviderRefusal('Provider HTTP 429',1200)
        service=m.Service(refused,lambda:clock[0])
        self.assertEqual(service.refresh()[0],429);clock[0]=131
        status,out=service.refresh();self.assertEqual(status,429);self.assertEqual(out['retry_after'],1169)
        self.assertEqual(len(calls),1)

    def test_transport_refuses_oversize_encoding_redirect_or_wrong_type(self):
        class Response(io.BytesIO):
            status=200
            def geturl(self):return self.url
        for payload,headers,url in [(b'x'*(m.BODY_LIMIT+1),{'Content-Type':'application/json'},m.URL),(raw(),{'Content-Type':'text/html'},m.URL),(raw(),{'Content-Type':'application/json','Content-Encoding':'gzip'},m.URL),(raw(),{'Content-Type':'application/json'},'https://other'),(raw(),{'Content-Type':'application/json','Content-Length':'999999'},m.URL)]:
            response=Response(payload);response.headers=headers;response.url=url
            with self.assertRaises(ValueError):m.fetch_once(SimpleNamespace(open=lambda *a,**k:response),lambda:NOW/1000)

    def test_worker_timeout_and_output_cap(self):
        import subprocess
        with patch.object(m.subprocess,'run',side_effect=subprocess.TimeoutExpired('test',15)):
            with self.assertRaisesRegex(ValueError,'15-second'):m.worker_result()
        with patch.object(m.subprocess,'run',return_value=SimpleNamespace(returncode=0,stdout=b'x'*8193)):
            with self.assertRaises(ValueError):m.worker_result()


if __name__=='__main__':unittest.main()
