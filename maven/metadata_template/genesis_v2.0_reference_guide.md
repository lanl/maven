# Genesis Mission Data Card v2.0.0 — Field Reference Guide

Document version: 2.0.0
Applies to template: Genesis Mission Data Card **v2.0.0** (`template_version: "2.0.0"`)
Companion schema: `genesis_datacard.yaml` (LinkML, `datacard_schema/src/genesis_datacard/schema/genesis_datacard.yaml`)

---

## How to Use This Guide

This guide is a companion to the Genesis Mission Data Card template (`genesis_datacard_merged_shared.md`, template v2.0.0). It explains every YAML frontmatter field: what it means, how to fill it in, which controlled vocabulary applies, and whether it accepts a single value or a list of entries. It also describes the Markdown narrative body of the template and, in the **Standards Alignment** section, how data card fields map to external metadata standards.

The guide mirrors the template's structure: a root `xCard` block and six intended-capability flags, followed by six top-level blocks — **Discoverability, Accessibility, Interoperability, Reusability, Governed Use,** and **AI Usability**.


---

## Getting Started

### What is a data card?

A data card combines structured metadata and computable natural language into a Markdown document that describes a dataset — what it is, where it came from, who created it, how it can be accessed, and how it can be used. Data cards serve both humans (who need to understand a dataset before using it) and machines (automated pipelines that ingest, catalog, and validate datasets).

In Genesis, every dataset — regardless of size, sensitivity, or publication state — should have a data card. A data card can be created at the same time as the dataset, or as early in the workflow as possible. Data cards may be updated over time as the dataset matures, and they may be shared publicly or kept private depending on the sensitivity of the data card itself (see **Sensitivity — two independent fields** below).

### Data cards and the xCard framework

The v2.0.0 template is designed to be used within the Genesis Mission **xCard** framework. xCards are structured metadata and narrative assets that describe research objects, including datasets, models, and AI agents. Every data (and xCard) card begins with a root `xCard` block that declares the card type. For data cards the type is always `dataset`.

### What's new in v2.0.0 (changes from v1.2)

**Structure**
- New root `xCard` block with `card_type: dataset` (required).
- `agent_type` and `type: person | organization` discriminator keys have been **removed**. An agent is now identified by *which* sub-block is populated (`person`, `organization`, `ai_model`, or `software`). See **Agent blocks** below.
- `authors`, `contributors`, and `review_provenance_companion[].reviewed_by` now accept all four agent types, including `ai_model` and `software`.
- `discoverability.contact` is now a **list**.
- The `_repository` reference block has been removed from the template.
- `use_governance.need_to_know_basis` has been removed from the template.
- `domain_metadata.fields` is now a **list of entries with a `name` key** (not a map keyed by field name), and the schema version moved to `domain_metadata.schema_reference.version`.
- `related_resources.publications` now uses `value` instead of `type` as the identifier for each related publication.
- `spatial_coverage.geo_location_box` sub-fields are now snake_case (`west_bound_longitude`, etc.).
- `change_log[]` uses `datacard_version` (was `data_card_version`).
- New fields: `dataset_publisher.description`; `research_organizations[].role`; `role` on contact persons; `description` on `source_data[]` and `related_resources.datasets[]` entries.
- `additional_contacts` no longer has a contact_details: wrapper; it has the same list structure as contact.
- `contact` may now be an organization; v1.2 allowed only a person.
- `review_provenance_companion[].reviewed_by.person.ror_id was removed.` The ROR ID now goes under person.affiliation.ror_id, and reviewer persons gain orcid, affiliation, and role.
- `additional_licenses[]` entries no longer have a "which subset" description; use the same four fields as license.
- `stewardship.maintainer` also lost its type key. The general bullet on discriminator keys covers this.
- Ownership, stewardship, and review `agent` blocks now include role, not just contact persons.

**Types and cardinality**
- `dataset_description.science_domain` and `domain_metadata.science_domain` are now lists (they were a single value).
- `normalized_control_basis` is now a list, with at least one value and no duplicates (it was a single value).
- `features[]` gains description, and range is a string.

**Controlled vocabularies**
- `RelationshipTypeEnum` is now a single DataCite-aligned vocabulary with ML extensions. The v1.2 "base" and "extended" relationship lists (`is_based_on`, `used_to_create`, `used_to_process`, `used_to_analyze`, `recorded_by`, `trained_on`, `evaluated_on`) are **no longer valid**.
- `RoleEnum` extended with DataCite contributor types. `Data_Curation` and `Data_Collection` are **no longer valid** (use `Data_Curator` or `Investigation`, as appropriate).
- `ProductTypeEnum` revised; default is now `Dataset` (was `Data`). Data, Paper_or_Proceedings were removed.
- `DatasetTypeEnum` reduced to the single value `Instrument`. OSTI codes that are now invalid are GD, IM, ND, SM, FP, I, MM, MD, AS, IP, and IG.
- `approved_environments` is now a controlled vocabulary (`ApprovedEnvironmentEnum`).
- All identifier `type` fields use the full `IdentifierTypeEnum`.
- `PrivacyControlBasisEnum` spelling corrected to `HIPAA`.
- `IdentifierTypeEnum` changed in both directions. osti, sand, la-ur, arxiv, and report were removed; purl, urn, uuid, and unregistered are available everywhere. The existing bullet ("all identifier type fields use the full enum") doesn't warn that some old values stop working.

**Requirements and annotations**
- New generic annotations: `[situational_required]`, `[if_applicable]`, `[recommended]`.
- Now `[situational_required]`: `authors`, `dataset_publisher`, `citation`, `compliance`, `embargo_until`, `classification_level`, `classification_category`, `cui_specified_categories`, `export_control_basis`, `agreement_type`, `*_use_conditions`, `checksum_type`, `checksum_value`.
- Version strings use three-part semantic versions (`"2.0.0"`, `"1.0.0"`).
- `license` is **strongly recommended** (no longer stated as required) when `release_status = Approved | Published`.
- New cross-field validation rules for sensitivity (see `discoverability.sensitivity`) and workflow (`embargo_until` must be absent when `state = Published`).
- Now required: `reusability.integrity` (was if-applicable) and `tags.object_type` ([discoverability_required] whenever tags is present).
- Now situational: `tags.project` and `preferred_citation.howpublished`.
- Now optional: `privacy.phi_status` (was [governed_use_required]) and `preferred_citation.publisher`. The v1.2 rule "either publisher or howpublished is required" is gone.
- `datacard.id` is no longer required by the schema, which resolves the earlier discrepancy.
- `identification.project` now defaults to "genesis" and accepts non-Genesis project names. v1.2 told authors to use not_applicable for non-Genesis projects.
- `normalized_control_basis`: if present, it must have at least one value.

**Migrating a v1.2 data card to v2.0.0**
1. Set `template_version: "2.0.0"` and add the root `xCard: {card_type: dataset}` block.
2. Delete every `agent_type:` and `type: person | organization` line (created_by, contact, authors, contributors, maintainer, reviewed_by).
3. Convert `contact` to a list; flatten `additional_contacts` (remove `contact_details:`).
4. In `review_provenance_companion[].reviewed_by.person`, move `ror_id` under `affiliation.ror_id`.
5. Rename `change_log[].data_card_version` → `datacard_version`.
6. Rename `geo_location_box` keys to snake_case.
7. Convert `domain_metadata.fields` from a map to a list of entries with `name`; move `domain_metadata.version` to `schema_reference.version`.
8. Wrap single values in lists: `science_domain` (both places) and `normalized_control_basis`.
9. Replace removed vocabulary values:
    - relationships (`used_to_*`, `trained_on`, `evaluated_on`, `recorded_by`, `is_based_on`)
    - roles (`Data_Curation`, `Data_Collection`)
    - `product_type: Data` → `Dataset`
    - OSTI `dataset_type` codes → `Instrument` or delete
    - identifier types `osti` / `sand` / `la-ur` / `arxiv` / `report` → `other` or `url` (report numbers can go in `citation.report_number`)
    - `HIPPA` → `HIPAA`
    - freetext `approved_environments` → `ApprovedEnvironmentEnum` values, with the freetext moved to `access_restrictions`
10. Remove the `_repository`, `need_to_know_basis`, and `additional_licenses[].description` content.
11. Add now-required content: `integrity` (if `supports_reusability = "Yes"`), and `tags.object_type` / `tags.project` if `tags` is present.
12. If `identification.project` was `not_applicable`, replace it with a project name.
13. **v1.2 → v2.0.0 relationship replacements:** `used_to_create` → `generates`; `used_to_process` → `processes`; `used_to_analyze` → `analyzes`; `trained_on` → `is_trained_on` / `is_used_for_training` (by direction); `evaluated_on` → `is_evaluated_on` / `is_used_for_evaluation`; `is_based_on` → `is_derived_from`; `recorded_by` → `is_collected_by`.
14. Validate against the v2.0.0 schema, then record the migration in `change_log` with a MAJOR `datacard_version` increment (e.g., `2.0.0`).

### Choose your intended capabilities first

The data card declares six independent **intended capability** flags at the document root. Each is a `"Yes"`/`"No"` switch that declares whether this data card is meant to support that capability, and each one turns on its own set of required and optional fields.

| Capability flag | Values | Meaning |
|---|---|---|
| `supports_discoverability` | **Always `"Yes"`** | Dataset is intended to be findable and identifiable in catalogs and repositories. Required for every data card. |
| `supports_accessibility` | `"Yes"` \| `"No"` | Dataset is intended to be shared or accessed by others — internally, with collaborators, or publicly. Optional but recommended. |
| `supports_interoperability` | `"Yes"` \| `"No"` | Dataset is intended to be integrated or combined with other datasets or systems. Optional but recommended. |
| `supports_reusability` | `"Yes"` \| `"No"` | Dataset is intended to be reused by others for the same or different purposes. Optional but recommended. |
| `supports_governed_use` | `"Yes"` \| `"No"` | Dataset is intended to be shared or accessed under specific governance or oversight (security controls, export control, IRB, formal review). Optional but **strongly recommended**. |
| `supports_ai_usability` | `"Yes"` \| `"No"` | Dataset is intended for AI training, evaluation, inference, or other AI-related purposes. Optional but **strongly recommended**. |

These capabilities are **not tiers you "upgrade" through** — they are independent toggles. A data card can have `supports_accessibility = "No"` and `supports_ai_usability = "Yes"` at the same time if that reflects the dataset's real situation. Setting a flag to `"Yes"` is a declaration of *intent*; it does not certify that the dataset currently meets every criterion of that capability. It tells catalog tooling which fields to expect.

When a flag is `"Yes"`, the corresponding top-level block (`accessibility`, `interoperability`, `reusability`, `governed_use`, `ai_usability`) **must be present** (schema rule). The `discoverability` block is always required.

The governance fields deserve special mention: sensitivity and control metadata are not just descriptive. They help determine what can be shown, to whom, at what level of detail, whether an asset is broadly discoverable or only partially visible, and whether access should be allowed, restricted, or routed for additional review.

You can start with only `supports_discoverability = "Yes"` for a brand-new in-workflow dataset and turn on more flags as the data card matures. Record each change in `change_log`.

### Understanding field annotations

Every field in the template is annotated to tell you whether you need to fill it in. A field may carry more than one annotation (e.g., `[if_applicable, recommended]`).

| Annotation | Meaning |
|---|---|
| `[required]` | Required for **all** data cards regardless of which capability flags are set. |
| `[situational_required]` | Required only when a condition on another field is met (e.g., "required if `classified_status = "Yes"`", "required when `release_status = Approved \| Published`"), or when its parent block is included (e.g., `given_name` is required *if* a `person` block is present). The condition is stated in the field's entry. |
| `[if_applicable]` | Optional; include when relevant and available. Not tied to a specific capability. |
| `[recommended]` | Strongly recommended but not required. Usually combined with another annotation. |
| `[discoverability_required]` | Required because `supports_discoverability = "Yes"` (i.e., always). |
| `[discoverability_if_applicable]` | Optional under discoverability; populate if it applies, otherwise leave blank or delete. |
| `[accessibility_required]` | Required when `supports_accessibility = "Yes"`. |
| `[accessibility_if_applicable]` | Optional under accessibility. |
| `[interoperability_required]` | Required when `supports_interoperability = "Yes"`. |
| `[interoperability_if_applicable]` | Optional under interoperability. |
| `[reusability_required]` | Required when `supports_reusability = "Yes"`. |
| `[reusability_if_applicable]` | Optional under reusability. |
| `[governed_use_required]` | Required when `supports_governed_use = "Yes"`. |
| `[governed_use_if_applicable]` | Optional under governed use; strongly recommended if applicable. |
| `[ai_usability_required]` | Required when `supports_ai_usability = "Yes"`. |
| `[ai_usability_if_applicable]` | Optional under AI usability; strongly recommended if applicable. |

> **Requirements nest.** A `[discoverability_required]` field inside a block that is itself optional (e.g., inside an optional `person` sub-block) is only required when that block is present. Likewise, `[*_required]` fields in the Accessibility, Interoperability, Reusability, Governed Use, and AI Usability blocks apply only when the corresponding capability flag is `"Yes"`.

### Understanding placeholder conventions

| Placeholder | Meaning |
|---|---|
| `${VALUE}` | Fill in your value. Used for required and situational-required fields. |
| `__VALUE__` | Fill in if applicable; otherwise delete, leave blank, or replace with `not_applicable` if the field definitively does not apply. |
| `${"Yes\|No"}` | Required Yes/No field — replace with exactly `"Yes"` or `"No"` (quoted). |
| `__"Yes\|No"__` | Optional Yes/No field — replace with `"Yes"` or `"No"`, or delete. |
| `[]` | Empty list — add entries as YAML list items, or leave as `[]`. |
| `not_applicable` | Literal value: this field definitively does not apply to this dataset. |

**Important distinction:** blank (or an unreplaced `__VALUE__`) means the information is *not yet known or not yet captured*. `not_applicable` means the field *definitively does not apply*. Catalog tooling uses this distinction for completeness scoring — blank fields may trigger reminders, while `not_applicable` fields are treated as complete. Some fields validate against a pattern that does not accept `not_applicable` (e.g., `publicly_facing_landing_page_url`, license `url`); for those, delete the field instead.

Before submission, replace or remove **every** `${...}` and `__...__` placeholder.

### Single-entry vs. multi-entry fields

Each field in this guide is marked as one of:
- **Single entry** — one object or scalar value (e.g., `dataset_description.dataset_summary`).
- **List (0 or more)** — a YAML list that may be empty (`[]`) or contain multiple entries (e.g., `additional_ids`, `related_resources.datasets`).
- **List (1 or more required)** — a YAML list that must contain at least one entry when its block is required (e.g., `keywords`, `created_by`, `contact`).

### Agent blocks: person, organization, ai_model, software

Many fields describe an *agent* — someone or something that created, contributed to, maintains, or reviewed the dataset or data card. In v2.0.0 there is **no `agent_type` or `type` key**. Instead, each agent entry contains exactly **one** populated sub-block, and the schema rejects entries with more than one:

| Sub-block | Use for | Sub-fields |
|---|---|---|
| `person` | A human individual | `given_name` *(situational_required)*, `family_name` *(situational_required)*, `orcid` *(if_applicable, recommended)*, `email` *(if_applicable)*, `affiliation.name` *(situational_required if affiliation is given)*, `affiliation.ror_id` *(if_applicable, recommended)*, `role` (**list**, `RoleEnum`) |
| `organization` | A team, office, lab, facility, or site without a named individual | `name` *(situational_required)*, `ror_id` *(if_applicable, recommended)*, `role` (**list**, `RoleEnum`) |
| `ai_model` | An AI model that generated or substantially contributed content | `name` *(situational_required)*, `version` *(if_applicable, recommended)*, `accessed_date` *(situational_required, `YYYY-MM-DD`)*, `identifier.type` / `identifier.value`, `role` (**list**), `relationship` *(situational_required, `RelationshipTypeEnum`)* |
| `software` | A pipeline, script, or tool that is not an LLM | `name` *(situational_required)*, `version` *(if_applicable, recommended)*, `identifier.type` / `identifier.value`, `role` (**list**), `relationship` *(situational_required, `RelationshipTypeEnum`)* |

Delete the sub-blocks you do not use. Which sub-blocks are allowed depends on the field:

| Field | Allowed sub-blocks |
|---|---|
| `datacard.created_by[].creator` | person, organization, ai_model, software |
| `authors[]`, `contributors[]` | person, organization, ai_model, software |
| `review_provenance_companion[].reviewed_by` | person, organization, ai_model, software |
| `contact[]`, `additional_contacts[]` | person, organization (at least one) |
| `reusability.stewardship.maintainer` | person **or** organization (not both) |

Formats:
- `orcid`: `https://orcid.org/0000-0000-0000-0000` (digits or uppercase letters; the final character may be `X`). Required where DOE employee/contractor author policy applies.
- `ror_id`: `https://ror.org/` followed by the 9-character ROR ID, e.g. `https://ror.org/02vwzrd76`.
- `email`: a valid address (`name@domain.tld`).


