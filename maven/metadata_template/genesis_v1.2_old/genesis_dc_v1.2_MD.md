### Instructions  
<INSTRUCTIONS: Provide relevant information regarding your dataset in this file.  The information can be a combination of values in YAML sections and text blocks in the markdown section.  For the markdown text, replace all Examples, and [!TODO], and REPLACE: ... placeholder tags with the appropriate information for your dataset. Be sure to remove the header TODO and INSTRUCTION tags once you have completed the data card.  In each section you can complete YAML values as available.  Required fields are marked.>  
  
<INSTRUCTIONS: Considerations for filling out the data card: Deciding the appropriate resolution for documenting a scientific dataset in a data card can be complex. Data cards may describe single or multiple data files, datasets, or versions. Too granular, and there will be too many data cards; too broad, and details may be lost. Consider the use, audience, and documentation the data card needs to provide to maintain transparency without duplication. Reflect on these relationships to balance clarity, usability, and sustainability.>
  
<INSTRUCTIONS: The sections and questions in the markdown section of this data card template are meant to be a guide for the types of information that should be included in a data card. You can choose to answer all, some, or additional questions as appropriate for your dataset. The goal is to provide enough information for users (humans and machines) to understand the dataset and its context, but you can use your judgment to determine what information is most relevant and important to include.>  
  
<INSTRUCTIONS: Structure of the Markdown Section: Data readiness in a shared environment can be generally sorted into six high-level categories:
* Discoverable: The dataset is described with sufficient metadata to be found and understood by potential users. This is the REQUIRED minimum for any dataset to be shared.
* Accessible: The dataset is available for access, with clear instructions and any necessary permissions or agreements in place.
* Interoperable: The dataset is in a format and structure that can be easily used and integrated with other datasets and tools, with clear documentation of its schema and semantics.
* Reusable: The dataset is of sufficient quality, with clear licensing and provenance information, to be confidently reused by others for various purposes.
* Governed Use: The dataset has defined use governance, compliance information, and review history to ensure responsible use and manage risks.
* AI Usable: The dataset is suitable for use in AI and ML workflows, with clear, explicit information about AI usage.
These categories describe usability, interoperability, and governance characteristics.  They do NOT represent dataset quality, scientific merit, or value ranking.  
Prompts for data are generally organized into sections that support these efforts.  Some fields are required to be considered for use at each level and for making datasets available to tools targeting each level.  Requirements are labelled for each level.  
>  
  
<INSTRUCTIONS: metadata_key: [KEY_NAME] tags indicate that the information for the markdown section can be found in the corresponding key in the YAML metadata at the top of this file, and is for use in the human and the automated bi-directional generation from YAML-to-markdown, or markdown-to-YAML. You can choose to manually copy, or you can leave the placeholders and use an automation tool (such as an LLM) to populate the sections. If you choose to automatically populate the markdown sections from the YAML metadata, make sure to replace metadata_key: [KEY_NAME] tags in each relevant markdown section before sharing the data card, and note the LLM or AI agent used in the data card.creation_method section of the YAML frontmatter metadata.>
  
  
# Datacard for ${DATASET_NAME}  

**Last Updated**: [!TODO]<REPLACE: YYYY-MM-DD>  

### Machine Usability Snapshot  
  
| Intended Capability | DataCard Support |  
| ------ | ------ |  
| Discoverability| Yes/No |
| Accessibility| Yes/No |
| Interoperability| Yes/No |  
| Reusability| Yes/No | 
| Governed Use | Yes/No |  
| AI Usability| Yes/No |  
| License Clarity | Yes/No | 
| Checksum / Fixity | Yes/No |  
| Semantic Context | Yes/No |
  
  
# ---- Discoverable ----  

## Description

### Dataset Description [discoverability_required]  
[!TODO] <REPLACE: Provide a concise description of the dataset, including its purpose, scope, and context.><metadata_key: discoverability.dataset_description.dataset_summary>

### Domain and Purpose [discoverability_if_applicable]
[!TODO] <REPLACE: Describe the domain and the key research areas involved in collecting the dataset. Can list below> <metadata_key: discoverability.dataset_description.purpose><metadata_key: discoverability.dataset_description.science_domain><metadata_key: interoperability.domain_metadata.science_domain>

