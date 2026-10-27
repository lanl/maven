# Breakdown generation review: config_v2.0.yaml

Items below are where the generator had to choose. Check them, then record any change in the config `overrides:` so the next run reproduces it.

## `required` taken from the schema, but the template tag disagrees (0)


## Dropdown options: schema enum differs from the template comment (schema used) (0)


## Extra 'nothing applies' option added to a required dropdown (Vedant's rule 2) (6)

- `discoverability.datacard.sensitivity.overall_sensitivity`: added `None`
- `discoverability.release_status`: added `None`
- `discoverability.sensitivity.overall_sensitivity`: added `None`
- `accessibility.access_policy.access_level`: added `None`
- `reusability.data_quality.known_issues`: added `None`
- `governed_use.non_sensitivity_governance_metadata.rights_release_records.public_release_status`: added `None`

## List fields rendered as a single-choice dropdown (MAVEN has no multiselect) (0)


## No schema enum; options taken from the template comment (0)


## Field not found in the schema; `required` taken from the template tag (0)


## Discriminators added for one-of blocks (7)

- `discoverability.datacard.created_by.creator`: added `agent_type` (options ['person', 'organization', 'ai_model', 'software']); not in the template
- `discoverability.contact`: added `agent_type` (options ['person', 'organization']); not in the template
- `discoverability.additional_contacts`: added `agent_type` (options ['person', 'organization']); not in the template
- `discoverability.authors`: added `agent_type` (options ['person', 'organization', 'ai_model', 'software']); not in the template
- `discoverability.contributors`: added `agent_type` (options ['person', 'organization', 'ai_model', 'software']); not in the template
- `reusability.stewardship.maintainer`: added `agent_type` (options ['person', 'organization']); not in the template
- `governed_use.review_provenance_companion.reviewed_by`: added `agent_type` (options ['person', 'organization', 'ai_model', 'software']); not in the template

## No template comment; description fallback (0)


## Top-level blocks excluded by config (1)

- `xCard` (template line 182)

## Manual overrides applied from the config (4)

- `discoverability.identification.name`: {'required': True}
- `discoverability.identification.primary_id.type`: {'required': True}
- `discoverability.identification.primary_id.value`: {'required': True}
- `discoverability.contact.person.email`: {'required': True}
