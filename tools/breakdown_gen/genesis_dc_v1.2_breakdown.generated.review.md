# Breakdown generation review: config_v1.2.yaml

Items below are where the generator had to choose. Check them, then record any change in the config `overrides:` so the next run reproduces it.

## `required` taken from the schema, but the template tag disagrees (0)


## Dropdown options: schema enum differs from the template comment (schema used) (0)


## Extra 'nothing applies' option added to a required dropdown (Vedant's rule 2) (3)

- `discoverability.datacard.created_by.creator.ai_model.relationship`: added `None`
- `discoverability.datacard.created_by.creator.software.relationship`: added `None`
- `discoverability.workflow.state`: added `None`

## List fields rendered as a single-choice dropdown (MAVEN has no multiselect) (0)


## No schema enum; options taken from the template comment (0)


## Field not found in the schema; `required` taken from the template tag (0)


## Discriminators added for one-of blocks (0)


## No template comment; description fallback (80)

- `discoverability.datacard.id.value`: empty
- `discoverability.datacard.created_by.creator.person`: empty
- `discoverability.datacard.created_by.creator.person.given_name`: empty
- `discoverability.datacard.created_by.creator.person.family_name`: empty
- `discoverability.datacard.created_by.creator.person.email`: empty
- `discoverability.datacard.created_by.creator.person.affiliation`: empty
- `discoverability.datacard.created_by.creator.person.affiliation.name`: empty
- `discoverability.datacard.created_by.creator.organization`: empty
- `discoverability.datacard.created_by.creator.organization.name`: empty
- `discoverability.datacard.created_by.creator.organization.ror_id`: empty
- `discoverability.datacard.created_by.creator.ai_model`: empty
- `discoverability.datacard.created_by.creator.ai_model.version`: empty
- `discoverability.datacard.created_by.creator.ai_model.accessed_date`: empty
- `discoverability.datacard.created_by.creator.ai_model.identifier`: empty
- `discoverability.datacard.created_by.creator.software`: empty
- `discoverability.datacard.created_by.creator.software.name`: empty
- `discoverability.datacard.created_by.creator.software.version`: empty
- `discoverability.datacard.created_by.creator.software.identifier`: empty
- `discoverability.datacard.created_by.creator.software.identifier.value`: empty
- `discoverability.identification.primary_id.value`: empty
- `discoverability.identification.supersedes.value`: empty
- `discoverability.identification.superseded_by.value`: empty
- `discoverability.identification.parent_collection.name`: empty
- `discoverability.identification.parent_collection.identifier`: empty
- `discoverability.identification.parent_collection.identifier.value`: empty
- `discoverability.contact.person`: empty
- `discoverability.contact.person.given_name`: empty
- `discoverability.contact.person.family_name`: empty
- `discoverability.contact.person.email`: empty
- `discoverability.contact.person.affiliation`: empty
- `discoverability.contact.person.affiliation.name`: empty
- `discoverability.authors.person`: empty
- `discoverability.authors.person.given_name`: empty
- `discoverability.authors.person.family_name`: empty
- `discoverability.authors.person.email`: empty
- `discoverability.authors.person.affiliation`: empty
- `discoverability.authors.person.affiliation.name`: empty
- `discoverability.authors.person.affiliation.ror_id`: empty
- `discoverability.authors.organization`: empty
- `discoverability.authors.organization.name`: empty
- `discoverability.authors.organization.ror_id`: empty
- `discoverability.sponsor_organizations.ror_id`: empty
- `discoverability.research_organizations.ror_id`: empty
- `accessibility.access.intended_repositories.date_deposited`: empty
- `accessibility.access.intended_repositories.data_services.endpoint`: empty
- `accessibility.access.intended_repositories.data_services.documentation_url`: empty
- `accessibility.access.intended_repositories.data_services.version`: empty
- `interoperability.data_structure`: empty
- `interoperability.data_structure.temporal_coverage.description`: empty
- `interoperability.provenance.source_data.name`: empty
- `interoperability.provenance.source_data.identifier`: empty
- `interoperability.provenance.source_data.identifier.value`: empty
- `interoperability.related_resources.datasets`: empty
- `interoperability.related_resources.software`: empty
- `interoperability.domain_metadata.name`: empty
- `interoperability.domain_metadata.schema_reference`: empty
- `interoperability.domain_metadata.schema_reference.value`: empty
- `interoperability.domain_metadata.version`: empty
- `reusability.stewardship.maintainer.person`: empty
- `reusability.stewardship.maintainer.person.given_name`: empty
- `reusability.stewardship.maintainer.person.family_name`: empty
- `reusability.stewardship.maintainer.person.email`: empty
- `reusability.stewardship.maintainer.person.affiliation`: empty
- `reusability.stewardship.maintainer.person.affiliation.name`: empty
- `reusability.stewardship.maintainer.person.affiliation.ror_id`: empty
- `reusability.stewardship.maintainer.organization`: empty
- `reusability.stewardship.maintainer.organization.name`: empty
- `reusability.stewardship.maintainer.organization.ror_id`: empty
- `reusability.data_quality.noise_characteristics`: empty
- `reusability.data_quality.missing_data_codes`: empty
- `reusability.citation.preferred_citation`: empty
- `governed_use.review_provenance_companion.reviewed_by.person`: empty
- `governed_use.review_provenance_companion.reviewed_by.person.given_name`: empty
- `governed_use.review_provenance_companion.reviewed_by.person.family_name`: empty
- `governed_use.review_provenance_companion.reviewed_by.person.email`: empty
- `governed_use.review_provenance_companion.reviewed_by.person.ror_id`: empty
- `governed_use.review_provenance_companion.reviewed_by.organization`: empty
- `governed_use.review_provenance_companion.reviewed_by.organization.name`: empty
- `governed_use.review_provenance_companion.reviewed_by.organization.ror_id`: empty
- `governed_use.review_provenance_companion.comments`: empty

## Top-level blocks excluded by config (1)

- `_repository` (template line 1117)

## Manual overrides applied from the config (4)

- `discoverability.identification.primary_id.value`: {'required': True}
- `discoverability.contact.person.email`: {'required': True}
- `discoverability.datacard.created_by.creator.organization.ror_id`: {'required': False}
- `discoverability.workflow.state`: {'options': ['Raw', 'Processing', 'QA', 'Analysis', 'Review', 'Embargo', 'Published', 'Archived', 'not_applicable']}
