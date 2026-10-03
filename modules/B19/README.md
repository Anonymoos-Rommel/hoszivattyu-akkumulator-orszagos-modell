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
