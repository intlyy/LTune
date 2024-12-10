from flask import Flask, request, jsonify
from openai import OpenAI
import json
import re
import os,sys
from comparator import comparator
import heapq


inner_metrics = """
{
    "lock_deadlocks": "Number of deadlocks",
    "lock_timeouts": "Number of lock timeouts",
    "lock_row_lock_current_waits": "Number of row locks currently being waited for (innodb_row_lock_current_waits)",
    "lock_row_lock_time": "Time spent in acquiring row locks, in milliseconds (innodb_row_lock_time)",
    "lock_row_lock_time_max": "The maximum time to acquire a row lock, in milliseconds (innodb_row_lock_time_max)",
    "lock_row_lock_waits": "Number of times a row lock had to be waited for (innodb_row_lock_waits)",
    "lock_row_lock_time_avg": "The average time to acquire a row lock, in milliseconds (innodb_row_lock_time_avg)",
    "buffer_pool_size": "Server buffer pool size (all buffer pools) in bytes",
    "buffer_pool_reads": "Number of reads directly from disk (innodb_buffer_pool_reads)",
    "buffer_pool_read_requests": "Number of logical read requests (innodb_buffer_pool_read_requests)",
    "buffer_pool_write_requests": "Number of write requests (innodb_buffer_pool_write_requests)",
    "buffer_pool_wait_free": "Number of times waited for free buffer (innodb_buffer_pool_wait_free)",
    "buffer_pool_read_ahead": "Number of pages read as read ahead (innodb_buffer_pool_read_ahead)",
    "buffer_pool_read_ahead_evicted": "Read-ahead pages evicted without being accessed (innodb_buffer_pool_read_ahead_evicted)",
    "buffer_pool_pages_total": "Total buffer pool size in pages (innodb_buffer_pool_pages_total)",
    "buffer_pool_pages_misc": "Buffer pages for misc use such as row locks or the adaptive hash index (innodb_buffer_pool_pages_misc)",
    "buffer_pool_pages_data": "Buffer pages containing data (innodb_buffer_pool_pages_data)",
    "buffer_pool_bytes_data": "Buffer bytes containing data (innodb_buffer_pool_bytes_data)",
    "buffer_pool_pages_dirty": "Buffer pages currently dirty (innodb_buffer_pool_pages_dirty)",
    "buffer_pool_bytes_dirty": "Buffer bytes currently dirty (innodb_buffer_pool_bytes_dirty)",
    "buffer_pool_pages_free": "Buffer pages currently free (innodb_buffer_pool_pages_free)",
    "buffer_pages_created": "Number of pages created (innodb_pages_created)",
    "buffer_pages_written": "Number of pages written (innodb_pages_written)",
    "buffer_pages_read": "Number of pages read (innodb_pages_read)",
    "buffer_data_reads": "Amount of data read in bytes (innodb_data_reads)",
    "buffer_data_written": "Amount of data written in bytes (innodb_data_written)",
    "os_data_reads": "Number of reads initiated (innodb_data_reads)",
    "os_data_writes": "Number of writes initiated (innodb_data_writes)",
    "os_data_fsyncs": "Number of fsync() calls (innodb_data_fsyncs)",
    "os_log_bytes_written": "Bytes of log written (innodb_os_log_written)",
    "os_log_fsyncs": "Number of fsync log writes (innodb_os_log_fsyncs)",
    "os_log_pending_fsyncs": "Number of pending fsync write (innodb_os_log_pending_fsyncs)",
    "os_log_pending_writes": "Number of pending log file writes (innodb_os_log_pending_writes)",
    "trx_rseg_history_len": "Length of the TRX_RSEG_HISTORY list",
    "log_waits": "Number of log waits due to small log buffer (innodb_log_waits)",
    "log_write_requests": "Number of log write requests (innodb_log_write_requests)",
    "log_writes": "Number of log writes (innodb_log_writes)",
    "log_padded": "Bytes of log padded for log write ahead",
    "adaptive_hash_searches": "Number of successful searches using Adaptive Hash Index",
    "adaptive_hash_searches_btree": "Number of searches using B-tree on an index search",
    "file_num_open_files": "Number of files currently open (innodb_num_open_files)",
    "ibuf_merges_insert": "Number of inserted records merged by change buffering",
    "ibuf_merges_delete_mark": "Number of deleted records merged by change buffering",
    "ibuf_merges_delete": "Number of purge records merged by change buffering",
    "ibuf_merges_discard_insert": "Number of insert merged operations discarded",
    "ibuf_merges_discard_delete_mark": "Number of deleted merged operations discarded",
    "ibuf_merges_discard_delete": "Number of purge merged  operations discarded",
    "ibuf_merges": "Number of change buffer merges",
    "ibuf_size": "Change buffer size in pages",
    "innodb_activity_count": "Current server activity count",
    "innodb_dblwr_writes": "Number of doublewrite operations that have been performed (innodb_dblwr_writes)",
    "innodb_dblwr_pages_written": "Number of pages that have been written for doublewrite operations (innodb_dblwr_pages_written)",
    "innodb_page_size": "InnoDB page size in bytes (innodb_page_size)",
    "innodb_rwlock_s_spin_waits": "Number of rwlock spin waits due to shared latch request",
    "innodb_rwlock_x_spin_waits": "Number of rwlock spin waits due to exclusive latch request",
    "innodb_rwlock_sx_spin_waits": "Number of rwlock spin waits due to sx latch request",
    "innodb_rwlock_s_spin_rounds": "Number of rwlock spin loop rounds due to shared latch request",
    "innodb_rwlock_x_spin_rounds": "Number of rwlock spin loop rounds due to exclusive latch request",
    "innodb_rwlock_sx_spin_rounds": "Number of rwlock spin loop rounds due to sx latch request",
    "innodb_rwlock_s_os_waits": "Number of OS waits due to shared latch request",
    "innodb_rwlock_x_os_waits": "Number of OS waits due to exclusive latch request",
    "innodb_rwlock_sx_os_waits": "Number of OS waits due to sx latch request",
    "dml_inserts": "Number of rows inserted",
    "dml_deletes": "Number of rows deleted",
    "dml_updates": "Number of rows updated"
}
"""
environment = """
    - Workload: OLTP, SYSBENCH Read-Write Mixed Model, Read-Write Ratio = 50%, threads=32 .
    - Data: 13 GB data contains 50 tables and each table contains 1,000,000 rows of record.
    - Database Kernel: RDS MySQL 5.7.
    - Hardware: 8 vCPUs and 16 GB RAM, Disk Type: HDD.
"""

