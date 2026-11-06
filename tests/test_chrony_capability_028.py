"""Fake-process contract tests; never execute dpkg-query, chrony or a shell."""
from contextlib import ExitStack,redirect_stdout,redirect_stderr
from dataclasses import replace
import importlib
import io
import json
import stat
import unittest
from unittest.mock import patch

from research import chrony_capability_028 as adapter
from research import utc_evidence_026 as utc


def identities():
    return {path:adapter.FileIdentity(path,1,index+1,stat.S_IFREG|0o755,100,1,1,str(index+1)*64)
            for index,path in enumerate((adapter.DPKG,*adapter.BINARIES))}


def context():
    return dict(origin='SYNTHETIC_CONTEXT',source_head='a'*40,clean=True,os='ubuntu-24.04',python='3.11.17',
                kernel='synthetic-kernel',image='synthetic-image',run_id='synthetic-run',job_id='synthetic-job')


def runs():
    outputs=(b'chrony\tinstall ok installed\t4.6-0synthetic028\tamd64\tchrony\t4.6-0synthetic028\n',
             b'chrony: /usr/sbin/chronyd\nchrony: /usr/bin/chronyc\n',
             b'chronyd (chrony) version 4.6 (+NTP +NTS +IPV6)\n',
             b'chronyc (chrony) version 4.6 (+IPV6)\n')
    return tuple(adapter.FakeRun((adapter.Event(data=raw),)) for raw in outputs)


def backend(values=None,**kwargs):
    return adapter.FakeBackend(runs() if values is None else values,identities(),context=context(),**kwargs)


def review():
    ids=identities()
    return adapter.MockReview('4.6-0synthetic028','4.6-0synthetic028','4.6',tuple(ids[p] for p in adapter.BINARIES))


def execute(model=None,**kwargs):
    return adapter.evaluate_offline(backend() if model is None else model,metadata_opt_in=True,version_opt_in=True,review=review(),**kwargs)


