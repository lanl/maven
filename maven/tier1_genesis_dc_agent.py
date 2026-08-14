from maven.ursa_utils import run_ursa_agent
import pandas as pd
from ursa.agents.chat_agent import ChatAgent


def yaml_card_prompt(datasheet_text: str, 
                        datacard_dict: dict,
                        flattened_fields: dict,
                        reference_guide: str
                    ) -> str:

    example_input = '''
        {
            "Field_A": {
                        "required": true,
                        "description": "this field is used for ....",
                        "value": {
                            "field_B": {
                                "required": true,
                                "description": "this field is used for ....",
                                "value": {
                                    "field_C": {
                                        "required": false,
                                        "description": "this field is used for ....",
                                        "value: "C_Placeholder"
                                    }
                                }
                            },
                            "field_D": {
                                "required": true,
                                "description": "this field is used for ....",
                                "value: "D_Placeholder"
                            },
                            .....
                        }
                    },
            "Field_E": {
                "required": true,
                "description": "this field is used for ....",
                "value: "E_Placeholder"
            }
        }
        '''
    
    example_output = '''
    {
        "Field_A.field_B.field_C": "extracted_for_field_C",
        "Field_A.field_D": "extracted_for_field_D",
        "Field_E": "extracted_for_field_E",
    }
    '''

    prompt = f'''
        You are an expert agent designed to extract technical information about a dataset and complete associated fields with precise, structured entries.
        The input context string is essentially a table of relevant dataset information with additional intermediate meta logs from previous URSA output.
        The additional yaml input and context dictionary contains all fields that need to be completed with description and if they are required.
        
        # Inputs
        ### **CONTEXT_INFORMATION** (from previous URSA output)
        {datasheet_text}

        ## **YAML_INPUT_WITH_CONTEXT**
        {datacard_dict}

        ### **REFERENCE_GUIDE**
        {reference_guide}

        ## **FLATTENED_FIELDS_OUTPUT**
        {flattened_fields}

        # TASK:
        Complete metadata fields with precise, structured entries that follow the output format in **FLATTENED_FIELDS_OUTPUT** using the dataset info 
        in **CONTEXT_INFORMATION**, **YAML_INPUT_WITH_CONTEXT** (which contains all YAML fields and a short description for each), and the detailed 
        reference guide described in **REFERENCE_GUIDE**

        # INSTRUCTIONS:
        - For each key in **YAML_INPUT_WITH_CONTEXT** whose value is not a nested dictionary, extract info to complete its value.
          Pre-existing text for a key's value is only a placeholder, and must be overwritten with an extracted value, even if that extracted value is empty.
        - Use a key's "description" field as reference for what information must be extracted. Many fields have more description in the **REFERENCE_GUIDE**
        - **REFERENCE_GUIDE takes precedence** for understanding conditional requirements and "one-of" relationships.
        - Extract the **most specific yet complete value** present using the **CONTEXT_INFORMATION** with only necessary info and concise.
        - At minimum, extract values for all fields that that have a `required` field which is True.

        # HANDLING CONDITIONAL REQUIREMENTS (CRITICAL):
        - When a field has `conditional_context: "one_of_alternatives"`, this means it's part of a mutually exclusive choice.
        - The `condition_discriminator` field (e.g., "type", "agent_type") determines which alternative to use.
        - **Process these fields as follows:**
          1. First, determine the value of the discriminator field from CONTEXT_INFORMATION
          2. Consult the REFERENCE_GUIDE for guidance on which alternative matches that discriminator value
          3. Populate ONLY the matching alternative block (e.g., if type="person", populate person block only)
          4. Within the selected alternative, treat all `required: true` fields as REQUIRED
          5. Completely ignore and leave empty all other alternative blocks
        - **Example:** If authors.type = "person", then:
          - Populate authors.person.given_name (required: true means required in this context)
          - Leave authors.organization completely empty (it's the non-selected alternative)

        - **REMEMBER:** None, NA, and Not provided mean different things:
            --`None` implies that no entries are present for the field (usually specified in the text);
            --`Not provided` implies that the entry for this field probably exists but is not provided in the given text;
            --`NA` implies the field itself is not applicable in the context of the particular dataset.
        - **DO NOT HALLUCINATE**. Return only values that are present in the text. If no matching value, leave that column/field value empty.
        - Return your output in **structured JSON** described below.
        - **DO NOT** include ANY verbose commentary, explanations, or text not corresponding to a field value.
        - Strictly follow one standard in terms of capitalization or choices for a categorical variable or value. DO NOT change structure of a key's name.
        - Certain keys in **YAML_INPUT_WITH_CONTEXT** have additional keys in its nested dictionary, type (either radio or dropdown) and options (a list of valid answers for that key).
          If options is present, then ensure that the completed/filled-in value for the key is one of the choices in the list.
          If the value for that key cannot be filled in, select No/None/Unknown/Other/Not_applicable, or a choice from the options list that best matches an empty value.

        # CRITICAL NOTES:
        - EACH ANSWER MUST BE UNIQUE: Every field should have a distinct answer tailored to that question.
          If multiple questions relate to similar themes, rephrase and focus each answer appropriately.
        
        ### Example Input (JSON):
        {example_input}

        OUTPUT FORMAT:
        Output should be a valid JSON that follows the exact keys that are in **FLATTENED_FIELDS_OUTPUT**. 
        Overwrite the existing values assigned to it with the extracted value. 
        
        For all nested keys, the keys in this JSON should be a dot notation to represent the actual structure. 
        That is how **FLATTENED_FIELDS_OUTPUT** is structured.
        Ex: if field_C is under field_B which is under field_A, field_C in the JSON will be "field_A.field_B.field_C" : value_for_field_C

        Each key should be in dot notation format with the value a string representation of the extracted info. If no value, then should be empty string.

        ### Example Output (JSON):
        {example_output}
        '''
    return prompt


