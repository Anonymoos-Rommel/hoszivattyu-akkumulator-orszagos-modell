# B17 environmental source references

`emission_factor_reference.py` retains the V1-029 external, complete 36-row
factor-reference contract. Its panel has not been reconstructed by V1-049.

`direct_gas_reference.py` adds a separately qualified narrow consumer: the
IPCC residential natural-gas CO2 default applied to the existing V1-045
original, standard or ambitious TABULA source-convention NCV heating activity.
Callers select a named case; there is no population or programme default.

This is a conditional direct-combustion inventory-method reference. Total fuel
carbon is expressed as CO2 under the source's oxidation-one convention; it is
not exact measured stack CO2. The source factor interval is reported at fixed
activity and does not cover full model uncertainty. Case differences share one
common factor. No electricity offset, net climate effect, health or valuation
is calculated. Source applicability and activity debt remain explicit.

Example: `python -m modules.B17.direct_gas_reference --package ambitious`

See [V1-049](../../docs/checkpoints/V1_049_DIRECT_GAS_CO2_REFERENCE.md) and the
[pinned source/applicability manifest](../../registry/b17_direct_gas_reference_manifest.json).
