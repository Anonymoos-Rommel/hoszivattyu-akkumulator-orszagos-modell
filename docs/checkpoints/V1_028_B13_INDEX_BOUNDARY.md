# B13 output Git-index boundary repair

This checkpoint repairs the B13 materializer's tracked-state check on top of
`72ec387538463101fc2f0847e78cf0d2c1b8ca26`. It changes storage admission only.
The fiscal reader, public source pins, arithmetic, registries, module status,
and downstream gates are unchanged.

## Failure and repair

For each prospective output in the intended checkout's ignored `data/interim`,
the guard asks Git whether the path is tracked and independently whether it is
ignored. Previously, every nonzero `git ls-files --error-unmatch` result was
treated as evidence that the path was untracked. A corrupt, truncated, or
directory-valued index returns 128, while `git check-ignore --no-index` can
still return 0. This admitted a missing output that the original intact index
identified as tracked and allowed execution to reach the fiscal-source reader.

The guard now accepts only the explicit untracked result, exit 1, together
with the successful ignore result, exit 0. All other tracked-state results
reject before the first fiscal-source read. The production change is one
condition in `tools/materialize_b13_fiscal_reference.py`.

## Synthetic regression coverage

The new tests use real disposable Git repositories and indexes for both
`fiscal_reference.json` and `receipt.json`. They cover corrupt, truncated,
and directory-valued indexes plus valid untracked/ignored, tracked/deleted,
tracked/present, and unignored neighbors. A valid index is created even for
the untracked controls. Every Git result is real.

The tests verify tracked status before each index fault and again after
restoring the exact original index bytes. Both direct guard and materializer
paths are exercised. A raising first-reader sentinel proves rejection occurs
before fiscal-source access, while allowed controls reach that sentinel.
Fixture paths, file bytes, and directory entries are compared before and
after each probe. No real fiscal panel or original source is read or written.

External admission also has a controlled positive test that masks only
inherited host Git markers outside the disposable fixture. Git discovery and
all fixture paths remain real. A separate external-positive test uses no
filesystem or Git mocks; it requires a Git-free temporary ancestry.

## Verification and remaining hosted check

```sh
python -B -m unittest tests.test_b13_fiscal_reference -v
python -B -m unittest tests.test_registry_contract -v
python -B tools/validate_registry.py
```

Local focused verification: 37 B13 tests run, 36 pass and one external-positive
test skips because the host temporary directory inherits protected Git
metadata; 15 registry-contract tests pass and registry validation passes.
The six new real-index fault subcases fail against the preserved original
source, and all eight neighboring controls pass against it.

The unchanged independent witness passes all 14 cases against this candidate:
both output names across the seven index/neighbor states, with zero unsafe
admissions. It exercises the direct guard and CLI with a first-reader sentinel
and verifies unchanged fixture bytes and candidate HEAD/source/index identity.
The witness SHA-256 is
`b54a9271f91624cf3406f59b6478f090fee660eea1e29536787b9abfa87dcf32`.

The unmocked test
`FiscalOutputIndexTests.test_real_external_directory_still_reaches_first_fiscal_source_read`
must report `ok` in clean hosted CI before closing this checkpoint. When
`GITHUB_ACTIONS=true`, unsuitable temporary ancestry fails instead of skipping;
that fail-required behavior was also verified locally. The controlled positive
is not evidence of a completed unmocked external-path check.

Full aggregate testing and independent integration review belong to the lead's
combined candidate. This isolated change grants no fiscal-model admission,
source-reuse permission, or B15 promotion.