**`role` controlled vocabulary** (`RoleEnum`, a list; combines CRediT, DataCite contributorType, Dublin Core, and PROV roles — see [Standards Alignment](#standards-alignment)):
`Conceptualization` \| `Contact_Person` \| `Contributor` \| `Creator` \| `Data_Curator` \| `Data_Manager` \| `Distributor` \| `Editor` \| `Formal_Analysis` \| `Funding_Acquisition` \| `Hosting_Institution` \| `Investigation` \| `Methodology` \| `Producer` \| `Project_Administration` \| `Project_Leader` \| `Project_Manager` \| `Project_Member` \| `Publisher` \| `Registration_Agency` \| `Registration_Authority` \| `Related_Person` \| `Researcher` \| `Research_Group` \| `Resources` \| `Rights_Holder` \| `Software` \| `Sponsor` \| `Supervision` \| `Translator` \| `Validation` \| `Visualization` \| `Work_Package_Leader` \| `Writing_Original_Draft` \| `Writing_Review_Editing` \| `Other`

Values use underscores, not spaces (`Data_Curator`, not `Data Curator`).

**`relationship` controlled vocabulary** (`RelationshipTypeEnum`) — used by `ai_model`/`software` agents, `provenance.source_data[]`, and all `related_resources` entries. Read each value as "*A* `<relationship>` *B*", where the direction is stated in the field's entry. Values:

| Group | Values |
|---|---|
| Citation & reference | `cites`, `is_cited_by`, `references`, `is_referenced_by` |
| Part / series | `is_part_of`, `has_part`, `in_series`, `is_published_in` |
| Versions & replacement | `has_version`, `is_version_of`, `is_previous_version_of`, `obsoletes`, `is_obsoleted_by`, `continues`, `is_continued_by` |
| Derivation & source | `is_derived_from`, `is_source_of`, `is_variant_form_of`, `is_original_form_of`, `is_identical_to`, `is_translation_of`, `has_translation` |
| Supplements & documentation | `is_supplement_to`, `is_supplemented_by`, `describes`, `is_described_by`, `documents`, `is_documented_by`, `has_metadata`, `is_metadata_for` |
| Review | `reviews`, `is_reviewed_by` |
| Dependencies | `requires`, `is_required_by` |
| Compilation & collection | `compiles`, `is_compiled_by`, `collects`, `is_collected_by` |
| Tools acting on data | `generates`, `is_generated_by`, `processes`, `is_processed_by`, `analyzes`, `is_analyzed_by` |
| ML / AI | `is_trained_on`, `is_used_for_training`, `is_evaluated_on`, `is_used_for_evaluation`, `tested_on`, `validated_on`, `fine_tuned_from`, `has_evaluation` |
| Fallback | `other` |

### Identifiers

Identifier blocks (`type` + `value`) appear throughout the template: `datacard.id`, `identification.primary_id`, `additional_ids`, `supersedes`, `superseded_by`, `parent_collection.identifier`, agent and resource `identifier` blocks, `domain_metadata.schema_reference`, and `related_resources.publications[]`. All use the same controlled vocabulary (`IdentifierTypeEnum`):

`ark` \| `doi` \| `handle` \| `local` \| `purl` \| `url` \| `urn` \| `uuid` \| `other` \| `unregistered`

**Rule:** if `type` is provided, `value` must also be provided, and vice versa. See [Appendix B](#appendix-b-identifier-type-quick-reference) for formats.

### Yes \| No fields

Yes/No fields are always single-entry. The only valid values are `"Yes"` or `"No"` — case-sensitive and **quoted**. Do not use `true`/`false`, `yes`/`no`, `1`/`0`, or other synonyms (unquoted `Yes`/`No` may be parsed as booleans by some YAML parsers). Some status fields use extended vocabularies (e.g., `"Pending_Review"`, `"Unknown"`, `"Conditional"`); these are noted field by field.

### Sensitivity — two independent fields, a critical concept

The template has two independent sensitivity blocks that are easy to confuse:

- **`discoverability.datacard.sensitivity`** — the sensitivity of *this data card document itself*
- **`discoverability.sensitivity`** — the sensitivity of *the dataset* the data card describes

These will often differ. A common and valid scenario: a publicly shareable data card (`discoverability.datacard.sensitivity.overall_sensitivity = Public`) describes a dataset containing controlled information (`discoverability.sensitivity.overall_sensitivity = CUI` or `Classified`). The open data card lets people discover that the dataset exists and understand its general contents, while the underlying data remains protected.

**Never set these to match each other by default.** Set each one independently based on what it describes. The same independence applies to `accessibility.access_policy`, which describes access conditions for the *dataset* (not the data card).

> Sensitivity terminology is still under Genesis governance review; the vocabulary may evolve.

### Workflow state vs. release status

Two fields describe complementary but distinct aspects of a dataset's lifecycle:

- **`discoverability.workflow.state`** — the technical/processing lifecycle position of the data itself (`Raw` → `Archived`)
- **`discoverability.release_status`** — the publication and governance state of the dataset record (`Draft` → `Deprecated`)

Keep them logically consistent. Common alignments:

| `workflow.state` | Expected `release_status` |
|---|---|
| `Raw`, `Processing`, `QA`, `Analysis` | `Draft` |
| `Review` | `Under_Review` |
| `Embargo`, `Published` | `Approved` or `Published` |
| `Archived` | `Deprecated` or `Published` |

`release_status` also drives several conditional requirements: when it is `Approved` or `Published`, at least one author and a `dataset_publisher` are required, and `license` and `citation` are expected. `compliance` is populated from `Under_Review` onward.

### Licenses and governance

A public/open license is not always the governing instrument for use. Some controlled datasets may not have an SPDX-style reuse license at all; use may instead be governed by contract, agreement, institutional review, or repository policy — see the `governed_use` block for those cases.

### Schema validation

A companion LinkML schema (and generated JSON Schema) for machine validation is available at https://gitlab.com/amsc2/modcon/dbs/data-cards/ — see the repository README for usage. Validate your data card before submission using the Genesis LinkML data card validator, or any JSON Schema–compatible YAML validator.

### Future extensions

The template will evolve. Fields under consideration include ontology alignment, further interoperability standards (DCAT, schema.org), audience classification, consent typing, and catalog-managed collection membership. See https://gitlab.com/amsc2/modcon/dbs/data-cards/-/milestones for the roadmap.

---

## Root: `xCard` and Capability Flags

These fields sit at the document root, above the `discoverability:` block.

### `xCard.card_type`
- **Annotation:** `[required]`
- **Single entry.**
- The xCard type. For every Genesis data card the only valid value is `dataset`. Do not modify.

```yaml
xCard:
  card_type: dataset
```

### Capability flags

| Field | Annotation | Single/Multi | Controlled vocabulary |
|---|---|---|---|
| `supports_discoverability` | `[required]` | Single | `"Yes"` (only valid value) |
| `supports_accessibility` | `[required]` | Single | `"Yes"` \| `"No"` |
| `supports_interoperability` | `[required]` | Single | `"Yes"` \| `"No"` |
| `supports_reusability` | `[required]` | Single | `"Yes"` \| `"No"` |
| `supports_governed_use` | `[required]` | Single | `"Yes"` \| `"No"` |
| `supports_ai_usability` | `[required]` | Single | `"Yes"` \| `"No"` |

Each flag is a statement of *intent* — see **Choose your intended capabilities first** above. When a flag is `"Yes"`, its top-level block must be present.

---

## Section: Discoverability `[discoverability_required — always Yes]`

The `discoverability:` block is required for **all** data cards because `supports_discoverability` is always `"Yes"`. Populate `[discoverability_required]` fields for every dataset; `[discoverability_if_applicable]` fields are optional but recommended.

---

### `discoverability.datacard` — Data Card Metadata

- **Annotation:** `[discoverability_required]`
- **Single entry.**
- This sub-block describes the **data card document itself** — not the dataset.

#### `datacard.template_version`
- **Annotation:** `[discoverability_required]`
- **Single entry.**
- Do not modify. Fixed at `"2.0.0"` for this template version; used by parsers to apply version-specific validation logic.

#### `datacard.datacard_version`
- **Annotation:** `[discoverability_required]`
- **Single entry.** Pattern: `MAJOR.MINOR` or `MAJOR.MINOR.PATCH`.
- The version of this data card document — not the dataset, not the template. Default `"1.0.0"` when first created.
- Increment PATCH (1.0.0 → 1.0.1) for minor corrections; MINOR (1.0.0 → 1.1.0) for content additions/updates; MAJOR (1.x → 2.0.0) for structural changes (e.g., migrating template versions, or enabling/disabling a capability flag in a way that changes which sections are populated).
- Every time you update `datacard_version`, add a corresponding `change_log` entry.

#### `datacard.filename`
- **Annotation:** `[discoverability_required]`
- **Single entry.**
- Naming convention: `genesis_datacard_<snake_case_dataset_name>.md`. For datasets not associated with a Genesis project or sub-project, use `genesis_datacard_other_<snake_case_dataset_name>.md`.
- The `<snake_case_dataset_name>` portion should match `identification.name` converted to snake_case.
- **Validation pattern:** `^genesis_datacard_[a-z0-9]+(_[a-z0-9]+)*\.(md|yml|yaml)$` — lowercase letters, digits, and single underscores only; no hyphens, spaces, or uppercase. `.yml`/`.yaml` are accepted for YAML-only cards.
- Example: "SNS Beam Position Monitor Data 2024" → `genesis_datacard_sns_beam_position_monitor_data_2024.md`
- Example (non-Genesis): "LCLS X-ray Diffraction Data" → `genesis_datacard_other_lcls_xray_diffraction_data.md`

#### `datacard.language`
- **Annotation:** `[discoverability_required]`
- **Single entry.** Pattern: two lowercase letters, or `not_applicable`.
- ISO 639-1 language code for the language this **data card document** is written in. Default `en`. Examples: `en` \| `es` \| `fr` \| `de` \| `zh` \| `ru` \| `ar` \| `pt` \| `ja` \| `ko`.
- Distinct from `interoperability.data_structure.language` (the language of the dataset content).

#### `datacard.id`
- **Annotation:** `[discoverability_if_applicable]`
- **Single entry** (sub-fields `type`, `value` — both `[if_applicable, recommended]`).
- A persistent identifier for the data card document itself, distinct from the dataset identifier. Most data cards will not have one initially. Populate only if the data card is registered in a catalog or repository as an independent object; otherwise delete the block.
- `type`: `IdentifierTypeEnum`. `value`: the identifier value. If either is provided, both must be.

#### `datacard.sensitivity` — sensitivity of the data card document
- **Annotation:** `[discoverability_required]` (block); sub-fields vary — see table.
- **Single entry.**
- See **Sensitivity — two independent fields** above. Ask: "if someone reads only this document, what is the most sensitive information they would see?"
- Shares an identical field layout with `discoverability.sensitivity` (the dataset's sensitivity).

| Field | Annotation | Single/Multi | Controlled vocabulary / format |
|---|---|---|---|
| `overall_sensitivity` | `[discoverability_required]` | Single | `OverallSensitivityEnum`: `Public` \| `Unclassified_Uncontrolled` \| `CUI` \| `UCNI` \| `Classified` \| `Legacy_Controlled` \| `Mixed` \| `Other_Controlled`. A **summary** field for display/discovery only; it does not replace the authoritative fields below. Use `Public` for unclassified, non-sensitive assets. |
| `source_marking_string` | `[discoverability_required]` | Single | Freetext — exact marking/banner/control text as it appears on the source artifact or authoritative review/release output. Use `not_applicable` if no markings apply. Separate multiple markings with `//` and no spaces. e.g. `not_applicable` \| `CUI//SP-EXPT//NOFORN` \| `SECRET//RD//SIGMA 15` |
| `source_marking_scheme` | `[discoverability_required]` | Single | `SourceMarkingSchemeEnum`: `DOE_CUI` \| `DOE_UCNI` \| `EO13526_Classified` \| `AEA_RD_FRD_TFNI` \| `DOD_CUI` \| `DHS_CUI` \| `Legacy_OUO` \| `Legacy_Site_Specific` \| `Other_Agency` \| `None`. Use `None` for unclassified, non-sensitive assets. |
| `classified_status` | `[discoverability_required]` | Single | `"Yes"` \| `"No"` |
| `classification_level` | `[situational_required]` — required if `classified_status = "Yes"` | Single | `ClassificationLevelEnum`: `Top_Secret` \| `Secret` \| `Confidential` |
| `classification_category` | `[situational_required]` — at least one required if `classified_status = "Yes"` | **List** | `ClassificationCategoryEnum`: `NSI` \| `RD` \| `FRD` \| `TFNI` \| `Other_Classified` |
| `classified_control_markings` | `[discoverability_if_applicable]` | **List** | Freetext, one marking per entry, e.g. `NOFORN`, `CNWDI`, `SIGMA 15`, `ORCON`, `REL TO USA, GBR` |
| `cui_status` | `[discoverability_required]` | Single | `"Yes"` \| `"No"` |
| `cui_basic_categories` | `[discoverability_if_applicable]` | **List** | DOE/ISOO-authoritative CUI Basic categories/subcategories, one per entry |
| `cui_specified_categories` | `[situational_required]` — at least one required if `cui_status = "Yes"` **or** `ucni_status = "Yes"` | **List** | DOE/ISOO-authoritative CUI Specified categories/subcategories, one per entry |
| `cui_limited_dissemination_controls` | `[discoverability_if_applicable]` | **List** | e.g. `NOFORN`, `REL TO USA, GBR`, `DISPLAY ONLY USA, GBR`, `RELIDO`. Follow authoritative agency ordering/formatting. If populated with NOFORN / REL TO / DISPLAY ONLY or similar, keep `governed_use.non_sensitivity_governance_metadata.export_control.foreign_national_access_status` consistent. |
| `ucni_status` | `[discoverability_required]` | Single | `"Yes"` \| `"No"` — UCNI is represented separately; do not treat it as an ordinary CUI category |
| `uk_mda_status` | `[discoverability_if_applicable]` | Single | `UKMDAStatusEnum`: `"Yes"` \| `"No"` \| `Unknown` \| `not_applicable` — whether the asset is subject to UK MDA-specific handling; use where relevant to local/site governance |
| `legacy_label_source` | `[discoverability_if_applicable]` | **List** | Freetext deprecated/local labels kept as provenance only, e.g. `OUO`, `SBU`, `Legacy_Site_Marking`. Populate if `source_marking_scheme = Legacy_OUO`. Unique entries. |
| `normalized_control_basis` | `[discoverability_if_applicable]` | **List** (if present, at least one value) | `NormalizedControlBasisEnum`: `Classified` \| `CUI` \| `UCNI` \| `Public_Release_Approved` \| `Legacy_Needs_Mapping` \| `Other_Controlled`. Interpreted basis for legacy/mixed/non-standard markings; does not replace source markings. If `source_marking_scheme = Legacy_OUO` and unresolved, use `Legacy_Needs_Mapping`. |

**Cross-field rules** (enforced by the schema; apply to both sensitivity blocks):

| If… | Then… |
|---|---|
| `overall_sensitivity = Classified` | `classified_status` must be `"Yes"` |
| `overall_sensitivity = CUI` | `cui_status` must be `"Yes"` **and** `classified_status` must be `"No"` |
| `overall_sensitivity = UCNI` | `ucni_status` must be `"Yes"` |
| `classified_status = "Yes"` | `classification_level` and `classification_category` must be present |
| `ucni_status = "Yes"` | `cui_specified_categories` must be present |
| `source_marking_scheme = Legacy_OUO` | `legacy_label_source` and `normalized_control_basis` should be present |

#### `datacard.creation_method`
- **Annotation:** `[discoverability_required]`
- **Single entry.**
- How this data card was created or most recently updated. `DatacardCreationMethodEnum`:
  - `Manual` — created entirely manually by a human author.
  - `Automated` — generated entirely by a pipeline, AI model, or other automated process.
  - `Hybrid` — created using a combination of manual and automated methods (e.g., generated automatically, then reviewed/edited by a person).
- Update to reflect the most recent significant update, not just the initial creation.

#### `datacard.created_date`
- **Annotation:** `[discoverability_required]`
- **Single entry.** ISO 8601 date (`"YYYY-MM-DD"`) the data card was first created. Does not change once set.

#### `datacard.updated_date`
- **Annotation:** `[discoverability_if_applicable]`
- **Single entry.** ISO 8601 date of the most recent update. Revise on every change, including minor edits and version updates.

#### `datacard.change_log`
- **Annotation:** `[discoverability_required]`
- **List (1 or more required)** — append-only, chronological.
- Add a new entry every time the data card is updated. Never delete or overwrite prior entries. If there have been no changes since creation, include a single entry with the creation date and the summary `Initial creation`.

| Sub-field | Annotation | Format |
|---|---|---|
| `change_date` | `[discoverability_required]` | ISO 8601 date (`YYYY-MM-DD`) of this change |
| `datacard_version` | `[discoverability_required]` | Data card version after this change (should match `datacard.datacard_version`) |
| `summary` | `[discoverability_required]` | Brief description of what changed and why, e.g. `Initial creation` \| `Updated license to CC-BY-4.0` \| `Added checksum after file transfer to OSTI` \| `Migrated to template 2.0.0` |

**Validator note:** the schema treats `change_date` as a unique key. If you make two changes on the same day, combine them into one entry.

#### `datacard.created_by`
- **Annotation:** `[discoverability_required]`
- **List (1 or more required)**, in chronological order of contribution.
- All individuals, organizations, AI models, or software tools that created or updated this data card. If an AI model generated the initial draft and a person then edited it, list the AI model first, followed by the person.

Each entry:

| Sub-field | Annotation | Notes |
|---|---|---|
| `contribution_date` | `[discoverability_required]` | ISO 8601 date of this contribution |
| `description` | `[if_applicable]` | What this contributor did, e.g. "Automated generation of data card from dataset metadata" |
| `creator` | `[discoverability_required]` | Agent block — populate exactly **one** of `person`, `organization`, `ai_model`, `software` (see **Agent blocks**) |

For `ai_model` and `software` creators, `relationship` describes the tool's relationship to the data card, typically `generates` (drafted content) or `processes` (transformed/edited content).

**Validator note:** the schema treats `contribution_date` as a unique key; two contributions on the same date may fail validation.

Example:
```yaml
created_by:
  - contribution_date: "2026-03-02"
    description: "Drafted data card from repository metadata"
    creator:
      ai_model:
        name: "Example LLM"
        version: "2026-01"
        accessed_date: "2026-03-02"
        identifier:
          type: "url"
          value: "https://example.org/models/example-llm"
        role: ["Writing_Original_Draft"]
        relationship: "generates"
  - contribution_date: "2026-03-04"
    description: "Reviewed and corrected draft"
    creator:
      person:
        given_name: "Jane"
        family_name: "Doe"
        orcid: "https://orcid.org/0000-0002-5755-8449"
        email: "jane.doe@example.org"
        affiliation:
          name: "Example National Laboratory"
          ror_id: "https://ror.org/02vwzrd76"
        role: ["Writing_Review_Editing", "Data_Curator"]
```

---

### `discoverability.identification`

- **Annotation:** `[discoverability_required]`
- **Single entry.** Key metadata fields that uniquely identify this dataset.

#### `identification.name`
- **Annotation:** required (no template annotation; required by the schema).
- **Single entry.**
- A human-readable name for this dataset. If this data card covers a collection, provide the collection name. Use the same name (in snake_case) in the data card filename.
- Be specific enough to distinguish this dataset from similar ones; avoid unexpanded acronyms. Good: "SNS Beam Position Monitor Calibration Data 2023–2024." Poor: "BPM_data."

#### `identification.project`
- **Annotation:** `[discoverability_required]` (template default `"genesis"`).
- **Single entry.**
- A single human-readable name for the project this dataset belongs to — a Genesis project or sub-project, or a non-Genesis project. Replace the default if necessary. Examples: `genesis` \| `genesis-fusion` \| `genesis-lightsource` \| `nuclear-physics`. Keep consistent with `dataset_description.tags.project`. If unsure which project name to use, contact your data manager.

#### `identification.version`
- **Annotation:** `[discoverability_required]` (template default `"1.0.0"`).
- **Single entry.** Pattern: `MAJOR.MINOR` or `MAJOR.MINOR.PATCH`.
- Dataset version using semantic versioning. Start at `1.0.0` for the first release. MAJOR: breaking changes (schema changed, files reorganized). MINOR: additions (new files, new variables, extended time range). PATCH: corrections.
- Distinct from `datacard.datacard_version`. See `supersedes` / `superseded_by` for linking versions, and `reusability.stewardship.versioning_strategy` for how versions are managed.

#### `identification.primary_id`
- **Annotation:** `[discoverability_required]`
- **Single entry** (sub-fields `type`, `value` — `[if_applicable, recommended]`; if one is given, both are required).
- The main identifier for the dataset; should be globally unique and resolvable if possible. A persistent identifier (DOI or ARK) is strongly recommended.
- Convention: use `ark` (or `local`) for pre-published states; mint a `doi` on publication and retain the ARK in `additional_ids` for provenance continuity. ARK format: `ark:/NAAN/shoulder+assigned_name`, resolvable via `https://n2t.net/ark:/NAAN/...`.

#### `identification.additional_ids`
- **Annotation:** `[discoverability_if_applicable]`
- **List (0 or more).**
- Secondary, legacy, or version-specific identifiers. Each entry: `type` (`IdentifierTypeEnum`), `value` (e.g., `SAND2024-XXXXX` \| `LAUR-XX-XXXXX`).

#### `identification.supersedes`
- **Annotation:** `[discoverability_if_applicable]`
- **Single entry** (`type`, `value`; `IdentifierTypeEnum`).
- Identifier of the prior version this dataset replaces.

#### `identification.superseded_by`
- **Annotation:** `[discoverability_if_applicable]`
- **Single entry** (`type`, `value`; `IdentifierTypeEnum`).
- Identifier of the newer version that replaces this dataset. Populate when this version is deprecated.

#### `identification.parent_collection`
- **Annotation:** `[discoverability_if_applicable]`
- **Single entry.**
- The collection or experimental campaign this dataset belongs to, when it is one of many in a larger organized collection or ensemble.
- Sub-fields: `name` (required if the block is present), `identifier.type` (`IdentifierTypeEnum`), `identifier.value`.

---

### `discoverability.dataset_description`

- **Annotation:** `[discoverability_required]`
- **Single entry.** At minimum a `dataset_summary` and `keywords` are required, even for early-stage datasets.

#### `dataset_description.science_domain`
- **Annotation:** `[discoverability_if_applicable]`
- **List (0 or more).**
- Scientific domain(s) the dataset primarily relates to, based on the OSTI Subject Areas and extended with `Other`. E-Link users can map to their own taxonomy.
- `ScienceDomainEnum`: `Biology and Medicine` \| `Chemistry` \| `Energy Storage, Conversion, and Utilization` \| `Engineering` \| `Environmental Sciences` \| `Fission and Nuclear Technologies` \| `Fossil Fuels` \| `Geosciences` \| `Materials` \| `Mathematics and Computing` \| `National Defense` \| `Physics` \| `Power Generation and Distribution` \| `Renewable Energy` \| `Other`

#### `dataset_description.dataset_summary`
- **Annotation:** `[discoverability_required]`
- **Single entry.**
- The most important descriptive field in the data card. Write 1–3 sentences giving a high-level overview of the dataset, its purpose, and potential applications, for a broad scientific audience unfamiliar with your project.
- Ask: if a colleague outside your group found this in the catalog, would this summary tell them whether it's relevant?
- Good: "This dataset contains time-series beam position monitor (BPM) readings from the Spallation Neutron Source (SNS) at ORNL, collected during accelerator commissioning runs in Q3 2023. Data includes horizontal and vertical beam positions at 120 monitor locations sampled at 1 MHz, with associated timestamps and beam current measurements. Intended for accelerator physics analysis and ML-based anomaly detection model development." Poor: "BPM data from SNS 2023."

#### `dataset_description.purpose`
- **Annotation:** `[discoverability_if_applicable]`
- **Single entry.**
- Why the dataset was created: the scientific question or problem it addresses. Distinct from `governed_use.use_governance.intended_use` (how it should be used).

#### `dataset_description.collection_methodology`
- **Annotation:** `[discoverability_if_applicable]`
- **Single entry.** How the data was acquired, e.g. `Experimental sensors` \| `Computational simulation` \| `Human annotation` \| `Derived from prior datasets` — freetext.

#### `dataset_description.data_characteristics`
- **Annotation:** `[discoverability_if_applicable]`
- **Single entry.** Key structural and content characteristics: scale, dimensionality, temporal coverage, spatial resolution.

#### `dataset_description.limitations`
- **Annotation:** `[discoverability_if_applicable, recommended]`
- **Single entry.** Known limitations, gaps, biases, or caveats. Be candid — undisclosed limitations that surface later damage trust.

#### `dataset_description.tags`
- **Annotation:** `[discoverability_if_applicable]`
- **Single entry** (structured tag block for catalog filtering).

| Sub-field | Annotation | Notes |
|---|---|---|
| `project` | `[situational_required]` | Same guidance as `identification.project`; keep consistent |
| `science` | `[discoverability_if_applicable]` | More specific domain, sub-discipline, or topic, e.g. `lightsource` \| `fusion` \| `synchrotron light source science` \| `magnetic confinement fusion` \| `materials under extreme conditions` |
| `object_type` | `[discoverability_required]` | `ObjectTypeEnum`: `Dataset` \| `Model` \| `Software` \| `AI_Agent` \| `Infrastructure` \| `Resource` \| `Other`. Use `Dataset` for data cards. |


#### `dataset_description.task_category`
- **Annotation:** `[discoverability_if_applicable]`; at least one value required if `task_subcategory` is present (schema rule).
- **List (0 or more).**
- Primary ML task category or categories. Freetext examples: `classification` \| `regression` \| `segmentation` \| `detection` \| `generation` \| `translation` \| `summarization` \| `ranking` \| `anomaly_detection` \| `clustering` \| `reinforcement_learning` \| `other`.

#### `dataset_description.task_subcategory`
- **Annotation:** `[discoverability_if_applicable]`
- **List (0 or more).**
- More specific ML task subcategories. Freetext examples: `binary_classification` \| `multi_class_classification` \| `multi_label_classification` \| `image_segmentation` \| `object_detection` \| `time_series_forecasting` \| `named_entity_recognition` \| `question_answering`.

#### `dataset_description.keywords`
- **Annotation:** `[discoverability_required]`
- **List (1 or more required).**
- Terms that aid discovery: domain terms (`neutron scattering`), methods (`Monte Carlo simulation`), instruments/facilities (`Spallation Neutron Source`, `DIII-D`), and ontology terms if known (`ENVO:00002006`).

---

### `discoverability.product_type`
- **Annotation:** `[discoverability_required]` (template default `"Dataset"`).
- **Single entry.**
- Primary type of product described by this card. Aligns with and extends the OSTI STI Product Types. Select the single best fit; `Dataset` is expected for a data card.
- `ProductTypeEnum`:

| Value | Meaning |
|---|---|
| `Dataset` | A dataset |
| `Collection` | A collection of STI products (e.g., a project data repository) |
| `Technical_Report` | A technical report or white paper |
| `Journal_Article` | A journal article |
| `Conference` | A conference or workshop, including proceedings |
| `Book` | A book or monograph |
| `Thesis/Dissertation` | A thesis or dissertation |
| `Accomplishment Report` | A report on project/program accomplishments |
| `Program_Document` | A program, project, or initiative document |
| `Factsheet` | A brief document with key information |
| `Software_Manual` | A software manual or user guide |
| `Patent` / `Patent_Application` | A patent / a patent application |
| `Computer_Related` | Software packages, pipelines, automated processes (Genesis extension) |
| `Model` | Computational model, simulation, or trained ML model (Genesis extension) |
| `Agent` | AI agent or automated system (Genesis extension) |
| `Miscellaneous` / `Other` | Anything not covered above |

Note that `Accomplishment Report` and `Thesis/Dissertation` are written exactly as shown (with a space / slash).

### `discoverability.dataset_type`
- **Annotation:** `[discoverability_if_applicable]`
- **Single entry.**
- OSTI DOE Dataset Type code. `DatasetTypeEnum` has a single value: `Instrument` — use it only for instrument data products. Otherwise leave null or delete the field.

---

### `discoverability.release_status`
- **Annotation:** `[discoverability_required]`
- **Single entry.**
- Current publication and governance state of the dataset record. See **Workflow state vs. release status**.
- `ReleaseStatusEnum`:

| Value | Meaning |
|---|---|
| `Draft` | Work in progress; not ready for sharing outside the immediate team |
| `Under_Review` | Submitted for formal review (security, export control, IRB, etc.) |
| `Approved` | Review complete; cleared for release |
| `Published` | Publicly released and accessible. Does not by itself indicate formal governance review — see the sensitivity block and `review_provenance_companion` for actual review/approval status. |
| `Deprecated` | Superseded or retired; no longer recommended for use |

### `discoverability.dataset_publisher`
- **Annotation:** `[situational_required]` — required when `release_status = Approved | Published` (schema rule).
- **Single entry.**
- Entity responsible for making the dataset available. Often the primary research organization, but may differ.
- Sub-fields: `name` (required if block present), `description` *(if_applicable)*, `ror_id` *(if_applicable, recommended)*.

---

### `discoverability.contact`
- **Annotation:** `[discoverability_required]`
- **List (1 or more required).**
- Point(s) of contact for questions about access to or use of this **dataset**. Every dataset must have a reachable contact. Prefer a named person; an organization (e.g., a data management office) may be used when no single named contact is appropriate.
- Each entry contains a `person` and/or `organization` block — at least one is required (schema rule). Using one per entry is recommended for clarity.
- `person` sub-fields as in **Agent blocks** (including `role`, e.g. `Contact_Person`); `organization`: `name`, `ror_id`, `role`.
- `valid_until` *(discoverability_if_applicable; `YYYY-MM-DD`)*: date after which this contact may no longer be valid — use for project-bound contacts (students, postdocs, term staff).
- `succession_note` *(discoverability_if_applicable)*: who to contact if this contact is no longer reachable, e.g. "Contact the ORNL data management office at data@ornl.gov."
- Choose a contact who will be reachable for the foreseeable future; for long retention periods consider whether they'll be associated with the project in 5–10 years.

```yaml
contact:
  - person:
      given_name: "Jane"
      family_name: "Doe"
      email: "jane.doe@example.org"
      affiliation:
        name: "Example National Laboratory"
        ror_id: "https://ror.org/02vwzrd76"
      role: ["Contact_Person"]
    valid_until: "2027-09-30"
    succession_note: "Contact the Example Lab data management office at data@example.org."
```

### `discoverability.additional_contacts`
- **Annotation:** `[discoverability_if_applicable]`
- **List (0 or more).**
- Additional contacts (e.g., instrument PI, data steward). Same structure as `contact`.

---

### `discoverability.authors`
- **Annotation:** `[discoverability_required]` — at least one author required when `release_status = Approved | Published`. For draft or in-workflow datasets, populate known authors as early as possible.
- **List** (1 or more when required).
- Authors are the agents with primary intellectual responsibility for the dataset — typically the PI, lead scientist, or data creator. For supporting roles use `contributors`.
- Each entry is an agent block with exactly one of `person`, `organization`, `ai_model`, `software` (see **Agent blocks**). `orcid` is strongly recommended for persons.

### `discoverability.contributors`
- **Annotation:** `[discoverability_if_applicable]`
- **List (0 or more).**
- Supporting contributors who are not primary authors — sample preparers, annotators, reviewers, submitters, or tools. Same structure as `authors`.

---

### `discoverability.sponsor_organizations`
- **Annotation:** `[discoverability_required]`
- **List (1 or more required).**
- Organizations that funded or sponsored this dataset. Populate with known information even for in-workflow data.

| Sub-field | Annotation | Notes |
|---|---|---|
| `name` | `[discoverability_required]` | e.g. `DOE Office of Science` \| `NNSA` \| `NSF` |
| `ror_id` | `[discoverability_if_applicable, recommended]` | e.g. `https://ror.org/02vwzrd76` |
| `award_number` | `[discoverability_if_applicable, recommended]` | e.g. `DE-AC05-00OR22725` |
| `funding_source` | `[discoverability_if_applicable, recommended]` | `FundingSourceEnum`: `DOE_Program_SC` \| `DOE_Program_NNSA` \| `LDRD` \| `WFO` \| `CRADA` \| `Other_Federal` \| `State_Government` \| `Subcontract` \| `Industry` \| `Nonprofit` \| `Internal` \| `Other` |
| `program` | `[discoverability_if_applicable, recommended]` | e.g. "Advanced Scientific Computing Research" |

### `discoverability.sponsoring_doe_program_office`
- **Annotation:** `[discoverability_if_applicable]`
- **Single entry.** DOE program office that sponsored or funded the research, e.g. "Office of Science".

### `discoverability.sponsoring_doe_subprogram`
- **Annotation:** `[discoverability_if_applicable]`
- **Single entry.** DOE subprogram that sponsored or funded the research, e.g. "Advanced Scientific Computing Research".

---

### `discoverability.research_organizations`
- **Annotation:** `[discoverability_required]`
- **List (1 or more required).**
- Organizations that created or collected the data.
- Each entry: `name` (e.g., `Oak Ridge National Laboratory`), `ror_id` *(if_applicable, recommended)*, `role` *(discoverability_if_applicable; list, `RoleEnum`)*.

### `discoverability.facilities`
- **Annotation:** `[discoverability_if_applicable]`
- **List (0 or more).**
- User facilities, HPC centers, or research infrastructure used to collect, process, or store the dataset.
- Each entry: `name` (e.g., `Spallation Neutron Source` \| `Frontier`), `ror_id` *(if_applicable, recommended)*, `role` (list, `RoleEnum`), and `location` *(discoverability_if_applicable)* — a point location for facility-based experimental data with `description` (required if `location` is present; place name, e.g. "SNS Beamline 1B, Oak Ridge National Laboratory, TN, USA") and `ror_id` *(if_applicable, recommended)*.

---

### `discoverability.sensitivity` — sensitivity of the dataset

- **Annotation:** `[discoverability_required]` (block); sub-fields as in the `datacard.sensitivity` table.
- **Single entry.**
- Sensitivity of the **dataset**, which may differ from the data card's sensitivity. Populate based on the dataset alone. This structure preserves authoritative source markings/designations while minimizing redundant manual entry, and separates source marking/control information from adjacent governance metadata (export control, privacy, rights, release, records — captured in `governed_use`).
- Uses the same fields, vocabularies, and **cross-field rules** as `discoverability.datacard.sensitivity` (see the table above).
- Design principles:
  - Preserve authoritative source markings as the primary source of truth.
  - Use `overall_sensitivity` for display/discovery, never as the sole governance basis.
  - Keep UCNI distinct from generic CUI.
  - Treat OUO and other deprecated labels as legacy provenance, not modern control categories.
  - Do not create or imply a Genesis-private marking scheme.

---

### `discoverability.workflow`
- **Annotation:** `[discoverability_required]`
- **Single entry.** Technical and processing lifecycle position of the dataset.

#### `workflow.state`
- **Annotation:** `[discoverability_required]`
- **Single entry.** `StateEnum`:

| Value | Meaning |
|---|---|
| `Raw` | As collected, unprocessed |
| `Processing` | Being cleaned, transformed, or reduced |
| `QA` | Undergoing quality assurance or validation |
| `Analysis` | In active scientific analysis |
| `Review` | Under formal review (security, export control, IRB, etc.) |
| `Embargo` | Complete but withheld from release until `embargo_until` |
| `Published` | Publicly released |
| `Archived` | Preserved; no longer actively maintained |
| `not_applicable` | Lifecycle state does not apply |

#### `workflow.is_intermediate`
- **Annotation:** `[discoverability_if_applicable, recommended]`
- **Single entry.** `"Yes"` if this is an intermediate pipeline product; `"No"` if final. Example: raw detector output before calibration is intermediate; calibrated, analysis-ready data is final.

#### `workflow.pipeline_stage`
- **Annotation:** `[discoverability_if_applicable, recommended]`
- **Single entry.** Freetext position in a processing pipeline, e.g. "raw telemetry, pre-calibration" \| "post-detector, pre-reconstruction."

#### `workflow.embargo_until`
- **Annotation:** `[situational_required]` — required if `state = Embargo`; must be **absent** if `state = Published` (schema rules).
- **Single entry.** ISO 8601 date after which release is permitted.

---

## Section: Accessibility `[accessibility_required when supports_accessibility = "Yes"]`

Metadata describing how this dataset can be accessed — access policy, access endpoints, and scale. Access policy is distinct from sensitivity (the nature of the data and its risks) and from release status (the publication state of the dataset record).

---

### `accessibility.access_policy`
- **Annotation:** `[accessibility_required]`
- **Single entry.** Who can access this dataset and under what conditions. Describes the **dataset**, not the data card.

#### `access_policy.access_level`
- **Annotation:** `[accessibility_required]`
- **Single entry.** `AccessLevelEnum`:

| Value | Meaning |
|---|---|
| `Open` | Anyone can discover and access without special permissions beyond standard account registration and terms of service. `Open` does not mean free of copyright or legal restrictions — only that no additional access controls apply. |
| `Restricted` | Data may be discoverable, but users must satisfy basic access requirements (authentication, affiliation, registration, agreement to terms, etc.). |
| `Controlled` | Access is granted only after review and explicit authorization based on the requester, intended use, legal requirements, or security considerations. |

`access_level` does not replace the authoritative classification, CUI, or other sensitivity fields.

#### `access_policy.access_restrictions`
- **Annotation:** `[accessibility_if_applicable]`; required if `authorization_required` includes `Other` (schema rule).
- **Single entry.** Freetext description of specific restrictions beyond `access_level`, e.g. "Requires signed DUA" \| "None — publicly accessible."

#### `access_policy.authorization_required`
- **Annotation:** `[accessibility_if_applicable]`; required if `access_level = Restricted | Controlled` (schema rule).
- **List.** `AuthorizationRequiredEnum`:

| Value | Meaning |
|---|---|
| `Account` | A registered account in the repository system |
| `User_Agreement` | Acceptance of a user agreement or terms of service |
| `Data_Use_Agreement` | A formal signed Data Use Agreement (DUA) |
| `Sponsor_Approval` | Approval from the dataset sponsor or PI |
| `Export_Control_Review` | A completed export control review |
| `IRB_Approval` | Institutional Review Board approval |
| `Other` | Describe in `access_restrictions` (required) |

#### `access_policy.intended_partner_classes`
- **Annotation:** `[accessibility_if_applicable]`
- **List.** `IntendedPartnerClassEnum`: `Internal_Team` \| `Tri_Lab` \| `DOE_NNSA_Lab` \| `Federal_Partner` \| `Contractor` \| `Academic_Researchers` \| `External_Research_Partner` \| `Industry_Partner` \| `Public` \| `Other`.
- Absent/null = not yet determined. `[]` = definitively no specific partner classes targeted. Use `Public` for broad public use.

#### `access_policy.approved_environments`
- **Annotation:** `[accessibility_if_applicable]`
- **List.** `ApprovedEnvironmentEnum`: `JUCE` \| `Classified Enclave` \| `CUI Approved Enclave` \| `Cloud Enclave (Authorized)` (write values exactly as shown, including spaces and parentheses).
- `[]` = no specific approved environments, or the dataset is publicly accessible. Null/absent = not yet determined whether approved environments are required.

#### `access_policy.policy_url`
- **Annotation:** `[accessibility_if_applicable]`
- **Single entry.** URL (`http(s)://…`) to the official access policy or data use agreement, or `not_applicable`.

#### `access_policy.policy_text`
- **Annotation:** `[accessibility_if_applicable]`
- **Single entry.** Inline summary of the key terms if no `policy_url` exists.

---

### `accessibility.access`
- **Annotation:** `[accessibility_required]`
- **Single entry.** Access endpoints: current location, landing page, and intended repositories. Complete what you know at creation; repository-assigned values (landing pages, accession numbers, access protocols) are resolved by the managing repository or catalog at ingest.

#### `access.current_location`
- **Annotation:** `[accessibility_required]`
- **Single entry.** Where the data physically resides right now — for in-workflow data not yet deposited, or any dataset with a known storage path. Examples: `/mnt/ecs/scientific-data/project/dataset/` \| `/lustre/orion/proj-shared/dataset/` \| `s3://genesis-bucket/dataset/`.

#### `access.publicly_facing_landing_page_url`
- **Annotation:** `[accessibility_if_applicable]`
- **Single entry.** Public URL (`http(s)://…`) describing the dataset and how to access it — the URL to share and cite. May differ from `current_location`. Delete the field if none exists (the pattern does not accept `not_applicable`).

#### `access.intended_repositories`
- **Annotation:** `[accessibility_if_applicable]`
- **List (0 or more).** Repositories you intend to deposit, or have deposited, this dataset in — institutional, project-owned, community, or national (e.g., OSTI, Zenodo, an institutional repository, a project data store).

| Sub-field | Annotation | Notes |
|---|---|---|
| `name` | required (if entry present) | e.g. "Zenodo" \| "OSTI" \| "Globus" \| "internal" |
| `access_level` | `[accessibility_required]` | `AccessLevelEnum` — intended access level at this repository; may differ per repository |
| `is_primary` | `[accessibility_if_applicable]` | `"Yes"` \| `"No"` — mark only one entry `"Yes"` |
| `date_deposited` | `[accessibility_if_applicable]` | ISO 8601 date |
| `data_services` | `[accessibility_if_applicable]` | **List** — see below |

`intended_repositories[].data_services` — APIs or service endpoints for this dataset in this repository. List all that apply.

| Sub-field | Annotation | Notes |
|---|---|---|
| `name` | required (if entry present) | e.g. "REST API" \| "GraphQL endpoint" |
| `endpoint` | `[accessibility_if_applicable]` | URL (`http(s)://…`) |
| `documentation_url` | `[accessibility_if_applicable]` | URL (`http(s)://…`) |
| `authentication` | `[accessibility_if_applicable]` | `AuthenticationTypeEnum`: `None` \| `API_Key` \| `OAuth2` \| `SAML` \| `Certificate` \| `OpenID_Connect` \| `Basic_Auth` \| `Bearer_Token` \| `Other` |
| `version` | — | API/service version, e.g. `2.1.0` |
| `rate_limit` | `[accessibility_if_applicable]` | e.g. "1000 requests/hour" |

---

### `accessibility.dataset_scale`
- **Annotation:** `[accessibility_if_applicable]`
- **Single entry.** Physical size and record counts — even approximate values help users judge whether a dataset is practical to download and use.

| Sub-field | Type | Notes |
|---|---|---|
| `record_count` | integer | Number of primary records, samples, files, or rows |
| `record_unit` | freetext | e.g. `samples` \| `files` \| `records` \| `timesteps` \| `images` \| `tokens` \| `other` |
| `compressed_bytes` | integer | Total size when compressed, in bytes |
| `uncompressed_bytes` | integer | Total size when uncompressed, in bytes |

---

## Section: Interoperability `[interoperability_required when supports_interoperability = "Yes"]`

Metadata that lets users integrate the dataset with other datasets or systems — data structure, provenance, dates, semantic context, related resources, and domain-specific metadata.

---

### `interoperability.data_structure`
- **Annotation:** `[interoperability_required]`
- **Single entry.** Format, encoding, and structure of the dataset.

#### `data_structure.formats`
- **Annotation:** `[interoperability_required]`
- **List (1 or more required).** File formats in the dataset, with version where relevant. e.g. `csv` \| `json` \| `parquet` \| `hdf5` \| `netcdf` \| `jpeg` \| `png` \| `tiff` \| `wav`.

#### `data_structure.encoding`
- **Annotation:** `[interoperability_if_applicable]`
- **Single entry.** Character encoding for text-based formats, e.g. `UTF-8` \| `ASCII` \| `Latin-1`. UTF-8 strongly recommended. Use `not_applicable` for binary formats.

#### `data_structure.schema_version`
- **Annotation:** `[interoperability_if_applicable]`
- **Single entry.** Pattern: `X.Y` or `X.Y.Z`, or `not_applicable`. Version of the data schema used in the dataset — distinct from `datacard_version`. Increment when field names, types, or structure change in a way that would break parsers.

#### `data_structure.modalities`
- **Annotation:** `[interoperability_required]`
- **List (1 or more required).** e.g. `tabular` \| `image` \| `time-series` \| `text` \| `graph` \| `point-cloud`.

#### `data_structure.features`
- **Annotation:** `[interoperability_required]`
- **List (1 or more required).** Primary variables, fields, or features. **Choose one form and use it consistently — do not mix.**
  - **Basic form:** each entry has only `name`.
  - **Structured form** (for interoperability, reuse, and AI-readiness): each entry has `name`, `description` *(if_applicable)*, `data_type` *(interoperability_if_applicable; freetext, e.g. `float` \| `int` \| `string` \| `boolean` \| `datetime` \| `other`)*, `unit` *(interoperability_if_applicable)*, `range` *(interoperability_if_applicable; a **string**)*.

```yaml
# Basic form
features:
  - name: temperature
  - name: pressure
  - name: timestamp

# Structured form
features:
  - name: temperature
    description: "Sample temperature at time of measurement"
    data_type: float
    unit: kelvin
    range: "273.15 - 373.15"
```

#### `data_structure.splits`
- **Annotation:** `[interoperability_if_applicable]`
- **List (0 or more).** Pre-defined splits, e.g. `["train", "test", "validation"]`.

#### `data_structure.language`
- **Annotation:** `[interoperability_if_applicable]` (template default `"en"`).
- **Single entry.** ISO 639-1 code(s) for the **dataset content** (text corpora, annotation labels) — distinct from `datacard.language`. **Replace the default with `not_applicable`** for non-linguistic data (numeric, image, simulation output, etc.).

#### `data_structure.spatial_coverage`
- **Annotation:** `[interoperability_if_applicable]`
- **Single entry.** Geographic coverage, for geospatial datasets or facility-based experiments.

| Sub-field | Annotation | Notes |
|---|---|---|
| `description` | `[if_applicable]` | Freetext, e.g. "Continental United States" \| "SNS Beamline 1B, ORNL" |
| `geo_location_box.west_bound_longitude` | `[interoperability_if_applicable]` | Decimal degrees (WGS84, float) |
| `geo_location_box.east_bound_longitude` | `[interoperability_if_applicable]` | Decimal degrees |
| `geo_location_box.south_bound_latitude` | `[interoperability_if_applicable]` | Decimal degrees |
| `geo_location_box.north_bound_latitude` | `[interoperability_if_applicable]` | Decimal degrees |

Use `geo_location_box` for genuine area coverage; `description` alone is sufficient for most facility-based experimental data.

#### `data_structure.temporal_coverage`
- **Annotation:** `[interoperability_if_applicable]`
- **Single entry** (`start_date`, `end_date` as `YYYY-MM-DD`; `description` freetext).
- The time period the **dataset content** represents — distinct from `interoperability.dates.data_collection_start` / `data_collection_end`, which describe **when collection occurred**.
- Use `temporal_coverage` when content is tied to a specific period (e.g., satellite imagery from June 2020; monthly climate averages for 1950–2020). Use the `dates` fields when collection spanned a period but content is not tied to it (e.g., articles collected 2015–2020).
- Example: climate averages for 1950–2020 collected in 2024 → `temporal_coverage.start_date: 1950-01-01`, `end_date: 2020-12-31`; `dates.data_collection_start: 2024-01-01`.

---

### `interoperability.provenance`
- **Annotation:** `[interoperability_required]`
- **Single entry.** Origin, history, and transformations: how the dataset was created, what it was derived from, and what processing was applied.

#### `provenance.was_generated_by`
- **Annotation:** `[interoperability_required]`
- **Single entry.** High-level description of the generating process. Even a one-line answer dramatically improves catalog value. e.g. "Neutron scattering experiment at SNS Beamline 1B" \| "Monte Carlo simulation using MCNP 6.2" \| "Derived from raw telemetry via calibration pipeline v2.1".

#### `provenance.source_data`
- **Annotation:** `[interoperability_if_applicable]`
- **List (0 or more).** Source datasets this dataset was derived from.
- Each entry: `name` (required), `description` *(if_applicable)*, `identifier.type` (`IdentifierTypeEnum`) / `identifier.value`, `relationship` *(interoperability_if_applicable; `RelationshipTypeEnum`, read as "this dataset `<relationship>` source" — typically `is_derived_from`)*.

#### `provenance.processing_steps`
- **Annotation:** `[interoperability_required]`
- **Single entry.** Key processing, cleaning, calibration, or transformation steps, with enough detail for a knowledgeable person in your domain to understand what was done.

#### `provenance.instrumentation`
- **Annotation:** `[interoperability_if_applicable]`
- **Single entry.** Instruments, sensors, detectors, or equipment used, including make/model/version. For computational datasets, may describe compute hardware.

#### `provenance.simulation_details`
- **Annotation:** `[interoperability_if_applicable]`
- **Single entry.** For simulation-derived data: code, version, setup, key parameters, configuration. e.g. "LAMMPS 23Jun2022, NVT ensemble, 300K, 10ns run, CHARMM36".

#### `provenance.software_environment`
- **Annotation:** `[interoperability_if_applicable]`
- **Single entry.** What is needed for computational reproducibility.

| Sub-field | Notes |
|---|---|
| `os` | e.g. "RHEL 8.6" \| "Ubuntu 22.04" |
| `compiler` | e.g. "GCC 11.3.0" \| "Intel oneAPI 2023.1" |
| `container` | e.g. "docker://registry/image:tag" |
| `hpc_environment` | e.g. "module load python/3.10 cuda/11.8 openmpi/4.1" |
| `notes` | Key library versions or a pointer to a manifest, e.g. "See requirements.txt in dataset root" |

---

### `interoperability.dates`
- **Annotation:** `[interoperability_if_applicable]`
- **Single entry.** All dates ISO 8601 (`YYYY-MM-DD`).

| Sub-field | Notes |
|---|---|
| `data_collection_start` | Date data collection or generation began |
| `data_collection_end` | Date data collection or generation ended |
| `issued` | Date the dataset was first publicly released |
| `modified` | Date of the most recent significant modification |

---

### `interoperability.semantic_layer`
- **Annotation:** `[interoperability_if_applicable]` — needed for agentic, federated, or cross-domain use; populate `schema_url` at minimum.
- **Single entry.**

| Sub-field | Single/Multi | Notes |
|---|---|---|
| `schema_url` | Single | URL to a formal schema or ontology (JSON Schema, XML Schema, NeXus application definition, etc.) |
| `semantic_context` | **List (0 or more)** | Semantic conventions applied, e.g. "NetCDF CF Conventions 1.10" \| "NeXus NXmonopd" \| "Custom schema with the following key classes and relationships: …" |

---

### `interoperability.related_resources`
- **Annotation:** `[interoperability_if_applicable]`
- **Single entry** containing four lists. Relationship values use `RelationshipTypeEnum` (see **Agent blocks**); read as "*this dataset* `<relationship>` *the resource*" for datasets and publications, and "*the tool/model* `<relationship>` *this dataset*" for software and AI models.

#### `related_resources.datasets`
- **List (0 or more).** Each entry: `name` (required), `description` *(if_applicable)*, `identifier.type` / `identifier.value`, `relationship`.

#### `related_resources.publications`
- **List (0 or more).** Each entry: `value`, `type` (`IdentifierTypeEnum`), `relationship` — all three required per entry. For an arXiv preprint use `type: url` (or `other`) with the arXiv URL/ID as `value`.

#### `related_resources.software`
- **List (0 or more).** Each entry: `name`, `version` *(recommended)*, `identifier.type` / `identifier.value`, `role` (list), `relationship` *(required)* — e.g. `processes`, `generates`, `analyzes`.

#### `related_resources.ai_models`
- **List (0 or more).** Each entry: `name`, `version` *(recommended)*, `accessed_date` *(required)*, `identifier.type` / `identifier.value`, `role` (list), `relationship` *(required)* — e.g. `is_trained_on`, `is_evaluated_on`, `tested_on`, `generates`.

```yaml
related_resources:
  datasets:
    - name: "Example Dataset A"
      description: "Raw detector output prior to calibration"
      identifier:
        type: "doi"
        value: "10.1234/example.dataset.a"
      relationship: "is_derived_from"
  publications:
    - value: "10.5678/example.publication"
      type: "doi"
      relationship: "is_referenced_by"
    - value: "https://arxiv.org/abs/2101.12345"
      type: "url"
      relationship: "is_documented_by"
  software:
    - name: "Example Software X"
      version: "1.2.3"
      identifier:
        type: "doi"
        value: "10.9876/example.software.x"
      role: ["Software", "Data_Curator"]
      relationship: "processes"
  ai_models:
    - name: "Example AI Model Y"
      version: "0.9.0"
      accessed_date: "2026-01-15"
      identifier:
        type: "doi"
        value: "10.5432/example.ai.model.y"
      role: ["Software"]
      relationship: "is_trained_on"
```

---

### `interoperability.domain_metadata`
- **Annotation:** `[interoperability_if_applicable]`
- **Single entry.** Domain-specific metadata not otherwise captured. Supplements — and should not replace — the common metadata elsewhere in the data card.

| Sub-field | Annotation | Notes |
|---|---|---|
| `name` | required (if block present) | e.g. "Accelerator Operations Metadata" |
| `description` | `[if_applicable]` | Purpose and important details of this domain metadata |
| `science_domain` | `[discoverability_if_applicable]` | **List**, `ScienceDomainEnum` |
| `schema_reference.type` / `.value` | `[interoperability_if_applicable]` | `IdentifierTypeEnum` + value of the domain schema or controlled vocabulary |
| `schema_reference.version` | — | Version of the referenced domain schema/convention |
| `fields` | — | **List (0 or more)** — see below |

Each `fields[]` entry:

| Sub-field | Annotation | Notes |
|---|---|---|
| `name` | `[situational_required]` | Field name |
| `field_value` | `[situational_required]` | The value (stored as a string) |
| `data_type` | `[situational_required]` | e.g. `string`, `integer`, `float`, `boolean` |
| `unit` | `[situational_required]` | Unit of measurement, or `not_applicable` |
| `description` | `[if_applicable]` | Meaning and significance |

```yaml
domain_metadata:
  name: "Accelerator Operations Metadata"
  description: "Beam parameters and machine settings for the run."
  science_domain: ["Physics"]
  schema_reference:
    type: "doi"
    value: "10.1234/accelerator.metadata.schema"
    version: "1.0.0"
  fields:
    - name: beam_energy
      field_value: "120"
      data_type: float
      unit: GeV
      description: "The energy of the particle beam."
    - name: beam_current
      field_value: "0.5"
      data_type: float
      unit: mA
      description: "The current of the particle beam."
```

---

## Section: Reusability `[reusability_required when supports_reusability = "Yes"]`

Metadata that lets others reuse the dataset — license and rights, stewardship, data quality, citation, and integrity.

---

### `reusability.license`
- **Annotation:** `[reusability_if_applicable]`; **strongly recommended** when `release_status = Approved | Published`. Use `Pending` for `spdx_id` if not yet assigned.
- **Single entry.**
- The license under which the dataset is released. A public/open license is not always the governing instrument; some controlled datasets have no SPDX-style license, and use is governed by contract, agreement, institutional review, or repository policy (see `governed_use`).

| Sub-field | Annotation | Notes |
|---|---|---|
| `spdx_id` | `[reusability_if_applicable]` | SPDX license identifier (https://spdx.org/licenses/), e.g. `CC-BY-4.0` \| `CC0-1.0` \| `Apache-2.0` \| `MIT`. Use `Other` if not in the SPDX list; `Pending` if not yet assigned. |
| `name` | `[reusability_if_applicable]`; required if `spdx_id = Other` | Human-readable license name (at least 3 characters) |
| `url` | `[reusability_if_applicable]` | URL (`http(s)://…`) to the full license text. For a license file in the dataset's repository, give its full URL. |
| `known_contractual_rights` | `[reusability_if_applicable]` | Rights or obligations not captured by the license — important for DOE/NNSA datasets, e.g. "Government has unlimited rights" \| "Contractor retains rights with government license." |

```yaml
license:
  spdx_id: "CC-BY-4.0"
  name: "Creative Commons Attribution 4.0 International"
  url: "https://creativecommons.org/licenses/by/4.0/"
  known_contractual_rights: "Government has unlimited rights."
```

### `reusability.additional_licenses`
- **Annotation:** `[reusability_if_applicable]`
- **List (0 or more).** Additional licenses when different parts of the dataset are under different terms (e.g., third-party content). Each entry uses the same four sub-fields as `license`. Use `known_contractual_rights` to state which subset the entry applies to.

---

### `reusability.stewardship`
- **Annotation:** `[reusability_if_applicable]`
- **Single entry.** Maintenance, updates, and versioning.
- **Note on versioning:** three fields work together — `discoverability.identification.version` (the version number), `identification.supersedes` / `superseded_by` (links to prior/successor versions), and `stewardship.versioning_strategy` (how versioning is managed).

#### `stewardship.level`
- **Annotation:** `[reusability_if_applicable]`
- **Single entry.** `StewardshipLevelEnum`:

| Value | Meaning |
|---|---|
| `Project_Managed` | Maintained by the originating project or team, based on project resources and priorities |
| `Repository_Managed` | Maintained by the hosting repository or catalog, with ongoing curation |
| `Externally_Managed` | Maintained by an external organization (agency, institution, commercial provider) |
| `not_applicable` | Not applicable or not known |

#### `stewardship.maintainer`
- **Annotation:** `[reusability_if_applicable]`
- **Single entry.** Person **or** organization responsible for ongoing maintenance, if different from the contact. Populate exactly one of `person` or `organization` (schema rule) — see **Agent blocks**.

#### `stewardship.update_frequency`
- **Annotation:** `[reusability_if_applicable]`
- **Single entry.** `UpdateFrequencyEnum`: `None` \| `Ad_Hoc` \| `Monthly` \| `Quarterly` \| `Annually` \| `Continuously` \| `Other`.

#### `stewardship.retention_policy`
- **Annotation:** `[reusability_if_applicable]`
- **Single entry.** How long the dataset will be retained and where; reference the applicable DOE policy. e.g. "Retained for 10 years per DOE data management policy."

#### `stewardship.versioning_strategy`
- **Annotation:** `[reusability_if_applicable]`
- **Single entry.** How versions are tracked, archived, and retired. e.g. "Semantic versioning; all versions retained indefinitely in Zenodo."

---

### `reusability.data_quality`
- **Annotation:** `[reusability_required]`
- **Single entry.** Be specific; vague entries like "good quality" reduce trust and reuse.

| Sub-field | Annotation | Notes |
|---|---|---|
| `completeness` | `[reusability_required]` | What fraction is present, what is missing and why. e.g. "All 120 BPM channels present; 2.1% of timesteps missing due to instrument downtime on 2023-04-12 (14:00–16:30 UTC)." |
| `known_issues` | `[reusability_required]` | Specific errors, anomalies, artifacts. Use `not_applicable` if there are genuinely none. |
| `validation_methods` | `[reusability_required]` | How quality was assessed. e.g. "Cross-validated against NIST SRM 640f; outlier detection using 3σ threshold." |
| `noise_characteristics` | `[reusability_if_applicable]` | Nature and magnitude of noise; say so explicitly if none is known |
| `uncertainty_notes` | `[reusability_if_applicable]` | Formal uncertainty quantification, e.g. "±0.5% (k=2) per GUM" |
| `missing_data_codes` | `[reusability_if_applicable]` | **List** — each entry `code` *(situational_required)*, e.g. `-9999` \| `NULL` \| `NaN`, and `description` *(situational_required)*, e.g. "Sensor malfunction — value not collected" |

---

### `reusability.citation`
- **Annotation:** `[situational_required]` — required when `release_status = Approved | Published`. Replace all placeholders before publishing.
- **Single entry.**

#### `citation.report_number`
- **Annotation:** `[reusability_if_applicable]`
- **Single entry.** Institutional report or release number, e.g. `SAND2024-XXXXX` \| `LAUR-XX-XXXXX` \| `ORNL/TM-2024/XXXXX`.

#### `citation.preferred_citation`
- **Annotation:** `[reusability_if_applicable]`
- **Single entry.** Fields for building a BibTeX-style citation. When included, `author`, `title`, `year`, and `publisher` are required, and at least one of `doi` or `url` must be provided.

| Sub-field | Requirement | Notes |
|---|---|---|
| `author` | Required if block present | e.g. "Smith, John A.; Doe, Jane B." |
| `title` | Required if block present | e.g. "Neutron Scattering Data from SNS Beamline 1B, April 2023" |
| `year` | Required if block present | Four-digit year as a **quoted string**, e.g. `"2024"` |
| `publisher` | Optional | e.g. "Oak Ridge National Laboratory" |
| `howpublished` | `[situational_required]` | e.g. "Online" \| "In Repository" \| "As Supplementary Material" |
| `doi` | At least one of `doi` / `url` | e.g. `10.1234/zenodo.1234567` |
| `url` | At least one of `doi` / `url` | Landing page or primary reference; corresponds to BibTeX `url` |
| `eprinttype` | Optional | e.g. `arXiv` \| `report_number` \| `pubmed` |
| `eprint` | Optional | Identifier matching `eprinttype`, e.g. `2101.12345` \| `SAND2024-XXXXX` |
| `note` | Optional | For identifiers that don't fit elsewhere, e.g. `Available at \url{ark:/12345/abcde}` |


```yaml
citation:
  report_number: "SAND2024-12345"
  preferred_citation:
    author: "Smith, John A.; Doe, Jane B."
    title: "Neutron Scattering Data from SNS Beamline 1B, April 2023"
    year: "2024"
    publisher: "Oak Ridge National Laboratory"
    doi: "10.1234/zenodo.1234567"
```

---

### `reusability.integrity`
- **Annotation:** `[reusability_required]`
- **Single entry.** Checksums enable automated validation after transfer or storage.

| Sub-field | Annotation | Notes |
|---|---|---|
| `checksum_available` | `[reusability_if_applicable]` | `"Yes"` \| `"No"` |
| `checksum_type` | `[situational_required]` — required if `checksum_available = "Yes"` | Algorithm: `sha256` strongly recommended; `sha512` acceptable; `md5` only for legacy data; `other` with explanation |
| `checksum_value` | `[situational_required]` — required if `checksum_available = "Yes"` | Checksum of the primary file, or for multi-file datasets the path/URL of a checksum manifest |
| `fixity_policy` | `[reusability_if_applicable]` | How and how often integrity is verified, e.g. "Monthly SHA-256 verification via repository integrity service; alerts on mismatch." |

If `checksum_available = "No"`, omit `checksum_type` and `checksum_value`.

---

## Section: Governed Use `[governed_use_required when supports_governed_use = "Yes"]`

Metadata describing how the dataset may be used, export control and privacy obligations, rights and agreements, compliance, and review history.

---

### `governed_use.use_governance`
- **Annotation:** `[governed_use_required]`
- **Single entry.** Guides appropriate use and prevents misuse.

| Sub-field | Annotation | Notes |
|---|---|---|
| `current_use` | `[governed_use_required]` | What the dataset is actively used for now. e.g. "Active training data for the Genesis anomaly detection pipeline" |
| `intended_use` | `[governed_use_if_applicable, recommended]` | Tasks/workflows the dataset is designed to support, so users can judge suitability. Distinct from `dataset_description.purpose`. |
| `permitted_use` | `[governed_use_if_applicable, recommended]` | Suitable uses beyond the intended use. Genesis governance expects explicit permitted uses. |
| `out_of_scope_use` | `[governed_use_if_applicable, recommended]` | Uses the dataset should not be applied to. Be specific, e.g. "clinical decision-making" \| "real-time control systems". |
| `prohibited_use` | `[governed_use_if_applicable, recommended]` | Explicitly prohibited uses (ethical, safety, legal, contractual). |

```yaml
use_governance:
  current_use: "Active training data for the Genesis anomaly detection pipeline"
  intended_use: "ML training for anomaly detection in accelerator operations"
  permitted_use: "Exploratory analysis and educational use"
  out_of_scope_use: "Real-time accelerator control — data latency precludes safety-critical use"
  prohibited_use: "Any use involving human subjects or clinical decision-making"
```

---

### `governed_use.non_sensitivity_governance_metadata`
- **Annotation:** `[governed_use_required]`
- **Single entry.** Governance metadata that affects sharing/use decisions but is not part of the source sensitivity/marking block (`discoverability.sensitivity`). Applies to the dataset as a whole.

#### `export_control`
- **Annotation:** `[governed_use_required]`

| Sub-field | Annotation | Controlled vocabulary |
|---|---|---|
| `export_control_status` | `[governed_use_required]` | `YesNoPendingUnknownEnum`: `"Yes"` \| `"No"` \| `Pending_Review` \| `Unknown` |
| `export_control_basis` | `[situational_required]` — required if `export_control_status = "Yes"` | `ExportControlBasisEnum`: `ITAR` \| `EAR` \| `DOE_Nuclear_Export_Control` \| `Other` \| `not_applicable`. Consult your export control office before selecting anything other than `not_applicable`. |
| `foreign_national_access_status` | `[governed_use_if_applicable]` | `ForeignNationalAccessStatusEnum`: `Allowed` \| `Restricted` \| `Prohibited` \| `Conditional` \| `Unknown`. The net outcome across export, classification, dissemination, agreement, and other constraints — not export-control-only. Keep consistent with `cui_limited_dissemination_controls`. |

#### `privacy`
- **Annotation:** `[governed_use_required]`

| Sub-field | Annotation | Controlled vocabulary |
|---|---|---|
| `privacy_status` | `[governed_use_required]` | `YesNoPendingUnknownEnum` |
| `pii_status` | `[governed_use_required]` | `YesNoPendingUnknownEnum` — contains personally identifiable information? |
| `phi_status` | `[governed_use_if_applicable]` | `YesNoPendingUnknownEnum` — contains protected health information? Quote values. |
| `privacy_control_basis` | `[governed_use_if_applicable]` | **List**, `PrivacyControlBasisEnum`: `HIPAA` \| `Privacy_Act` \| `Human_Subjects` \| `Other_Regulated_Privacy` \| `Site_Specific` \| `not_applicable`. Use `not_applicable` explicitly if no regime applies. |
| `privacy_regime_notes` | `[governed_use_if_applicable]` | Freetext for nuances not captured above |

#### `rights_release_records`
- **Annotation:** `[governed_use_required]`

| Sub-field | Annotation | Controlled vocabulary |
|---|---|---|
| `ip_restriction_type` | `[governed_use_if_applicable]` | `IPRestrictionTypeEnum` (below) |
| `agreement_required` | `[governed_use_required]` | `"Yes"` \| `"No"` — is an agreement (DUA, license, NDA…) required to access or use the dataset? |
| `agreement_type` | `[situational_required]` — at least one if `agreement_required = "Yes"` | **List**, `AgreementTypeEnum`: `DUA` \| `CRADA` \| `MOU` \| `NDA` \| `LICENSE` \| `WFO` \| `OTHER` |
| `public_release_status` | `[governed_use_required]` | `PublicReleaseStatusEnum` (below) |
| `record_status` | `[governed_use_required]` | `RecordStatusEnum` (below) |

`IPRestrictionTypeEnum`:

| Value | Meaning |
|---|---|
| `Proprietary` | Contains proprietary information; distribution restricted |
| `Limited_Rights` | Government may use but not disclose outside government |
| `Restricted_Rights` | Computer software with limited government rights |
| `Government_Purpose_Rights` | Government may use and disclose only for government purposes |
| `Unlimited_Rights` | Government may use, disclose, reproduce, and distribute without restriction |
| `Third_Party_Licensed` | Contains third-party licensed content with specific terms |
| `None` | No IP restrictions |

`PublicReleaseStatusEnum`: `Approved` (approved for public release) \| `Pending` (review in progress) \| `Not_Approved` \| `Requires_STI_Review` (STI review needed before status can be determined).

`RecordStatusEnum`: `Federal_Record` \| `Contractor_Record` \| `Non_Record` \| `Mixed` \| `Unknown`.

---

### `governed_use.compliance`
- **Annotation:** `[governed_use_required]` — populate when `release_status = Under_Review | Approved | Published`; omit for `Draft` and in-workflow datasets. When present, all three sub-fields are required.
- **Single entry.** All three use `YesNoUnknownNotApplicableEnum`: `"Yes"` \| `"No"` \| `Unknown` \| `not_applicable`.

| Sub-field | Notes |
|---|---|
| `doe_data_management_plan` | Is the dataset covered by a DOE Data Management Plan (DMP)? `not_applicable` if not DOE-funded. |
| `osti_elink2_metadata_compliant` | Does the metadata comply with OSTI E-Link 2.0 requirements? Check with your data manager before `"Yes"`. |
| `irb_approved` | Has IRB approval been obtained? Use `not_applicable` if no human subjects — `"No"` implies review was needed but not obtained. |

---

### `governed_use.review_provenance_companion`
- **Annotation:** `[governed_use_if_applicable, recommended]`
- **List (0 or more)** — append-only, chronological.
- Running history of formal reviews. Add one entry per review stage; never overwrite earlier entries. Extends the Genesis Sensitivity V2 `review_provenance_companion` (single review) to support multiple review records.

| Sub-field | Annotation | Notes |
|---|---|---|
| `source_review_reference` | `[governed_use_if_applicable, recommended]` | Identifier or citation for the authoritative review/release/source document; where no document ID exists, a review type such as `internal_qa` \| `security` \| `export_control` \| `irb` \| `quality_assessment` \| `partner` \| `publication` \| `other` |
| `review_purpose` | `[governed_use_if_applicable, recommended]` | Purpose/focus of the review, e.g. "Export control review prior to public release" |
| `source_review_authority` | `[governed_use_if_applicable]` | Office, system, or authority of record for the determination, e.g. "DOE Export Control Officer" \| "ORNL IRB" |
| `review_contact_name` | `[governed_use_if_applicable]` | Human point of contact, if appropriate |
| `review_contact_email` | `[governed_use_if_applicable]` | Contact email, if appropriate |
| `reviewed_by` | `[governed_use_if_applicable]` | Agent block — exactly one of `person`, `organization`, `ai_model`, `software` |
| `decontrol_or_declassify_on` | `[governed_use_if_applicable]` | `"YYYY-MM-DD"` or `not_applicable` |
| `review_date` | `[governed_use_if_applicable]` | `"YYYY-MM-DD"` the review was completed/last updated, or `not_applicable` if not completed |
| `comments` | `[governed_use_if_applicable, recommended]` | Reviewer notes, conditions, required follow-up |

```yaml
review_provenance_companion:
  - source_review_reference: "ECR-2024-0613"
    review_purpose: "Export control review prior to public release"
    source_review_authority: "DOE Export Control Officer"
    review_contact_name: "Jane Doe"
    review_contact_email: "jane.doe@example.org"
    reviewed_by:
      person:
        given_name: "Jane"
        family_name: "Doe"
        email: "jane.doe@example.org"
        affiliation:
          name: "Example National Laboratory"
          ror_id: "https://ror.org/02vwzrd76"
    decontrol_or_declassify_on: "not_applicable"
    review_date: "2024-06-15"
    comments: "Approved for public release with no restrictions."
  - source_review_reference: "irb"
    review_purpose: "IRB determination for human subjects data"
    source_review_authority: "ORNL IRB"
    reviewed_by:
      organization:
        name: "ORNL Institutional Review Board"
    decontrol_or_declassify_on: "not_applicable"
    review_date: "2024-06-20"
    comments: "Determined not human subjects research."
```

---

## Section: AI Usability `[ai_usability_required when supports_ai_usability = "Yes"]`

Whether and how this dataset may be used in AI/ML workflows. Be explicit — these fields are read by automated pipeline tooling and AI agents; vague or blank entries may cause pipelines to reject the dataset or apply incorrect handling.

### `ai_usability.ai_usage`
- **Annotation:** `[ai_usability_required]`
- **Single entry.**

| Sub-field | Annotation | Notes |
|---|---|---|
| `training_use_status` | `[ai_usability_required]` | `YesNoConditionalEnum`: `"Yes"` \| `"No"` \| `Conditional` |
| `training_use_conditions` | `[situational_required]` — required if `training_use_status = Conditional` | e.g. "Only for non-commercial research" \| "Requires citation of SAND2024-XXXXX" |
| `inference_use_status` | `[ai_usability_required]` | `YesNoConditionalEnum` |
| `inference_use_conditions` | `[situational_required]` — required if `inference_use_status = Conditional` | e.g. "Outputs must be reviewed by a domain expert before operational use" |
| `evaluation_use_status` | `[ai_usability_required]` | `YesNoConditionalEnum` |
| `evaluation_use_conditions` | `[situational_required]` — required if `evaluation_use_status = Conditional` | e.g. "Results may not be published without review by the originating team" |
| `restrictions` | `[ai_usability_required]` | Restrictions beyond the per-task fields. Use `not_applicable` if none. |
| `bias_risks` | `[ai_usability_required]` | Known/potential biases or representational gaps. Use `not_applicable` if none known. |
| `safety_considerations` | `[ai_usability_required]` | Safety or ethical considerations. Use `not_applicable` if none. |
| `human_review_required` | `[ai_usability_required]` | `"Yes"` \| `"No"` — whether human review is **recommended** when using the dataset (or its derived outputs) in AI/ML workflows, based on quality, completeness, relevance, and known risks |


---

## Section: The Markdown Narrative Body

Below the YAML frontmatter, the template contains a Markdown body for human-readable narrative. It is organized by the same six capabilities — **Discoverable, Accessible, Interoperable, Reusable, Governed Use, AI Usable** — which describe usability, interoperability, and governance characteristics; they do **not** rank dataset quality, scientific merit, or value.

- **Instructions** blocks (`<INSTRUCTIONS: …>`) explain how to complete the body and choose an appropriate documentation resolution (single files, datasets, collections, versions). Delete them when done.
- **`[!TODO] <REPLACE: …>`** markers indicate text to write. Replace all of them and all example tables.
- **`<metadata_key: path.to.field>`** tags link a narrative section to its YAML field(s). They support bi-directional YAML↔Markdown generation — keep narrative and YAML consistent, and keep the tags.
- Each section heading carries the same annotation as its YAML fields (e.g., `[discoverability_required]`).
- The **Machine Usability Snapshot** table near the top summarizes the capability flags plus three quick indicators (License Clarity, Checksum/Fixity, Semantic Context). Fill in `Yes`/`No` to match the YAML.

| Body section | Primary YAML fields |
|---|---|
| Dataset Description | `dataset_description.dataset_summary` |
| Domain and Purpose | `dataset_description.purpose`, `science_domain`; `domain_metadata.science_domain` |
| Keywords | `dataset_description.keywords` |
| Security / Marking Considerations | `discoverability.sensitivity.*` |
| Resources used / Developed by / Contributed by | `sponsor_organizations`, `facilities`, `authors`, `contributors` |
| Dataset generation, collection, and procedures | `collection_methodology`, `provenance.*` |
| Sharing & Access | `accessibility.access`, `accessibility.access_policy` |
| Files & Structure; Specialized formats | `data_characteristics`, `dataset_scale`, `data_structure.*` |
| Related Resources | `interoperability.related_resources.*` |
| Understanding the Data (variables table) | `data_structure.features` |
| Related Schemas or Ontologies; Semantic / Schema Information | `semantic_layer.*` |
| Codes used for missing data | `data_quality.missing_data_codes` |
| Data Processing; Software used | `provenance.processing_steps`, `provenance.software_environment`, `related_resources.software` |
| Citation; License and Usage Rights | `reusability.citation`, `reusability.license` |
| Maintenance & Updates | `reusability.stewardship.*` |
| Data Quality & Limitations; Integrity & Versioning | `reusability.data_quality.*`, `reusability.integrity.*` |
| Access and Permissions; Access conditions | `governed_use.non_sensitivity_governance_metadata.*` |
| Release review process | `governed_use.review_provenance_companion` |
| AI / Machine Learning Considerations | `ai_usability.ai_usage.*` |

> Some `metadata_key` tags in the v2.0.0 template body still use older names (`ai_usage.training_use_allowed`, `inference_use_allowed`, `evaluation_use_allowed`, `license.license_name`). The correct YAML fields are `*_use_status` and `license.name`.

---

## Standards Alignment

The Genesis data card schema is defined in LinkML. Alongside each field's definition, the schema records how that field (or controlled-vocabulary value) corresponds to terms in established external metadata standards. These **mappings** let catalogs, harvesters, and AI agents translate a data card into schema.org, DCAT, Dublin Core, DataCite, PROV, and other formats, and help authors understand what each field means in terms they may already know.

This section lists every mapping declared in `genesis_datacard.yaml` (v2.0.0), grouped by the external standard's prefix. Mappings are declared on schema **slots** (fields), on **classes** (blocks), and on **enumeration values** (e.g., individual `role` and `relationship` values).

### Mapping types

Mapping types follow the LinkML mapping properties, which are based on the W3C SKOS mapping relations. Each describes how closely the **data card term** corresponds to the **external term**.

| Mapping type | LinkML property | SKOS basis | Definition | How to use it |
|---|---|---|---|---|
| **exact** | `exact_mappings` | `skos:exactMatch` | The two terms have the same meaning and can be used interchangeably across a wide range of applications. | Values can be copied directly to the external term (subject to format conversion). |
| **close** | `close_mappings` | `skos:closeMatch` | The terms are similar enough to be used interchangeably in some applications, but differ in scope, structure, or nuance. | Safe for most crosswalks; review edge cases and direction. |
| **broad** | `broad_mappings` | `skos:broadMatch` | The **external term is broader** (more general) than the data card term. The data card term is a specific kind or component of the external concept. | Map data card → external freely (information is generalized); do not map external → data card without additional context. |
| **narrow** | `narrow_mappings` | `skos:narrowMatch` | The **external term is narrower** (more specific) than the data card term. | Map external → data card freely; map data card → external only when the value fits the narrower meaning. *(Defined for completeness; no narrow mappings are currently declared.)* |
| **related** | `related_mappings` | `skos:relatedMatch` | The terms are associated — they describe related aspects of the same thing — but are not equivalent and neither is a generalization of the other. | Use as a hint for discovery or alignment, not as a direct crosswalk. |

**Reading the tables.** "Data card term" gives the field path(s) in the template (or `field = value` for a controlled-vocabulary value). "External term" uses the prefix declared in the schema (`prefix:localName`). Where a single schema slot is reused in several places (e.g., `description`, `ror_id`, identifier `type`/`value`), the mapping applies to every use.

**Structural differences.** A mapping describes semantic correspondence, not identical structure. For example, the data card stores `provenance.was_generated_by` as freetext, whereas `prov:wasGeneratedBy` points to a PROV Activity; and the data card's `relationship` values describe a link *from* the dataset, while some external vocabularies express the inverse. Crosswalk implementations should handle such conversions explicitly.

### Namespace summary

| Prefix | Namespace (as declared in the schema) | Standard | Mappings |
|---|---|---|---|
| `schema` | `http://schema.org/` | [Schema.org](#std-schema) | 27 |
| `dcterms` | `http://purl.org/dc/terms/` | [DCMI Metadata Terms (Dublin Core)](#std-dcterms) | 40 |
| `dcat` | `http://www.w3.org/ns/dcat#` | [W3C Data Catalog Vocabulary (DCAT)](#std-dcat) | 17 |
| `spar_datacite` | `http://purl.org/spar/datacite/` | [SPAR DataCite Ontology](#std-spar-datacite) | 6 |
| `datacite_relations` | `https://datacite-metadata-schema.readthedocs.io/en/latest/appendices/appendix-1/relationType/#` | [DataCite Metadata Schema — relationType](#std-datacite-relations) | 42 |
| `datacite_contributor` | `https://datacite-metadata-schema.readthedocs.io/en/latest/appendices/appendix-1/contributorType/#` | [DataCite Metadata Schema — contributorType](#std-datacite-contributor) | 22 |
| `datacite_geo` | `https://datacite-metadata-schema.readthedocs.io/en/latest/properties/geolocation/#` | [DataCite Metadata Schema — geoLocation](#std-datacite-geo) | 5 |
| `prov` | `http://www.w3.org/ns/prov#` | [W3C PROV Ontology (PROV-O)](#std-prov) | 12 |
| `credit` | `https://casrai.org/credit/roles/` | [CRediT — Contributor Roles Taxonomy](#std-credit) | 14 |
| `fair4ml` | `https://w3id.org/fair4ml#` | [FAIR4ML metadata schema](#std-fair4ml) | 13 |
| `spdx` | `http://spdx.org/rdf/terms#` | [SPDX 2.2 RDF terms](#std-spdx) | 2 |


<a id="std-schema"></a>
### `schema` — Schema.org

- **Namespace:** [http://schema.org/](http://schema.org/)
- **Prefix:** `schema`

Schema.org is a collaborative, community-maintained vocabulary for structured data on the web, founded in 2011 by Google, Microsoft, Yahoo, and Yandex. Its `Dataset` type and related properties (`description`, `identifier`, `temporalCoverage`, `spatialCoverage`, `inLanguage`, etc.) are the basis for dataset discovery services such as Google Dataset Search and are widely embedded in repository landing pages as JSON-LD. Schema.org's canonical namespace is now `https://schema.org/`; the `http://` form declared in the schema is still recognized.

Alignment with schema.org makes data card content directly publishable as JSON-LD on landing pages and harvestable by web-scale dataset search.

**Mappings (27):**

| Data card term | External term | Mapping type |
|---|---|---|
| `description` (all description sub-fields) | `schema:description` | exact |
| `datacard.language`, `data_structure.language` | `schema:inLanguage` | exact |
| `datacard.id` | `schema:identifier` | broad |
| `identifier` blocks (agents, resources, `parent_collection`) | `schema:identifier` | broad |
| identifier `value` (all identifier blocks) | `schema:identifier` | exact |
| `identification.primary_id` | `schema:identifier` | broad |
| `identification.additional_ids` | `schema:identifier` | broad |
| `features[].unit`, `domain_metadata.fields[].unit` | `schema:unitText` | exact |
| `features[].data_type`, `domain_metadata.fields[].data_type` | `schema:valueReference` | related |
| `spatial_coverage.geo_location_box` | `schema:spatialCoverage` | related |
| `geo_location_box.west_bound_longitude` | `schema:spatialCoverage` | related |
| `geo_location_box.east_bound_longitude` | `schema:spatialCoverage` | related |
| `geo_location_box.south_bound_latitude` | `schema:spatialCoverage` | related |
| `geo_location_box.north_bound_latitude` | `schema:spatialCoverage` | related |
| `data_structure.temporal_coverage` | `schema:temporalCoverage` | related |
| `temporal_coverage.start_date` | `schema:temporalCoverage` | related |
| `temporal_coverage.end_date` | `schema:temporalCoverage` | related |
| `accessibility.dataset_scale` | `schema:size` | broad |
| `dataset_scale.record_count` | `schema:size` | broad |
| `dataset_scale.compressed_bytes` | `schema:size` | broad |
| `dataset_scale.uncompressed_bytes` | `schema:size` | broad |
| `dates.data_collection_start` | `schema:date` | broad |
| `dates.data_collection_end` | `schema:date` | broad |
| `dates.issued` | `schema:datePublished` | close |
| `dates.modified` | `schema:dateModified` | exact |
| `data_services[].endpoint` | `schema:WebAPI` | close |
| `relationship` = `is_derived_from` | `schema:isBasedOn` | exact |

---

<a id="std-dcterms"></a>
### `dcterms` — DCMI Metadata Terms (Dublin Core)

- **Namespace:** [http://purl.org/dc/terms/](http://purl.org/dc/terms/)
- **Prefix:** `dcterms`

The DCMI Metadata Terms, maintained by the Dublin Core Metadata Initiative, are the most widely used general-purpose metadata vocabulary. They extend the original fifteen-element Dublin Core set (standardized as ISO 15836) with properties such as `identifier`, `replaces`, `isReplacedBy`, `temporal`, `spatial`, `extent`, `issued`, `modified`, `isPartOf`, `references`, and `source`. DCAT, DataCite, and many repository platforms reuse these terms directly.

Alignment with Dublin Core gives the data card a baseline crosswalk that nearly every catalog and repository can consume.

**Mappings (40):**

| Data card term | External term | Mapping type |
|---|---|---|
| `description` (all description sub-fields) | `dcterms:description` | exact |
| `datacard.language`, `data_structure.language` | `dcterms:language` | exact |
| `datacard.id` | `dcterms:identifier` | broad |
| `identifier` blocks (agents, resources, `parent_collection`) | `dcterms:identifier` | broad |
| identifier `value` (all identifier blocks) | `dcterms:identifier` | exact |
| `person.orcid` | `dcterms:identifier` | exact |
| `ror_id` (organizations, affiliations, facilities) | `dcterms:identifier` | exact |
| `identification.primary_id` | `dcterms:identifier` | broad |
| `identification.additional_ids` | `dcterms:identifier` | broad |
| `identification.supersedes` | `dcterms:replaces` | exact |
| `identification.superseded_by` | `dcterms:isReplacedBy` | close |
| `spatial_coverage.geo_location_box` | `dcterms:spatial` | exact |
| `geo_location_box.west_bound_longitude` | `dcterms:spatial` | related |
| `geo_location_box.east_bound_longitude` | `dcterms:spatial` | related |
| `geo_location_box.south_bound_latitude` | `dcterms:spatial` | related |
| `geo_location_box.north_bound_latitude` | `dcterms:spatial` | related |
| `data_structure.temporal_coverage` | `dcterms:temporal` | related |
| `temporal_coverage.start_date` | `dcterms:date` | narrow |
| `temporal_coverage.end_date` | `dcterms:date` | narrow |
| `accessibility.dataset_scale` | `dcterms:extent` | broad |
| `dataset_scale.record_count` | `dcterms:extent` | broad |
| `dataset_scale.compressed_bytes` | `dcterms:extent` | broad |
| `dataset_scale.uncompressed_bytes` | `dcterms:extent` | broad |
| `dates.data_collection_start` | `dcterms:date` | broad |
| `dates.data_collection_end` | `dcterms:date` | broad |
| `dates.issued` | `dcterms:issued` | exact |
| `dates.modified` | `dcterms:modified` | exact |
| `provenance.source_data` | `dcterms:source` | related |
| `role` = `Contributor` | `dcterms:contributor` | close |
| `role` = `Creator` | `dcterms:creator` | close |
| `role` = `Publisher` | `dcterms:publisher` | exact |
| `relationship` = `is_cited_by` | `dcterms:isReferencedBy` | close |
| `relationship` = `cites` | `dcterms:references` | exact |
| `relationship` = `in_series` | `dcterms:isPartOf` | close |
| `relationship` = `is_part_of` | `dcterms:isPartOf` | exact |
| `relationship` = `has_part` | `dcterms:hasPart` | exact |
| `relationship` = `is_referenced_by` | `dcterms:isReferencedBy` | exact |
| `relationship` = `references` | `dcterms:references` | exact |
| `relationship` = `is_derived_from` | `dcterms:source` | exact |
| `relationship` = `other` | `dcterms:relation` | close |

---

<a id="std-dcat"></a>
### `dcat` — W3C Data Catalog Vocabulary (DCAT)

- **Namespace:** [http://www.w3.org/ns/dcat#](http://www.w3.org/ns/dcat#)
- **Prefix:** `dcat`

DCAT is a W3C Recommendation (version 3, 2024) for describing datasets, their distributions, and data services in catalogs published on the web. Its core classes — `dcat:Catalog`, `dcat:Dataset`, `dcat:Distribution`, `dcat:DataService` — and properties such as `accessURL`, `endpointURL`, `byteSize`, `version`, `inSeries`, and `previousVersion` underpin government and research data portals (including DCAT-AP in Europe and DCAT-US for data.gov).

Alignment with DCAT supports federation of Genesis data cards into data catalogs and portals.

**Mappings (17):**

| Data card term | External term | Mapping type |
|---|---|---|
| `data_services[].name` | `dcat:accessService` | close |
| `DatasetClass` (class of `related_resources.datasets[]`, `provenance.source_data[]`) | `dcat:Dataset` | exact |
| `identification.version` (and other `version` fields) | `dcat:version` | exact |
| `role` (all agent blocks) | `dcat:Role` | related |
| `role` (all agent blocks) | `dcat:hadRole` | exact |
| `identification.supersedes` | `dcat:replaces` | exact |
| `dataset_scale.compressed_bytes` | `dcat:byteSize` | broad |
| `dataset_scale.uncompressed_bytes` | `dcat:byteSize` | broad |
| `access.current_location` | `dcat:Distribution` | related |
| `access.current_location` | `dcat:distribution` | close |
| `access.publicly_facing_landing_page_url` | `dcat:landingPage` | exact |
| `intended_repositories[].data_services` | `dcat:DataService` | close |
| `data_services[].endpoint` | `dcat:endpointURL` | exact |
| `relationship` = `in_series` | `dcat:inSeries` | exact |
| `relationship` = `has_version` | `dcat:hasVersion` | close |
| `relationship` = `is_previous_version_of` | `dcat:previousVersion` | exact |
| `relationship` = `obsoletes` | `dcat:replaces` | exact |

---

<a id="std-spar-datacite"></a>
### `spar_datacite` — SPAR DataCite Ontology

- **Namespace:** [http://purl.org/spar/datacite/](http://purl.org/spar/datacite/)
- **Prefix:** `spar_datacite`

The DataCite Ontology is part of the SPAR (Semantic Publishing and Referencing) Ontologies. It is an OWL ontology — distinct from, but inspired by, the DataCite Metadata Schema — for describing identifiers and identifier schemes of resources and agents (e.g., DOIs, ORCIDs, ROR IDs) in RDF.

Alignment with this ontology gives the data card's identifier blocks (`type` + `value`) and agent identifiers (`orcid`, `ror_id`) a formal semantic interpretation.

**Mappings (6):**

| Data card term | External term | Mapping type |
|---|---|---|
| identifier `type` (all identifier blocks) | `spar_datacite:IdentifierScheme` | exact |
| `person.orcid` | `spar_datacite:AgentIdentifier` | exact |
| `ror_id` (organizations, affiliations, facilities) | `spar_datacite:AgentIdentifier` | exact |
| `identification.primary_id` | `spar_datacite:Identifier` | broad |
| `identification.additional_ids` | `spar_datacite:Identifier` | broad |
| `license.spdx_id` | `spar_datacite:RightsIdentifier` | exact |

---

<a id="std-datacite-relations"></a>
### `datacite_relations` — DataCite Metadata Schema — relationType

- **Namespace:** [https://datacite-metadata-schema.readthedocs.io/en/latest/appendices/appendix-1/relationType/#](https://datacite-metadata-schema.readthedocs.io/en/latest/appendices/appendix-1/relationType/#)
- **Prefix:** `datacite_relations`

The DataCite Metadata Schema is the metadata standard for resources registered with DataCite DOIs, used by thousands of research data repositories. Its `relationType` controlled list (Appendix 1) defines how a resource relates to other identified resources — e.g., `IsDerivedFrom`, `IsPartOf`, `IsPreviousVersionOf`, `References`, `IsSupplementTo`. The Genesis `RelationshipTypeEnum` adopts this list (in snake_case) and adds ML-specific relationships aligned with FAIR4ML.

Alignment with DataCite relationTypes means `relationship` values can be exported directly into DataCite `relatedIdentifier` metadata when minting DOIs (e.g., through OSTI).

**Mappings (42):**

| Data card term | External term | Mapping type |
|---|---|---|
| `identification.supersedes` | `datacite_relations:Obsoletes` | exact |
| `identification.superseded_by` | `datacite_relations:IsObsoletedBy` | close |
| `relationship` = `is_cited_by` | `datacite_relations:IsCitedBy` | exact |
| `relationship` = `cites` | `datacite_relations:Cites` | exact |
| `relationship` = `is_supplement_to` | `datacite_relations:IsSupplementTo` | exact |
| `relationship` = `is_supplemented_by` | `datacite_relations:IsSupplementedBy` | exact |
| `relationship` = `is_continued_by` | `datacite_relations:IsContinuedBy` | exact |
| `relationship` = `continues` | `datacite_relations:Continues` | exact |
| `relationship` = `describes` | `datacite_relations:Describes` | exact |
| `relationship` = `is_described_by` | `datacite_relations:IsDescribedBy` | exact |
| `relationship` = `has_metadata` | `datacite_relations:HasMetadata` | exact |
| `relationship` = `is_metadata_for` | `datacite_relations:IsMetadataFor` | exact |
| `relationship` = `has_version` | `datacite_relations:HasVersion` | exact |
| `relationship` = `is_version_of` | `datacite_relations:IsVersionOf` | exact |
| `relationship` = `is_previous_version_of` | `datacite_relations:IsPreviousVersionOf` | exact |
| `relationship` = `is_part_of` | `datacite_relations:IsPartOf` | exact |
| `relationship` = `has_part` | `datacite_relations:HasPart` | exact |
| `relationship` = `is_published_in` | `datacite_relations:IsPublishedIn` | exact |
| `relationship` = `is_referenced_by` | `datacite_relations:IsReferencedBy` | exact |
| `relationship` = `references` | `datacite_relations:References` | exact |
| `relationship` = `is_documented_by` | `datacite_relations:IsDocumentedBy` | exact |
| `relationship` = `documents` | `datacite_relations:Documents` | exact |
| `relationship` = `is_compiled_by` | `datacite_relations:IsCompiledBy` | exact |
| `relationship` = `compiles` | `datacite_relations:Compiles` | exact |
| `relationship` = `is_variant_form_of` | `datacite_relations:IsVariantFormOf` | exact |
| `relationship` = `is_original_form_of` | `datacite_relations:IsOriginalFormOf` | exact |
| `relationship` = `is_identical_to` | `datacite_relations:IsIdenticalTo` | exact |
| `relationship` = `is_reviewed_by` | `datacite_relations:IsReviewedBy` | exact |
| `relationship` = `reviews` | `datacite_relations:Reviews` | exact |
| `relationship` = `is_derived_from` | `datacite_relations:IsDerivedFrom` | exact |
| `relationship` = `is_source_of` | `datacite_relations:IsSourceOf` | exact |
| `relationship` = `is_required_by` | `datacite_relations:IsRequiredBy` | exact |
| `relationship` = `requires` | `datacite_relations:Requires` | exact |
| `relationship` = `obsoletes` | `datacite_relations:Obsoletes` | exact |
| `relationship` = `is_obsoleted_by` | `datacite_relations:IsObsoletedBy` | exact |
| `relationship` = `is_collected_by` | `datacite_relations:IsCollectedBy` | exact |
| `relationship` = `collects` | `datacite_relations:Collects` | exact |
| `relationship` = `is_translation_of` | `datacite_relations:IsTranslationOf` | exact |
| `relationship` = `has_translation` | `datacite_relations:HasTranslation` | exact |
| `relationship` = `other` | `datacite_relations:Other` | exact |
| `relationship` = `generates` | `datacite_relations:Compiles` | related |
| `relationship` = `is_generated_by` | `datacite_relations:IsCompiledBy` | related |

**Mapping notes:**

- The Genesis-specific values `generates`, `is_generated_by`, `processes`, `is_processed_by`, `analyzes`, `is_analyzed_by`, `is_used_for_training`, and `is_used_for_evaluation` have no DataCite equivalent; `generates`/`is_generated_by` are mapped `broad` to `compiles`/`iscompiledby`. When exporting to DataCite, map the others to `References`/`IsReferencedBy`.

---

<a id="std-datacite-contributor"></a>
### `datacite_contributor` — DataCite Metadata Schema — contributorType

- **Namespace:** [https://datacite-metadata-schema.readthedocs.io/en/latest/appendices/appendix-1/contributorType/#](https://datacite-metadata-schema.readthedocs.io/en/latest/appendices/appendix-1/contributorType/#)
- **Prefix:** `datacite_contributor`

DataCite's `contributorType` controlled list (Appendix 1) classifies the role of contributors to a resource — e.g., `ContactPerson`, `DataCurator`, `DataManager`, `HostingInstitution`, `ProjectLeader`, `RightsHolder`, `Sponsor`, `Supervisor`. The Genesis `RoleEnum` includes these values alongside CRediT roles.

Alignment with DataCite contributorTypes lets the data card's `role` values be exported as DataCite `contributor` metadata.

**Mappings (22):**

| Data card term | External term | Mapping type |
|---|---|---|
| `role` = `Contact_Person` | `datacite_contributor:ContactPerson` | exact |
| `role` = `Data_Curator` | `datacite_contributor:DataCurator` | exact |
| `role` = `Data_Manager` | `datacite_contributor:DataManager` | exact |
| `role` = `Distributor` | `datacite_contributor:Distributor` | exact |
| `role` = `Editor` | `datacite_contributor:Editor` | exact |
| `role` = `Hosting_Institution` | `datacite_contributor:HostingInstitution` | exact |
| `role` = `Producer` | `datacite_contributor:Producer` | exact |
| `role` = `Project_Leader` | `datacite_contributor:ProjectLeader` | exact |
| `role` = `Project_Manager` | `datacite_contributor:ProjectManager` | exact |
| `role` = `Project_Member` | `datacite_contributor:ProjectMember` | exact |
| `role` = `Registration_Agency` | `datacite_contributor:RegistrationAgency` | exact |
| `role` = `Registration_Authority` | `datacite_contributor:RegistrationAuthority` | exact |
| `role` = `Related_Person` | `datacite_contributor:RelatedPerson` | exact |
| `role` = `Researcher` | `datacite_contributor:Researcher` | exact |
| `role` = `Research_Group` | `datacite_contributor:ResearchGroup` | exact |
| `role` = `Rights_Holder` | `datacite_contributor:RightsHolder` | exact |
| `role` = `Sponsor` | `datacite_contributor:Sponsor` | exact |
| `role` = `Supervision` | `datacite_contributor:Supervisor` | exact |
| `role` = `Translator` | `datacite_contributor:Translator` | exact |
| `role` = `Work_Package_Leader` | `datacite_contributor:WorkPackageLeader` | exact |
| `role` = `Other` | `datacite_contributor:Other` | exact |
| `role` = `Writing_Review_Editing` | `datacite:Editor` | close |


---

<a id="std-datacite-geo"></a>
### `datacite_geo` — DataCite Metadata Schema — geoLocation

- **Namespace:** [https://datacite-metadata-schema.readthedocs.io/en/latest/properties/geolocation/#](https://datacite-metadata-schema.readthedocs.io/en/latest/properties/geolocation/#)
- **Prefix:** `datacite_geo`

The DataCite `geoLocation` property describes the spatial region or named place where data was gathered or that the resource is about, including `geoLocationPlace`, `geoLocationPoint`, `geoLocationBox` (with `westBoundLongitude`, `eastBoundLongitude`, `southBoundLatitude`, `northBoundLatitude`), and `geoLocationPolygon`.

The data card's `spatial_coverage.geo_location_box` follows this model exactly, so bounding boxes can be exported to DataCite without conversion.

**Mappings (5):**

| Data card term | External term | Mapping type |
|---|---|---|
| `geo_location_box.west_bound_longitude` | `datacite_geo:westboundlongitude` | exact |
| `geo_location_box.east_bound_longitude` | `datacite_geo:eastboundlongitude` | exact |
| `geo_location_box.south_bound_latitude` | `datacite_geo:southboundlatitude` | exact |
| `geo_location_box.north_bound_latitude` | `datacite_geo:northboundlatitude` | exact |
| `spatial_coverage.description` | `datacite_geo:geoLocationPlace` | exact |

---

<a id="std-prov"></a>
### `prov` — W3C PROV Ontology (PROV-O)

- **Namespace:** [http://www.w3.org/ns/prov#](http://www.w3.org/ns/prov#)
- **Prefix:** `prov`

PROV-O is the OWL encoding of the W3C PROV data model (W3C Recommendation, 2013) for representing provenance: the **entities** (data), **activities** (processes), and **agents** (people, organizations, software) involved in producing something, and the relationships among them (`wasGeneratedBy`, `used`, `wasDerivedFrom`, `wasAttributedTo`, `startedAtTime`, `endedAtTime`, …).

Alignment with PROV supports machine-readable lineage and reproducibility, and links the data card's provenance, dates, and tool relationships to a formal provenance graph.

**Mappings (12):**

| Data card term | External term | Mapping type |
|---|---|---|
| `discoverability.datacard` | `prov:Entity` | exact |
| `dates.data_collection_start` | `prov:startedAtTime` | exact |
| `dates.data_collection_end` | `prov:endedAtTime` | exact |
| `provenance.was_generated_by` | `prov:wasGeneratedBy` | exact |
| `relationship` = `cites` | `prov:wasQuotedFrom` | close |
| `relationship` = `is_derived_from` | `prov:wasDerivedFrom` | exact |
| `relationship` = `generates` | `prov:generated` | related |
| `relationship` = `is_generated_by` | `prov:wasGeneratedBy` | related |
| `relationship` = `processes` | `prov:used` | related |
| `relationship` = `is_processed_by` | `prov:used` | related |
| `relationship` = `analyzes` | `prov:used` | related |
| `relationship` = `is_analyzed_by` | `prov:used` | related |

---

<a id="std-credit"></a>
### `credit` — CRediT — Contributor Roles Taxonomy

- **Namespace:** [https://credit.niso.org/contributor-roles/conceptualization/](https://credit.niso.org/contributor-roles/conceptualization/)
- **Prefix:** `credit`

CRediT is a taxonomy of 14 roles describing contributions to research outputs (Conceptualization, Data curation, Formal analysis, Funding acquisition, Investigation, Methodology, Project administration, Resources, Software, Supervision, Validation, Visualization, Writing – original draft, Writing – review & editing). Originally developed through CASRAI, it is now an ANSI/NISO standard (Z39.104-2022) maintained by NISO at https://credit.niso.org/. The Genesis `RoleEnum` includes the CRediT roles for attributing contributions by people, organizations, AI models, and software.

Alignment with CRediT lets data card contributor roles be reported consistently with journal and publisher contributor statements.

**Mappings (14):**

| Data card term | External term | Mapping type |
|---|---|---|
| `role` = `Conceptualization` | `credit:conceptualization` | exact |
| `role` = `Data_Curator` | `credit:data-curation` | exact |
| `role` = `Formal_Analysis` | `credit:formal-analysis` | exact |
| `role` = `Funding_Acquisition` | `credit:funding-acquisition` | exact |
| `role` = `Investigation` | `credit:investigation` | exact |
| `role` = `Methodology` | `credit:methodology` | exact |
| `role` = `Project_Administration` | `credit:project-administration` | exact |
| `role` = `Resources` | `credit:resources` | exact |
| `role` = `Software` | `credit:software` | exact |
| `role` = `Supervision` | `credit:supervision` | exact |
| `role` = `Validation` | `credit:validation` | exact |
| `role` = `Visualization` | `credit:visualization` | exact |
| `role` = `Writing_Original_Draft` | `credit:writing-original-draft` | exact |
| `role` = `Writing_Review_Editing` | `credit:writing-review-editing` | exact |

---

<a id="std-fair4ml"></a>
### `fair4ml` — FAIR4ML metadata schema

- **Namespace:** [https://w3id.org/fair4ml#](https://w3id.org/fair4ml#)
- **Prefix:** `fair4ml`

FAIR4ML is a metadata schema for describing machine learning models, developed by the Research Data Alliance (RDA) FAIR for Machine Learning (FAIR4ML) Interest Group as an extension of schema.org. It adds properties such as `trainedOn`, `testedOn`, `validatedOn`, `evaluatedOn`, `fineTunedFrom`, `intendedUse`, `mlTask`, and fields for risks, biases, limitations, and ethical/legal considerations. The current published release is v0.1.0.

Alignment with FAIR4ML connects Genesis data cards to model cards: the same dataset–model relationships and AI-use considerations can be read from either side.

**Mappings (13):**

| Data card term | External term | Mapping type |
|---|---|---|
| `use_governance.intended_use` | `fair4ml:intendedUse` | exact |
| `access_policy.policy_text` | `fair4ml:legal` | related |
| `dataset_description.task_category` | `fair4ml:mlTask` | exact |
| `ai_usage.restrictions` | `fair4ml:modelRisksBiasLimitations` | related |
| `ai_usage.bias_risks` | `fair4ml:modelRisksBiasLimitations` | related |
| `ai_usage.bias_risks` | `fair4ml:ethicalSocial` | related |
| `ai_usage.safety_considerations` | `fair4ml:modelRisksBiasLimitations` | related |
| `relationship` = `is_trained_on` | `fair4ml:trainedOn` | exact |
| `relationship` = `is_evaluated_on` | `fair4ml:evaluatedOn` | exact |
| `relationship` = `tested_on` | `fair4ml:testedOn` | exact |
| `relationship` = `validated_on` | `fair4ml:validatedOn` | exact |
| `relationship` = `fine_tuned_from` | `fair4ml:fineTunedFrom` | exact |
| `relationship` = `has_evaluation` | `fair4ml:hasEvaluation` | close |

**Mapping notes:**

- `ai_usage.restrictions`, `bias_risks`, and `safety_considerations` are `related` (not exact) because FAIR4ML's fields describe model risks rather than dataset-use constraints.

---

<a id="std-spdx"></a>
### `spdx` — SPDX 2.2 RDF terms

- **Namespace:** [http://spdx.org/rdf/terms#](http://spdx.org/rdf/terms#)
- **Prefix:** `spdx`

SPDX (Software Package Data Exchange) is a Linux Foundation standard for communicating software bill-of-materials information — packages, files, licenses, copyrights, and checksums. SPDX 2.2.1 is also published as ISO/IEC 5962:2021. The SPDX License List supplies the identifiers used in `reusability.license.spdx_id` (e.g., `CC-BY-4.0`, `MIT`).

Alignment with SPDX gives the data card's integrity fields a standard checksum representation and its license identifiers a standard vocabulary.

**Mappings (2):**

| Data card term | External term | Mapping type |
|---|---|---|
| `integrity.checksum_type` | `spdx:algorithm` | close |
| `integrity.checksum_value` | `spdx:checksumValue` | exact |

---

### Fields without external mappings

Many data card fields are Genesis- or DOE-specific and currently have no declared external mapping — notably the sensitivity block (`overall_sensitivity`, `source_marking_*`, `cui_*`, `ucni_status`, etc.), `governed_use` fields (export control, privacy, rights/release/records, compliance), `access_policy.access_level` and `authorization_required`, `workflow.release_status`, `sponsor_organizations`, `ai_usage.*_use_status`, and `data_quality.*`. Candidate alignments for future versions include `dcterms:accessRights` / `dcat:accessRights` for `access_level`, `dcterms:publisher` / `schema:publisher` for `dataset_publisher`, `dcterms:license` / `schema:license` for `license`, `schema:funder` / DataCite `fundingReference` for `sponsor_organizations`, `schema:keywords` / `dcat:keyword` for `keywords`, `dcterms:title` / `schema:name` for `identification.name`, `dcat:contactPoint` for `contact`, `dcterms:creator` / `schema:creator` for `authors`, and `dcterms:bibliographicCitation` / `schema:citation` for `preferred_citation`.

---

## Appendix A: Common Mistakes

| Mistake | Correct approach |
|---|---|
| Setting `discoverability.datacard.sensitivity` to match `discoverability.sensitivity` by default | Set each independently — the data card document vs. the dataset. They will often differ. |
| Leaving `agent_type:` or `type: person` lines from a v1.2 card | Delete them. In v2.0.0 the populated sub-block (`person`, `organization`, `ai_model`, `software`) identifies the agent. |
| Populating more than one agent sub-block in a single entry | Use exactly one sub-block per entry; create additional entries for additional agents. |
| Writing `contact:` as a single block | `contact` is a list: `contact:` → `- person: …` |
| Using v1.2 relationship values (`used_to_process`, `trained_on`, `is_based_on`, …) | Use `RelationshipTypeEnum` values: `processes`, `is_trained_on`, `is_derived_from`, etc. |
| Using role values with spaces or removed values (`"Data Curation"`, `Data_Collection`) | Use `RoleEnum` values exactly, e.g. `Data_Curator`, `Investigation`. |
| `product_type: Data` | Use `Dataset`. |
| Using an OSTI code (`ND`, `IM`, …) for `dataset_type` | Only `Instrument` is valid; otherwise omit. |
| Setting `overall_sensitivity: CUI` but leaving `cui_status: "No"` | Keep the summary and status fields consistent — the schema enforces this. |
| Using `"No"` for `irb_approved` when the dataset has no human subjects | Use `not_applicable`. |
| Leaving `restrictions`, `bias_risks`, or `safety_considerations` blank | Use `not_applicable` explicitly. |
| Setting `doi` as `primary_id.type` before a DOI has been minted | Use `ark` or `local` until assigned; retain the ARK in `additional_ids` afterwards. |
| Leaving `provenance.was_generated_by` and `processing_steps` blank | Both are `[interoperability_required]`. Even a single sentence helps. |
| Writing "good" or "clean" for `data_quality` fields | Be specific — what is present, missing, why, and when. |
| Not updating `change_log` when editing | Add an entry every time; never delete or overwrite prior entries. |
| Setting `foreign_national_access_status` without checking `cui_limited_dissemination_controls` | Keep them consistent (NOFORN / REL TO → `Prohibited` or `Conditional`). |
| Writing `features[].range` as a list (`[0, 1000]`) | `range` is a string: `"0 - 1000"`. |
| Writing `domain_metadata.fields` as a map keyed by field name | Use a list of entries, each with `name`, `field_value`, `data_type`, `unit`, `description`. |
| Leaving the default `data_structure.language: "en"` on numeric data | Replace with `not_applicable` for non-linguistic data. |
| Using `true`/`false` or unquoted `Yes`/`No` | Use quoted `"Yes"` / `"No"`. |
| Setting `export_control_basis` without consulting your export control office | Consult before selecting a value other than `not_applicable`. |
| Omitting `succession_note` for project-bound contacts | If `valid_until` is set, always provide a `succession_note`. |
| Using a relative path such as `LICENSE.md` for `license.url` | Provide a full `https://` URL. |
| Uppercase letters, hyphens, or spaces in `filename` | Lowercase letters, digits, and underscores only. |

---

## Appendix B: Identifier Type Quick Reference

All identifier `type` fields use `IdentifierTypeEnum`.

| Type | Format | When to use |
|---|---|---|
| `doi` | `10.XXXXX/XXXXXXX` | Published datasets with a registered DOI |
| `ark` | `ark:/NAAN/shoulder+name` | Pre-publication datasets at ARK-enabled institutions; retained after a DOI is minted |
| `handle` | `XXXXX/XXXXXXX` | Handle-based repositories |
| `purl` | `https://purl.org/...` | PURL-based persistent identifiers |
| `url` | `https://...` | When a stable URL is the best available identifier (including arXiv abstract pages) |
| `urn` | `urn:...` | URN-based persistent identifiers |
| `uuid` | `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx` | UUID-based local identifiers |
| `local` | Any internal ID | Pre-publication datasets with only an internal identifier (e.g., `genesis-ds-2024-0042`) |
| `other` | Any | Identifier systems not covered above (e.g., report numbers) |
| `unregistered` | — | The object (typically the data card) has not been registered |

If `type` is given, `value` must be given, and vice versa. ARKs resolve via `https://n2t.net/ark:/NAAN/...`.

---

## Appendix C: Sensitivity Quick Reference

Both `discoverability.datacard.sensitivity` and `discoverability.sensitivity` use `OverallSensitivityEnum`. Set each independently.

| Value | Meaning | Required consistency |
|---|---|---|
| `Public` | No sensitivity; publicly shareable | — |
| `Unclassified_Uncontrolled` | Unclassified and uncontrolled; minimal sensitivity; generally shareable with minimal controls | — |
| `CUI` | Controlled Unclassified Information; handle per CUI guidelines; access controls required | `cui_status: "Yes"`, `classified_status: "No"` |
| `UCNI` | Unclassified Controlled Nuclear Information; strict access controls required | `ucni_status: "Yes"`, `cui_specified_categories` present |
| `Classified` | Classified information; handle per classification level and guide | `classified_status: "Yes"`, `classification_level` and `classification_category` present |
| `Legacy_Controlled` | Legacy controlled information; handling per legacy controls | Typically `source_marking_scheme: Legacy_OUO` with `legacy_label_source` and `normalized_control_basis` |
| `Mixed` | Combination of sensitive and non-sensitive information | Populate all applicable status fields |
| `Other_Controlled` | Other controlled information with specific handling requirements | — |

---

## Appendix D: Field Requirements Summary

`✅` required when the capability flag is `"Yes"` · `◐` situational (condition noted) · `○` optional / if-applicable · `★` recommended · `—` not governed by this capability. Discoverability is always `"Yes"`.

| Field | Capability | Requirement | Condition / note |
|---|---|---|---|
| `xCard.card_type` | Root | ✅ | Always `dataset` |
| `supports_*` (six flags) | Root | ✅ | — |
| `datacard.template_version`, `datacard_version`, `filename`, `language` | Discoverability | ✅ | — |
| `datacard.id` | Discoverability | ○ | - |
| `datacard.sensitivity` (block) | Discoverability | ✅ | Sub-fields below |
| `*.sensitivity.overall_sensitivity`, `source_marking_string`, `source_marking_scheme`, `classified_status`, `cui_status`, `ucni_status` | Discoverability | ✅ | Both sensitivity blocks |
| `*.sensitivity.classification_level`, `classification_category` | Discoverability | ◐ | `classified_status = "Yes"` |
| `*.sensitivity.cui_specified_categories` | Discoverability | ◐ | `cui_status` or `ucni_status = "Yes"` |
| `*.sensitivity` other sub-fields | Discoverability | ○ | — |
| `datacard.creation_method`, `created_date`, `change_log`, `created_by` | Discoverability | ✅ | — |
| `datacard.updated_date` | Discoverability | ○ | — |
| `identification.name`, `project`, `version`, `primary_id` | Discoverability | ✅ | — |
| `identification.additional_ids`, `supersedes`, `superseded_by`, `parent_collection` | Discoverability | ○ | — |
| `dataset_description.dataset_summary`, `keywords` | Discoverability | ✅ | — |
| `dataset_description.limitations` | Discoverability | ○★ | — |
| `dataset_description.science_domain`, `purpose`, `collection_methodology`, `data_characteristics`, `tags`, `task_category`, `task_subcategory` | Discoverability | ○ | `task_category` required if `task_subcategory` present |
| `product_type`, `release_status` | Discoverability | ✅ | — |
| `dataset_type` | Discoverability | ○ | Instrument data only |
| `dataset_publisher` | Discoverability | ◐ | `release_status = Approved \| Published` |
| `contact` | Discoverability | ✅ | List, ≥ 1 |
| `additional_contacts`, `contributors`, `facilities`, `sponsoring_doe_program_office`, `sponsoring_doe_subprogram` | Discoverability | ○ | — |
| `authors` | Discoverability | ◐ | `release_status = Approved \| Published` |
| `sponsor_organizations`, `research_organizations` | Discoverability | ✅ | List, ≥ 1 |
| `discoverability.sensitivity` (block) | Discoverability | ✅ | See sensitivity rows |
| `workflow.state` | Discoverability | ✅ | — |
| `workflow.is_intermediate`, `pipeline_stage` | Discoverability | ○★ | — |
| `workflow.embargo_until` | Discoverability | ◐ | Required if `state = Embargo`; absent if `Published` |
| `access_policy.access_level` | Accessibility | ✅ | — |
| `access_policy.authorization_required` | Accessibility | ◐ | `access_level = Restricted \| Controlled` |
| `access_policy.access_restrictions` | Accessibility | ◐ | `authorization_required` includes `Other` |
| `access_policy.intended_partner_classes`, `approved_environments`, `policy_url`, `policy_text` | Accessibility | ○ | — |
| `access.current_location` | Accessibility | ✅ | — |
| `access.publicly_facing_landing_page_url`, `intended_repositories` | Accessibility | ○ | `intended_repositories[].access_level` required per entry |
| `dataset_scale` | Accessibility | ○ | — |
| `data_structure.formats`, `modalities`, `features` | Interoperability | ✅ | — |
| `data_structure.encoding`, `schema_version`, `splits`, `language`, `spatial_coverage`, `temporal_coverage` | Interoperability | ○ | — |
| `provenance.was_generated_by`, `processing_steps` | Interoperability | ✅ | — |
| `provenance.source_data`, `instrumentation`, `simulation_details`, `software_environment` | Interoperability | ○ | — |
| `dates`, `semantic_layer`, `related_resources`, `domain_metadata` | Interoperability | ○ | — |
| `license`, `additional_licenses` | Reusability | ○★ | License strongly recommended when Approved/Published |
| `stewardship` | Reusability | ○ | Maintainer: person XOR organization |
| `data_quality.completeness`, `known_issues`, `validation_methods` | Reusability | ✅ | — |
| `data_quality.noise_characteristics`, `uncertainty_notes`, `missing_data_codes` | Reusability | ○ | — |
| `citation` | Reusability | ◐ | `release_status = Approved \| Published` |
| `integrity` | Reusability | ○ | `checksum_type`/`value` required if `checksum_available = "Yes"`; validator note |
| `use_governance.current_use` | Governed Use | ✅ | — |
| `use_governance.intended_use`, `permitted_use`, `out_of_scope_use`, `prohibited_use` | Governed Use | ○★ | — |
| `export_control.export_control_status` | Governed Use | ✅ | — |
| `export_control.export_control_basis` | Governed Use | ◐ | `export_control_status = "Yes"` |
| `export_control.foreign_national_access_status` | Governed Use | ○ | — |
| `privacy.privacy_status`, `pii_status`, `phi_status` | Governed Use | ✅ | - |
| `privacy.privacy_control_basis`, `privacy_regime_notes` | Governed Use | ○ | — |
| `rights_release_records.agreement_required`, `public_release_status`, `record_status` | Governed Use | ✅ | — |
| `rights_release_records.agreement_type` | Governed Use | ◐ | `agreement_required = "Yes"` |
| `rights_release_records.ip_restriction_type` | Governed Use | ○ | — |
| `compliance.*` | Governed Use | ◐ | `release_status = Under_Review \| Approved \| Published`; |
| `review_provenance_companion` | Governed Use | ○★ | — |
| `ai_usage.training_use_status`, `inference_use_status`, `evaluation_use_status`, `restrictions`, `bias_risks`, `safety_considerations`, `human_review_required` | AI Usability | ✅ | - |
| `ai_usage.*_use_conditions` | AI Usability | ◐ | Corresponding status = `Conditional` |

---

## Appendix E: Getting Help

| Resource | Location |
|---|---|
| Genesis data management team | TBD |
| Template, schema, and validator | https://gitlab.com/amsc2/modcon/dbs/data-cards |
| Template roadmap | https://gitlab.com/amsc2/modcon/dbs/data-cards/-/milestones |
| ROR ID lookup | https://ror.org |
| ORCID registration | https://orcid.org |
| SPDX license list | https://spdx.org/licenses/ |
| CUI registry | https://www.archives.gov/cui |
| ARK identifier information | https://arks.org |
| OSTI E-Link 2 API documentation | https://www.osti.gov/elink |
| CRediT taxonomy | https://credit.niso.org |
| DataCite Metadata Schema | https://datacite-metadata-schema.readthedocs.io |

---

