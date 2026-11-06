"""Deterministic proof policy tests; no crypto or independent UTC claim."""
import copy
from contextlib import ExitStack
import json
import unittest
from unittest.mock import patch
from research import utc_evidence_026 as utc


def binding():return utc.Binding('a'*40,'offline-run','b'*64,'c'*64)
def window(**changes):
    fields=dict(send_mono=1_000_000_000,recv_mono=1_100_000_000,send_boot=2_000_000_000,
                recv_boot=2_100_000_000,now_mono=1_100_000_000,now_boot=2_100_000_000,boot='b'*64)
    fields.update(changes);return utc.Window(**fields)
def envelope(**changes):
    value=dict(version='utc-envelope-model-v1',authority='NOT_A_TIME_AUTHORITY',key_id='NO_REAL_KEY',
               algorithm='MOCK_ONLY',revision='a'*40,run='offline-run',boot='b'*64,nonce='c'*64,
               utc_ns=1900000802000000000,accuracy_ns=100_000_000,lease_ns=10*utc.NS,
               signature='MOCK_SIGNATURE_NOT_CRYPTOGRAPHY')
    value.update(changes);return value
def enroll(model=None,value=None,stamp=None,verifier=None):
    model=utc.EnvelopeModel(binding()) if model is None else model
    value=envelope() if value is None else value
    verifier=utc.MockSignature(utc.canonical({k:v for k,v in value.items() if k!='signature'})) if verifier is None else verifier
    return model.enroll(utc.canonical(value),window() if stamp is None else stamp,signature_verifier=verifier)


