import unittest,sys
from pathlib import Path
import numpy as np
import pandas as pd
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from common import sensitivity_threshold,metrics
from features import segment_features,CHANNELS,ROOT
import companion
import sensitivity
class ScientificChecks(unittest.TestCase):
    def test_threshold_maximality_and_monotonicity(self):
        rng=np.random.default_rng(17)
        for _ in range(50):
            y=np.r_[np.ones(25),np.zeros(29)];p=rng.uniform(size=len(y));t=sensitivity_threshold(y,p)
            self.assertLessEqual(t,.5);self.assertGreaterEqual(np.mean(p[y==1]>=t),.9)
            candidates=np.unique(np.r_[.5,0,p[(y==1)&(p<=.5)]])
            self.assertTrue(all(np.mean(p[y==1]>=v)<.9 for v in candidates if v>t))
            self.assertLessEqual(metrics(y,p,t)['false_negatives'],metrics(y,p,.5)['false_negatives'])
            self.assertGreaterEqual(metrics(y,p,t)['false_positives'],metrics(y,p,.5)['false_positives'])
            self.assertEqual(metrics(y,p,t)['auroc'],metrics(y,p,.5)['auroc'])
    def test_feature_order_and_scale_invariance(self):
        rng=np.random.default_rng(18);x=rng.normal(size=(16,1280))
        a=segment_features(x,CHANNELS,256);order=rng.permutation(16)
        b=segment_features(7*x[order],[CHANNELS[i] for i in order],256)
        np.testing.assert_allclose(list(a.values()),list(b.values()),rtol=1e-7,atol=1e-7)
        self.assertEqual(len(a),564)
    def test_source_and_target_isolation(self):
        a=pd.read_csv(ROOT/'data_raw/source_features.csv');b=pd.read_csv(ROOT/'data_raw/external_features.csv')
        self.assertEqual((len(a),int(a.y.sum()),len(b),int(b.y.sum())),(54,25,23,12))
        self.assertEqual(a.columns.tolist(),b.columns.tolist());self.assertFalse(set(a.id)&set(b.id))
        _,_,_,forbidden=sensitivity.ex.load_development('eeg_ad_ftd');self.assertFalse(set(a.id)&forbidden)
        for kind in companion.MODELS:self.assertFalse(set(companion.columns(a,kind))&{'y','id','mmse'})
    def test_classifier_rejects_training_subjects(self):
        a=pd.read_csv(ROOT/'data_raw/source_features.csv');b=companion.fit(a,'spectral',17)
        with self.assertRaises(AssertionError):companion.predict(b,a)
    def test_original_gate_input_restrictions(self):
        d,b,a,_=sensitivity.ex.load_development('eeg_ad_ftd')
        tr,va=next(sensitivity.StratifiedKFold(4,shuffle=True,random_state=15).split(d,d.y))
        bundle=sensitivity.fit(d.iloc[tr],b,a,17);original=d.iloc[va].copy();modified=original.copy();modified.y=1-modified.y
        p,r=sensitivity.predict(bundle,original);q,s=sensitivity.predict(bundle,modified)
        for key in p:np.testing.assert_allclose(p[key],q[key])
        cov=[c for c in modified if c.startswith('cov_')];modified[cov]=modified[cov]+1
        _,s=sensitivity.predict(bundle,modified)
        for key in r:np.testing.assert_array_equal(r[key],s[key])
if __name__=='__main__':unittest.main()
