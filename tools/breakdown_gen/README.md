# breakdown_gen: generate MAVEN breakdown files from a Genesis datacard template

MAVEN's Tier 1 form is driven by a *breakdown* YAML file (`maven/metadata_template/genesis_dc_breakdown.yaml`).
For datacard v1.2 that file was written by hand from the datacard template. This folder contains a script that
produces the same kind of file automatically, so a new datacard version (v2.0, v2.1, v3.0, ...) becomes a config
change and a re-run instead of a hand conversion.

- No LLM is used. Every output is produced by code and can be regenerated at any time.
- Every place where the script had to make a judgment call is listed in a review report next to the output.
- Decisions made by a person are recorded as `overrides` in the config, so the next run reproduces them.

---

## 1. What is in this folder

| File | What it is |
|---|---|
| `generate_breakdown.py` | The generator. Reads a config, writes a breakdown YAML and a review report. |
| `compare_breakdowns.py` | Checks a breakdown against MAVEN's form rules, and optionally compares it field by field with a reference breakdown. |
| `test_generate.py` | Regression test: regenerates v1.2 and checks it against Vedant's v1.2 breakdown. |
| `validate_breakdown.py` | Independent check that a breakdown (hand-made, LLM-made or generated) matches its template, section by section. Does not use the generator's code. |
| `test_validate.py` | Tests for the validator, including deliberately broken copies. |
| `validation_v1.2.md`, `validation_v2.0.md` | Validation reports for the generated files. |
| `config_v1.2.yaml` | Inputs and decisions for datacard v1.2. |
| `config_v2.0.yaml` | Inputs and decisions for datacard v2.0. |
| `genesis_dc_v1.2_breakdown.generated.yaml` | Generated v1.2 breakdown. |
| `genesis_dc_v1.2_breakdown.generated.review.md` | Review report for the v1.2 run. |
| `v1.2_vs_vedant.diff.md` | Field-by-field differences between the generated v1.2 file and Vedant's hand-made one. |
| `genesis_dc_v2.0_breakdown.generated.yaml` | Generated v2.0 breakdown (380 of the 510 template fields: Vedant removed 130 on 2026-11-05, see `exclude` in the config). |
| `genesis_dc_v2.0_breakdown.generated.review.md` | Review report for the v2.0 run: the items that need a human decision. |
| `v2.0_vs_manual.diff.md` | Differences between the generated v2.0 file and the partial hand-made v2.0 breakdown (`maven/metadata_template/genesis_dc_v2.0_breakdown.yaml`). |
| `inputs/` | Where you put the downloaded datacard archives. Ignored by git (see `.gitignore`). |
| `templates/` | Templates kept in git: `genesis_datacard_v2.0.0_vedant.yaml`, Vedant's edited v2.0 template (read by `config_v2.0.yaml`). |
| `../verify_v12_mapping.py` | The analysis script that established which sources the v1.2 breakdown was built from (section 4.1). |

---

## 2. Setup

### 2.1 Python environment

The scripts only need Python 3.12+ and `pyyaml`, both already in MAVEN's `requirements.txt`. If MAVEN runs on
your machine, use the same environment:

```bash
conda activate maven_env          # or however you activate the MAVEN environment
python -c "import yaml; print('ok')"
```

### 2.2 Download the datacard archives

The datacard template and reference guide are not stored in this repository. Download them once:

1. Open https://edx.netl.doe.gov/dataset/genesis-data-card-schema-template-and-supporting-tools
2. Download `data-cards-v1.2.0.tar.gz` and `data-cards-v2.0.0.zip`.
3. Put both files, **unchanged and unextracted**, in `tools/breakdown_gen/inputs/` (create the folder if it
   does not exist):

```
tools/breakdown_gen/inputs/
    data-cards-v1.2.0.tar.gz
    data-cards-v2.0.0.zip
```

`templates/genesis_datacard_v2.0.0_vedant.yaml` (committed, no download needed) is Vedant's edited copy of the zip template (received 2026-11-05, saved as
`diana_genesis_v2.0.yaml`): 7 list blocks made single entries (`change_log`, `created_by`, `additional_ids`, `contact`,
`intended_repositories`, `data_services`, `source_data`) and the `Perfer` typo fixed. `config_v2.0.yaml` reads it.

The scripts read the files they need directly from inside the archives, in memory. Nothing is extracted and
nothing inside the archives is executed. If you keep the archives somewhere else, edit the `template:` and
`guide:` lines in the configs (section 5.1) instead of copying them.

### 2.3 Check that everything works

From the repository root:

```bash
cd tools/breakdown_gen
python test_generate.py
```

