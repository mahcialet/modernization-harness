"""架空のテンプレートでローカル更新の境界条件を検査する。"""
from pathlib import Path
import copy
import importlib.util
import json
import os
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('template_tool',ROOT/'tools/template.py')
t=importlib.util.module_from_spec(spec); spec.loader.exec_module(t)

class TemplateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.src=self.root/'source'; self.target=self.root/'target'; self.review=self.root/'review'
        self.manifest={'template_id':'test','template_version':'0.1.0','schema_version':'0.1.0','parameters':{'system_id':{'pattern':'[a-z][a-z0-9-]*'}},'files':[{'path':'AGENTS.md','ownership':'managed'},{'path':'system.yaml','ownership':'seed'}]}
        self.write_template({'AGENTS.md':'名前={{system_id}}\n旧手順\n','system.yaml':'owner: 初期\n'})
        t.init(self.src,{'system_id':'demo'},self.target)
    def write_template(self,files=None):
        self.src.mkdir(exist_ok=True)
        (self.src/'template.json').write_bytes(t.encode(self.manifest))
        for p,data in (files or {}).items():
            dest=self.src/'files'/p; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_text(data,encoding='utf-8')
    def bump(self,files=None):
        self.manifest['template_version']='0.1.1'; self.write_template(files)
    def plan(self): return t.plan_update(self.target,self.src,self.review)
    def apply(self): return t.apply(self.review,(self.review/'plan.sha256').read_text().strip())
    def test_init_and_status(self):
        self.assertIn('名前=demo',(self.target/'AGENTS.md').read_text())
        self.assertTrue(all(x['state']=='unchanged' for x in t.status(self.target)['files']))
    def test_existing_destination_protected(self):
        with self.assertRaises(t.TemplateError): t.init(self.src,{'system_id':'demo'},self.target)
    def test_wrong_variables_rejected(self):
        with self.assertRaises(t.TemplateError): t.read_template(self.src,{'typo':'demo'})
    def test_parameter_validation(self):
        with self.assertRaises(t.TemplateError): t.read_template(self.src,{'system_id':'../../oops'})
    def test_missing_token_rejected(self):
        self.write_template({'AGENTS.md':'{{missing}}'})
        with self.assertRaises(t.TemplateError): t.read_template(self.src,{'system_id':'demo'})
    def test_update_and_seed_preserved(self):
        (self.target/'system.yaml').write_text('owner: 個別\n')
        self.bump({'AGENTS.md':'名前={{system_id}}\n新手順\n','system.yaml':'owner: 新雛形\n'})
        self.plan(); self.apply()
        self.assertIn('新手順',(self.target/'AGENTS.md').read_text())
        self.assertEqual((self.target/'system.yaml').read_text(),'owner: 個別\n')
        self.assertEqual(t.status(self.target)['template_version'],'0.1.1')
    def test_local_managed_change_preserved(self):
        (self.target/'AGENTS.md').write_text('独自変更\n')
        self.bump(); self.plan(); self.apply()
        self.assertEqual((self.target/'AGENTS.md').read_text(),'独自変更\n')
    def test_both_changed_conflict(self):
        (self.target/'AGENTS.md').write_text('独自変更\n')
        self.bump({'AGENTS.md':'新しい共通内容\n'}); p=self.plan()
        self.assertEqual(next(a for a in p['actions'] if a['path']=='AGENTS.md')['action'],'conflict')
        with self.assertRaises(t.TemplateError): self.apply()
    def test_resolve_keep_local(self):
        (self.target/'AGENTS.md').write_text('独自変更\n')
        self.bump({'AGENTS.md':'新しい共通内容\n'}); self.plan()
        t.resolve(self.review,'AGENTS.md','keep-local',None); self.apply()
        self.assertEqual((self.target/'AGENTS.md').read_text(),'独自変更\n')
    def test_resolve_incoming(self):
        (self.target/'AGENTS.md').write_text('独自変更\n')
        self.bump({'AGENTS.md':'新しい共通内容\n'}); self.plan()
        t.resolve(self.review,'AGENTS.md','use-incoming',None); self.apply()
        self.assertEqual((self.target/'AGENTS.md').read_text(),'新しい共通内容\n')
    def test_resolve_file(self):
        (self.target/'AGENTS.md').write_text('独自変更\n')
        self.bump({'AGENTS.md':'新しい共通内容\n'}); self.plan()
        merged=self.root/'merged.md'; merged.write_text('レビュー済み統合\n')
        t.resolve(self.review,'AGENTS.md','file',merged); self.apply()
        self.assertEqual((self.target/'AGENTS.md').read_text(),'レビュー済み統合\n')
    def test_stale_approval_rejected(self):
        self.bump({'AGENTS.md':'新内容\n'}); self.plan()
        with self.assertRaises(t.TemplateError): t.apply(self.review,'0'*64)
    def test_target_changed_after_plan(self):
        self.bump({'AGENTS.md':'新内容\n'}); self.plan()
        (self.target/'AGENTS.md').write_text('計画後に変更\n')
        with self.assertRaises(t.TemplateError): self.apply()
    def test_candidate_tampering(self):
        self.bump({'AGENTS.md':'新内容\n'}); self.plan()
        (self.review/'candidate/AGENTS.md').write_text('改変\n')
        with self.assertRaises(t.TemplateError): self.apply()
    def test_incoming_tampering(self):
        self.bump({'AGENTS.md':'新内容\n'}); self.plan()
        (self.review/'incoming/system.yaml').write_text('改変\n')
        with self.assertRaises(t.TemplateError): self.apply()
    def test_baseline_tampering(self):
        lock=json.loads((self.target/t.LOCK).read_text())
        (self.target/lock['base_dir']/'AGENTS.md').write_text('改変\n')
        with self.assertRaises(t.TemplateError): t.status(self.target)
    def test_same_version_different_content(self):
        self.write_template({'AGENTS.md':'同版改変\n'})
        with self.assertRaises(t.TemplateError): self.plan()
    def test_downgrade_rejected(self):
        self.manifest['template_version']='0.0.9'; self.write_template()
        with self.assertRaises(t.TemplateError): self.plan()
    def test_schema_migration_explicit(self):
        self.manifest['schema_version']='1.0.0'; self.bump()
        with self.assertRaises(t.TemplateError): self.plan()
    def test_new_file_and_delete(self):
        self.manifest['files']=[{'path':'new.md','ownership':'managed'},{'path':'system.yaml','ownership':'seed'}]
        self.bump({'new.md':'追加\n'}); self.plan(); self.apply()
        self.assertFalse((self.target/'AGENTS.md').exists())
        self.assertTrue((self.target/'new.md').exists())
    def test_deleted_upstream_modified_local_conflict(self):
        (self.target/'AGENTS.md').write_text('個別\n')
        self.manifest['files']=self.manifest['files'][1:]; self.bump(); self.plan()
        with self.assertRaises(t.TemplateError): self.apply()
    def test_seed_to_managed_conflict(self):
        self.manifest['files'][1]['ownership']='managed'; self.bump(); self.plan()
        with self.assertRaises(t.TemplateError): self.apply()
    def test_unmanaged_record_preserved(self):
        rec=self.target/'record.md'; rec.write_text('調査履歴\n')
        self.bump({'AGENTS.md':'新内容\n'}); self.plan(); self.apply()
        self.assertEqual(rec.read_text(),'調査履歴\n')
    def test_traversal_rejected(self):
        self.manifest['files'][0]['path']='../escape'; self.write_template()
        with self.assertRaises(t.TemplateError): t.read_template(self.src,{'system_id':'demo'})
    def test_reserved_path_rejected(self):
        self.manifest['files'][0]['path']='.git/config'; self.write_template()
        with self.assertRaises(t.TemplateError): t.read_template(self.src,{'system_id':'demo'})
    def test_casefold_duplicate_rejected(self):
        self.manifest['files'].append({'path':'agents.md','ownership':'managed'}); self.write_template({'agents.md':'衝突'})
        with self.assertRaises(t.TemplateError): t.read_template(self.src,{'system_id':'demo'})
    @unittest.skipIf(os.name=='nt','Windowsのsymlink権限に依存するため別環境で実証する')
    def test_symlink_rejected(self):
        path=self.target/'AGENTS.md'; path.unlink(); path.symlink_to(self.root/'external')
        self.bump({'AGENTS.md':'新内容'})
        with self.assertRaises(t.TemplateError): self.plan()
    def test_output_inside_target_rejected(self):
        self.bump()
        with self.assertRaises(t.TemplateError): t.plan_update(self.target,self.src,self.target/'review')
    def test_normal_exception_rollback(self):
        self.bump({'AGENTS.md':'新内容\n'}); self.plan()
        before=(self.target/'AGENTS.md').read_bytes(); oldlock=(self.target/t.LOCK).read_bytes()
        original=t.atomic_write; once=[True]
        def fail_once(path,data):
            if path==self.target/t.LOCK and once[0]:
                once[0]=False; raise OSError('検査用の書込失敗')
            original(path,data)
        with patch.object(t,'atomic_write',side_effect=fail_once):
            with self.assertRaises(OSError): self.apply()
        self.assertEqual((self.target/'AGENTS.md').read_bytes(),before)
        self.assertEqual((self.target/t.LOCK).read_bytes(),oldlock)
        self.assertFalse((self.target/'.harness/template-update.lock').exists())

if __name__=='__main__': unittest.main()
