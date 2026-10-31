# Historical EOH validation versus current replay admission

Historical validation boundary: only the B11 physical-displacement entry in the EOH comparison-support and annual-transfer manifests is historical validation against each manifest’s exact original base commit. The original manifests remain byte-identical. All other protected-file checks remain current-byte checks.

The validator requires those commits and blobs locally; missing history or mismatched content fails closed. It never fetches automatically. Replacement Git objects are disabled. A source archive without the original Git history is insufficient for this check.

This does not permit an EOH replay on the modified runtime. The annual analyzer’s current-ROOT protected-file checks remain unchanged and reject the new B11 bytes before output creation. Historical registry validity is not current replay readiness, installed-model acceptance or proof of a new EOH result.

The B07 shared-use registry is an independent live dependency binding. Its engine hash changes from `4534c94ceef913f141f430a8e5854dd87d5af5df15ed103eccf81767fc878fe8` to `40c7354d31649f32f47987df761e2bde45b4056ca94e19092fc6f69850c93ada` for the SCN-only direct-executor validation fix. Other bindings and authority flags are unchanged.

Historical validation and the live dependency binding are distinct from current replay readiness. Neither establishes a new EOH replay result or installed-model acceptance.