def markdown_card_prompt(datasheet_text: str, markdown_template: str, reference_guide: str) -> str:
    prompt = f'''
        You are an expert agent designed to extract technical information about a dataset. 
        Using previous context about this dataset, complete entries for a markdown template.

        # Inputs
        ### **CONTEXT_INFORMATION** (from previous URSA output)
        {datasheet_text}

        ## **MARKDOWN_TEMPLATE**
        {markdown_template}

        ### **REFERENCE_GUIDE**
        {reference_guide}

        # TASK:
        Complete associated fields with precise, structured entries following the format shown in **MARKDOWN_TEMPLATE** with detailed reference guide 
        described in **REFERENCE_GUIDE** and dataset information in **CONTEXT_INFORMATION**.

        # INSTRUCTIONS:
        - Read the instructions in the top of MARKDOWN_TEMPLATE.
        - The CONTEXT_INFORMATION contains the needed dataset information to parse and complete the MARKDOWN_TEMPLATE.
        - When completing the MARKDOWN_TEMPLATE extract the **most specific yet complete value** present based on the text.
        - Do not extract unnecessary phrases, keep the fields as concise as possible.
        - At minimum, extract values for all fields that are in each table with a `required` True bool.
        - **REMEMBER:** Follow all guidance in REFERENCE_GUIDE
        - **REMEMBER:** None, NA, and Not provided mean different things:
            --`None` implies that no entries are present for the field (usually specified in the text);
            --`Not provided` implies that the entry for this field probably exists but is not provided in the given text;
            --`NA` implies the field itself is not applicable in the context of the particular dataset.
        - **DO NOT HALLUCINATE**. Return only values that are present in the text. If no matching value, then follow the REFERENCE_GUIDE.
        
        # OUTPUT:
        - Return the autocompleted MARKDOWN_TEMPLATE as a string with all **[!TODO] <REPLACE:** replaced with the correct values. 
        - The output string should be a direct copy of MARKDOWN_TEMPLATE that is edited for the [!TODO] <REPLACE: entries.
        - Follow any formatting guidance that is in the description following [!TODO] <REPLACE:
        - Exclude the INSTRUCTIONS sections at the top the MARKDOWN_TEMPLATE.
        - **DO NOT** include ANY verbose commentary, explanations, or text not corresponding to a field value.
        - DO NOT return empty values for the MARKDOWN_TEMPLATE.
    '''
    return prompt


def run_tier1_catalog(chat_agent: ChatAgent,
                      datasheet: pd.DataFrame, 
                      datacard_dict: dict[str, dict[str, str]],
                      tier1_cards: dict[dict[str, str], str],
                      flattened_fields: dict) -> dict[str, dict[str, str]]:

    datasheet_string = datasheet.to_string(index=False)


    yaml_prompt = yaml_card_prompt(datasheet_string, datacard_dict, flattened_fields, tier1_cards["card_reference"])
    yaml_payload = run_ursa_agent(chat_agent, yaml_prompt)
    
    markdown_prompt = markdown_card_prompt(datasheet_string, tier1_cards["markdown_template"], tier1_cards["card_reference"])
    markdown_payload = run_ursa_agent(chat_agent, markdown_prompt, extract_json=False)

    return {"datacard_yaml": yaml_payload, "datacard_markdown": {"markdown_output": markdown_payload}}