# V1-031 — Hungarian MFH roof-ratio source precision

Date: 2026-10-02. Correction base:
`a43327e1239ddc6f3ec9dff217cbc3d86c4342c1`.

## Corrected source cell

`SRC-B02-EU-TABULA-DATABASE-EVALUATION-2015`, IWU/EPISCOPE,
*Evaluation of the TABULA Database*, document date 2015-12-10,
April 2015 database version, Table 4, printed page 8 (PDF page index 7):

- **HU**, **MFH**, **A_Roof / A_C_Ref**: **0.36 m2/m2** (`DER`)
- **Common**, **MFH**, same row: **0.35 m2/m2** (`DER`, comparison only)
- HU SFH **0.84** and HU AB **0.20 m2/m2** are unchanged

[Original source](https://episcope.eu/fileadmin/tabula/public/docs/report/TABULA_WorkReport_EvaluationDatabase.pdf).
The retained PDF was independently inspected on 2026-10-02, including its table
pixels, with SHA-256:

`800959c8ac321144d2e8cbe42b5a17f94c41587fde8fc63f445d6e35cdfc2a63`

The existing source registry's retrieval date remains 2026-09-22. The new
[precision manifest](../../registry/b02_p93_top_ratio_source_precision.json)
records that registry date separately from the retained-byte inspection date.
External PDF/image redistribution remains `REPOSITORY_COPY_NOT_CLEARED`; no
raw source document, image or full-table transcription is added.

The historical P93 input incorrectly selected the Common-column value. This
checkpoint supersedes that transcription, including the cumulative historical
P93 wording in `registry/open_questions.csv`; it does not erase that history.
The correction uses the published ratio cell directly. Dividing published
average absolute roof area by published average floor area would be a different
estimator and is not done.

## Canonical and generated change

The canonical computation remains
`modules/B02/hungarian_top_envelope_area.py`. Its
`TABULA_HU_MFH_TOP_TO_CONDITIONED_FLOOR_RATIO` changes from `0.35` to `0.36`.
P93's `MULTI_DWELLING` set-valued ratio interval becomes `[0.20, 0.36]`;
the unidentified MFH/AB mixture remains unidentified.

The formulas and units are unchanged:

```text
A_top = [A_C,lo * r_lo, A_C,hi * r_hi]            [m2/dwelling]
H_top,max = A_top,hi * 0.204                     [W/K/dwelling]
```

P96 retains its independent upper U authority and thermal-bridge correction,
`0.17 * (1 + 0.20) = 0.204 W/m2K`. Only the propagated geometry changes.

The following derived reference-programme upper bounds change. Area entries
remain `DER/SCN_PROXY`; thermal entries remain `POL/DER/SCN`. Period groups below
cover the seven `MULTI_DWELLING` strata, not population weights.

| WBL periods | Rows | Old area upper (m2/dwelling) | Corrected area upper | Old H upper (W/K/dwelling) | Corrected H upper |
| --- | ---: | ---: | ---: | ---: | ---: |
| Y_LT1919; Y1919-1945 | 2 | 30.572500000000 | 31.446000000000 | 6.236790000000 | 6.414984000000 |
| Y1946-1960; Y1961-1980; Y1981-2000 | 3 | 27.206666666655 | 27.983999999988 | 5.550159999998 | 5.708735999998 |
| Y2001-2010; Y_GE2011 | 2 | 30.514166666655 | 31.385999999988 | 6.224889999998 | 6.402743999998 |

These upper components rise by `0.36 / 0.35 - 1 = 2.857142857%` (`DER`).
That percentage is not a national load, energy, savings or capacity result.
The global descriptive extrema remain unchanged: P93 area
`10.96777777778 .. 196.392 m2/dwelling`; P96 H upper maximum
`40.063968 W/K/dwelling`.

Both generated artifacts preserve all seven `FAMILY_HOUSE` rows byte-for-byte.
Every lower bound, identifier, candidate mapping, evidence/status field and
existing note is unchanged. Only P93 ratio-upper/area-upper and P96
area-upper/H-upper change in the seven `MULTI_DWELLING` rows.
The precision manifest preserves original artifact hashes and exact SFH-row
fingerprints for historical reconciliation.

## Reproduction and validation

The materializer has no download or raw-source extraction step. It only handles
the two existing derived P93/P96 artifacts, in dependency order. Check mode
does not write; replacement requires explicit `--write`:

```sh
python tools/materialize_b02_top_envelope.py --check
python tools/materialize_b02_top_envelope.py --write
python tools/materialize_b02_top_envelope.py --check
python -m unittest tests.test_b02_p93_hungarian_top_envelope_area tests.test_b02_p96_pitched_roof_poststate_u -v
```

Validation for this isolated candidate:

- **20 targeted tests pass**, including source-cell/column binding, canonical
  and registry ratio agreement, every materialized row's numeric/semantic
  agreement, all seven corrected thermal uppers and exact SFH-row preservation
- Materializer `--check` passes for both generated files
- External-copy negative controls reject stale P93 and stale P96 interior-row
  values without writing; explicit regeneration is byte-idempotent
- Exact cell comparison confirms the seven-row/two-column limit per artifact
- `registry/sources.csv` changes only the existing TABULA source row;
  unrelated rows are byte-preserved

The full repository aggregate is not run by this checkpoint. Combined review,
full-suite validation and publication ordering remain subsequent steps.

## Integration boundary

V1-030's SFH diagnostic uses the unchanged `0.84` ratio and unchanged SFH
surface rows. Whole-file hashes of shared P93/P96 dependencies still change:
its source pins must be rebound to the final integrated bytes and its output
rechecked for exact numerical invariance. This checkpoint does not edit that
candidate or claim that its independent validation is complete.

Corrected artifact SHA-256 values:

- P93 `fe7eceee8d439b2b436bbb92254f9d233c902829ced7c8789d078793eb78beda`
- P96 `455c21cab940975919f93b63c38d5902cdbdd5ec7565dd68c84498cc07a49eee`

Earlier observed/source files, P80/P83/P91 historical slices, population and
service assumptions, evidence tiers, source reuse restrictions, `Q-B02-004`
status, B02 readiness **55%** and B06 `PEAK_LOAD_EFFECT` readiness **50%** are
unchanged. This correction supplies no national weights, realized-project
acceptance, national output, new legal/source acquisition or new model claim.
