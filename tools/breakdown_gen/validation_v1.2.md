# Breakdown validation

- Template: `../../maven/metadata_template/genesis_dc_v1.2_YAML.yaml`
- Breakdown: `genesis_dc_v1.2_breakdown.generated.yaml`

| Section | Template keys | Breakdown fields | Errors | Warnings | Expected |
|---|---|---|---|---|---|
| intended capabilities (supports_*) | 6 | 6 | 0 | 0 | 0 |
| discoverability | 170 | 170 | 0 | 0 | 0 |
| accessibility | 29 | 29 | 0 | 0 | 0 |
| interoperability | 64 | 64 | 0 | 0 | 0 |
| reusability | 50 | 50 | 0 | 0 | 0 |
| governed_use | 48 | 48 | 0 | 0 | 0 |
| ai_usability | 12 | 12 | 0 | 0 | 0 |
| _repository | 24 | 0 | 0 | 0 | 24 |

## ERROR (0)


## WARNING (0)


## EXPECTED (24)

- `_repository`: not in breakdown: [reference_only] block (_repository)
- `_repository.populated_by_repository`: not in breakdown: [reference_only] block (_repository.populated_by_repository)
- `_repository.ingest_date`: not in breakdown: [reference_only] block (_repository.ingest_date)
- `_repository.repository_catalog_id`: not in breakdown: [reference_only] block (_repository.repository_catalog_id)
- `_repository.completeness_score`: not in breakdown: [reference_only] block (_repository.completeness_score)
- `_repository.datacard_checksum`: not in breakdown: [reference_only] block (_repository.datacard_checksum)
- `_repository.datacard_checksum.type`: not in breakdown: [reference_only] block (_repository.datacard_checksum.type)
- `_repository.datacard_checksum.value`: not in breakdown: [reference_only] block (_repository.datacard_checksum.value)
- `_repository.repositories`: not in breakdown: [reference_only] block (_repository.repositories)
- `_repository.repositories.name`: not in breakdown: [reference_only] block (_repository.repositories.name)
- `_repository.repositories.identifier`: not in breakdown: [reference_only] block (_repository.repositories)
- `_repository.repositories.identifier.type`: not in breakdown: [reference_only] block (_repository.repositories.identifier.type)
- `_repository.repositories.identifier.value`: not in breakdown: [reference_only] block (_repository.repositories.identifier.value)
- `_repository.repositories.dataset_landing_page`: not in breakdown: [reference_only] block (_repository.repositories.dataset_landing_page)
- `_repository.repositories.dataset_download_url`: not in breakdown: [reference_only] block (_repository.repositories.dataset_download_url)
- `_repository.repositories.dataset_id_in_repo`: not in breakdown: [reference_only] block (_repository.repositories.dataset_id_in_repo)
- `_repository.repositories.access_protocol`: not in breakdown: [reference_only] block (_repository.repositories.access_protocol)
- `_repository.usage_metrics`: not in breakdown: [reference_only] block (_repository.usage_metrics)
- `_repository.usage_metrics.download_count`: not in breakdown: [reference_only] block (_repository.usage_metrics)
- `_repository.usage_metrics.view_count`: not in breakdown: [reference_only] block (_repository.usage_metrics)
- `_repository.usage_metrics.citation_count`: not in breakdown: [reference_only] block (_repository.usage_metrics)
- `_repository.usage_metrics.last_accessed`: not in breakdown: [reference_only] block (_repository.usage_metrics)
- `_repository.distributions`: not in breakdown: [reference_only] block (_repository.distributions)
- `_repository.data_services`: not in breakdown: [reference_only] block (_repository.data_services)
