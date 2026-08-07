from maven.ursa_utils import run_ursa_agent, assemble_genesis_datacard
import pandas as pd
from typing import Tuple
from ursa.agents.chat_agent import ChatAgent

def create_tier1_prompt(datasheet_text: str, all_classes_dict: dict[str, dict[str, str]]) -> str:
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
        - For each table in **all_tables_dict**, extract a value for each field following the field's description provided. 
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


def genesis_card_prompt(class_payload: dict[str, dict[str, str]], tier1_cards: dict[str, dict[str, str]]) -> str:

    prompt = f'''
        You are an expert agent designed to extract technical information about a dataset.
        
        # Inputs
        ### CONTEXT INFORMATION (from previous URSA output)
        {class_payload}

        ### MARKDOWN TEMPLATE
        {tier1_cards["markdown_template"]}

        ### REFERENCE_GUIDE
        {tier1_cards["card_reference"]}

        # TASK:

        Complete associated fields with precise, structured entries following the format shown in **DATA_CARD_ALL** with detailed reference guide described in **REFERENCE_GUIDE** for the fileds shown in **DATA_CARD_FIELDS**.

        # INSTRUCTIONS:
        - Read the instructions in the top of MARKDOWN TEMPLATE.
        - The CONTEXT INFORMATION contains the needed information to parse and complete the MARKDOWN TEMPLATE.
        - When completing the MARKDOWN TEMPLATE extract the **most specific yet complete value** present based on the text.
        - Do not extract unnecessary phrases, keep the fields as concise as possible.
        - At minimum, extract values for all fields that are in each table with a `required` True bool.
        - **REMEMBER:** Foolow all guidance in REFERENCE_GUIDE
        - **DO NOT HALLUCINATE**. Return only values that are present in the text. If no matching value, then follow the REFERENCE_GUIDE.
        
        # OUTPUT:
        - Return the autocompleted MARKDOWN TEMPLATE as a string with all **[!TODO] <REPLACE:** replaced with the correct values. 
        - The output string should be a direct copy of MARKDOWN TEMPLATE that is editted for the [!TODO] <REPLACE: entries.
        - Follow any formatting guidance that is in the description following [!TODO] <REPLACE:
        - Remove instruction in the MARKDOWN TEMPLATE.
        - **DO NOT** include ANY verbose commentary, explanations, or text not corresponding to a field value.
        - DO NOT return empty values for the MARKDOWN TEMPLATE.
        '''
    return prompt


def run_tier1_catalog(chat_agent: ChatAgent,
                      datasheet: pd.DataFrame, 
                      all_classes_dict: dict[str, dict[str, str]],
                      tier1_cards: dict[dict[str, str], str]) -> dict[str, dict[str, str]]:

    datasheet_string = datasheet.to_string(index=False)
    tier1_prompt = create_tier1_prompt(datasheet_string, all_classes_dict)
    class_payload = run_ursa_agent(chat_agent, tier1_prompt)

    # tier1_card_prompt = genesis_card_prompt(class_payload, tier1_cards)
    # card_payload = run_ursa_agent(chat_agent, tier1_card_prompt, extract_json=False)
    # assemble_genesis_datacard(class_payload, card_payload, yaml_card_out)
    print(class_payload)

    return class_payload