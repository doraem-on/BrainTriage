from pathlib import Path
import sys, unittest, itertools
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import research as r
import numpy as np

class ScientificInvariants(unittest.TestCase):
    def test_optimal_ranking_and_regret_bound(self):
        rng=np.random.default_rng(42)
        for _ in range(100):
            gain=rng.uniform(-1,1,7);eps=.15;estimated=gain+rng.uniform(-eps,eps,7)
            best=max(sum(gain[list(s)]) for s in itertools.combinations(range(7),3))
            selected=r.original.refer_mask(estimated,3/7)
            self.assertLessEqual(best-gain[selected].sum(),2*3*eps+1e-10)
            true_selected=r.original.refer_mask(gain,3/7)
            self.assertAlmostEqual(gain[true_selected].sum(),best)
    def test_brier_variance_identity(self):
        weights=np.array([.2,.3,.5]);posterior=np.array([.1,.5,.9]);prior=weights@posterior
        basic=prior*(1-prior);advanced=np.sum(weights*posterior*(1-posterior))
        self.assertAlmostEqual(basic-advanced,np.sum(weights*(posterior-prior)**2))
    def test_gates_ignore_outcomes_and_advanced_features(self):
        d,b,a,tr,_=r.load('oasis2');dev=d.iloc[tr].reset_index(drop=True)
        fit,ev=r.train_test_split(np.arange(len(dev)),test_size=.25,stratify=dev.y,random_state=4)
        model=r.fit(dev.iloc[fit],b,a);x=dev.iloc[ev].copy();p=r.predict(model,x)
        changed=x.copy();changed.y=1-changed.y;changed[a]=changed[a]*3
        q=r.predict(model,changed)
        cols=['basic','information','bayes_mean','gain_sd','bayes_lcb_1','confidence','ridge_gain','cost_gain_5']
        np.testing.assert_allclose(p[cols],q[cols],atol=1e-12)
        np.testing.assert_allclose(p.bayes_lcb_1,p.bayes_mean-p.gain_sd)
        self.assertTrue((p.gain_sd>=0).all())
        missing=x.copy();missing['age']=np.nan;missing['mmse']=np.nan
        stress=r.predict(model,missing)
        self.assertTrue(np.isfinite(stress[cols]).all().all())
        with self.assertRaises(AssertionError):r.predict(model,dev.iloc[fit])
    def test_weighted_decisions(self):
        np.testing.assert_array_equal(r.weighted_loss([1,0,1,0],[.1,.8,.6,.1],5),[5,1,0,0])
    def test_partitions_and_no_label_predictors(self):
        for cohort in ['oasis2','oasis1','csf','eeg_ad_ftd']:
            d,b,a,tr,te=r.load(cohort)
            self.assertTrue(d.id.is_unique)
            self.assertFalse(set(d.iloc[tr].id)&set(d.iloc[te].id))
            self.assertFalse(set(['y','CDR','Diagnostic','Group'])&set(b+a))

if __name__=='__main__':unittest.main()
