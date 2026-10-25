"""人工的な契約セットで形式と横断参照を検査する。"""
import copy
import importlib.util
import json
from pathlib import Path
import unittest
import yaml

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('validator',ROOT/'tools/validate.py')
v=importlib.util.module_from_spec(spec); spec.loader.exec_module(v)

class ContractTests(unittest.TestCase):
    def setUp(self): self.data=json.loads((ROOT/'examples/contracts/fixture-system.json').read_text())
    def test_valid_fixture(self): self.assertEqual(v.validate_bundle(self.data),[])
    def test_ready_rejects_fixture(self): self.assertTrue(v.validate_bundle(self.data,ready=True))
    def test_schemas_well_formed(self):
        for p in (ROOT/'schemas').glob('*.schema.json'):
            with self.subTest(schema=p.name): v.Draft202012Validator.check_schema(json.loads(p.read_text()))
    def test_generated_manifests(self):
        base=ROOT/'examples/order-system-ops'
        checks=[('system.yaml','system'),('repositories.lock.yaml','repository-lock'),('.harness/template.lock.json','template-lock'),('verification/scenarios/order-create.yaml','scenario')]
        checks += [(f'environments/{n}/environment.yaml','environment') for n in ('local','staging','production')]
        for file,name in checks:
            with self.subTest(file=file): self.assertEqual(v.schema_errors(yaml.safe_load((base/file).read_text()),name),[])
    def test_missing_evidence(self):
        self.data['claims'][0]['evidence_ids']=['EV-absent']
        self.assertTrue(any('参照先' in e for e in v.validate_bundle(self.data)))
    def test_duplicate_id(self):
        self.data['claims'].append(copy.deepcopy(self.data['claims'][0]))
        self.assertTrue(any('重複' in e for e in v.validate_bundle(self.data)))
    def test_snapshot_mismatch(self):
        self.data['evidence'][0]['locator']['commit']='9'*40
        self.assertTrue(any('SHAが不一致' in e for e in v.validate_bundle(self.data)))
    def test_task_cycle(self):
        self.data['tasks'][0]['depends_on']=[self.data['tasks'][0]['id']]
        self.assertTrue(any('循環' in e for e in v.validate_bundle(self.data)))
    def test_runtime_cycle_is_valid(self):
        d=copy.deepcopy(self.data['dependencies'][0]); d['id']='DEP-reverse'; d['consumer_id'],d['provider_id']=d['provider_id'],d['consumer_id']
        self.data['dependencies'].append(d)
        self.assertEqual(v.validate_bundle(self.data),[])
    def test_incomplete_comparison(self):
        self.data['observations'][0]['completed']=False
        self.assertTrue(any('比較前提' in e for e in v.validate_bundle(self.data)))
    def test_initial_state_mismatch(self):
        self.data['observations'][0]['initial_state_digest']='8'*64
        self.assertTrue(any('比較前提' in e for e in v.validate_bundle(self.data)))
    def test_production_reset(self):
        self.data['environments'][0]['classification']='production'
        self.assertTrue(any('本番環境' in e for e in v.validate_bundle(self.data)))
    def test_unapproved_decision(self):
        self.data['tasks'][0]['status']='ready'
        self.assertTrue(any('未承認Decision' in e for e in v.validate_bundle(self.data)))
    def test_confirmed_requires_evidence(self):
        self.data['claims'][0]['evidence_ids']=[]
        self.assertTrue(v.validate_bundle(self.data))
    def test_task_requires_acceptance(self):
        self.data['tasks'][0]['acceptance']=[]
        self.assertTrue(v.validate_bundle(self.data))
    def test_negative_fixture_cycle(self):
        data=json.loads((ROOT/'fixtures/negative/cyclic-tasks.json').read_text())
        self.assertTrue(v.cycle_errors(data['tasks']))

if __name__=='__main__': unittest.main()
