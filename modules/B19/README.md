# B19: historical joint-condition reference

`historical_joint_stress.calculate_reference(source_paths, handoff_paths,
weather_path=..., window_hours=...)` implements a bounded part of B19-D01.
It replays accepted source-native Hungarian load/generation and pairs hourly
means with the exact Budapest 44527 temperature intervals for UTC2025.

The caller must state a physical duration. Every complete hourly-start window
is considered; all exact ties are kept. Coldest station temperature, highest
source load and highest source-reference residual each select their own dated
window and its actual coincident quantities. This does not assert that every
variable was jointly extreme. Exact ratios preserve arithmetic and tie ranking.

The resulting DER/E2 historical reference is not observed exchange, shortage,
future adequacy, risk probability, national weather, programme impact or a
feasibility verdict. No original source or complete numeric panel is written.
The five prior central-heat debts and B08/B09 validation debt are unaffected.

See [V1-048](../../docs/checkpoints/V1_048_HISTORICAL_JOINT_STRESS.md) for method,
source scope, the explicitly declared 72-hour example and verification.


## Joint historical HU–AT price comparison

`historical_joint_market.calculate_reference(source_paths, handoff_paths, *,
weather_path, hu_source_paths, at_source_paths, window, window_hours)` extends
this reference through a separate interface. Both `window="utc2025"` and the
physical analysis duration are explicit. It joins accepted HU and independently
qualified AT publisher-hourly prices to the same observed weather/load/signed
source-generation intervals, retaining every complete window and exact ties.

Five separate selectors preserve actual co-occurring vectors. Same-domain
rank counts and intersections of tied-window coverage unions are descriptive;
they are not joint probabilities or adopted policy stress. HU−AT differences
supply one named regional market comparison, with both source retrieval
vintages retained. They do not establish physical imports, congestion,
available support, EU-wide conditions or programme value.

Use `tools/materialize_b19_joint_market.py` only with explicit private original
paths and an allowed private output directory. The detailed receipt is not a
public data artifact. Existing B19/B04 APIs and results remain unchanged.

See [V1-058](../../docs/checkpoints/V1_058_JOINT_MARKET_WINDOWS.md) for source,
time, structural uncertainty and review boundaries. B19 module readiness stays
unchanged; this individual historical handoff does not close national gates.
