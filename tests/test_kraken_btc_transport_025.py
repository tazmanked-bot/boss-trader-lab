"""Controlled offline IO plus real local POSIX worker lifecycle, never a network."""
import copy
from contextlib import ExitStack, redirect_stdout, redirect_stderr
from datetime import datetime, timezone
from email.utils import format_datetime
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import resource
import signal
import ssl
import threading
import time
import unittest
from unittest.mock import patch

from research import kraken_btc_transport_025 as transport
from research import kraken_probe_corrections as corrections
from research import kraken_spot_diagnostic as diagnostic

FIXTURE = json.loads((Path(__file__).parent/'fixtures/kraken_reversal_groundwork_022.json').read_text())
T = FIXTURE['independent_synthetic_reference']['as_of']
def utc(): return transport.SyntheticUTC((T+2)*transport.NS)


def payloads():
    observations = copy.deepcopy(FIXTURE['input']['observations']['BTC/USD'])
    return [observations['identity']['payload'], observations['ohlc']['capture']['response']]


def wire(payload=None, *, status=200, body=None, date=T+2, extra=b''):
    body = json.dumps(payload, separators=(',', ':'), allow_nan=False).encode() if body is None else body
    date = format_datetime(datetime.fromtimestamp(date, timezone.utc), usegmt=True)
    return (f'HTTP/1.1 {status} Test\r\nContent-Type: application/json\r\nContent-Length: {len(body)}\r\nDate: {date}\r\n'.encode()+extra+b'\r\n'+body)


class Stream:
    def __init__(self, value, fault=None):
        self.value, self.pos, self.fault = value, 0, fault
        self.sent, self.timeouts, self.reads = [], [], []
        self.closed = 0
    def settimeout(self, value):
        assert 0 < value <= 10
        self.timeouts.append(value)
    def connect(self, address):
        assert address == ('8.8.8.8',443)
        if self.fault == 'connect': raise OSError('DO_NOT_EXPOSE')
        if self.fault == 'connect_hang':
            while True: time.sleep(1)
    def do_handshake(self):
        if self.fault == 'tls': raise ssl.SSLError('DO_NOT_EXPOSE')
        if self.fault == 'tls_hang':
            while True: time.sleep(1)
    def selected_alpn_protocol(self): return 'h2' if self.fault == 'alpn' else 'http/1.1'
    def sendall(self, value): self.sent.append(value)
    def recv_into(self, view, size):
        self.reads.append((len(view),size))
        if self.fault == 'read_hang':
            while True: time.sleep(1)
        if self.fault == 'read_error': raise OSError('DO_NOT_EXPOSE')
        if self.fault == 'overread': return size+1
        n = min(size, len(self.value)-self.pos)
        view[:n] = self.value[self.pos:self.pos+n]
        self.pos += n
        return n
    def close(self): self.closed += 1


class TLS:
    check_hostname = True
    verify_mode = ssl.CERT_REQUIRED
    minimum_version = ssl.TLSVersion.TLSv1_2
    def __init__(self): self.alpn = self.server = None
    def set_alpn_protocols(self, protocols): self.alpn = protocols
    def wrap_socket(self, stream, *, server_hostname, do_handshake_on_connect):
        assert server_hostname == 'api.kraken.com' and do_handshake_on_connect is False
        self.server = server_hostname
        return stream


def factory_for(values=None, fault=None, child_required=False):
    values = [wire(p) for p in payloads()] if values is None else values
    parent = os.getpid()
    def factory(request):
        if child_required:
            assert os.getpid() != parent
            assert os.getsid(0) == os.getpid()
            assert resource.getrlimit(resource.RLIMIT_AS)[0] <= transport.ADDRESS_SPACE_BYTES
            assert resource.getrlimit(resource.RLIMIT_NOFILE)[0] <= 32
            assert resource.getrlimit(resource.RLIMIT_CORE)[0] == 0
        stream = Stream(values[0 if request.path.endswith('AssetPairs') else 1], fault)
        def dns(host, port):
            assert (host,port) == ('api.kraken.com',443)
            if fault == 'dns_hang':
                while True: time.sleep(1)
            return ('8.8.8.8',)
        return dns, lambda:stream, TLS()
    return factory


