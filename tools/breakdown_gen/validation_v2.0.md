# Breakdown validation

- Template: `inputs/data-cards-v2.0.0.zip::data-cards-v2.0.0/template/latest/template/genesis_datacard_merged_shared.yaml`
- Breakdown: `genesis_dc_v2.0_breakdown.generated.yaml`

| Section | Template keys | Breakdown fields | Errors | Warnings | Expected |
|---|---|---|---|---|---|
| xCard | 2 | 0 | 0 | 0 | 2 |
| intended capabilities (supports_*) | 6 | 6 | 0 | 0 | 0 |
| discoverability | 242 | 247 | 0 | 1 | 5 |
| accessibility | 29 | 29 | 0 | 1 | 0 |
| interoperability | 94 | 94 | 0 | 0 | 0 |
| reusability | 57 | 58 | 0 | 0 | 1 |
| governed_use | 68 | 69 | 0 | 0 | 1 |
| ai_usability | 12 | 12 | 0 | 0 | 0 |

## ERROR (0)


## WARNING (2)

- `discoverability.dataset_description.tags.object_type`: tagged [discoverability_required] but required: false (inside optional block `discoverability.dataset_description.tags`; MAVEN would otherwise force it)
- `accessibility.access.intended_repositories.access_level`: tagged [accessibility_required] but required: false (inside optional block `accessibility.access.intended_repositories`; MAVEN would otherwise force it)

## EXPECTED (9)

- `xCard`: not in breakdown: excluded by --allow-missing
- `xCard.card_type`: not in breakdown: excluded by --allow-missing
- `discoverability.datacard.created_by.creator.agent_type`: discriminator added for the one-of blocks ['person', 'organization', 'ai_model', 'software']
- `discoverability.contact.agent_type`: discriminator added for the one-of blocks ['person', 'organization']
- `discoverability.additional_contacts.agent_type`: discriminator added for the one-of blocks ['person', 'organization']
- `discoverability.authors.agent_type`: discriminator added for the one-of blocks ['person', 'organization', 'ai_model', 'software']
- `discoverability.contributors.agent_type`: discriminator added for the one-of blocks ['person', 'organization', 'ai_model', 'software']
- `reusability.stewardship.maintainer.agent_type`: discriminator added for the one-of blocks ['person', 'organization']
- `governed_use.review_provenance_companion.reviewed_by.agent_type`: discriminator added for the one-of blocks ['person', 'organization', 'ai_model', 'software']