class CapabilityTests(unittest.TestCase):
    def setUp(self):
        stack=ExitStack();self.addCleanup(stack.close)
        guards=[stack.enter_context(patch(name,side_effect=AssertionError('REAL_OPERATION_FORBIDDEN'))) for name in (
            'socket.socket','socket.getaddrinfo','socket.create_connection','urllib.request.urlopen',
            'http.client.HTTPSConnection','subprocess.Popen','subprocess.run','os.system','os.fork','os.execve','time.time')]
        self.addCleanup(lambda:[g.assert_not_called() for g in guards])

    def gates(self,result):
        self.assertEqual(result['overall'],'HOLD');self.assertEqual(result['B4'],'NO-GO')
        self.assertTrue(all(result[k]=='HOLD' for k in ('B1','B2','B3','B5')))
        self.assertEqual(result['provenance'],'AUTHENTIC_PROVENANCE_NOT_COLLECTED')
        self.assertFalse(result['independent_utc']);self.assertEqual(result['live_source_admission'],'HOLD')
        self.assertEqual(result['policy'],'NO ORDERS');self.assertEqual(result['process_launches'],0)
        self.assertEqual(result['requests'],0);self.assertIsNone(result['actual_package_version'])

    def test_default_import_and_all_native_opt_ins_are_zero_effects(self):
        with patch('builtins.open',side_effect=AssertionError),patch('os.open',side_effect=AssertionError),patch('time.monotonic_ns',side_effect=AssertionError):
            importlib.reload(adapter)
            for flags in ({},{'metadata':True},{'versions':True},{'metadata':True,'versions':True}):
                result=adapter.disabled(**flags);self.gates(result)
            self.gates(adapter.evaluate_offline())
            for options in ([],['--metadata'],['--versions'],['--metadata','--versions'],['--plan']):
                with patch('sys.argv',['adapter',*options]),redirect_stdout(io.StringIO()) as out:
                    self.assertEqual(adapter.main(),2)
                self.gates(json.loads(out.getvalue()))

    def test_exact_fixed_plan_environment_and_launch_contract(self):
        commands=adapter.plan();self.assertEqual(len(commands),4)
        self.assertEqual(commands[0].argv,(adapter.DPKG,'--no-pager','--show','--showformat='+adapter.FORMAT,'chrony'))
        self.assertEqual(commands[1].argv,(adapter.DPKG,'--no-pager','--search',*adapter.BINARIES))
        for index,c in enumerate(commands):
            adapter.check_command(index,c);self.assertEqual(dict(c.env),{'LC_ALL':'C','LANG':'C','DPKG_COLORS':'never'})
            self.assertEqual(c.cwd,'/');self.assertEqual(c.stdin,'DEVNULL');self.assertTrue(c.close_fds)
            self.assertFalse(c.shell);self.assertTrue(c.new_session)
            self.assertNotIn('PATH',dict(c.env));self.assertNotIn('LD_PRELOAD',dict(c.env))
        self.assertEqual(commands[2].argv,('/usr/sbin/chronyd','--version'))
        self.assertEqual(commands[3].argv,('/usr/bin/chronyc','--version'))

    def test_argv_path_argument_environment_shell_injection_refused(self):
        original=adapter.plan()[2]
        changed=[replace(original,argv=('/tmp/chronyd','--version')),replace(original,argv=('/usr/sbin/chronyd','-Q')),
                 replace(original,argv=('/usr/sbin/chronyd','--version','--server=bad')),
                 replace(original,env=(('LD_PRELOAD','bad'),)),replace(original,cwd='/tmp'),replace(original,shell=True),
                 replace(original,close_fds=False),replace(original,stdin='INHERIT')]
        for command in changed:
            with self.subTest(command=command),self.assertRaisesRegex(adapter.Refused,'COMMAND_REFUSED'):adapter.check_command(2,command)
        with self.assertRaises(adapter.Refused):adapter.check_command(True,original)

    def test_cli_has_no_arbitrary_command_path_or_traffic_option(self):
        for argument in ('--live','--command=chronyd','--path=/tmp/x','--env=LD_PRELOAD','--query'):
            with self.subTest(argument=argument),patch('sys.argv',['adapter',argument]),redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):adapter.main()

    def test_fake_positive_is_not_native_evidence(self):
        result=execute();self.gates(result)
        self.assertEqual(result['fake_launches'],4);self.assertEqual(result['model_status'],'FAKE_VERSION_RECIPE_PASSED')
        self.assertEqual(result['model_package']['provenance'],'LOCAL_METADATA_ONLY')
        self.assertEqual(result['model_versions'][adapter.BINARIES[0]]['nts_flag'],'CLIENT_REPORTED_NTS_BUILD_FLAG')
        self.assertEqual(result['model_versions'][adapter.BINARIES[1]]['nts_flag'],'UNKNOWN')
        self.assertLess(len(json.dumps(result)),adapter.REPORT_BYTES)
        self.assertEqual(utc.authentic_verifier()['B4'],'NO-GO')

    def test_metadata_opt_in_does_not_imply_version_opt_in(self):
        model=backend();result=adapter.evaluate_offline(model,metadata_opt_in=True)
        self.gates(result);self.assertEqual(result['fake_launches'],2)
        self.assertEqual(result['model_status'],'METADATA_SHAPE_VALID')
        self.assertEqual(len(model.cleanup),2)

    def test_no_factory_or_true_marker_can_enable_native_execution(self):
        for model in (None,True,lambda *a:True,{'contained':True}):
            result=adapter.evaluate_offline(model,metadata_opt_in=True,version_opt_in=True)
            self.gates(result);self.assertEqual(result['reason'],'REAL_EXECUTION_BLOCKED')

    def test_package_required_installed_status_and_exact_owner(self):
        for raw,reason in [(b'', 'PACKAGE_METADATA_INVALID'),
            (b'chrony\tdeinstall ok config-files\t4.6\tamd64\tchrony\t4.6\n','PACKAGE_NOT_INSTALLED'),
            (b'other\tinstall ok installed\t4.6\tamd64\tchrony\t4.6\n','PACKAGE_MISMATCH'),
            (b'chrony\tinstall ok installed\t4.6\tarm64\tchrony\t4.6\n','ARCHITECTURE_UNREVIEWED'),
            (b'chrony\tinstall ok installed\t\tamd64\tchrony\t4.6\n','PACKAGE_VERSION_UNKNOWN')]:
            values=list(runs());values[0]=adapter.FakeRun((adapter.Event(data=raw),))
            model=backend(tuple(values));result=execute(model);self.gates(result)
            self.assertEqual(result['reason'],reason);self.assertEqual(result['fake_launches'],1)

    def test_unknown_unreviewed_installed_version_stops_before_version_binary(self):
        result=adapter.evaluate_offline(backend(),metadata_opt_in=True,version_opt_in=True)
        self.assertEqual(result['reason'],'BUILD_UNREVIEWED');self.assertEqual(result['fake_launches'],2)
        values=list(runs());values[0]=adapter.FakeRun((adapter.Event(data=b'chrony\tinstall ok installed\t4.5-1ubuntu4.2\tamd64\tchrony\t4.5-1ubuntu4.2\n'),))
        result=execute(backend(tuple(values)))
        self.assertEqual(result['reason'],'BUILD_UNREVIEWED');self.assertEqual(result['fake_launches'],2)

    def test_unowned_diverted_duplicate_or_additional_paths_refuse(self):
        for raw in (b'other: /usr/sbin/chronyd\nchrony: /usr/bin/chronyc\n',
                    b'chrony: /usr/bin/chronyc\nchrony: /usr/bin/chronyc\n',
                    b'local diversion: /usr/sbin/chronyd\nchrony: /usr/bin/chronyc\n',
                    b'chrony, other: /usr/sbin/chronyd\nchrony: /usr/bin/chronyc\n'):
            values=list(runs());values[1]=adapter.FakeRun((adapter.Event(data=raw),))
            result=execute(backend(tuple(values)));self.gates(result)
            self.assertEqual(result['fake_launches'],2);self.assertEqual(result['model_status'],'REFUSED')

    def test_symlink_setid_or_file_capability_identity_refuses_before_launch(self):
        for change in ({'mode':stat.S_IFLNK|0o777},{'mode':stat.S_IFREG|0o4755},{'capabilities':'CAP_SYS_TIME'}):
            ids=identities();ids[adapter.BINARIES[0]]=replace(ids[adapter.BINARIES[0]],**change)
            model=adapter.FakeBackend(runs(),ids,context=context());result=execute(model)
            self.assertEqual(result['reason'],'IDENTITY_UNSAFE');self.assertEqual(result['fake_launches'],0)

    def test_replacement_or_digest_mismatch_before_and_after_version_refuses(self):
        base=identities()[adapter.BINARIES[0]]
        changed=replace(base,inode=12345,sha256='9'*64)
        # Calls: initial, pre-version, pre-launch, post-exit.
        for sequence,count in [((base,changed),2),((base,base,changed),2),((base,base,base,changed),3)]:
            model=backend(snapshots={adapter.BINARIES[0]:sequence});result=execute(model)
            self.assertEqual(result['reason'],'IDENTITY_CHANGED');self.assertEqual(result['fake_launches'],count)
        wrong=replace(review(),identities=(changed,identities()[adapter.BINARIES[1]]))
        result=adapter.evaluate_offline(backend(),metadata_opt_in=True,version_opt_in=True,review=wrong)
        self.assertEqual(result['reason'],'BUILD_UNREVIEWED');self.assertEqual(result['fake_launches'],2)

    def test_metadata_tool_replacement_refuses(self):
        base=identities()[adapter.DPKG]
        model=backend(snapshots={adapter.DPKG:(base,base,replace(base,mtime_ns=10))})
        result=execute(model);self.assertEqual(result['reason'],'IDENTITY_CHANGED');self.assertEqual(result['fake_launches'],1)

    def test_negative_missing_contradictory_or_wrong_version_banner(self):
        cases=[(b'chronyd (chrony) version 4.6 (-NTS)\n','NTS_BUILD_FLAG_UNSUPPORTED_OR_UNKNOWN'),
               (b'chronyd (chrony) version 4.6 (+IPV6)\n','NTS_BUILD_FLAG_UNSUPPORTED_OR_UNKNOWN'),
               (b'chronyd (chrony) version 4.6 (+NTS -NTS)\n','NTS_BUILD_FLAG_UNSUPPORTED_OR_UNKNOWN'),
               (b'chronyd (chrony) version 9.9 (+NTS)\n','VERSION_MISMATCH'),(b'green +NTS','VERSION_BANNER_INVALID')]
        for raw,reason in cases:
            values=list(runs());values[2]=adapter.FakeRun((adapter.Event(data=raw),))
            result=execute(backend(tuple(values)));self.assertEqual(result['reason'],reason)
            self.assertEqual(result['fake_launches'],3);self.gates(result)

    def test_overflow_is_checked_while_streaming_combined_output(self):
        values=list(runs());values[0]=adapter.FakeRun((adapter.Event(data=b'a'*12000),adapter.Event(channel='stderr',data=b'b'*5000)))
        model=backend(tuple(values));result=execute(model)
        self.assertEqual(result['reason'],'OUTPUT_OVERFLOW');self.assertEqual(result['fake_launches'],1)
        self.assertEqual(result['receipts'][0]['bytes'],12000)
        self.assertTrue(model.cleanup[0]['kill_owned_group'])

    def test_hang_timeout_kill_group_reap_and_no_next_command(self):
        for index in range(4):
            values=list(runs());values[index]=adapter.FakeRun(hang=True)
            model=backend(tuple(values));result=execute(model)
            self.assertEqual(result['reason'],'TIMEOUT');self.assertEqual(result['fake_launches'],index+1)
            self.assertTrue(model.cleanup[-1]['kill_owned_group']);self.assertTrue(model.cleanup[-1]['reap_exact_child'])
            self.assertLessEqual(result['receipts'][-1]['elapsed_ns'],adapter.CHILD_NS)

    def test_excessive_launch_cannot_claim_per_child_deadline_success(self):
        values=list(runs());values[0]=replace(values[0],launch_ns=3*adapter.NS)
        result=execute(backend(tuple(values)));self.assertEqual(result['reason'],'TIMEOUT')
        self.assertTrue(result['receipts'][0]['child_budget_exceeded']);self.assertEqual(result['fake_launches'],1)

    def test_nonzero_signal_and_stderr_refuse_redacted(self):
        for status in (1,-9):
            values=list(runs());values[0]=adapter.FakeRun((adapter.Event(channel='stderr',data=b'SECRET'),),exit_status=status)
            result=execute(backend(tuple(values)));self.gates(result)
            self.assertEqual(result['reason'],'PROCESS_SIGNAL' if status<0 else 'PROCESS_NONZERO')
            self.assertNotIn('SECRET',json.dumps(result));self.assertEqual(result['fake_launches'],1)
        values=list(runs());values[0]=adapter.FakeRun((adapter.Event(channel='stderr',data=b'SECRET'),))
        result=execute(backend(tuple(values)));self.assertEqual(result['reason'],'STDERR_REFUSED')

    def test_uncertain_reap_descendants_or_cleanup_latency_is_stop(self):
        for change in ({'reaped':False},{'group_empty':False},{'cleanup_ns':adapter.CLEANUP_NS+1}):
            values=list(runs());values[0]=replace(values[0],**change)
            model=backend(tuple(values));result=execute(model)
            self.assertEqual(result['reason'],'CLEANUP_UNCERTAIN_STOP');self.assertEqual(result['fake_launches'],1)
            self.assertEqual(result['receipts'][0]['cleanup'],'UNCERTAIN')

    def test_root_context_missing_or_wrong_target_does_not_launch(self):
        self.assertEqual(execute(backend(root=True))['reason'],'PRIVILEGE_REFUSED')
        for field,value in [('clean',False),('source_head','not-sha'),('os','debian'),('python','3.12.14')]:
            ctx=context();ctx[field]=value
            model=adapter.FakeBackend(runs(),identities(),context=ctx)
            result=execute(model);self.assertEqual(result['fake_launches'],0);self.gates(result)

    def test_fake_context_is_single_use_and_has_at_most_four_children(self):
        model=backend();execute(model);result=execute(model)
        self.assertEqual(result['reason'],'FAKE_CONTEXT_REUSED');self.assertEqual(result['fake_launches'],4)
        with self.assertRaises(adapter.Refused):adapter.FakeBackend(runs()+runs(),identities())

    def test_stream_event_limit_and_aggregate_budget_stop(self):
        values=list(runs());values[0]=adapter.FakeRun(tuple(adapter.Event(delta_ns=1) for _ in range(adapter.MAX_EVENTS+1)))
        result=execute(backend(tuple(values)));self.assertEqual(result['reason'],'STREAM_EVENT_LIMIT')
        original=adapter._process
        def advance(model,index,deadline,identity,receipts):
            value=original(model,index,deadline,identity,receipts)
            model.now=deadline
            return value
        with patch.object(adapter,'_process',side_effect=advance):result=execute()
        self.assertEqual(result['fake_launches'],1);self.assertEqual(result['reason'],'TIMEOUT')

    def test_no_environment_or_raw_error_fields_are_reflected(self):
        ctx=context();ctx['SECRET_TOKEN']='DO_NOT_PRINT'
        result=execute(adapter.FakeBackend(runs(),identities(),context=ctx))
        self.assertEqual(result['reason'],'CONTEXT_UNVERIFIED');self.assertNotIn('DO_NOT_PRINT',json.dumps(result))


if __name__=='__main__':unittest.main()