class UTCModelTests(unittest.TestCase):
    def setUp(self):
        stack=ExitStack();self.addCleanup(stack.close)
        for name in ('socket.socket','socket.getaddrinfo','socket.create_connection','urllib.request.urlopen',
                     'subprocess.Popen','time.time','time.monotonic_ns','builtins.open'):
            stack.enter_context(patch(name,side_effect=AssertionError('FORBIDDEN_IO')))

    def test_default_authentic_adapter_always_disabled(self):
        self.assertEqual(utc.authentic_verifier(envelope(),trusted=True)['B4'],'NO-GO')
        self.assertFalse(utc.authentic_verifier()['independent_utc'])
        with self.assertRaisesRegex(utc.Refused,'AUTHORITY_ADAPTER_DISABLED'):
            utc.EnvelopeModel(binding()).enroll(utc.canonical(envelope()),window())

    def test_success_is_only_mock_arithmetic_not_independent_time(self):
        result=enroll()
        self.assertEqual(result['B4'],'NO-GO');self.assertEqual(result['live_admission'],'HOLD')
        self.assertFalse(result['independent_utc'])
        self.assertEqual(result['initial_uncertainty_ns'],152005000)
        self.assertEqual(result['utc_low_ns'],envelope()['utc_ns']-102_000_000)
        self.assertEqual(result['utc_high_ns'],envelope()['utc_ns']+202_010_000)

    def test_growth_uses_ceil_and_never_assumes_symmetric_delay(self):
        model=utc.EnvelopeModel(binding());initial=enroll(model)
        grown=model.estimate(window(now_mono=2_100_000_001,now_boot=3_100_000_001))
        self.assertGreater(grown['uncertainty_ns'],initial['uncertainty_ns'])
        self.assertEqual(grown['uncertainty_ns']-initial['uncertainty_ns'],100001)

    def test_each_binding_field_is_required(self):
        for key,value in (('revision','d'*40),('run','different'),('boot','d'*64),('nonce','d'*64)):
            with self.subTest(key=key),self.assertRaisesRegex(utc.Refused,'BINDING_MISMATCH'):enroll(value=envelope(**{key:value}))

    def test_replay_or_conflicting_second_envelope_is_rejected(self):
        for value in (envelope(),envelope(utc_ns=envelope()['utc_ns']+1)):
            model=utc.EnvelopeModel(binding());enroll(model)
            with self.assertRaisesRegex(utc.Refused,'REPLAY_OR_CONFLICT'):enroll(model,value)

    def test_failed_signature_burns_challenge(self):
        model=utc.EnvelopeModel(binding())
        with self.assertRaisesRegex(utc.Refused,'FORGED_MOCK_EVIDENCE'):
            enroll(model,value=envelope(signature='forged'))
        with self.assertRaisesRegex(utc.Refused,'REPLAY_OR_CONFLICT'):enroll(model)

    def test_forged_contents_do_not_match_fixed_mock_fixture(self):
        original=envelope();verifier=utc.MockSignature(utc.canonical({k:v for k,v in original.items() if k!='signature'}))
        with self.assertRaisesRegex(utc.Refused,'FORGED_MOCK_EVIDENCE'):enroll(value=envelope(utc_ns=1),verifier=verifier)

    def test_boolean_or_callback_cannot_be_a_signature_verifier(self):
        for verifier in (True,lambda *a:True,{'trusted':True}):
            with self.subTest(verifier=type(verifier)),self.assertRaisesRegex(utc.Refused,'AUTHORITY_ADAPTER_DISABLED'):enroll(verifier=verifier)

    def test_stale_at_enrollment_and_expired_lease_invalidate(self):
        with self.assertRaisesRegex(utc.Refused,'LEASE_EXPIRED'):
            enroll(stamp=window(now_mono=11_100_000_000,now_boot=12_100_000_000))
        model=utc.EnvelopeModel(binding());enroll(model)
        with self.assertRaisesRegex(utc.Refused,'LEASE_EXPIRED'):
            model.estimate(window(now_mono=11_100_000_000,now_boot=12_100_000_000))
        with self.assertRaisesRegex(utc.Refused,'NO_ENROLLED_MODEL'):model.estimate(window())

    def test_initial_or_grown_uncertainty_must_not_exceed_two_seconds(self):
        with self.assertRaisesRegex(utc.Refused,'INITIAL_UNCERTAINTY_EXCESSIVE'):enroll(value=envelope(accuracy_ns=2*utc.NS))
        # Initial ~1.999905s passes, later drift growth crosses the unchanged cap.
        model=utc.EnvelopeModel(binding());enroll(model,value=envelope(accuracy_ns=1_947_900_000))
        with self.assertRaisesRegex(utc.Refused,'GROWN_UNCERTAINTY_EXCESSIVE'):
            model.estimate(window(now_mono=3_100_000_000,now_boot=4_100_000_000))

    def test_rollback_during_or_after_capture_refuses(self):
        for stamp in (window(recv_mono=1),window(now_mono=1),window(recv_boot=1)):
            with self.subTest(stamp=stamp),self.assertRaises(utc.Refused):enroll(stamp=stamp)
        model=utc.EnvelopeModel(binding());enroll(model)
        model.estimate(window(now_mono=2_100_000_000,now_boot=3_100_000_000))
        with self.assertRaisesRegex(utc.Refused,'MONOTONIC_ROLLBACK'):model.estimate(window())

    def test_suspend_boot_change_and_window_rebinding_refuse(self):
        for stamp in (window(recv_boot=2_200_000_000,now_boot=2_200_000_000),window(now_boot=4_100_000_000),window(boot='e'*64)):
            with self.subTest(stamp=stamp),self.assertRaises(utc.Refused):enroll(stamp=stamp)
        model=utc.EnvelopeModel(binding());enroll(model)
        with self.assertRaisesRegex(utc.Refused,'WINDOW_REBOUND'):
            model.estimate(window(send_mono=999999999))

    def test_excessive_roundtrip_or_boolean_samples_refuse(self):
        for stamp in (window(send_mono=True),window(recv_mono=4*utc.NS,now_mono=4*utc.NS,recv_boot=5*utc.NS,now_boot=5*utc.NS)):
            with self.subTest(stamp=stamp),self.assertRaises(utc.Refused):enroll(stamp=stamp)

    def test_exact_schema_bounds_and_no_http_date_or_wall_clock_substitutes(self):
        values=[envelope(trusted=True),envelope(algorithm='Ed25519'),envelope(utc_ns=True),envelope(accuracy_ns=-1),
                envelope(lease_ns=0),envelope(lease_ns=utc.MAX_LEASE_NS+1),envelope(signature='x'*129),envelope(nonce='0'),
                {'Date':'Mon, 01 Jan 2024 00:00:00 GMT'}]
        for value in values:
            with self.subTest(value=value),self.assertRaises(utc.Refused):utc.parse(utc.canonical(value))
        for raw in (b'x'*8193,b'{"utc_ns":1,"utc_ns":2}',b'{"x":NaN}',b'\xff',b'[]'):
            with self.subTest(raw=raw[:20]),self.assertRaises(utc.Refused):utc.parse(raw)


if __name__=='__main__':unittest.main()
