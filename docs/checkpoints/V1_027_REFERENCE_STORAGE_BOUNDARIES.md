# V1-027 — Reference materializer storage boundaries

## Scope

This bounded repair covers only output-path safeguards for the B08 GUI load,
B09 GUI generation, B09 future supply, and B18 supply source materializers.
B08 additionally gains explicit fresh-output behavior. It does not change source
admission, parsers, pinned identities, numeric or scientific semantics, output
filenames, evidence labels, reuse rights, or B13. No filesystem permissions,
account settings, sharing settings, or repository configuration are changed.

| Materializer | Permitted destination |
| --- | --- |
| B08 GUI load | This checkout's ignored `data/interim` only |
| B09 GUI generation | This checkout's ignored `data/interim` only |
| B09 future supply | Ignored `data/interim`, or an external directory outside Git |
| B18 supply source | Ignored `data/interim`, or an external directory outside Git |

## Enforced boundary

Before source access or output creation, every materializer walks the resolved
output directory and all ancestors up to the declared repository root. A `.git`
marker below that root rejects the destination, whether it is a directory, a
linked-worktree file, or a symbolic link. Missing intermediate directories do
not stop the ancestor walk. The declared checkout's own marker is permitted.
External-capable materializers continue the walk to the filesystem root for an
external destination and reject foreign Git ownership.

Lexical path symlinks, target symlinks including broken links, existing targets,
public repository paths, and traversal to public paths are rejected. In-repo
targets must also be untracked and covered by the actual repository ignore
policy. Only the explicit `git ls-files --error-unmatch` exit code 1 permits
an untracked target; tracked exit code 0 and every Git/index error reject the
destination. A successful `check-ignore --no-index` cannot override a failed
index query. Resolving the output before computing Git-relative target names
preserves valid lexical parent aliases inside ignored storage.

B08 preflights both its CSV and receipt before its first source read and creates
both with exclusive mode. Existing sentinel bytes are preserved, including when
a target file or symlink appears after the initial preflight. The other three
writers retain their existing exclusive-creation behavior.

These checks do not make the multi-file write transactional. A later failure can
leave an earlier newly created output, and the repair does not claim protection
against concurrent replacement of ancestor directories after preflight.

## Synthetic verification

The four corresponding test files contain a 27-case matrix per materializer:
deep ignored output; normalized ignored paths; nested repositories and real
linked worktrees; nested output roots; deep missing ancestors; deleted targets
still tracked in the outer or nested index; removed ignore policy; existing CSV
or receipt; file and directory symlinks, broken links and a symlinked interim
root; public traversal; foreign repositories/worktrees; and broken Git markers.
Every matrix case also invokes the CLI with a first-source-reader sentinel.
Rejected cases must leave that reader uncalled, preserve existing sentinel bytes,
and create no filesystem entries. Accepted cases reach that reader without
creating an output.

Of the 108 matrix cases, 104 use real filesystem and Git metadata throughout.
The four explicitly named `external_non_git_controlled_metadata` cases mask only
inherited host `.git` markers outside their disposable fixture. Fixture markers,
indexes, worktrees, symlinks, and target paths remain real. They prove the intended
external policy under controlled metadata, not a physically marker-free host.

Separate unmocked tests named
`test_real_external_non_git_directory_remains_allowed` cover B09 future and B18.
This execution environment has `.git` markers above every permitted temporary
location, so both unmocked positive tests report explicit skips locally. They
must execute successfully without skips in clean hosted CI before this repair
is closed. When `GITHUB_ACTIONS=true`, a host Git marker makes these tests fail
instead of skip. A separate expected-negative local check verifies both failures.
No host markers are removed and no production guard is weakened to
accommodate the environment.

A further 24 real disposable-index cases cover valid untracked, deleted tracked,
and unignored neighbors alongside corrupt, truncated, and directory-valued Git
indexes for all four materializers. They verify actual Git return codes, refusal
before the first source read, and preservation of all fixture entries and bytes.
Restoring only each disposable index confirms the deleted target remains tracked.
The independent reviewer's 24-case witness also passes against the candidate.

B08 also has an exact synthetic CSV/receipt-content check and four exclusive-write
collision cases covering both named outputs as files and symlinks arriving after
preflight. All source and seasonal functions in these write probes use invented
one-record stand-ins; these are storage tests, not real-source admission.

Focused command:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests python -m unittest \
  test_b08_gui_load_reference test_b09_gui_generation_reference \
  test_b09_future_supply_reference test_b18_supply_source_reference -v
python tools/validate_registry.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=tests python -m unittest test_registry_contract -v
```

Revision 2 local result: 115 test methods, 113 executed successfully and the two explicit
external-positive skips; all 15 shared registry tests, registry contracts and
B01–B20 dependency gates pass.
This is a focused result, not an aggregate-suite or hosted-CI pass.

The original audit, reproducer, results, and ten audited original files are
preserved byte-for-byte outside the candidate worktree. Implementation receipts
bind the owned tools, tests, and this checkpoint to exact SHA-256 and Git blob
digests. Independent review of those exact bytes remains required before publication;
hosted execution of the unmocked external positives is required before closure.
