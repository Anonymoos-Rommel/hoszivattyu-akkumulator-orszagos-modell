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
`BOUNDED_SCOPE_TOTAL` means the sum of the explicit bounded records, not a
national estimate. Every source entity must be present at every run timestamp;
missing values, duplicate keys, alternate boundaries, mixed region schemes,
mixed truth contexts, negative physical inputs, naive timestamps, and
inconsistent timesteps fail closed. Timestamps are timezone-aware and
canonicalized to UTC; each timestamp denotes the start of an explicit interval
whose duration is `timestep_hours`.