It prints `ok` when the v1.2 output still matches Vedant's breakdown. If it fails with `FileNotFoundError`,
the archives are not in `inputs/` (see section 9).

---

## 3. Quick start

All commands are run from `tools/breakdown_gen/`.

```bash
# 1. Generate a breakdown (writes the .yaml and its .review.md)
python generate_breakdown.py config_v2.0.yaml

# 2. Check it against MAVEN's form rules
python compare_breakdowns.py genesis_dc_v2.0_breakdown.generated.yaml

# 3. Optional: compare it with a reference breakdown, and write the per-field differences
python compare_breakdowns.py genesis_dc_v1.2_breakdown.generated.yaml \
    --reference ../../maven/metadata_template/genesis_dc_breakdown.yaml \
    --diff v1.2_vs_vedant.diff.md
```

(On Windows PowerShell, put the command on one line or replace `\` with a backtick.)

### 3.1 Validate a breakdown

`validate_breakdown.py` answers "was anything lost or invented when this template was converted?" It works on
any breakdown, however it was produced, and does not reuse the generator's code: it reads the template with
plain `yaml.safe_load` and its own comment reader.

```bash
python validate_breakdown.py ../../maven/metadata_template/genesis_dc_v1.2_YAML.yaml     genesis_dc_v1.2_breakdown.generated.yaml --report validation_v1.2.md
python validate_breakdown.py templates/genesis_datacard_v2.0.0_vedant.yaml     genesis_dc_v2.0_breakdown.generated.yaml --allow-missing-from config_v2.0.yaml --report validation_v2.0.md
```

It prints one row per section (template keys, breakdown fields, errors, warnings) and exits with code 1 if there
is any error.

| Severity | Check |
|---|---|
| ERROR | A template key is missing from the breakdown, or the breakdown has a key the template does not have |
| ERROR | A leaf's placeholder value differs from the template (in the v2 format an empty value is accepted, and a placeholder may be pre-filled, reported as EXPECTED; a pre-filled dropdown value must be one of its options) |
| ERROR | MAVEN's form rules fail (same check as `compare_breakdowns.py`) |
| WARNING | A `[*_required]` field is not required; a comment lists choices but there is no dropdown; a dropdown option does not appear in the template comment |
| EXPECTED | Blocks tagged `[reference_only…]`, named with `--allow-missing` (`*` patterns allowed) or listed in the config given to `--allow-missing-from`; discriminators added next to one-of blocks |

Run on Vedant's v1.2 file, it reports 0 errors and 8 warnings, which are the known mistakes in that file
(the copied `classification_category` options, missing dropdowns; the `Resourcesm` typo was fixed on 2026-11-04). The generated v1.2 file has 0
errors and 0 warnings; the generated v2.0 file has 0 errors and 3 warnings (`processing_steps`, made optional by Vedant on 2026-11-05, and 2 required-tagged fields inside optional
blocks, which are `false` on purpose).

To try a generated file in MAVEN, copy it over `maven/metadata_template/genesis_dc_breakdown.yaml` (the file
`app.py` loads). Keep a copy of the original first. This works for v1.2 only: the v2.0 file uses Vedant's
`output_format: v2` (types `string` / `list` / `int` / `float`, `visible`, `mapping`), which today's `app.py` does not
render yet (it stops with `Unsupported type`).

---

## 4. Inputs: where the content comes from

### 4.1 How the v1.2 breakdown was made

`../verify_v12_mapping.py` compared all 379 nodes of Vedant's v1.2 breakdown
(`maven/metadata_template/genesis_dc_breakdown.yaml`) with three candidate sources:

1. **The annotated template**: `genesis_dc_v1.2_YAML.yaml`. This is the original template in the tarball
   (`template/latest/genesis_datacard_merged_shared.yaml`) with its YAML lists flattened into dicts.
2. **The LinkML schema**: `datacard_schema/src/genesis_datacard/schema/genesis_datacard.yaml`.
3. **The reference guide**: `template/latest/data_card_field_reference_guide.md`, identical to
   `maven/metadata_template/genesis_dc_v1.2_reference_guide.md`.

Wherever the template and the schema disagree, the breakdown follows the template. For example,
`primary_id.type` offers `osti`, which exists only in the template comment and not in the schema's enum.
The schema therefore does not appear to have been used. The reference guide was used for the descriptions of
the top-level `supports_*` keys.

To re-run that analysis (it reads the v1.2 archive from `inputs/`):

```bash
cd tools
python verify_v12_mapping.py
```

### 4.2 Inputs the generator uses

| Version | Template | Reference guide |
|---|---|---|
| v1.2 | `data-cards-v1.2.0.tar.gz` → `data-cards-v1.2.0/template/latest/genesis_datacard_merged_shared.yaml` | `data-cards-v1.2.0.tar.gz` → `data-cards-v1.2.0/template/latest/data_card_field_reference_guide.md` |
| v2.0 | `templates/genesis_datacard_v2.0.0_vedant.yaml` (Vedant's edit of `data-cards-v2.0.0.zip` → `data-cards-v2.0.0/template/latest/template/genesis_datacard_merged_shared.yaml`) | `data-cards-v2.0.0.zip` → `data-cards-v2.0.0/template/latest/template/data_card_field_reference_guide_v2.0.0.md` |

- The generator reads the **original** template and flattens the lists itself, the same way Vedant's
  `genesis_dc_v1.2_YAML.yaml` was flattened. No hand editing is needed.
- The v2.0 template in the zip is line-for-line identical to `genesis_dc_v2.0_YAML.yaml`; Vedant's copy differs only
  in the 7 de-listed blocks, the typo and blank lines.
- For v2.0 the guide is read but not used, because `guide_for_top_level` is `false` in `config_v2.0.yaml`.
- The LinkML schema is optional. The `schema:` line is commented out in both configs (section 7.2).

---

## 5. The config file

Each datacard version has one config. Paths are relative to the config file. An input can be a plain file
path or a file inside an archive, written as `archive::path/inside/archive`.

### 5.1 Keys

```yaml
title: Genesis Data Card Breakdown Schema v2.0      # first line of the output file
output: genesis_dc_v2.0_breakdown.generated.yaml    # output file name

template: templates/genesis_datacard_v2.0.0_vedant.yaml
output_format: v2                                   # optional: Vedant's 2026-11-04 field format (section 6)
guide: inputs/data-cards-v2.0.0.zip::data-cards-v2.0.0/template/latest/template/data_card_field_reference_guide_v2.0.0.md
# schema: ...                                       # optional, see section 7.2
root_class: GenesisDatacardClass                    # only used with a schema

alternatives:                                       # one-of agent blocks
  blocks: [person, organization, ai_model, software]
  discriminator_keys: [agent_type, type]            # existing sibling keys that pick a block
  synthesize_as: agent_type                         # add this discriminator when the template has none (v2.0)
  required_keys: [given_name, family_name, name, version, affiliation, type, value]
  choice_hint:                                      # optional (v2.0): append "Fill in only if <role> is <kind>; leave <others> empty."
    roles: {creator: the creator, authors: this author}   # keyed by the group's key; default "this entry"
    kinds: {person: a person, organization: an organization, ai_model: an AI model, software: a software tool}

extra_option: None                                  # added to a required dropdown with no none/other choice
no_extra_option:                                    # fields that must not get it
  - discoverability.datacard.creation_method

guide_for_top_level: false                          # prefix supports_* descriptions with the guide text
exclude_top_level: []                               # top-level blocks to leave out (xCard was, until 2026-11-05)
exclude:                                           # any field (and its children); '*' matches any part of a path
  - "*.orcid"
  - discoverability.contributors
hidden:                                            # output_format v2: visible: false on the field and everything under it
  - "*.organization"
blank:                                             # output_format v2: empty description and options (field and below)
  - "*.organization"
map_from:                                          # output_format v2: {target block: source block}, leaf by leaf
  discoverability.datacard.sensitivity: discoverability.sensitivity

overrides:                                          # manual decisions, applied last
  discoverability.identification.name: {required: true}
description_add:                                   # keep the template text, add a note before / after it
  discoverability.contact.succession_note: {after: "Include both a person and a group."}
```

### 5.2 Recording a decision with `overrides`

**Do not edit a `.generated.yaml` file by hand.** The next run overwrites it. Put the decision in the config
instead:

```yaml
overrides:
  interoperability.provenance.source_data.name: {required: true}
  discoverability.additional_contacts: {type: null, options: null}
  discoverability.release_status: {options: [Draft, Under_Review, Approved, Published, Deprecated]}
```

The key is the field path with dots (as in the diff and review files). The value is a dict of breakdown keys
to set on that field. Re-run `generate_breakdown.py`. Every override applied is listed in the review report.

---

## 6. How each part of a field is decided

The template decides everything by default, the same way the v1.2 breakdown was built.

| Breakdown key | Rule |
|---|---|
| structure | Template keys, in template order, minus `exclude` (applied first, so one-of groups and `required` see the reduced tree; a pattern that matches nothing, or that empties a block, stops the run). YAML lists (`- item:`) are flattened: the first item's keys become children. |
| `value` | The template's placeholder, verbatim (`${…}`, `__…__`, `[]`, or a literal). A key followed by `- __X__` takes `__X__`. |
| `required` | A `[*_required]` tag, or a `${…}` placeholder unless a `[required if …]` tag makes it conditional. An untagged folder is required when one of its children is (agent blocks and discriminators excluded). Inside a person/organization/ai_model/software block, `[situational_required]`, `${…}` a key in `alternatives.required_keys`, or a `[required for <block>]` tag naming that block means "required if this block is chosen" (Vedant's email). A discriminator is required when its block is present. A field inside an optional block is not required (MAVEN would otherwise force it whenever the capability is "Yes"), except inside a one-of block: MAVEN enforces those fields only when the discriminator selects that block (`app.py`, `render_tier1_yaml_form`). |
| `type` / `options` | A `${"A\|B"}` placeholder, or a vocabulary written in the comment: `A \| B \| "C d"` anywhere (`select one from list:`, `use vocabulary:`, `Allowed values:`), a bullet list `- A: meaning`, or aligned rows `GD  Genome/Genetic Data  — …`. Lists after `e.g.`, and lists inside a commented-out YAML example, are skipped. Exactly Yes/No becomes `radio`, anything else `dropdown`. A list match that starts inside a token (`openmpi/4.1 \| Summit`) is skipped. A required dropdown with no none/n/a/other choice gets `extra_option` (rule 2 in Vedant's email). Top-level `supports_*` get no type: MAVEN always renders them as Yes/No. |
| `description` | The template comment without its `[tag]` and `###---X---###` heading, except that a condition written in the tag (`[required if …]`, `[either … or … is required]`, `[at least one … required if …]`) is kept at the front, because MAVEN does not enforce it; otherwise the comment lines above the key. Quoted as `" …"`, or `' …'` when the text contains `"`. With `guide_for_top_level: true`, top-level keys are prefixed with the guide's table text. A `[situational_required]` field in an optional list item whose comment states no condition gets "Required if an entry is added." in front (MAVEN cannot enforce it). With `alternatives.choice_hint`, each one-of block gets "Fill in only if <role> is <kind>; leave <others> empty." |
| `conditional_context` / `condition_discriminator` | When a block has two or more agent sub-blocks: use the existing sibling key from `discriminator_keys`, or add one named `synthesize_as` (v2.0 has none). |
| `description_add` | Applied with the overrides: `{before: text, after: text}` is joined to the template description (a period is added before `after` when the text ends without one). |
| `overrides` | Applied last. Any key can be set, e.g. `{type: int}`; with `output_format: v2` also `visible`, `mapping` and a pre-filled `value`. |
| `output_format: v2` | Vedant's field format (2026-11-04), written after all rules above. Every field: `description`, `visible` (default `true`), `value`. A leaf also gets `type` (`int` \| `float` \| `string` \| `list` \| `dropdown`; `radio` and the top-level `supports_*` become a Yes/No `dropdown`; `[]` becomes `list`, anything else `string`), `options` (the list for a dropdown, otherwise `null`), `length` (`0` for a list, otherwise `null`), `required`, `value` (empty: `""`, or `[]` for a list, unless an override sets it) and `mapping` (`null` unless an override sets a field path). Parents get no `required`. `conditional_context` / `condition_discriminator` are kept. Then `hidden` (paths or `*` patterns) sets `visible: false` on a field and everything under it, and `map_from` sets each leaf's `mapping` to the same leaf in the source block; a path that matches nothing stops the run. Pre-filled values come from `overrides` (`{value: ...}`). | `blank` (paths or `*` patterns) empties the description of a field and everything under it and the options of its leaves (a dropdown left without options gets `type: null`). A hidden leaf with a pre-filled value or a mapping gets an empty description and `type` / `options` / `length` null. Leaf sub-fields are written one per line in the order description, visible, mapping, type, options, length, required, value.

---

## 7. Results

### 7.1 v1.2: generated vs. Vedant's breakdown

| Part | Match |
|---|---|
| Field paths | 379 / 379 (100%), none missing or extra |
| `value` | 379 / 379 (100%) |
| `conditional_context` / discriminator | 379 / 379 (100%) |
| `required` | 365 / 379 (96%) |
| `type` | 370 / 379 (98%) |
| `options` | 356 / 379 (94%) |
| `description` | 290 / 379 (77%, at ≥ 80% text similarity) |
| MAVEN form rule check | 0 problems |

Every remaining difference is listed in `v1.2_vs_vedant.diff.md`. Most of them are not generator errors:

- **`required` (14):** `creator.ai_model.relationship` and `creator.software.relationship` are `true` because their
  tags say `[required for ai_model]` / `[required for software]` (the v1.2 file has `false`). The other 12 are places where the v1.2 file is not consistent, which Vedant confirmed (2026-10-28) are
  quick choices rather than rules: `organization.ror_id` should be `false`; fields inside an optional block
  (`source_data.*`, `maintainer.*`, `reviewed_by.*`) follow the rule in section 6. `contact.person.email` and
  `primary_id.value` are set to `true` with `overrides`, as Vedant asked.
- **`type` (9):** fields that have a vocabulary in their comment but were not made dropdowns in the v1.2 file
  (e.g. `workflow.state`, `checksum_type`, `agreement_type`).
- **`options` (30):** the 9 fields above, and mostly the extra `None`. The generator adds it to *required* dropdowns, as Vedant's
  email asks. The v1.2 file added it to some *optional* dropdowns instead. Also a typo in the v1.2 file
  (`Resourcesm`, fixed in the repo file on 2026-11-04) and the classification levels copied into `classification_category`.
- **`description` (99):** wording only; the v1.2 file often left the text empty or merged guide text.

How to read a line of the diff file:

```
- `discoverability.contact.person.email`: generated `False` / reference `True`
```

means that, for that field, the generator wrote `required: false` and Vedant's file has `required: true`.

### 7.2 Template only vs. LinkML schema

The schema can be switched on by uncommenting the `schema:` line in a config. The schema then decides
`required` and the dropdown options. Against Vedant's v1.2 file it matches less well (`required` 352,
`options` 342, `description` 224), which is why it is off by default. It remains useful as a cross-check: the
schema is what the datacard validator uses.

