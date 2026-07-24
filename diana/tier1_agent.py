from diana.ursa_utils import run_ursa_agent
import pandas as pd
from typing import Tuple


def create_tier1_prompt(metadata_info: dict[str, str], datasheet_text: str, all_classes_dict: dict[str, dict[str, str]]) -> str:
    """Use the LLM to retrieve relevant information from the datashee to fill out all tier 1 metadata fields."""
    if not datasheet_text:
        return ""

    example_output = '''
    {
        "AffiliationClass": {
                    "name": "Bragg Cohorent Diffraction Imaging (BCDI)",
                    "ror_id": "23",
                    ....
                }
    }
    {
        "PersonClass": {
                    "given_name": "John",
                    "family_name": "Doe",
                    "orcid: "00001",
                    "email": "john_doe@gmail.com",
                    ....
                }
    }
    '''

    prompt = f'''
        
        You are an expert agent designed to extract technical information about a dataset and complete associated fields with precise, structured entries.
        The input context text string is essentially a table of relevant dataset information and some additional intermediate meta logs from a previous agent.

        # TASK:
        Extract the metadata fields precisely and accurately for each table in the scientific data described in the text. provided in json format, given the following:
        1. **all_tables_dict** - a nested dictionary:
            - each outer key is a name of a table
            - each inner key are the field names in the table that contain `desription` string describing the column and `required` bool if it is a required field.
        2. **text** — a string containing relevant information to be extracted. The previous agent's logs can be found in `agent_meta` and `user_clarifications`.

        # INSTRUCTIONS:
        - For each table in **all_tables_dict**, extract a value for each field. Each field's description can be found in **metadata_info**. 
          Extract the **most specific yet complete value** present based on the text.
        - Do not extract unnecessary phrases, keep the fields as concise as possible.
        - At minimum, extract values for all fields that are in each table with a `required` True bool.
        - **REMEMBER:** None, NA, and Not provided mean different things:
            --`None` implies that no entries are present for the field (usually specified in the text);
            --`Not provided` implies that the entry for this field probably exists but is not provided in the given text;
            --`NA` implies the field itself is not applicable in the context of the particular dataset.
        - **DO NOT HALLUCINATE**. Return only values that are present in the text. If no matching value, leave that column/field value empty.
        - Return your output in **structured JSON** described below.
        - **DO NOT** include ANY verbose commentary, explanations, or text not corresponding to a field value.
        - Strictly follow one standard in terms of capitalization or choices for a categorical variable or value.
        

        # CRITICAL NOTES:
        1. EACH ANSWER MUST BE UNIQUE: Every field should have a distinct answer tailored to that question.
        If multiple questions relate to similar themes, rephrase and focus each answer appropriately.

        # INPUT:
 
        ### All tables dictionary. Each outer key is a table name. Each value is a dictionary with inner keys as field names with descriptions & required bool
        {all_classes_dict}

        ### Contextual Text:
        {datasheet_text}


        OUTPUT:
        JSON with table names from **all_tables_dict** as highest level keys. 
        Each value should be a nested dictionary whose keys are all the field names defined from the description and required inputs.
        - DO NOT return empty dictionary for any table
        
        ### Example Output (JSON):
        {example_output}
        '''
    
    return prompt


def run_tier1_catalog(diana_dir: str, 
                      datasheet: pd.DataFrame, 
                      metadata_fields_dict: dict[str, str], 
                      all_classes_dict: dict[str, dict[str, str]]) -> dict[str, dict[str, str]]:

    datasheet_string = datasheet.to_string(index=False)
    tier1_prompt = create_tier1_prompt(metadata_fields_dict, datasheet_string, all_classes_dict)

    payload = run_ursa_agent(diana_dir, tier1_prompt)
    # print(payload)
    return payload