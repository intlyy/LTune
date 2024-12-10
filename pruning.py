from openai import OpenAI
import re
import json
import os

def get_knob_details(knob_set, json_file_path):
    # Extract the detailed information that matches the selected knobs

    with open(json_file_path, 'r',encoding='utf-8') as file:
        knob_details = json.load(file)
    
    result = {knob: knob_details[knob] for knob in knob_set if knob in knob_details}

    return json.dumps(result, indent=4)

def call_open_source_llm_1(model,knob_list):
    client = OpenAI(
        api_key= , # your api_key
        base_url=
    )

    messages = [
    {"role": "system", "content": "You are an experienced database administrators, skilled in database knob tuning."},
    {
        "role": "user",
        "content": f"""
            Task Overview: 
            Given the knob name along with its suggestion and tuning task information, your job is to offer intervals for each knob that may lead to the best performance of the system and meet the hardware resource constraints. 
            In addition, if there is a special value (e.g., 0, -1, etc.), please mark it with “special value”.
            Workload and database kernel information: 
            - Workload: OLTP, SYSBENCH Read-Write Mixed Model, Read-Write Ratio = 50%, threads=32 .
            - Data: 13 GB data contains 50 tables and each table contains 1,000,000 rows of record.
            - Database Kernel: RDS MySQL 5.7.
            - Hardware: 8 vCPUs and 16 GB RAM.
            Knobs:
            {knob_list}
            Output Format:
            "knob_name"{{
                "min_value": MIN_VALUE,
                "max_value": MAX_VALUE,
                "special_value": SPECIAL_VALUE
            }} 
            Now let us think step by step.        
        """
    }
    ]
    print(messages)

    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature = 0
    )

    for choice in completion.choices:
        print(choice.message)
        print("--------------------------")
        pattern = r"\*\*(.+?)\*\*:\n\s+- \"min_value\": (.+?) \(.+?\)\n\s+- \"max_value\": (.+?) \(.+?\)\n\s+- \"special_value\": (.+?)\n"

        # Parse data using regex
        matches = re.findall(pattern, choice.message)

        # Convert matches to a list of dictionaries
        parsed_data = []
        for match in matches:
            knob_name = match[0]
            min_value = match[1].strip()
            max_value = match[2].strip()
            special_value = match[3].strip()
            
            # Process special_value to handle None or lists
            if special_value == "None":
                special_value = None
            elif ", " in special_value:
                special_value = [val.strip() for val in special_value.split(",")]
            else:
                try:
                    special_value = int(special_value)  # Convert to int if possible
                except ValueError:
                    pass  # Leave as string if not convertible
            
            parsed_data.append({
                "knob": knob_name,
                "min_value": min_value,
                "max_value": max_value,
                "special_value": special_value
            })

        # Convert the result to JSON
        json_file_path = os.path.join("knob", "opt_space.json")
        with open(json_file_path, "w") as f:
            json.dump(parsed_data, f, indent=4)
            f.close()

def prune(knob_list):

    model = "gpt-4-0125-preview"
    # To avoid the prompt being too long, we only include the detailed information of the knobs 
    # during pruning. The json_file_path is the file path where the knob details are stored. 
    # Similar to the selection phase, this information can be easily scraped from the DB documentation.
    json_file_path = os.path.join("knob", "candidate_knobs", "100_mysql.json")
    knob_list = get_knob_details(knob_list,json_file_path)

    call_open_source_llm_1 (model,knob_list)