### 7.3 v2.0

- 380 template fields are generated (510 minus the 130 in `exclude`), plus 6 `agent_type`; 111 of the 297 leaves are hidden (part 4); the file passes the rule check with 0 problems (for the v2 format,
  `compare_breakdowns.check_rules` checks Vedant's keys: every leaf has all 8, `options` only on dropdowns,
  `length` only on lists, `mapping` points to an existing field).
- Against the 59 fields built by hand so far (`supports_*`, `datacard`, `identification`): `required`, `type`,
  `description` and `conditional_context` match 100%. The `value` differences are the generator using v2.0's
  own placeholders (e.g. `${SOURCE_MARKING_STRING}`) where the hand copy kept v1.2's (`${STRING}`). The
  `options` differences are the hand copy adding `None` to optional dropdowns.
- The items that still need a human decision are in `genesis_dc_v2.0_breakdown.generated.review.md`.

---

## 8. Adding a new datacard version

1. Download the new archive into `inputs/`.
2. Copy the closest config, e.g. `config_v2.0.yaml` → `config_v2.1.yaml`.
3. Update `title`, `output`, `template` and `guide`. Open the archive to find the exact file paths inside it.
4. Run `python generate_breakdown.py config_v2.1.yaml`.
5. Read the `.review.md` report. For every decision, add an entry under `overrides:` and re-run.
   A path in `overrides` or `no_extra_option` that is not in the new template stops the run with a `KeyError`
   that lists every such path (`override paths not in the template: [...]`): the field was renamed or moved, so
   update the path (or drop the entry).
6. Run `python compare_breakdowns.py <output>.yaml`. It must report 0 problems.
7. Optional: compare with the previous version's breakdown (`--reference`) to see what changed.

---

## 9. Troubleshooting

| Message | Cause and fix |
|---|---|
| `FileNotFoundError: ... inputs/data-cards-...` | The archive is not in `inputs/`, or has a different name. See section 2.2. |
| `KeyError` naming a path inside the archive | The path inside the archive is wrong (it changes between versions). List the archive's contents and fix `template:` / `guide:`. |
| `ModuleNotFoundError: No module named 'yaml'` | Activate the MAVEN environment, or `pip install pyyaml`. |
| `MAVEN rule check: N problem(s)` | Each problem names the field and the rule; fix it with an `overrides` entry. |

---

## 10. Known limits

- MAVEN's form has no multiselect, so list fields with a vocabulary (e.g. `role`) become single-choice
  dropdowns.
- v2.0 has no discriminator (`alternatives.synthesize_as: null`, Vedant 2026-11-05): no `agent_type`, no
  `conditional_context`; `person` / `organization` / ... are plain sub-blocks.
- `xCard` is included in v2.0 since 2026-11-05 (hidden, `card_type: dataset`); the v2 rule check has no `supports_xCard` rule.
