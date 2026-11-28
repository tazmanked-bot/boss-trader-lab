"""Deterministic Debian hierarchy fixtures. No system writes, cgroup creation or build."""
import copy
import unittest
from unittest.mock import patch
from research import memory_headroom_037 as m, portable_runtime_036 as p, controlled_build_037 as b

G=1024**3
ROOT='/sys/fs/cgroup'


class Hierarchy:
    def __init__(self,process='/user.slice/session.scope'):
        self.files={'/proc/meminfo':'MemTotal: 6000000 kB\nMemAvailable: 5678440 kB\n',
                    '/proc/self/cgroup':'0::'+process+'\n',
                    '/proc/self/mountinfo':'29 23 0:26 / /sys/fs/cgroup rw,nosuid,nodev,noexec - cgroup2 cgroup rw,nsdelegate\n',
                    ROOT+'/cgroup.controllers':'cpuset cpu io memory hugetlb pids\n',
                    ROOT+'/cgroup.type':'domain\n',ROOT+'/cgroup.subtree_control':'cpu memory pids\n'}
        self.node('/user.slice');self.node('/user.slice/session.scope');self.node('/build.slice')
    def node(self,name,maximum='max',high='max',current=0):
        root=ROOT+name
        self.files.update({root+'/cgroup.type':'domain\n',root+'/cgroup.subtree_control':'cpu memory pids\n',
                           root+'/memory.max':str(maximum)+'\n',root+'/memory.high':str(high)+'\n',root+'/memory.current':str(current)+'\n'})
    def read(self,path):
        value=self.files.get(path)
        if value is None:raise FileNotFoundError(path)
        if isinstance(value,Exception):raise value
        return value
    def snapshot(self,parent=ROOT+'/build.slice'):return m.snapshot(parent,reader=self.read)


