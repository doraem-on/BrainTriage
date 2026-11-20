# Mathematical formulation

These are explicit decision-theoretic derivations for this benchmark, not claims of new general mathematical results.

## Setup

Let X be recorded basic measurements, Z an advanced panel and Y a binary recorded outcome. The fitted basic and advanced predictors p0(X) and p1(X,Z) are fixed when considering an evaluation batch. Define the conditional benefit

G(x) = E[(Y − p0(x))² − (Y − p1(x,Z))² | X=x].

This is an expectation over an unobserved advanced panel and outcome, conditional on information available before acquisition. It is not the observed per-person loss difference (which requires Y), a causal treatment effect, or a clinical cost-effectiveness measure. The fitting procedure estimates it from cross-fitted training predictions.

## Proposition 1 Optimal equal-cost allocation

For a batch of n people, write Gi = G(xi). Assume the decision for one person does not alter another person's conditional outcome distribution or predictor, all panels have the same cost, and exactly k panels must be acquired. Any set S of k selected people has expected total squared loss

R(S) = sum_i E[(Yi − p0(xi))² | Xi=xi] − sum_(i in S) Gi.

Therefore selecting the k largest Gi minimizes R. If |S| ≤ k is allowed, choose only strictly positive gains among the largest k. If acquisition adds a constant cost c in the same loss units, replace Gi by Gi − c. For person-specific unequal costs under a total-cost budget, the problem is generally a knapsack problem; benefit-per-cost ranking is not asserted to be exactly optimal.

Proof. The first term does not depend on S. Maximizing the second term over fixed-cardinality sets is achieved by the k largest values. Exchanging a selected lower value with an unselected higher value cannot reduce the sum. For a capacity upper bound, adding a negative gain cannot improve the objective.

## Proposition 2 Gain-estimation regret

Suppose |Ghat_i − Gi| ≤ epsilon for all n evaluation candidates. Let Sstar maximize the true sum among sets of size k and Shat maximize the estimated sum. Then

0 ≤ R(Shat) − R(Sstar) ≤ 2 k epsilon.

For average loss, the bound is 2k epsilon / n. It does not require independence between patients for linearity of expected loss, but assumes fixed, separable conditional benefits and the stated uniform error bound.

Proof. Add and subtract estimated gains:

sum_(Sstar) Gi − sum_(Shat) Gi
= sum_(Sstar)(Gi − Ghat_i) + [sum_(Sstar) Ghat_i − sum_(Shat) Ghat_i] + sum_(Shat)(Ghat_i − Gi)
≤ k epsilon + 0 + k epsilon.

The middle term is nonpositive by the definition of Shat. The empirical experiment does not establish the uniform estimation-error assumption. The result explains why ranking accuracy matters; it is not a numerical performance guarantee for fitted models.

## Proposition 3 Brier value of information for coherent Bayes predictors

If eta0(X)=E[Y|X] and eta1(X,Z)=E[Y|X,Z], then the expected Brier improvement is

G_Bayes(x) = Var(eta1(x,Z) | X=x) ≥ 0.

Proof. Conditional squared-loss risk of a conditional mean is conditional variance. Apply the law of total variance:

Var(Y|X) = E[Var(Y|X,Z)|X] + Var(E[Y|X,Z]|X).

Subtract the expected advanced risk from the basic risk. The result is nonnegative because conditional expectation uses nested information sets. Separately fitted or miscalibrated practical predictors need not satisfy these assumptions; their actual expected improvement can be negative. Individual realized improvements can be negative even when expected improvement is positive.

## Confidence is a different quantity

For Y=1, p0=0.4 and p1=0.1, distance from 0.5 increases from 0.1 to 0.4, but squared error increases from 0.36 to 0.81. This elementary counterexample explains why a confidence-gain target is not identical to a loss-gain target. It does not imply that a learned loss target will generalize better.

## Bayesian benefit estimator

The gate fits g_i = phi(x_i)^T beta + e_i with a Gaussian likelihood and isotropic Gaussian coefficient prior. Empirical Bayes estimates the precision parameters. With posterior coefficient mean m and covariance Sigma, the fitted conditional mean is mu(x)=phi(x)^T m and its conditional posterior standard deviation is s(x)=sqrt(phi(x)^T Sigma phi(x)). A constant is included in phi so its uncertainty is represented. The score is mu(x) − kappa s(x), using kappa in {0, 0.5, 1, 2}; kappa=1 is the main extension contrast against kappa=0.

This posterior is conditional on the cross-fitted gain targets, design matrix and estimated hyperparameters. It omits upstream classifier, calibration and cross-fitting uncertainty. The lower score is a conservative ranking heuristic, not a valid distribution-free lower confidence bound or conformal guarantee. We call it an uncertainty-adjusted score in substantive conclusions.

## Information-gain comparator

Fit a training-only linear conditional mean for standardized Z given basic features and a shrinkage covariance for its residuals. For 32 Gaussian draws Z^(b)|x, evaluate p_b=p1(x,Z^(b)). The score is H(mean_b p_b) − mean_b H(p_b), with Bernoulli entropy H. Under the assumed conditional feature model and Bernoulli predictive model, this estimates conditional mutual information. The assumptions are approximations, especially for non-Gaussian biomarkers and correlated bounded spectral features. The draws are integration variables; they are not training patients or reported measurements. This implementation is inspired by generative acquisition literature, not a reproduction of EDDI, GSMRL or L2M.

## Cost-sensitive extension

For false-negative weight w and false-positive weight 1, use the illustrative probability threshold 1/(1+w). Define l_w(y,p)=w y I[p<1/(1+w)] + (1−y) I[p≥1/(1+w)]. A separate ridge gate learns the cross-fitted difference l_w(Y,p0)−l_w(Y,p1). The variable-capacity policy acquires when estimated improvement exceeds acquisition cost c. Evaluate J=mean(l_w)+c times referral_fraction. All weights are hypothetical sensitivity scenarios, not elicited clinical utilities or currency amounts.

## Statistical scope

The earlier study's test results were already known before this extension. Reuse is exploratory. The new EEG cohort has an independently assigned holdout but a different endpoint and refitted models, so it tests methodological feasibility across tasks rather than external transport of an MRI model. Fixed-model bootstrap intervals do not include retraining or allocation uncertainty. Repeated development folds are correlated; their spread is descriptive, not an independent-sample confidence interval.