## Keywords [discoverability_required]  
[!TODO] <REPLACE: Provide a comma-separated list of keywords that describe the dataset and can help with discoverability.><metadata_key: discoverability.dataset_description.keywords>

## Sensitivity [discoverability_required]

### Security / Marking Considerations [discoverability_required]
[!TODO]<Describe classification, CUI marking, distribution limitations, and handling requirements.>
<metadata_key: discoverability.sensitivity.overall_sensitivity><metadata_key: discoverability.sensitivity.classified_status><metadata_key: discoverability.sensitivity.cui_status><metadata_key: discoverability.sensitivity.ucni_status>

## Context and Provenance [discoverability_required]

### Resources used, including funding and facilities, to create the dataset  
[!TODO] <REPLACE: Provide a list of the resources used to create the dataset, including funding sources, facilities, computing resources, and any other relevant resources. Facilities can include user facilities, national laboratories, research institutions, and other organizations that provided access to equipment, data, or expertise. Funding sources can include government agencies, private foundations, industry partners, and other organizations that provided financial support for the dataset creation. Computing resources can include high-performance computing clusters, cloud computing platforms, and other computational resources used for data processing and analysis. Include [ROR ID](https://ror.org/), grant numbers, contract numbers, or other identifiers as appropriate. Can list below><metadata_key: discoverability.sponsor_organizations><metadata_key: discoverability.sponsoring_doe_program_office><metadata_key: discoverability.sponsoring_doe_subprogram><metadata_key: discoverability.research_organizations><metadata_key: discoverability.facilities>

### Developed by [discoverability_required]
[!TODO] <REPLACE: A person or group that was primarily responsible for the creation and design of the dataset. It suggests a leading role, such as a Principal Investigator, in the development of the dataset. If available, provide the Name, [ORCID](https://orcid.org/), affiliation ([ROR ID](https://ror.org/)) and email address of the person or group responsible for the dataset.><metadata_key: discoverability.authors>

### Contributed by  [discoverability_if_applicable]
[!TODO] <REPLACE: Person, or group that provided input or support to the datasets development but may not have been the primary creators. Contributions can include sample collection, processing, analysis, documentation, and-or submission of the dataset. This suggests collaboration, where multiple parties might have played various roles in the dataset development. Can list below> <metadata_key: discoverability.contributors>

## Methods  [discoverability_if_applicable]
  
### Dataset generation, collection, and procedures  [discoverability_if_applicable] [interoperability_required]
[!TODO] <REPLACE: Describe how the dataset was generated or collected. For example, raw experimental measurements from user facilities, processed, physics-ready experimental data, outputs from computational simulations, or data derived from prior datasets? For each instrument, facility, or source used to generate and collect the data, what mechanisms or procedures were used for the data collection? If the data was derived, list and describe the source(s) and describe how they were used.>  <metadata_key: discoverability.dataset_description.collection_methodology><metadata_key: interoperability.provenance.processing_steps><metadata_key: interoperability.provenance.instrumentation><metadata_key: interoperability.provenance.simulation_details>

---  

# ---- Accessible ----  

## Sharing & Access  [accessibility_required]
[!TODO] <REPLACE:  Describe the sharing methods and any contact information for access. If applicable, include a legal rights statement, separate from or in addition to the license.><metadata_key: accessibility.access><metadata_key: accessibility.access_policy>  

---  

# ---- Interoperable ----  

## Data Structure

### Files & Structure  [interoperability_required]
[!TODO] <REPLACE: Summarize dataset organization, formats, and relationships between files.><metadata_key: discoverability.dataset_description.data_characteristics><metadata_key: accessibility.dataset_scale>

### Specialized formats or other abbreviations used  [interoperability_if_applicable]
[!TODO] <REPLACE: Describe any specialized data formats, abbreviations, or conventions used in the dataset or file. For example, if the dataset is in a specific file format (e.g., ROOT, HDDM, HDF5), or if there are any domain-specific abbreviations used in variable names or values.><metadata_key: interoperability.data_structure.formats>

## Related Resources [interoperability_if_applicable]
  
### Related datasets, standards, metadata, and ontologies [interoperability_if_applicable]
[!TODO] <REPLACE: If the dataset is related to or derived from other datasets, standards, metadata and ontologies, please list those datasets and describe the relationship. For example, This dataset was derived from [DATASET NAME] (DOI: [DATASET DOI]) by applying [TRANSFORMATION OR PROCESS].><metadata_key: interoperability.related_resources.datasets><metadata_key: interoperability.domain_metadata><metadata_key: interoperability.semantic_layer.schema_url><metadata_key: interoperability.semantic_layer.semantic_context>
  
### Related publications [interoperability_if_applicable]
[!TODO] <REPLACE: List any publications that are associated with the dataset, including DOIs, arXiv IDs, or URLs.><metadata_key: interoperability.related_resources.publications>
  
### Related software [interoperability_if_applicable]
[!TODO] <REPLACE: List any software that is associated with the dataset, including links or PIDs if available.><metadata_key: interoperability.related_resources.software>

### Related ai model [interoperability_if_applicable]
[!TODO] <REPLACE: List any AI models that are associated with the dataset, including links or PIDs if available.><metadata_key: interoperability.related_resources.ai_models>

## Understanding the Data [interoperability_required]

### List of variable name(s), description(s), unit(s), and value labels for each variable in the dataset/file.  [interoperability_required]
[!TODO] <REPLACE: If appropriate, replace the example table with a table listing each variable in the dataset or file, along with its description, unit, and any value labels if applicable.><metadata_key: interoperability.data_structure.features>
  
For example:  
| Variable Name | Description  | Unit  | Value Labels  |  
|---------------|---------------------------|-----------|-----------------------------|  
| temp  | Temperature measurement  | Celsius  | N/A  |  
| status  | Operational status  | N/A  | 0 = Off, 1 = On  |  

### Related Schemas or Ontologies [interoperability_if_applicable]
[!TODO] <REPLACE: list any relevant schemas, ontologies, or vocabularies.><metadata_key: interoperability.semantic_layer.schema_url><metadata_key: interoperability.semantic_layer.semantic_context>

### Codes used for missing data [interoperability_if_applicable] [reusability_if_applicable]
[!TODO] <REPLACE: Replace the example table of codes used to represent missing data in the dataset or file.><metadata_key: reusability.data_quality.missing_data_codes>
  
For example:  
| Code | Description  |  
|------|---------------------------|  
| -999 | Data not collected  |  
| -888 | Measurement error  |  


### Example of the contents  [interoperability_if_applicable]
[!TODO] <REPLACE: Optional. Provide a sample of the dataset or file, or a citation (in bibtex format) or link to where one can review an example of the contents. This can help users understand the structure and content of the dataset.>  

### Data Processing  [interoperability_required]
[!TODO] <REPLACE: Describe preprocessing, calibration, filtering, labeling, or transformations applied to the dataset.><metadata_key: interoperability.provenance.processing_steps>

### Software used to preprocess/ clean/ label the data  [interoperability_if_applicable]
[!TODO] <REPLACE: If the software used to preprocess, clean, or label the data is available, please provide a bibtex format, PID, link, or other access point, along with descriptions of any required packages or libraries to run the scripts.><metadata_key: interoperability.provenance.was_generated_by><metadata_key: interoperability.provenance.software_environment>

## Semantic / Schema Information  [interoperability_if_applicable]
[!TODO] <REPLACE: Describe schema, ontology alignment, semantic context, and controlled vocabularies. If no formal schema or ontology exists, this section may remain empty.  Examples may include:  JSON Schema or XML schema, NETCDF CF conventions, data dictionary or feature definitions, domain  ontologies like ENVO, controlled vocabularies, or units standards. For example:  schema_URL: "https://example.org/schema.json" or ontology_alignment: "http://purl.obolibrary.org/obo/ENVO_00002005"><metadata_key: interoperability.domain_metadata>

---  

# ---- Reusable ----  

## Citation  [reusability_if_applicable]
[!TODO] <REPLACE: Provide a recommended citation if known. Recommend bibtex format.><metadata_key: reusability.citation.preferred_citation>

## License and Usage Rights  [reusability_if_applicable]
[!TODO] <REPLACE: Describe the license under which the dataset is shared, and any usage and contractual rights or restrictions. If no formal license, describe specific permissions for reuse.><metadata_key: reusability.license.spdx_id><metadata_key: reusability.license.license_name> <metadata_key: reusability.license.license_url><metadata_key: reusability.additional_licenses>

## Maintenance & Updates  [reusability_if_applicable]
[!TODO] <REPLACE: Describe update expectations and stewardship responsibility.><metadata_key: reusability.stewardship.maintainer><metadata_key: reusability.stewardship.level><metadata_key: reusability.stewardship.update_frequency><metadata_key: reusability.stewardship.retention_policy>
<metadata_key: reusability.stewardship.versioning_strategy>

## Data Characteristics  [reusability_required] [interoperability_if_applicable]
[!TODO] <REPLACE: Describe variables or features, schema conventions, and missing data handling.><metadata_key: interoperability.data_structure.features><metadata_key: interoperability.data_structure.splits><metadata_key: interoperability.data_structure.spatial_coverage><metadata_key: interoperability.data_structure.temporal_coverage><metadata_key: interoperability.data_structure.modalities>
  
## Data Quality & Limitations  [reusability_required]
[!TODO] <REPLACE: Describe completeness, known issues, uncertainties, noise characteristics, and bias considerations.><metadata_key: reusability.data_quality.completeness><metadata_key: reusability.data_quality.known_issues><metadata_key: reusability.data_quality.validation_methods><metadata_key: reusability.data_quality.noise_characteristics><metadata_key: reusability.data_quality.uncertainty_notes><metadata_key: discoverability.dataset_description.limitations>

## Integrity & Versioning  [reusability_if_applicable]
[!TODO] <REPLACE: Describe checksum availability, fixity strategy, and dataset versioning approach.><metadata_key: reusability.integrity.checksum_available><metadata_key: reusability.integrity.checksum_type><metadata_key: reusability.integrity.checksum_value><metadata_key: reusability.integrity.fixity_policy><metadata_key: reusability.stewardship.versioning_strategy>

---  

# ---- Governed Use ----  

## Access and Permissions  [governed_use_required]
[!TODO] <REPLACE: Describe the dataset`s access posture and any high-level agreements or review constraints.><metadata_key: governed_use.non_sensitivity_governance_metadata.export_control.export_control_status><metadata_key: governed_use.non_sensitivity_governance_metadata.privacy.privacy_status><metadata_key: governed_use.non_sensitivity_governance_metadata.privacy.pii_status><metadata_key: governed_use.non_sensitivity_governance_metadata.privacy.phi_status><metadata_key: governed_use.non_sensitivity_governance_metadata.privacy.privacy_regime_notes><metadata_key: governed_use.compliance.doe_data_management_plan><metadata_key: governed_use.compliance.irb_approved>

## Access conditions   [governed_use_required]
[!TODO] <REPLACE: Describe any conditions that must be met to access the dataset, such as training requirements, proposal processes, collaboration requirements, data use agreements, etc.><metadata_key: governed_use.non_sensitivity_governance_metadata.rights_release_records.ip_restriction_type><metadata_key: governed_use.non_sensitivity_governance_metadata.rights_release_records.agreement_required><metadata_key: governed_use.non_sensitivity_governance_metadata.rights_release_records.agreement_type><metadata_key: governed_use.non_sensitivity_governance_metadata.rights_release_records.public_release_status><metadata_key: governed_use.non_sensitivity_governance_metadata.rights_release_records.record_status>

## Review Provenance [governed_use_if_applicable]

### Release review process  [governed_use_if_applicable]
[!TODO] <REPLACE: Describe the release review process for the dataset, including any institutional reviews, export control reviews, IRB reviews, or other review processes that were conducted before the dataset was released.><metadata_key: governed_use.review_provenance_companion> 

---  

# ---- AI Usable ----  

## AI / Machine Learning Considerations  [ai_usability_required]
[!TODO] <REPLACE: Describe appropriate AI/ML uses, restrictions, bias risks, and safety considerations.><metadata_key: ai_usability.ai_usage.training_use_allowed><metadata_key: ai_usability.ai_usage.inference_use_allowed><metadata_key: ai_usability.ai_usage.evaluation_use_allowed><metadata_key: ai_usability.ai_usage.restrictions><metadata_key: ai_usability.ai_usage.bias_risks><metadata_key: ai_usability.ai_usage.safety_considerations><metadata_key: ai_usability.ai_usage.human_review_required>
  
---  

# Additional Information  
[!TODO] <REPLACE: Optional. Include any relevant contextual notes.>  