OLAP_environment = """
    - Workload: OLAP, JOB(join-order-benchmark) contains 113 multi-joint queries with realistic and complex joins, Read-Only .
    - Data: 13 GB data contains 50 tables and each table contains 1,000,000 rows of record.
    - Database Kernel: RDS MySQL 5.7.
    - Hardware: 8 vCPUs and 16 GB RAM.
"""

db_metric = "throughput"

def extract_key_value_pairs(json_string):
    pattern = re.compile(r'"(\w+)":\s*([\d.]+)')
    matches = pattern.findall(json_string)
    data = {key: int(value) for key, value in matches}
    return data

def convert_to_bytes(value):
    units = {
        'B': 1,
        'KB': 1024,
        'MB': 1024**2,
        'GB': 1024**3,
        'TB': 1024**4
    }
    match = re.match(r'(\d+)([KMGT]B)', value)
    if match:
        number = int(match.group(1))
        unit = match.group(2)
        return number * units[unit]
    return int(value)

def replace_units(json_string):
    def replace_match(match):
        return str(convert_to_bytes(match.group(0)))
    
    # Replace the values with units
    json_string = re.sub(r'\d+[KMGT]B', replace_match, json_string)
    return json_string


def remove_comments(json_string):
    # Remove single-line comments 
    json_string = re.sub(r'//.*', '', json_string)
    # Remove multi-line comments
    json_string = re.sub(r'/\*.*?\*/', '', json_string, flags=re.DOTALL)
    # Remove unnecessary commas
    json_string = re.sub(r',\s*}', '}', json_string)
    json_string = re.sub(r',\s*]', ']', json_string)
    return json_string

