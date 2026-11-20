import sys,unittest
from pathlib import Path
import numpy as np
from sklearn.model_selection import train_test_split
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import experiment as e
from extract_features import matrix_log_vector

class ResearchInvariants(unittest.TestCase):
    def test_blend_minimizes_constrained_empirical_brier(self):
        rng=np.random.default_rng(7)
        for _ in range(100):
            y=rng.integers(0,2,31);pb=rng.uniform(size=31);pa=rng.uniform(size=31)
            a=e.blend_weight(y,pb,pa);loss=np.mean((y-(pb+a*(pa-pb)))**2)
            grid=np.linspace(0,1,501)
            all_losses=np.mean((y[:,None]-pb[:,None]-(pa-pb)[:,None]*grid)**2,axis=0)
            self.assertLessEqual(loss,float(all_losses.min())+1e-12)
        self.assertEqual(e.blend_weight(y,pb,pb),0)

    def test_log_covariance_preserves_geometry_and_scale(self):
        m=np.array([[2.,.4],[.4,1.]])
        np.testing.assert_allclose(matrix_log_vector(m),matrix_log_vector(7*m),atol=1e-12)
        vals,vecs=np.linalg.eigh(m/np.trace(m));logged=(vecs*np.log(vals))@vecs.T
        self.assertAlmostEqual(np.sum(matrix_log_vector(m)**2),np.sum(logged**2))

    def test_all_original_holdouts_excluded(self):
        for cohort in e.PLAN['cohorts']:
            d,b,a,forbidden=e.load_development(cohort)
            self.assertTrue(d.id.is_unique);self.assertFalse(set(d.id)&forbidden)
            self.assertFalse(set(b+a)&{'y','CDR','Diagnostic','Group'})
            if cohort=='eeg_ad_ftd':self.assertEqual(len(d),41)

    def test_nested_partitions_and_gate_input_restrictions(self):
        d,b,a,_=e.load_development('oasis2')
        tr,va=train_test_split(np.arange(len(d)),test_size=.25,stratify=d.y,random_state=12)
        fit=d.iloc[tr];evaluation=d.iloc[va];bundle=e.fit_bundle(fit,b,a,'legacy_fixed',42)
        for nested in bundle['nested_partitions']:
            self.assertFalse(set(nested['training_ids'])&set(nested['validation_ids']))
            self.assertEqual(set(nested['training_ids'])|set(nested['validation_ids']),set(fit.id))
            self.assertFalse(set(nested['training_ids'])&set(evaluation.id))
        p=e.predict(bundle,evaluation,'blend');modified=evaluation.copy()
        modified.y=1-modified.y;modified[a]=modified[a]*3
        q=e.predict(bundle,modified,'blend')
        for col in ['basic','ridge_gain','nonlinear_gain','confidence','uncertainty']:
            np.testing.assert_allclose(p[col],q[col],atol=1e-12)
        self.assertTrue(np.isfinite(p.drop(columns='id')).all().all())
        with self.assertRaises(AssertionError):e.predict(bundle,fit,'raw')

    def test_rich_features_and_budget_are_fixed(self):
        d,b,a,_=e.load_development('eeg_ad_ftd')
        self.assertEqual(len([c for c in d if c.startswith('cov_')]),760)
        self.assertEqual(len([c for c in d if c.startswith('rich_')]),25)
        self.assertEqual(len(e.candidate_specs('advanced','nested_rich',True)),9)
        for n in [18,30,41,120]:
            mask=e.prior.original.refer_mask(np.zeros(n),.3)
            self.assertEqual(int(mask.sum()),int(np.floor(.3*n)))

if __name__=='__main__':unittest.main()
