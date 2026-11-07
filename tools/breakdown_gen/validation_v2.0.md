# Breakdown validation

- Template: `templates/genesis_datacard_v2.0.0_vedant.yaml`
- Breakdown: `genesis_dc_v2.0_breakdown.generated.yaml`

| Section | Template keys | Breakdown fields | Errors | Warnings | Expected |
|---|---|---|---|---|---|
| xCard | 2 | 2 | 0 | 0 | 0 |
| intended capabilities (supports_*) | 6 | 6 | 0 | 0 | 6 |
| discoverability | 242 | 170 | 0 | 1 | 77 |
| accessibility | 29 | 29 | 0 | 1 | 0 |
| interoperability | 94 | 61 | 0 | 1 | 33 |
| reusability | 57 | 42 | 0 | 0 | 15 |
| governed_use | 68 | 59 | 0 | 0 | 9 |
| ai_usability | 12 | 12 | 0 | 0 | 0 |

## ERROR (0)


## WARNING (3)

- `discoverability.dataset_description.tags.object_type`: tagged [discoverability_required] but required: false
- `accessibility.access.intended_repositories.access_level`: tagged [accessibility_required] but required: false
- `interoperability.provenance.processing_steps`: tagged [interoperability_required] but required: false

## EXPECTED (140)