class HeadroomTests(unittest.TestCase):
    def test_reported_debian_root_absence_unlimited_delegation(self):
        h=Hierarchy();r=h.snapshot()
        self.assertEqual(r['status'],'PASS');self.assertEqual(r['available_bytes'],5678440*1024)
        self.assertGreater(r['available_bytes'],4*G)
        self.assertTrue(any(e['state']=='HIERARCHY_ROOT_NO_MEMORY_INTERFACES' for e in r['limits'] if 'state' in e))
    def test_process_root_without_memory_files_is_not_zero(self):
        r=Hierarchy(process='/').snapshot()
        self.assertEqual(r['status'],'PASS');self.assertEqual(r['available_bytes'],5678440*1024)
    def test_finite_process_limit_applies(self):
        h=Hierarchy();h.node('/user.slice/session.scope',maximum=5*G,current=2*G)
        self.assertEqual(h.snapshot()['available_bytes'],3*G)
    def test_finite_process_ancestor_applies_with_unlimited_leaf(self):
        h=Hierarchy();h.node('/user.slice',maximum=5*G,current=2*G)
        self.assertEqual(h.snapshot()['available_bytes'],3*G)
    def test_finite_build_parent_applies_when_not_process_ancestor(self):
        h=Hierarchy();h.node('/build.slice',maximum=5*G,current=2*G)
        self.assertEqual(h.snapshot()['available_bytes'],3*G)
    def test_build_ancestor_high_limit_is_conservative(self):
        h=Hierarchy();h.node('/build.slice',high=5*G,current=2*G);h.node('/build.slice/delegated')
        self.assertEqual(h.snapshot(ROOT+'/build.slice/delegated')['available_bytes'],3*G)
    def test_shared_ancestors_checked_once(self):
        h=Hierarchy();h.node('/user.slice/build');r=h.snapshot(ROOT+'/user.slice/build')
        paths=[e['path'] for e in r['limits']];self.assertEqual(len(paths),len(set(paths)))
    def test_kernel_availability_remains_upper_bound(self):
        h=Hierarchy();h.files['/proc/meminfo']='MemAvailable: 1048576 kB\n'
        self.assertEqual(h.snapshot()['available_bytes'],G)
    def test_limit_below_current_clamps_to_zero(self):
        h=Hierarchy();h.node('/build.slice',maximum=G,current=2*G)
        self.assertEqual(h.snapshot()['available_bytes'],0)
    def test_nonroot_missing_enabled_interfaces_holds(self):
        h=Hierarchy()
        for name in ('max','high','current'):h.files.pop(ROOT+'/build.slice/memory.'+name)
        r=h.snapshot();self.assertEqual(r['status'],'HOLD');self.assertIn('MISSING_ENABLED',r['reason'])
    def test_nonroot_controller_not_enabled_checks_ancestors(self):
        h=Hierarchy();h.node('/user.slice',maximum=5*G,current=2*G)
        for name in ('max','high','current'):h.files.pop(ROOT+'/user.slice/session.scope/memory.'+name)
        h.files[ROOT+'/user.slice/cgroup.subtree_control']='cpu pids\n'
        self.assertEqual(h.snapshot()['available_bytes'],3*G)
    def test_missing_nonroot_directory_never_assumed_unlimited(self):
        r=Hierarchy().snapshot(ROOT+'/missing');self.assertEqual(r['status'],'HOLD')
    def test_permission_denied_fails_closed_even_at_root(self):
        h=Hierarchy();h.files[ROOT+'/memory.max']=PermissionError('denied')
        self.assertEqual(h.snapshot()['status'],'HOLD')
    def test_partial_interface_fails_closed(self):
        h=Hierarchy();h.files.pop(ROOT+'/build.slice/memory.current')
        self.assertEqual(h.snapshot()['status'],'HOLD')
    def test_invalid_negative_nan_empty_limit_or_usage_fails(self):
        for name,value in (('max','-1'),('high','NaN'),('current',''),('max',str(2**64))):
            h=Hierarchy();h.files[ROOT+'/build.slice/memory.'+name]=value
            with self.subTest(name=name,value=value):self.assertEqual(h.snapshot()['status'],'HOLD')
    def test_missing_or_wrong_memavailable_units_holds(self):
        for value in ('MemTotal: 6000000 kB\n','MemAvailable: 5678440 B\n','MemAvailable: -1 kB\n'):
            h=Hierarchy();h.files['/proc/meminfo']=value
            with self.subTest(value=value):self.assertEqual(h.snapshot()['status'],'HOLD')
    def test_cgroup_v1_or_ambiguous_membership_holds(self):
        for value in ('2:memory:/user.slice\n','0::/\n0::/user.slice\n'):
            h=Hierarchy();h.files['/proc/self/cgroup']=value
            with self.subTest(value=value):self.assertEqual(h.snapshot()['status'],'HOLD')
    def test_hidden_mount_ancestors_hold(self):
        h=Hierarchy();h.files['/proc/self/mountinfo']='29 23 0:26 /user.slice /sys/fs/cgroup rw - cgroup2 cgroup rw\n'
        self.assertEqual(h.snapshot()['reason'],'CGROUP_ANCESTORS_NOT_VISIBLE')
    def test_outside_build_path_and_traversal_hold(self):
        for value in ('/tmp/not-cgroup','/sys/fs/cgroup/../other','relative',5):
            with self.subTest(value=value):self.assertEqual(Hierarchy().snapshot(value)['status'],'HOLD')
    def test_controller_unavailable_holds(self):
        h=Hierarchy();h.files[ROOT+'/cgroup.controllers']='cpu pids\n'
        self.assertEqual(h.snapshot()['reason'],'MEMORY_CONTROLLER_UNAVAILABLE')
    def test_scope_migration_mid_measurement_holds(self):
        h=Hierarchy();calls=[0]
        def reader(path):
            if path=='/proc/self/cgroup':
                calls[0]+=1
                if calls[0]>1:return '0::/different\n'
            return h.read(path)
        r=m.snapshot(ROOT+'/build.slice',reader=reader)
        self.assertEqual(r['reason'],'CGROUP_SCOPE_CHANGED')
    def test_limit_change_mid_read_holds(self):
        h=Hierarchy();calls=[0]
        def reader(path):
            if path==ROOT+'/build.slice/memory.max':
                calls[0]+=1
                if calls[0]>1:return str(G)
            return h.read(path)
        self.assertEqual(m.snapshot(ROOT+'/build.slice',reader=reader)['reason'],'MEMORY_LIMIT_CHANGED')
    def test_036_wrapper_is_backward_compatible_and_fail_closed(self):
        with patch.object(m,'snapshot',return_value={'available_bytes':123}) as mock:
            self.assertEqual(p.resources(),123);mock.assert_called_once_with(None)
    def test_budget_uses_build_path_and_exact_4g_boundary(self):
        plan={'limits':b.LIMITS,'config':{'cgroup_parent':ROOT+'/build.slice'},'job':'/synthetic'}
        for value,passed in ((4*G,True),(4*G-1,False),(3*G,False)):
            with self.subTest(value=value),patch.object(m,'snapshot',return_value={'status':'PASS','available_bytes':value}) as mock,patch.object(p,'compatibility'),patch('shutil.disk_usage',return_value=type('D',(),{'free':10*G})()):
                if passed:b.budget_check(plan)
                else:
                    with self.assertRaisesRegex(ValueError,'RAM_HEADROOM_HOLD'):b.budget_check(plan)
                mock.assert_called_once_with(ROOT+'/build.slice')
        self.assertEqual(b.LIMITS['memory_max_bytes'],3*G);self.assertEqual(b.LIMITS['available_ram_min_bytes'],4*G)


    def test_escaped_mountpoint_is_resolved(self):
        h=Hierarchy();point='/sys/fs/cgroup space'
        h.files={key.replace(ROOT,point):value for key,value in h.files.items()}
        h.files['/proc/self/mountinfo']='29 23 0:26 / /sys/fs/cgroup\\040space rw - cgroup2 cgroup rw\n'
        r=m.snapshot(point+'/build.slice',reader=h.read)
        self.assertEqual(r['status'],'PASS');self.assertEqual(r['available_bytes'],5678440*1024)
    def test_ambiguous_mounts_fail_closed(self):
        h=Hierarchy();h.files['/proc/self/mountinfo']*=2
        self.assertEqual(h.snapshot()['reason'],'AMBIGUOUS_CGROUP_MOUNT')
    def test_malformed_mount_metadata_fails_closed(self):
        for value in ('29 - \n','29 - cgroup2 cgroup rw\n'):
            h=Hierarchy();h.files['/proc/self/mountinfo']=value
            with self.subTest(value=value):self.assertEqual(h.snapshot()['status'],'HOLD')
    def test_unreadable_current_and_high_fail_closed(self):
        for name in ('current','high'):
            h=Hierarchy();h.files[ROOT+'/build.slice/memory.'+name]=PermissionError('denied')
            with self.subTest(name=name):self.assertEqual(h.snapshot()['status'],'HOLD')
    def test_zero_high_and_duplicate_memavailable_cannot_pass(self):
        h=Hierarchy();h.node('/build.slice',high=0,current=0)
        self.assertEqual(h.snapshot()['available_bytes'],0)
        h=Hierarchy();h.files['/proc/meminfo']+='MemAvailable: 9999999 kB\n'
        self.assertEqual(h.snapshot()['status'],'HOLD')

    def test_namespace_root_interfaces_do_not_hide_unknown_outer_limits(self):
        h=Hierarchy()
        h.files.update({ROOT+'/memory.max':'max',ROOT+'/memory.high':'max',ROOT+'/memory.current':'0'})
        self.assertEqual(h.snapshot()['reason'],'CGROUP_NAMESPACE_ROOT_REVIEW_REQUIRED')

    def test_existing_benign_config_path_spelling_remains_compatible(self):
        for value in (ROOT+'/build.slice/',ROOT+'/./build.slice','//sys/fs/cgroup/build.slice'):
            with self.subTest(value=value):self.assertEqual(Hierarchy().snapshot(value)['available_bytes'],5678440*1024)