def call_open_source_llm(model, messages,filename):

    client = OpenAI(
        api_key= , # your api_key
        base_url= 
    )

    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature = 1,
        top_p = 0.98
    )

    for choice in completion.choices:

        pattern = r'\{[^{}]+\}'
        match = re.search(pattern, choice.message.content, re.DOTALL)

        if match:
            json_str = match.group(0)
            json_str = replace_units(json_str)
            config_dict = extract_key_value_pairs(json_str)

            print(config_dict)
            # Check if the parameter format is valid
            if not config_dict:
                return
            config_dict = json.dumps(config_dict)
            with open(filename, 'r') as f:
                data_str = f.read()

            # Split the data into individual JSON strings
            json_strings = data_str.strip().split('\n')


            # Remove duplicates
            if config_dict in json_strings :
                return
            with open(filename, 'a') as f:
                print("sucess recommendation!")
                f.write('\n')
                f.write(config_dict)

        else:
            print("No JSON configuration found in the input.")



history_top5 = []
app = Flask(__name__)
request_count = 0
@app.route('/process', methods=['POST'])
def process_data():


    global request_count
    global history_top5
    request_count += 1
    filename = os.path.join("knob", "candidate_configs")
    with open(filename, 'w') as file:
        pass 

    data = request.get_json()
    for item in data:
        last_knobs = item.get('knob')
        throughput = item.get('throughput')
        now_inner_metrics = item.get('metric')

        last_knobs = json.dumps(last_knobs, indent=4)
        now_inner_metrics = json.dumps(now_inner_metrics, indent=4)

        print(last_knobs)
        print(now_inner_metrics)
        print(throughput)

        if len(history_top5) < 5:
            # add the record directly if the memory window is not full
            heapq.heappush(history_top5, (throughput, item))
        else:
            # compare the minimum value. If the current record is larger, replace it.
            heapq.heappushpop(history_top5, (throughput, item))

        if throughput == 0 :
            throughput = "0, because database starting failed under current configuration"
        
        json_file_path = os.path.join("knob", "opt_space.json")
        with open(json_file_path, 'r') as file:
            knob_sapce = json.load(file)
        
        knobs = json.dumps(knob_sapce, indent=4)


        messages = [
        {
            "role": "system",
            "content": """
                You are an experienced database administrators, skilled in database knob tuning.
            """
        },
        {
            "role": "user",
            "content": """
                Task Overview: 
                Recommend optimal knob configuration based on the inner metrics and workload characteristics in order to optimize the {db_metric} metric.

                Workload and database kernel information: 
                {environment}

                Descriptions of Knobs and Inner Metrics:
                - knobs
                {knob}
                - inner metrics
                {inner_metric}

                Historical Knob Tuning Tasks:
                {Memeory_Window}

                Output Format:
                Strictly utilize the aforementioned knobs, ensuring that the generated configuration are formatted as follows:
                {{
                    "knob": value, 
                    ……
                }}

                Current Configuration:
                {last_knob}
                Database Feedback:
                - Throughput : {throughput} 
                - Inner Metrics: 
                {now_inner_metric}

                Now, let's think step by step.

            """.format(knob=knobs, inner_metric=inner_metrics, last_knob = last_knobs, now_inner_metric = now_inner_metrics, throughput = throughput, environment=environment, db_metric = db_metric, Memeory_Window=history_top5 )
        }
        ]

        model = "gpt-4-0125-preview"

        i = 0
        while i<5 :
            i = i+1
            call_open_source_llm(model, messages, filename)
    
    with open(filename, 'r') as f:
        data_str = f.read()
        check = data_str.strip() 
        if not check:  # Failed to find a new configuration
            print("File is empty")
            exit(0)
    
    with open(filename, 'r') as f:
        data_str = f.read()
        # Split the data into individual JSON strings
        json_strings = data_str.strip().split('\n')
    
    # select the top 2 from the candidate set through comparator
    if request_count % 20 == 0:
        comparator.online_train_comparator('record/history')
    top_two = comparator.sort_list(now_inner_metrics, json_strings)

    # Return the result to tuner
    return jsonify(top_two)

if __name__ == '__main__':
    # port
    app.run(host='0.0.0.0', port=5000)