- `discoverability.datacard.created_by.creator.person.orcid`: not in breakdown: excluded by --allow-missing
- `discoverability.datacard.created_by.creator.person.affiliation.ror_id`: not in breakdown: excluded by --allow-missing
- `discoverability.datacard.created_by.creator.organization.ror_id`: not in breakdown: excluded by --allow-missing
- `discoverability.datacard.created_by.creator.ai_model.identifier`: not in breakdown: excluded by --allow-missing
- `discoverability.datacard.created_by.creator.ai_model.identifier.type`: not in breakdown: excluded by --allow-missing
- `discoverability.datacard.created_by.creator.ai_model.identifier.value`: not in breakdown: excluded by --allow-missing
- `discoverability.datacard.created_by.creator.software.identifier`: not in breakdown: excluded by --allow-missing
- `discoverability.datacard.created_by.creator.software.identifier.type`: not in breakdown: excluded by --allow-missing
- `discoverability.datacard.created_by.creator.software.identifier.value`: not in breakdown: excluded by --allow-missing
- `discoverability.dataset_type`: not in breakdown: excluded by --allow-missing
- `discoverability.dataset_publisher.ror_id`: not in breakdown: excluded by --allow-missing
- `discoverability.contact.person.orcid`: not in breakdown: excluded by --allow-missing
- `discoverability.contact.person.affiliation.ror_id`: not in breakdown: excluded by --allow-missing
- `discoverability.contact.organization.ror_id`: not in breakdown: excluded by --allow-missing
- `discoverability.additional_contacts.person.orcid`: not in breakdown: excluded by --allow-missing
- `discoverability.additional_contacts.person.affiliation.ror_id`: not in breakdown: excluded by --allow-missing
- `discoverability.additional_contacts.organization.ror_id`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.person.orcid`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.person.affiliation.ror_id`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.organization.ror_id`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.ai_model`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.ai_model.name`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.ai_model.version`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.ai_model.accessed_date`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.ai_model.identifier`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.ai_model.identifier.type`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.ai_model.identifier.value`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.ai_model.role`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.ai_model.relationship`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.software`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.software.name`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.software.version`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.software.identifier`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.software.identifier.type`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.software.identifier.value`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.software.role`: not in breakdown: excluded by --allow-missing
- `discoverability.authors.software.relationship`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.person`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.person.given_name`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.person.family_name`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.person.orcid`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.person.email`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.person.affiliation`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.person.affiliation.name`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.person.affiliation.ror_id`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.person.role`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.organization`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.organization.name`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.organization.ror_id`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.organization.role`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.ai_model`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.ai_model.name`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.ai_model.version`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.ai_model.accessed_date`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.ai_model.identifier`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.ai_model.identifier.type`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.ai_model.identifier.value`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.ai_model.role`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.ai_model.relationship`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.software`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.software.name`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.software.version`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.software.identifier`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.software.identifier.type`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.software.identifier.value`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.software.role`: not in breakdown: excluded by --allow-missing
- `discoverability.contributors.software.relationship`: not in breakdown: excluded by --allow-missing
- `discoverability.sponsor_organizations.ror_id`: not in breakdown: excluded by --allow-missing
- `discoverability.research_organizations.ror_id`: not in breakdown: excluded by --allow-missing
- `discoverability.facilities.ror_id`: not in breakdown: excluded by --allow-missing
- `discoverability.facilities.location.ror_id`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.features`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.features.name`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.features.description`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.features.data_type`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.features.unit`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.features.range`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.splits`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.spatial_coverage`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.spatial_coverage.description`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.spatial_coverage.geo_location_box`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.spatial_coverage.geo_location_box.west_bound_longitude`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.spatial_coverage.geo_location_box.east_bound_longitude`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.spatial_coverage.geo_location_box.south_bound_latitude`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.spatial_coverage.geo_location_box.north_bound_latitude`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.temporal_coverage`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.temporal_coverage.start_date`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.temporal_coverage.end_date`: not in breakdown: excluded by --allow-missing
- `interoperability.data_structure.temporal_coverage.description`: not in breakdown: excluded by --allow-missing
- `interoperability.provenance.software_environment`: not in breakdown: excluded by --allow-missing
- `interoperability.provenance.software_environment.os`: not in breakdown: excluded by --allow-missing
- `interoperability.provenance.software_environment.compiler`: not in breakdown: excluded by --allow-missing
- `interoperability.provenance.software_environment.container`: not in breakdown: excluded by --allow-missing
- `interoperability.provenance.software_environment.hpc_environment`: not in breakdown: excluded by --allow-missing
- `interoperability.provenance.software_environment.notes`: not in breakdown: excluded by --allow-missing
- `interoperability.semantic_layer`: not in breakdown: excluded by --allow-missing
- `interoperability.semantic_layer.schema_url`: not in breakdown: excluded by --allow-missing
- `interoperability.semantic_layer.semantic_context`: not in breakdown: excluded by --allow-missing
- `interoperability.related_resources.software.identifier`: not in breakdown: excluded by --allow-missing
- `interoperability.related_resources.software.identifier.type`: not in breakdown: excluded by --allow-missing
- `interoperability.related_resources.software.identifier.value`: not in breakdown: excluded by --allow-missing
- `interoperability.related_resources.ai_models.identifier`: not in breakdown: excluded by --allow-missing
- `interoperability.related_resources.ai_models.identifier.type`: not in breakdown: excluded by --allow-missing
- `interoperability.related_resources.ai_models.identifier.value`: not in breakdown: excluded by --allow-missing
- `reusability.additional_licenses`: not in breakdown: excluded by --allow-missing
- `reusability.additional_licenses.spdx_id`: not in breakdown: excluded by --allow-missing
- `reusability.additional_licenses.name`: not in breakdown: excluded by --allow-missing
- `reusability.additional_licenses.url`: not in breakdown: excluded by --allow-missing
- `reusability.additional_licenses.known_contractual_rights`: not in breakdown: excluded by --allow-missing
- `reusability.stewardship.maintainer.person.orcid`: not in breakdown: excluded by --allow-missing
- `reusability.stewardship.maintainer.person.affiliation.ror_id`: not in breakdown: excluded by --allow-missing
- `reusability.stewardship.maintainer.organization.ror_id`: not in breakdown: excluded by --allow-missing
- `reusability.citation.preferred_citation.eprinttype`: not in breakdown: excluded by --allow-missing
- `reusability.citation.preferred_citation.eprint`: not in breakdown: excluded by --allow-missing
- `reusability.integrity`: not in breakdown: excluded by --allow-missing
- `reusability.integrity.checksum_available`: not in breakdown: excluded by --allow-missing
- `reusability.integrity.checksum_type`: not in breakdown: excluded by --allow-missing
- `reusability.integrity.checksum_value`: not in breakdown: excluded by --allow-missing
- `reusability.integrity.fixity_policy`: not in breakdown: excluded by --allow-missing
- `governed_use.review_provenance_companion.reviewed_by.person.orcid`: not in breakdown: excluded by --allow-missing
- `governed_use.review_provenance_companion.reviewed_by.person.affiliation.ror_id`: not in breakdown: excluded by --allow-missing
- `governed_use.review_provenance_companion.reviewed_by.organization.ror_id`: not in breakdown: excluded by --allow-missing
- `governed_use.review_provenance_companion.reviewed_by.ai_model.identifier`: not in breakdown: excluded by --allow-missing
- `governed_use.review_provenance_companion.reviewed_by.ai_model.identifier.type`: not in breakdown: excluded by --allow-missing
- `governed_use.review_provenance_companion.reviewed_by.ai_model.identifier.value`: not in breakdown: excluded by --allow-missing
- `governed_use.review_provenance_companion.reviewed_by.software.identifier`: not in breakdown: excluded by --allow-missing
- `governed_use.review_provenance_companion.reviewed_by.software.identifier.type`: not in breakdown: excluded by --allow-missing
- `governed_use.review_provenance_companion.reviewed_by.software.identifier.value`: not in breakdown: excluded by --allow-missing
- `supports_discoverability`: pre-filled: template '${"Yes|No"}' -> breakdown 'Yes'
- `supports_accessibility`: pre-filled: template '${"Yes|No"}' -> breakdown 'Yes'
- `supports_interoperability`: pre-filled: template '${"Yes|No"}' -> breakdown 'Yes'
- `supports_reusability`: pre-filled: template '${"Yes|No"}' -> breakdown 'Yes'
- `supports_governed_use`: pre-filled: template '${"Yes|No"}' -> breakdown 'Yes'
- `supports_ai_usability`: pre-filled: template '${"Yes|No"}' -> breakdown 'Yes'
- `discoverability.datacard.id.type`: pre-filled: template '__TYPE__' -> breakdown 'unregistered'
- `discoverability.datacard.created_by.creator.ai_model.role`: pre-filled: template [] -> breakdown 'Writing_Original_Draft'
- `discoverability.datacard.created_by.creator.ai_model.relationship`: pre-filled: template '${RELATIONSHIP}' -> breakdown 'generates'
- `discoverability.datacard.created_by.creator.software.role`: pre-filled: template [] -> breakdown 'Software'
- `discoverability.datacard.created_by.creator.software.relationship`: pre-filled: template '${RELATIONSHIP}' -> breakdown 'processes'