class BoundaryTests(unittest.TestCase):
    def setUp(self):
        stack = ExitStack(); self.addCleanup(stack.close)
        guards = [stack.enter_context(patch(name,side_effect=AssertionError('REAL_IO_FORBIDDEN'))) for name in (
            'socket.socket','socket.create_connection','socket.getaddrinfo','urllib.request.urlopen',
            'http.client.HTTPSConnection','subprocess.Popen','subprocess.run','time.time')]
        self.addCleanup(lambda:[guard.assert_not_called() for guard in guards])

    def direct(self, value=None, fault=None, request=None, dns=None, context=None):
        stream = Stream(wire(payloads()[0]) if value is None else value, fault)
        context = TLS() if context is None else context
        dns = (lambda h,p:('8.8.8.8',)) if dns is None else dns
        budget = transport.Deadline(time.monotonic_ns()+transport.DEADLINE_NS,time.monotonic_ns)
        output = transport.exchange(transport.manifest(T)[0] if request is None else request,T,
                                    (dns,lambda:stream,context),budget)
        return output,stream,context

    def blocked(self,result,attempts=None):
        self.assertEqual(result['decision'],'BLOCKED')
        self.assertEqual(result['overall'],'HOLD')
        self.assertEqual(result['clock'],'B4_NO_GO')
        self.assertEqual(result['live_source_admission'],'HOLD')
        self.assertEqual(result['policy'],'NO ORDERS')
        self.assertEqual(result['requests'],0)
        self.assertEqual(result['completed_hourly_candles'],0)
        self.assertNotIn('bridge_ref',result)
        if attempts is not None:self.assertEqual(result['offline_attempts'],attempts)

    def test_import_and_default_cli_have_no_io_or_worker(self):
        with patch('builtins.open',side_effect=AssertionError), patch('os.fork',side_effect=AssertionError),patch.object(time,'monotonic_ns',side_effect=AssertionError):
            importlib.reload(transport)
            self.blocked(transport.observe_offline(),0)
            with patch('sys.argv',['boundary']),redirect_stdout(io.StringIO()) as out:
                self.assertEqual(transport.main(),2)
            self.assertEqual(json.loads(out.getvalue())['requests'],0)

    def test_cli_rejects_live_or_urls(self):
        for option in ('--live','https://api.kraken.com','--api-key=secret'):
            with self.subTest(option=option),patch('sys.argv',['boundary',option]),redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit) as raised:transport.main()
                self.assertEqual(raised.exception.code,2)

    def test_exact_manifest_and_request_bytes(self):
        identity,ohlc = transport.manifest(T)
        self.assertEqual(identity.target(),'/0/public/AssetPairs?pair=XBTUSD&aclass_base=currency&info=info')
        self.assertEqual(ohlc.target(),f'/0/public/OHLC?pair=XBTUSD&interval=60&since={T-86400}')
        self.assertEqual(transport.manifest(T+123)[1].params[-1],('since',T-86400))
        _,stream,tls = self.direct()
        self.assertEqual(tls.alpn,['http/1.1'])
        self.assertEqual(tls.server,'api.kraken.com')
        self.assertEqual(stream.sent,[('GET '+identity.target()+' HTTP/1.1\r\nHost: api.kraken.com\r\nAccept: application/json\r\nAccept-Encoding: identity\r\nConnection: close\r\n\r\n').encode()])
        self.assertTrue(all(n<=4096 and n==size for n,size in stream.reads))
        self.assertGreater(stream.closed,0)

    def test_other_symbol_private_endpoint_or_changed_parameters_refused_before_dns(self):
        requests = [diagnostic.Request('XRP/USD','/0/public/AssetPairs',()),
                    diagnostic.Request('BTC/USD','/0/private/AddOrder',()),
                    diagnostic.Request('BTC/USD','/0/public/OHLC',(('pair','XBTUSD'),('interval',1),('since',T-86400)))]
        for request in requests:
            with self.subTest(request=request),self.assertRaises(transport.Refused):
                self.direct(request=request,dns=lambda *a:self.fail('DNS reached'))

    def test_bad_dns_and_no_address_fallback(self):
        for addresses in ((),['8.8.8.8'],('127.0.0.1',),('169.254.169.254',),('::1',),('bad',),('8.8.8.8',)*9):
            with self.subTest(addresses=addresses),self.assertRaises((transport.Refused,ValueError)):
                self.direct(dns=lambda *a:addresses)
        with self.assertRaises(transport.Refused) as raised:self.direct(fault='connect')
        self.assertEqual(raised.exception.reason,'NETWORK_UNAVAILABLE')

    def test_tls_requires_certificate_hostname_and_minimum_version(self):
        for name,value in [('check_hostname',False),('verify_mode',ssl.CERT_NONE),('minimum_version',ssl.TLSVersion.TLSv1)]:
            context=TLS();setattr(context,name,value)
            with self.subTest(name=name),self.assertRaises(transport.Refused):
                self.direct(context=context,dns=lambda *a:self.fail('DNS reached'))
        for fault in ('tls','alpn'):
            with self.subTest(fault=fault),self.assertRaises(transport.Refused) as raised:self.direct(fault=fault)
            self.assertEqual(raised.exception.reason,'TLS_FAILURE')

    def test_stream_errors_and_overread_refuse(self):
        for fault in ('read_error','overread'):
            with self.subTest(fault=fault),self.assertRaises(transport.Refused):self.direct(fault=fault)

    def test_status_codes_never_read_body(self):
        for status in (101,302,429,451,500):
            value=wire({},status=status)
            stream=Stream(value)
            with self.subTest(status=status),self.assertRaises(transport.Refused):
                transport.read_wire(stream,transport.Deadline(time.monotonic_ns()+transport.DEADLINE_NS,time.monotonic_ns))
            self.assertEqual(stream.pos,value.index(b'\r\n\r\n')+4)

    def test_malicious_headers_before_body_allocation(self):
        extra=[b'Content-Length: 1\r\n',b'Transfer-Encoding: chunked\r\n',b'Content-Encoding: gzip\r\n',
               b'X: '+b'x'*1024+b'\r\n',b' folded: bad\r\n',b'X: a\n',
               b''.join(f'X-{i}: a\r\n'.encode() for i in range(65)),
               b''.join(f'X-{i}: '.encode()+b'x'*900+b'\r\n' for i in range(12))]
        for header in extra:
            with self.subTest(header=header[:40]),self.assertRaises(transport.Refused):self.direct(wire({},extra=header))
        value=wire({}).replace(b'Content-Length: 2',b'Content-Length: 262145')
        with self.assertRaises(transport.Refused) as raised:self.direct(value)
        self.assertEqual(raised.exception.reason,'BODY_LIMIT')

    def test_eof_trailing_invalid_json_and_duplicate_keys(self):
        values=[wire({})[:-1],wire({})+b'X',wire(body=b'{"x":NaN}'),wire(body=b'{"x":1e999}'),
                wire(body=b'{"x":1,"x":2}'),wire(body=b'\xff'),wire(body=b'[]'),wire(body=b'')]
        for value in values:
            with self.subTest(value=value[-20:]),self.assertRaises((transport.Refused,corrections.Refused)):self.direct(value)

    def test_deadline_expiry_and_monotonic_reversal(self):
        values=iter([10,9]);budget=transport.Deadline(20,lambda:next(values));budget.remaining()
        with self.assertRaises(transport.Refused):budget.remaining()
        with self.assertRaises(transport.Refused):transport.Deadline(10,lambda:10).remaining()

    def test_real_child_session_resource_limits_and_bounded_ipc(self):
        request=transport.manifest(T)[0]
        value=transport.isolated_exchange(request,T,dependencies_factory=factory_for(child_required=True))
        self.assertEqual(value,wire(payloads()[0]))

    def test_real_child_hanging_dns_and_read_killed_and_reaped(self):
        for fault in ('dns_hang','connect_hang','tls_hang','read_hang'):
            start=time.monotonic()
            with self.subTest(fault=fault),self.assertRaises(transport.Refused) as raised:
                transport.isolated_exchange(transport.manifest(T)[0],T,dependencies_factory=factory_for(fault=fault),timeout_ns=100_000_000)
            self.assertEqual(raised.exception.reason,'TIMEOUT')
            self.assertLess(time.monotonic()-start,1.0) # Local observation, not runner guarantee.

    def test_worker_huge_response_over_pipe_capacity_has_no_deadlock(self):
        value=wire(body=json.dumps({'padding':'x'*100000}).encode())
        self.assertEqual(transport.isolated_exchange(transport.manifest(T)[0],T,dependencies_factory=factory_for([value,value])),value)

    def test_worker_absence_of_provider_and_unsupported_threading(self):
        with patch('os.fork',side_effect=AssertionError):
            with self.assertRaises(transport.Refused) as raised:transport.isolated_exchange(transport.manifest(T)[0],T)
            self.assertEqual(raised.exception.reason,'AUTHORIZATION_MISSING')
        with patch.object(threading,'active_count',return_value=2):
            with self.assertRaises(transport.Refused) as raised:
                transport.isolated_exchange(transport.manifest(T)[0],T,dependencies_factory=factory_for())
            self.assertEqual(raised.exception.reason,'PLATFORM_UNSUPPORTED')

    def test_worker_launch_expired_before_release(self):
        original=transport.os.fork
        def slowfork():
            pid=original()
            if pid:time.sleep(.03)
            return pid
        with patch.object(transport.os,'fork',side_effect=slowfork):
            with self.assertRaises(transport.Refused) as raised:
                transport.isolated_exchange(transport.manifest(T)[0],T,dependencies_factory=lambda r:self.fail('RELEASED'),timeout_ns=10_000_000)
        self.assertEqual(raised.exception.reason,'TIMEOUT')

    def test_unreapable_reports_stop(self):
        def reap_then_report(pid,deadline):
            original(pid,deadline)
            raise transport.Refused('WORKER_UNREAPED')
        original=transport._reap
        with patch.object(transport,'_reap',side_effect=reap_then_report):
            result=transport.observe_offline(dependencies_factory=factory_for(fault='dns_hang'),synthetic_utc=utc(),timeout_ns=30_000_000)
        self.blocked(result,1)
        self.assertEqual(result['reason'],'WORKER_UNREAPED')

    def test_corrupted_result_frame_refuses(self):
        payload=b'W'+wire({});frame=transport.encode_frame(payload)
        storage=frame+b'\0'*(transport.MAP_SIZE-len(frame))
        self.assertEqual(transport.decode_frame(storage),payload[1:])
        variants=[storage[:-1],b'\xff'*4+storage[4:],storage[:4]+b'X'*32+storage[36:],storage[:-1]+b'X']
        for value in variants:
            with self.subTest(value=value[:8]),self.assertRaises(transport.Refused):transport.decode_frame(value)
        for payload in (b'Zbad',b'Esecret error message'):
            value=transport.encode_frame(payload);value+=b'\0'*(transport.MAP_SIZE-len(value))
            with self.assertRaises(transport.Refused):transport.decode_frame(value)

    def test_resource_setup_failure_never_releases(self):
        with patch.object(resource,'setrlimit',side_effect=OSError):
            with self.assertRaises(transport.Refused):
                transport.isolated_exchange(transport.manifest(T)[0],T,dependencies_factory=lambda r:self.fail('RELEASED'))

    def test_worker_exception_is_redacted_and_no_second_stage(self):
        result=transport.observe_offline(dependencies_factory=lambda r:(_ for _ in ()).throw(RuntimeError('SECRET')),synthetic_utc=utc())
        self.blocked(result,1)
        self.assertEqual(result['reason'],'WORKER_INVALID')
        self.assertNotIn('SECRET',json.dumps(result))

    def test_complete_offline_identity_to_ohlc_observation_no_candidates(self):
        result=transport.observe_offline(dependencies_factory=factory_for(child_required=True),synthetic_utc=utc())
        self.assertEqual(result['decision'],'OBSERVE_ONLY',result)
        self.assertEqual(result['offline_attempts'],2)
        self.assertEqual(result['completed_hourly_candles'],21)
        self.assertEqual(result['requests'],0)
        self.assertEqual(result['clock'],'B4_NO_GO')
        self.assertNotIn('candidates',result)
        self.assertLess(len(json.dumps(result)),8192)

    def test_first_failure_status_or_api_error_stops(self):
        for value in (wire({},status=429),wire({},status=451),wire({'error':['DO_NOT_EXPOSE'],'result':{}})):
            result=transport.observe_offline(dependencies_factory=factory_for([value,wire(payloads()[1])]),synthetic_utc=utc())
            self.blocked(result,1)
            self.assertNotIn('DO_NOT_EXPOSE',json.dumps(result))

    def test_pair_status_alias_quote_or_unknown_schema_stops(self):
        for field,value in [('status','cancel_only'),('altname','BTCUSD'),('quote','USDT'),('extra','unknown')]:
            values=payloads();values[0]['result']['XXBTZUSD'][field]=value
            result=transport.observe_offline(dependencies_factory=factory_for([wire(p) for p in values]),synthetic_utc=utc())
            self.blocked(result,1)

    def test_missing_fake_clock_bad_uncertainty_and_trusted_true_are_not_authentic(self):
        for coordinate in (None,{'trusted':True,'utc_ns':utc().utc_ns},transport.SyntheticUTC(utc().utc_ns,2*transport.NS+1),transport.SyntheticUTC(True)):
            result=transport.observe_offline(dependencies_factory=lambda r:self.fail('WORKER'),synthetic_utc=coordinate)
            self.blocked(result,0)
            self.assertEqual(result['reason'],'CLOCK_UNVERIFIED')

    def test_http_date_is_only_consistency_not_utc_authority(self):
        values=[wire(payloads()[0],date=T-100),wire(payloads()[1])]
        result=transport.observe_offline(dependencies_factory=factory_for(values),synthetic_utc=utc())
        self.blocked(result,1)
        self.assertEqual(result['reason'],'SERVICE_TIME_CONFLICT')
        bad=wire(payloads()[0]).replace(b'Date: ',b'Date: invalid ')
        self.blocked(transport.observe_offline(dependencies_factory=factory_for([bad,values[1]]),synthetic_utc=utc()),1)

    def test_full_history_gap_duplicate_stale_and_short_history_refuse(self):
        for mutate in (lambda rows:rows.pop(5),lambda rows:rows.insert(5,copy.deepcopy(rows[4])),
                       lambda rows:rows.pop(),lambda rows:rows.__delitem__(slice(0,2))):
            values=payloads();mutate(values[1]['result']['XXBTZUSD'])
            result=transport.observe_offline(dependencies_factory=factory_for([wire(p) for p in values]),synthetic_utc=utc())
            self.blocked(result,2)

    def test_invalid_eight_field_ohlcv_volume_vwap_and_prices_refuse(self):
        for index,value in ((1,'0'),(2,'1'),(4,'NaN'),(5,'999999'),(6,'-1'),(7,1.5)):
            values=payloads();values[1]['result']['XXBTZUSD'][0][index]=value
            self.blocked(transport.observe_offline(dependencies_factory=factory_for([wire(p) for p in values]),synthetic_utc=utc()),2)
        values=payloads();values[1]['result']['XXBTZUSD'][0].append('extra')
        self.blocked(transport.observe_offline(dependencies_factory=factory_for([wire(p) for p in values]),synthetic_utc=utc()),2)

    def test_unfinished_candle_exclusion_and_no_lookahead(self):
        baseline=transport.observe_offline(dependencies_factory=factory_for(),synthetic_utc=utc())
        values=payloads();values[1]['result']['XXBTZUSD'][-1][1:7]=['999']*6
        changed=transport.observe_offline(dependencies_factory=factory_for([wire(p) for p in values]),synthetic_utc=utc())
        self.assertEqual(changed,baseline)
        self.assertEqual(changed['completed_hourly_candles'],21)

    def test_fd_cleanup_success_and_timeout(self):
        before=set(os.listdir('/proc/self/fd'))
        for fault in (None,'dns_hang'):
            try:transport.isolated_exchange(transport.manifest(T)[0],T,dependencies_factory=factory_for(fault=fault),timeout_ns=50_000_000)
            except transport.Refused:pass
        self.assertEqual(set(os.listdir('/proc/self/fd')),before)

    def test_child_closes_parent_only_file_descriptors(self):
        read_fd,write_fd=os.pipe()
        base=factory_for(child_required=True)
        def factory(request):
            for fd in (read_fd,write_fd):
                try:os.fstat(fd)
                except OSError:continue
                raise AssertionError('INHERITED_FD_OPEN')
            return base(request)
        try:
            self.assertEqual(transport.isolated_exchange(transport.manifest(T)[0],T,dependencies_factory=factory),wire(payloads()[0]))
        finally:
            os.close(read_fd);os.close(write_fd)

    def test_corruption_written_by_actual_worker_is_not_accepted(self):
        with patch.object(transport,'encode_frame',return_value=b'\xff'*4):
            with self.assertRaises(transport.Refused) as raised:
                transport.isolated_exchange(transport.manifest(T)[0],T,dependencies_factory=factory_for())
        self.assertEqual(raised.exception.reason,'IPC_INVALID')

    def test_proxy_environment_never_changes_explicit_manifest(self):
        with patch.dict(os.environ,{'HTTPS_PROXY':'http://forbidden.invalid:8080','ALL_PROXY':'http://forbidden.invalid:8080'}):
            output,_,_=self.direct()
        self.assertEqual(output,wire(payloads()[0]))

    def test_one_budget_decreases_through_dns_tls_send_and_all_reads(self):
        class Clock:
            value=0
            def __call__(self):self.value+=1000;return self.value
        clock=Clock();stream=Stream(wire(payloads()[0]));tls=TLS()
        transport.exchange(transport.manifest(T)[0],T,((lambda h,p:('8.8.8.8',)),lambda:stream,tls),transport.Deadline(transport.DEADLINE_NS,clock))
        self.assertTrue(all(a>b for a,b in zip(stream.timeouts,stream.timeouts[1:])))

    def test_illegal_cutoff_and_timeout_cannot_start_worker(self):
        for cutoff in (True,-1,2**63):
            with self.subTest(cutoff=cutoff),self.assertRaises(transport.Refused):transport.manifest(cutoff)
        for timeout in (True,0,transport.DEADLINE_NS+1):
            with self.subTest(timeout=timeout),patch('os.fork',side_effect=AssertionError),self.assertRaises(transport.Refused):
                transport.isolated_exchange(transport.manifest(T)[0],T,dependencies_factory=factory_for(),timeout_ns=timeout)

    def test_timeout_reaps_the_exact_killed_pid(self):
        killed=[];original=os.kill
        def kill(pid,sig):
            killed.append((pid,sig));return original(pid,sig)
        with patch.object(transport.os,'kill',side_effect=kill):
            with self.assertRaises(transport.Refused):
                transport.isolated_exchange(transport.manifest(T)[0],T,dependencies_factory=factory_for(fault='dns_hang'),timeout_ns=50_000_000)
        self.assertEqual(len(killed),1)
        self.assertEqual(killed[0][1],signal.SIGKILL)
        with self.assertRaises(ChildProcessError):os.waitpid(killed[0][0],os.WNOHANG)


if __name__=='__main__':unittest.main()
