"""Fictional regression fixtures for frame-independent inheritance checks."""
import csv
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
if not (ROOT/'scripts/verify_analysis.py').is_file():
    ROOT=ROOT/'analysis'
spec=importlib.util.spec_from_file_location('verifier_under_test',ROOT/'scripts/verify_analysis.py')
verify=importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)

def csv_file(p,rows):
    with p.open('w',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)

class InheritanceChecks(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='ce-fictional-verifier-')
        self.p=Path(self.tmp.name);(self.p/'restricted').mkdir()
        self.rows=[
            {'mapping_id':'fictional-map-1','station_id':'ST00','human_review_status':'pending','evidence_tier':'HIGH_CONFIDENCE_CANDIDATE','mapping_class':'EXACT_PROMPT_ANCHOR','minimum_link_window':'0'},
            {'mapping_id':'fictional-map-2','station_id':'ST01','human_review_status':'pending','evidence_tier':'PROBABLE_CANDIDATE','mapping_class':'CONTEXT_REFERENCE_WITHIN_20','minimum_link_window':'10'},
            {'mapping_id':'fictional-map-3','station_id':'ST02','human_review_status':'pending','evidence_tier':'CLEAN_ORIGIN_CANDIDATE','mapping_class':'CLEAN_ORIGIN_CANDIDATE','minimum_link_window':''}]
        self.windows=[{'window':w,'candidate_positive':1 if w==5 else 2,'eligible_rows':2,'candidate_positive_rate':.5 if w==5 else 1.,'unresolved':1 if w==5 else 0} for w in (5,10,20,50,106)]
        self.summary={'scope':{'prior_ce_predecessor_dispositions':['candidate_strong','candidate_probable'],
            'action_eligible_comparison_rows_mapped':3,'eligible_rows_with_prior_action_eligible_ce':2,
            'clean_origin_candidates':1,'high_confidence_candidates':1,'probable_candidates':1,'unresolved_primary_rule':0},
            'tier_counts':{'HIGH_CONFIDENCE_CANDIDATE':1,'PROBABLE_CANDIDATE':1,'CLEAN_ORIGIN_CANDIDATE':1},
            'class_counts':{'EXACT_PROMPT_ANCHOR':1,'CONTEXT_REFERENCE_WITHIN_20':1,'CLEAN_ORIGIN_CANDIDATE':1},'sensitivity':self.windows}
        self.save()
    def tearDown(self):self.tmp.cleanup()
    def save(self):
        csv_file(self.p/'restricted/inheritance_candidate_map.csv',self.rows)
        csv_file(self.p/'inheritance_window_sensitivity.csv',self.windows)
        (self.p/'inheritance_pilot_summary.json').write_text(json.dumps(self.summary))
    def test_non_R1_size_accepted(self):self.assertEqual(verify.verify_inheritance(self.p),2)
    def test_wrong_scope_count_rejected(self):
        self.summary['scope']['action_eligible_comparison_rows_mapped']=3502;self.save()
        with self.assertRaises(RuntimeError):verify.verify_inheritance(self.p)
    def test_wrong_rate_rejected(self):
        self.windows[0]['candidate_positive_rate']=.75;self.save()
        with self.assertRaises(RuntimeError):verify.verify_inheritance(self.p)
    def test_duplicate_identity_rejected(self):
        self.rows[1]['mapping_id']=self.rows[0]['mapping_id'];self.save()
        with self.assertRaises(RuntimeError):verify.verify_inheritance(self.p)
    def test_unperformed_review_not_relabelled(self):
        self.rows[0]['human_review_status']='completed';self.save()
        with self.assertRaises(RuntimeError):verify.verify_inheritance(self.p)
    def test_csv_summary_disagreement_rejected(self):
        changed=[dict(r) for r in self.windows];changed[0]['eligible_rows']=3
        csv_file(self.p/'inheritance_window_sensitivity.csv',changed)
        with self.assertRaises(RuntimeError):verify.verify_inheritance(self.p)

if __name__=='__main__':unittest.main()