class PreflightTests(unittest.TestCase):
    def test_read_only_survey_preserves_config_and_inventory_and_lists_multiple_holds(self):
        import json,os,tempfile,time
        from pathlib import Path
        old=os.umask(0o077)
        try:
            with tempfile.TemporaryDirectory(dir=Path(__file__).parent) as directory:
                root=Path(directory).resolve();tools=root/'tools.json';system=root/'system.json';health=root/'health.json'
                tools.write_text(json.dumps({'packages':{'inert':'0'},'licenses':{'inert':'original'},'review_ref':'SYNTHETIC_ONLY'}));system.write_text('{}')
                health.write_text(json.dumps({'version':'external-recorder-health-037-v1','recorder_id':'inert',
                    'measured_at':int(time.time()),'last_collection_at':int(time.time()),'healthy':True,'desktop_stable':True}))
                config={'source':'/inert-original-source','job':str(root/'new-job'),'protected_roots':['/inert-recorder'],
                        'cgroup_parent':ROOT,'health_file':str(health),'recorder_id':'inert','collection_cadence_seconds':60,
                        'toolchain_evidence':str(tools),'system_libraries':str(system)}
                before=copy.deepcopy(config);files={p.name:p.read_bytes() for p in root.iterdir()}
                with patch.object(m,'snapshot',return_value=Hierarchy().snapshot()),patch.object(p,'compatibility',return_value={'synthetic':True}),patch.object(b,'tools_inventory',side_effect=ValueError('MISSING_TEST_TOOL')),patch.object(b,'validate_system',return_value={}),patch.object(b.subprocess,'Popen',side_effect=AssertionError('must not execute')):
                    report=b.preflight(config)
                self.assertEqual(report['readiness'],'HOLD');self.assertFalse(report['qualified']);self.assertEqual(report['writes'],0)
                self.assertEqual(report['checks']['memory']['status'],'PASS')
                self.assertEqual(report['checks']['toolchain']['status'],'HOLD');self.assertEqual(report['checks']['delegation_readiness']['status'],'HOLD')
                self.assertEqual(report['checks']['actual_containment']['status'],'UNVERIFIED')
                self.assertEqual(config,before);self.assertEqual({p.name:p.read_bytes() for p in root.iterdir()},files)
        finally:os.umask(old)
    def test_cli_does_not_confuse_ready_survey_with_qualified_containment(self):
        ready={'operation':'READ_ONLY_PREFLIGHT','readiness':'READY_FOR_HARMLESS_QUALIFICATION_REVIEW','qualified':False}
        with patch.object(b,'read_json',return_value={}),patch.object(b,'preflight',return_value=ready),patch('builtins.print'):
            self.assertEqual(b.main(['preflight','--config','/synthetic']),0)
        ready['readiness']='HOLD'
        with patch.object(b,'read_json',return_value={}),patch.object(b,'preflight',return_value=ready),patch('builtins.print'):
            self.assertEqual(b.main(['preflight','--config','/synthetic']),2)


if __name__=='__main__':unittest.main()
