# Breakdown generation review: config_v2.0.yaml

Items below are where the generator had to choose. Check them, then record any change in the config `overrides:` so the next run reproduces it.

## `required` taken from the schema, but the template tag disagrees (0)


## Dropdown options: schema enum differs from the template comment (schema used) (0)


## Extra 'nothing applies' option added to a required dropdown (Vedant's rule 2) (0)


## List fields rendered as a single-choice dropdown (MAVEN has no multiselect) (0)


## No schema enum; options taken from the template comment (0)


## Field not found in the schema; `required` taken from the template tag (0)


## Discriminators added for one-of blocks (0)


## No template comment; description fallback (1)

- `xCard.card_type`: empty

## Blocks excluded by config (exclude_top_level, exclude) (20)

- `*.ror_id`: 19 template fields
- `*.orcid`: 7 template fields
- `*.software.identifier`: 15 template fields
- `*.ai_model.identifier`: 12 template fields
- `*.ai_models.identifier`: 3 template fields
- `discoverability.contributors`: 31 template fields
- `discoverability.dataset_type`: 1 template fields
- `discoverability.contact.valid_until`: 1 template fields
- `discoverability.authors.ai_model`: 9 template fields
- `discoverability.authors.software`: 8 template fields
- `interoperability.data_structure.features`: 6 template fields
- `interoperability.data_structure.splits`: 1 template fields
- `interoperability.data_structure.spatial_coverage`: 7 template fields
- `interoperability.data_structure.temporal_coverage`: 4 template fields
- `interoperability.provenance.software_environment`: 6 template fields
- `interoperability.semantic_layer`: 3 template fields
- `reusability.citation.preferred_citation.eprinttype`: 1 template fields
- `reusability.citation.preferred_citation.eprint`: 1 template fields
- `reusability.integrity`: 5 template fields
- `reusability.additional_licenses`: 5 template fields

## Manual overrides applied from the config (39)

- `discoverability.identification.name`: {'required': True}
- `discoverability.identification.primary_id.type`: {'required': True}
- `discoverability.identification.primary_id.value`: {'required': True}
- `discoverability.contact.person.email`: {'required': True}
- `interoperability.domain_metadata.fields.data_type`: {'type': 'dropdown', 'options': ['float', 'int', 'string', 'boolean', 'datetime', 'other']}
- `accessibility.dataset_scale.record_unit`: {'type': 'dropdown', 'options': ['samples', 'files', 'records', 'timesteps', 'images', 'tokens', 'other']}
- `governed_use.non_sensitivity_governance_metadata.rights_release_records.public_release_status`: {'options': ['Approved', 'Pending', 'Not_Approved', 'Requires_STI_Review', 'not_applicable']}
- `discoverability.dataset_description.tags.project`: {'description': ' Required when tags is provided. Replace default value if necessary with a single human-readable name from the project this dataset belongs to. May be a Genesis project or sub-project, or a non-Genesis project or sub-project. Use the same name in the datacard filename. e.g., genesis | genesis-fusion | genesis-lightsource | nuclear-physics'}
- `accessibility.dataset_scale.record_count`: {'type': 'int'}
- `accessibility.dataset_scale.compressed_bytes`: {'type': 'int'}
- `accessibility.dataset_scale.uncompressed_bytes`: {'type': 'int'}
- `reusability.citation.preferred_citation.year`: {'type': 'int'}
- `reusability.citation.preferred_citation.howpublished`: {'description': ' Required when a preferred_citation is provided. How the dataset was published or released. how_published: is intended as a component of a bibtex citation when preferred_citation is provided e.g., Online | In Repository | As Supplementary Material'}
- `xCard.card_type`: {'value': 'dataset', 'description': 'The xCard type (from the template header: for datasets, the xCard type is "dataset").'}
- `discoverability.datacard.template_version`: {'value': '2.0.0'}
- `discoverability.datacard.datacard_version`: {'value': '1.0.0'}
- `discoverability.datacard.language`: {'value': 'en'}
- `discoverability.datacard.id.type`: {'value': 'unregistered'}
- `discoverability.datacard.created_by.creator.ai_model.role`: {'value': 'Writing_Original_Draft'}
- `discoverability.datacard.created_by.creator.ai_model.relationship`: {'value': 'generates'}
- `discoverability.datacard.created_by.creator.software.role`: {'value': 'Software'}
- `discoverability.datacard.created_by.creator.software.relationship`: {'value': 'processes'}
- `discoverability.identification.project`: {'value': 'genesis'}
- `discoverability.product_type`: {'value': 'Dataset'}
- `supports_discoverability`: {'value': 'Yes'}
- `supports_accessibility`: {'value': 'Yes'}
- `supports_interoperability`: {'value': 'Yes'}
- `supports_reusability`: {'value': 'Yes'}
- `supports_governed_use`: {'value': 'Yes'}
- `supports_ai_usability`: {'value': 'Yes'}
- `interoperability.provenance.processing_steps`: {'required': False}
- `discoverability.sensitivity`: {'description': "Sensitivity of the DATASET and of the DATA CARD: the data card's sensitivity (discoverability.datacard.sensitivity) is filled from these values. NOTE: Sensitivity terminology is still under Genesis governance review. Vocabulary may evolve."}
- `discoverability.datacard.sensitivity.source_marking_string`: {'description_add': {'after': 'If the data is open (public), enter None.'}}
- `discoverability.sensitivity.source_marking_string`: {'description_add': {'after': 'If the data is open (public), enter None.'}}
- `discoverability.datacard.sensitivity.source_marking_scheme`: {'description_add': {'after': 'If the data is open (public), select None.'}}
- `discoverability.sensitivity.source_marking_scheme`: {'description_add': {'after': 'If the data is open (public), select None.'}}
- `discoverability.dataset_description.task_category`: {'description_add': {'before': 'A task category is the kind of AI/ML task the dataset is meant to support, i.e. what a model trained or evaluated on it is asked to do (e.g., classify images, predict a value, detect objects).'}}
- `discoverability.contact.succession_note`: {'description_add': {'after': 'Include both a person and a group (e.g., a team or office) to contact, for clarity.'}}
- `accessibility.access.intended_repositories`: {'description_add': {'after': 'If the project is moving to a DIANA Campaign, leave this empty.'}}

## Hidden fields and mappings (output_format v2: config hidden, map_from) (25)

- `*.organization`: hidden
- `supports_*`: hidden
- `xCard`: hidden
- `discoverability.datacard.template_version`: hidden
- `discoverability.datacard.datacard_version`: hidden
- `discoverability.datacard.filename`: hidden
- `discoverability.datacard.language`: hidden
- `discoverability.datacard.id`: hidden
- `discoverability.datacard.sensitivity`: hidden
- `discoverability.datacard.change_log`: hidden
- `discoverability.datacard.created_by`: hidden
- `discoverability.identification.project`: hidden
- `discoverability.identification.additional_ids`: hidden
- `discoverability.identification.supersedes`: hidden
- `discoverability.identification.superseded_by`: hidden
- `discoverability.identification.parent_collection`: hidden
- `discoverability.dataset_description.task_subcategory`: hidden
- `discoverability.product_type`: hidden
- `discoverability.additional_contacts.valid_until`: hidden
- `interoperability.domain_metadata`: hidden
- `reusability.data_quality`: hidden
- `governed_use.compliance`: hidden
- `governed_use.review_provenance_companion`: hidden
- `discoverability.datacard.sensitivity`: leaves mapped from `discoverability.sensitivity`
- `discoverability.datacard.created_by.creator.person`: leaves mapped from `discoverability.contact.person`
