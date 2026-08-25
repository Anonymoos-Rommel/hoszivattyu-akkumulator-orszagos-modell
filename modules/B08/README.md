# B08 – bounded electrical system-load aggregation

B08 aggregates explicit AC/grid-side household boundary records. Its canonical
identity is `net_grid_load_kw = gross_grid_import_kw - gross_grid_export_kw`,
with energy derived as power times the explicit timestep. Import/export and
physical up/down flexibility remain separate; flexibility is not dispatch.

The B05 heat-pump load is already included in the B07 household balance and is
handed to B08 once through `B08PhysicalHandoff`. B01 state is carried only as
trace metadata. B02 eligibility/readiness, legal export, tariffs, B09 dispatch,
B10 headroom/reinforcement, seasonal peaks, population scaling, and national
claims remain outside this bounded contract and are Q/partial.

The supplied fixture is SCN-only, dataset-licensed, two-region and explicit.
`NATIONAL_FIXTURE_TOTAL` means the sum of those fixture records, not a national
estimate. Missing values, duplicate keys, mixed region schemes, mixed truth
contexts, negative physical inputs, and inconsistent timesteps fail closed.
