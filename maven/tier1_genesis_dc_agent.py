from maven.ursa_utils import run_ursa_agent
import pandas as pd
from ursa.agents.chat_agent import ChatAgent


def yaml_card_prompt(datasheet_text: str, datacard_dict: dict, flattened_fields: dict, reference_guide: str, old_datacard_dict: dict | None = None) -> str:

    example_input = '''
        {
            "Field_A": {
                        "description": "this field is used for ....",
                        "visible": true,
                        "value": {
                            "field_B": {
                                "description": "this field is used for ....",
                                "visible": true,
                                "value": {
                                    "field_C": {
                                        "description": "this field is used for ....",
                                        "visible": true,
                                        "required": false,
                                        "mapping": null
                                        "type": string
                                        "options": null
                                        "length": null
                                        "required": false
                                        "value": ''
                                    },
                                    "field_D": {
                                        "description": "this field is used for ....",
                                        "visible": false,
                                        "required": false,
                                        "mapping": null
                                        "type": string
                                        "options": null
                                        "length": null
                                        "required": false
                                        "value": ''
                                    }
                                }
                            },
                            "field_E": {
                                "description": "this field is used for ....",
                                "visible": true,
                                "required": false,
                                "mapping": null
                                "type": int
                                "options": null
                                "length": null
                                "required": false
                                "value": ''
                            },
                            .....
                        }
                    },
            "Field_F": {
                "description": "this field is used for ....",
                "visible": false,
                "required": false,
                "mapping": null
                "type": int
                "options": null
                "length": null
                "required": false
                "value": ''
            }
        }
        '''

    example_output = '''
    {
        "Field_A.field_B.field_C": "extracted_for_field_C",
        "Field_A.field_B.field_D": "",
        "Field_A.field_E": number_value_for_field_E,
        "Field_F": "",
    }
    '''

    if old_datacard_dict is None:
        old_datacard_dict = {}
    if old_datacard_dict:
        input_datacard_string = f'''
        ### **OLD_DATACARD_CONTEXT** (previous datacard version)
        {old_datacard_dict}
        '''

        input_context_string = f'''
        **OLD_DATACARD_CONTEXT** is a dict of fields and values from a previous datacard version. 
        These values can be useful if the field keys match the keys in **FLATTENED_FIELDS_INPUT**
        '''

    prompt = f'''
        You are an expert agent designed to extract technical information about a dataset and complete associated fields with precise, structured entries.
        The input context string is essentially a table of relevant dataset information with additional intermediate meta logs from previous URSA output.
        The additional yaml input and context dictionary contains all fields that need to be completed with description and if they are required.
        
        # INPUTS
        ### **CONTEXT_INFORMATION** (from previous URSA output)
        {datasheet_text}

        {input_datacard_string if old_datacard_dict else ""}

        ## **YAML_INPUT_WITH_CONTEXT**
        {datacard_dict}

        ### **REFERENCE_GUIDE**
        {reference_guide}

        ## **FLATTENED_FIELDS_INPUT**
        {flattened_fields}

        # INPUT INFORMATION:
        **CONTEXT_INFORMATION** is a string of dataset info in a tabular format.

        **YAML_INPUT_WITH_CONTEXT** is a nested dict of all YAML fields in a machine readable format. All fields have a description, visible, and value sub-fields. 
        Only leaf nodes (the most nested fields who actually have a scalar or list value) have additional sub-fields such as mapping, type, options, length, and required.
        The parent fields (non-leaf nodes) can be identified by their value sub-field being a dict -- indicating a child node. 

        **REFERENCE_GUIDE** is a large string with detailed descriptions of each field and provides more context on the YAML structure.

        **FLATTENED_FIELDS_INPUT** is a dict of all leaf-node fields from **YAML_INPUT_WITH_CONTEXT**. 
        Each leaf node's value is a nested dict with 2 keys: required and visible.
        Each of their respective value is a bool of true/false. Ex: fieldA: {{required: true, visible: false}}

        {input_context_string if old_datacard_dict else ""}

        # TASK
        Complete values for all YAML leaf-node fields from **YAML_INPUT_WITH_CONTEXT** with precise, structured answers. 
        Only generate the value for leaf-node fields whose sub-field 'visible'=True. DO NOT generate value for fields whose sub-field 'visible'=False.

        Use the **CONTEXT_INFORMATION** {"and **OLD_DATACARD_CONTEXT**" if old_datacard_dict else ""} as dataset info context. 
        Use **REFERENCE_GUIDE** and each field's 'description' sub-field for more information about that field.

        # INSTRUCTIONS:
        - For each key in **YAML_INPUT_WITH_CONTEXT** whose value is not a nested dictionary (leaf node field), extract info to complete its value.
        - Use a key's "description" sub-field as reference for what information must be extracted. Many fields have more description in the **REFERENCE_GUIDE**
        - If a key's 'visible' sub-field is set to false, DO NOT generate an answer for its value. Just leave that field's value empty in the output JSON.
        - **REFERENCE_GUIDE takes precedence** for understanding conditional requirements and "one-of" relationships.
        - Extract the **most specific yet complete value** present using the **CONTEXT_INFORMATION** {"and **OLD_DATACARD_CONTEXT**" if old_datacard_dict else ""} 
          with only necessary info and be concise.
        - At minimum, extract values for all fields that whose `required` sub-field is True.
        - **REMEMBER:** None, NA, and Not provided mean different things:

            --`None` implies that no entries are present for the field (usually specified in the text);
            --`Not provided` implies that the entry for this field probably exists but is not provided in the given text;
            --`NA` implies the field itself is not applicable in the context of the particular dataset.
        - **DO NOT HALLUCINATE**. ONLY fill in values that are present in the context. If no matching value, leave that field value empty.
        - Return your output in **structured JSON** described below.
        - **DO NOT** include ANY verbose commentary, explanations, or text not corresponding to a field value.
        - Strictly follow one standard in terms of capitalization or choices for a categorical variable or value. DO NOT change structure of a key's name.
        - If the sub-field type=dropdown for a leaf-node key in **YAML_INPUT_WITH_CONTEXT**, its generated value MUST come from the list in the sub-field 'options'.
          'options' is the list of valid answers for that key. 
          If 'options' is not null, ensure that the completed/filled-in value for the key is one of the choices in the list.
          If the value for that key cannot be filled in, select No/None/Unknown/Other/Not_applicable, or a choice from the options list that best matches an empty value.

        # CRITICAL NOTES:
        - EACH ANSWER MUST BE UNIQUE: Every field should have a distinct answer tailored to that question.
          If multiple questions relate to similar themes, rephrase and focus each answer appropriately.
        
        # Example Input (JSON)
        - Example note: field_A.field_B.field_D has visible=False, so its value in the final output JSON should be empty.
        {example_input}

        OUTPUT FORMAT:
        Output should be a valid JSON that has ALL THE EXACT keys in **FLATTENED_FIELDS_INPUT**. 
        IF A FIELD DOES NOT HAVE AN EXTRACTED VALUE OR HAS VISIBLE=FALSE in **FLATTENED_FIELDS_INPUT** IT SHOULD STILL BE A KEY IN THE OUTPUT JSON.
        Keys/leaf nodes who have an extracted info (only if visible=True) should have a filled value. Otherwise, the value should be an empty string.

        NOTE: For leaf node fields with extracted values, ensure the generated value's python type matches that field's 'type' sub-field. 
        
        - If type=string, the value MUST be a string. 
        - If type=dropdown, the value MUST be a string. NOT a list. ONLY ONE CHOICE from the 'options' sub-field list should be the value.
          Ex: if field_G is type=dropdown and options=["hello", "world", "okay"] the value can be "hello". NOT ["hello", world"]. NOT ["hello"]
        - If type=int, the value should be a number. 
        - If type=list, the value should be a list of strings where the list length CANNOT exceed the number in sub-field 'length'.
          ex: if field_G is type=list and length=3 and info could be extracted to fill it in, the list MUST NOT be longer than 3 elements. 

        For all nested keys, the keys in this JSON should use dot notation to represent the actual structure. 
        That is how **FLATTENED_FIELDS_INPUT** is structured.
        Ex: if field_C is under field_B which is under field_A, field_C in the JSON will be "field_A.field_B.field_C" : value_for_field_C

        Each key should be in dot notation format with the value a representation of the extracted info. If no value, then should be empty string.

        ### Example Output (JSON):
        {example_output}
        '''
    return prompt


def run_tier1_yaml(chat_agent: ChatAgent,
                   datasheet: pd.DataFrame, 
                   datacard_dict: dict[str, dict[str, str]],
                   reference_guide: str,
                   flattened_fields: dict,
                   old_datacard_dict: dict | None = None) -> dict[str, str]:

    datasheet_string = datasheet.to_string(index=False)

    #only keep required and visible keys for each field's dict
    flattened_fields_no_value = {
        field_name: {
            key: value
            for key, value in field_config.items()
            if key in ["required", "visible"]
        }
        for field_name, field_config in flattened_fields.items()
    }

    yaml_prompt = yaml_card_prompt(datasheet_string, datacard_dict, flattened_fields_no_value, reference_guide, old_datacard_dict)
    yaml_payload = run_ursa_agent(chat_agent, yaml_prompt)

    return yaml_payload