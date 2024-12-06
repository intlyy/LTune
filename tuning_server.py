from flask import Flask, request, jsonify
from openai import OpenAI
import json
import re
import os,sys
from comparator import comparator
import heapq

history_knobs = """
{
    "tmp_table_size": 16127516,
    "max_heap_table_size": 542958715,
    "query_prealloc_size": 2897026,
    "innodb_thread_concurrency": 126,
    "sort_buffer_size": 127236112,
    "innodb_buffer_pool_size": 15169920679,
    "innodb_max_dirty_pages_pct_lwm": 54,
    "innodb_purge_threads": 29,
    "table_open_cache_instances": 53,
    "innodb_compression_failure_threshold_pct": 64,
    "innodb_purge_batch_size": 4630,
    "expire_logs_days": 55,
    "innodb_lru_scan_depth": 5027,
    "innodb_max_dirty_pages_pct": 59,
    "innodb_write_io_threads": 9,
    "innodb_stats_transient_sample_pages": 18,
    "div_precision_incrementm": 28,
    "innodb_spin_wait_delay": 5779,
    "innodb_compression_pad_pct_max": 29,
    "innodb_read_ahead_threshold": 25
}
"""
OLAP_history_knobs = """
{
    "innodb_buffer_pool_size": 134217728
    "sort_buffer_size": 262144
    "read_buffer_size": 131072
    "innodb_log_buffer_size": 16777216
    "innodb_io_capacity": 200
    "innodb_io_capacity_max": 2000
    "max_connections": 151
    "innodb_thread_concurrency": 0
    "query_cache_size": 1048576
    "tmp_table_size": 16777216
}
"""

history_metrics = """
{
    "lock_deadlocks": 0,
    "lock_timeouts": 0,
    "lock_row_lock_current_waits": 0,
    "lock_row_lock_time": 0,
    "lock_row_lock_time_max": 0,
    "lock_row_lock_waits": 0,
    "lock_row_lock_time_avg": 0,
    "buffer_pool_size": 16106127360,
    "buffer_pool_reads": 94203,
    "buffer_pool_read_requests": 2990409,
    "buffer_pool_write_requests": 469598,
    "buffer_pool_wait_free": 0,
    "buffer_pool_read_ahead": 2317,
    "buffer_pool_read_ahead_evicted": 0,
    "buffer_pool_pages_total": 982980,
    "buffer_pool_pages_misc": 577,
    "buffer_pool_pages_data": 104773,
    "buffer_pool_bytes_data": 1716600832,
    "buffer_pool_pages_dirty": 40527,
    "buffer_pool_bytes_dirty": 663994368,
    "buffer_pool_pages_free": 877630,
    "buffer_pages_created": 705,
    "buffer_pages_written": 10900,
    "buffer_pages_read": 104068,
    "buffer_data_reads": 1703793152,
    "buffer_data_written": 394297344,
    "os_data_reads": 104135,
    "os_data_writes": 13327,
    "os_data_fsyncs": 5230,
    "os_log_bytes_written": 37642752,
    "os_log_fsyncs": 1979,
    "os_log_pending_fsyncs": 0,
    "os_log_pending_writes": 0,
    "trx_rseg_history_len": 4317,
    "log_waits": 0,
    "log_write_requests": 83048,
    "log_writes": 1959,
    "log_padded": 6734848,
    "adaptive_hash_searches": 131228,
    "adaptive_hash_searches_btree": 430491,
    "file_num_open_files": 66,
    "ibuf_merges_insert": 7424,
    "ibuf_merges_delete_mark": 14342,
    "ibuf_merges_delete": 3468,
    "ibuf_merges_discard_insert": 0,
    "ibuf_merges_discard_delete_mark": 0,
    "ibuf_merges_discard_delete": 0,
    "ibuf_merges": 16996,
    "ibuf_size": 77,
    "innodb_activity_count": 57537,
    "innodb_dblwr_writes": 437,
    "innodb_dblwr_pages_written": 10867,
    "innodb_page_size": 16384,
    "innodb_rwlock_s_spin_waits": 0,
    "innodb_rwlock_x_spin_waits": 0,
    "innodb_rwlock_sx_spin_waits": 290,
    "innodb_rwlock_s_spin_rounds": 17032,
    "innodb_rwlock_x_spin_rounds": 6593,
    "innodb_rwlock_sx_spin_rounds": 1292,
    "innodb_rwlock_s_os_waits": 93,
    "innodb_rwlock_x_os_waits": 38,
    "innodb_rwlock_sx_os_waits": 10,
    "dml_inserts": 13829,
    "dml_deletes": 13829,
    "dml_updates": 27658
}
"""

OLAP_history_output = """
{
    "innodb_buffer_pool_size": 13145128679, "sort_buffer_size": 98807428, "read_buffer_size": 256284660, "innodb_log_buffer_size": 371545610, "innodb_io_capacity": 80637, "innodb_io_capacity_max": 17548, "max_connections": 29461, "innodb_thread_concurrency": 265, "query_cache_size": 708770588, "tmp_table_size": 673863811
}
"""

history_output = """
{
    "tmp_table_size": 866896964,
    "max_heap_table_size": 643296362,
    "query_prealloc_size": 2092905,
    "innodb_thread_concurrency": 285,
    "sort_buffer_size": 79669047,
    "innodb_buffer_pool_size": 11003533276,
    "innodb_max_dirty_pages_pct_lwm": 87,
    "innodb_purge_threads": 29,
    "table_open_cache_instances": 28,
    "innodb_compression_failure_threshold_pct": 80,
    "innodb_purge_batch_size": 4223,
    "expire_logs_days": 32,
    "innodb_lru_scan_depth": 9632,
    "innodb_max_dirty_pages_pct": 57,
    "innodb_write_io_threads": 31,
    "innodb_stats_transient_sample_pages": 80,
    "div_precision_increment": 5,
    "innodb_spin_wait_delay": 3278,
    "innodb_compression_pad_pct_max": 25,
    "innodb_read_ahead_threshold": 29
}
"""

OLAP_knobs = """
    {
    "innodb_buffer_pool_size": {
        "max": 17179869184,   
        "min": 10737418240,
        "type": "integer",
        "description": "The size in bytes of the buffer pool, the memory area where InnoDB caches table and index data."
    },
    "sort_buffer_size": {
        "max": 134217728,
        "min": 32768,
        "type": "integer",
        "description": "This variable defines: For related information, see Section 14."
    },
    "read_buffer_size": {
        "max": 2147479552,
        "min": 8192,
        "type": "integer",
        "description": "Each thread that does a sequential scan for a MyISAM table allocates a buffer of this size (in bytes) for each table it scans."
    },
    "innodb_log_buffer_size": {
        "max": 4294967295,
        "min": 262144,
        "type": "integer",
        "description": "The size in bytes of the buffer that InnoDB uses to write to the log files on disk."
    },
    "innodb_io_capacity": {
        "max": 2000000,
        "min": 100,
        "type": "integer",
        "description": "The innodb_io_capacity variable defines the number of I/O operations per second (IOPS) available to InnoDB background tasks, such as flushing pages from the buffer pool and merging data from the change buffer."
    },
    "innodb_io_capacity_max": {
        "max": 40000,
        "min": 100,
        "type": "integer",
        "description": "If flushing activity falls behind, InnoDB can flush more aggressively, at a higher rate of I/O operations per second (IOPS) than defined by the innodb_io_capacity variable."
    },
    "max_connections": {
        "max": 100000,
        "min": 1,
        "type": "integer",
        "description": "The maximum permitted number of simultaneous client connections."

    },
    "innodb_thread_concurrency": {
        "max": 1000,
        "min": 0,
        "type": "integer",
        "description": "Defines the maximum number of threads permitted inside of InnoDB."
    },
    "query_cache_size": {
        "max": 2147483648,
        "min": 0,
        "type": "integer",
        "description": "The amount of memory allocated for caching query results."
    },
    "tmp_table_size": {
        "max": 1073741824,
        "min": 1024,
        "type": "integer",
        "description": "The maximum size of internal in-memory temporary tables."
    }
}
"""

knobs = """
{
    "innodb_buffer_pool_size": {
        "min": "8G",
        "max": "12G",
        "type": "integer",
        "special_value": null,
        "description": "Caches table and index data, significantly impacting read and write performance."
    },
    "innodb_log_file_size": {
        "min": "256M",
        "max": "2G",
        "type": "integer",
        "special_value": null,
        "description": "Affects the performance of write operations and recovery time."
    },
    "innodb_flush_log_at_trx_commit": {
        "enum_values": ["0", "1", "2"],
        "type": "enum",
        "special_value": ["0", "1", "2"],  // 0: Improves performance but sacrifices durability; 1: Ensures durability for each transaction; 2: Balances performance with some durability
        "description": "Controls the durability of transactions, influencing write throughput."
    },
    "innodb_thread_concurrency": {
        "min": 0,
        "max": 16,
        "type": "integer",
        "special_value": 0,  // 0: Allows unlimited concurrent threads
        "description": "Limits the number of threads that can enter InnoDB, affecting concurrency."
    },
    "innodb_io_capacity": {
        "min": 200,
        "max": 2000,
        "type": "integer",
        "description": "Determines the I/O capacity for background operations, impacting write performance."
    },
    "innodb_read_io_threads": {
        "min": 2,
        "max": 8,
        "type": "integer",
        "description": "Number of I/O threads for read operations, affecting read throughput."
    },
    "innodb_write_io_threads": {
        "min": 2,
        "max": 8,
        "type": "integer",
        "description": "Number of I/O threads for write operations, affecting write throughput."
    },
    "innodb_max_dirty_pages_pct": {
        "min": 60,
        "max": 90,
        "type": "integer",
        "description": "Controls the percentage of dirty pages in the buffer pool, impacting flushing behavior."
    },
    "innodb_adaptive_flushing": {
        "enum_values": ["ON", "OFF"],
        "type": "enum",
        "special_value": ["ON", "OFF"],  // ON: Enables adaptive flushing; OFF: Disables adaptive flushing
        "description": "Helps in maintaining a steady state of flushing, impacting write performance."
    },
    "innodb_flush_neighbors": {
        "min": 0,
        "max": 2,
        "type": "integer",
        "special_value": [0, 1, 2],  // 0: Disables flush neighbors (better for SSDs); 1: Enables neighbor flushing; 2: Maximizes neighbor flushing
        "description": "Affects the flushing of pages, impacting I/O performance."
    },
    "innodb_adaptive_hash_index": {
        "enum_values": ["ON", "OFF"],
        "type": "enum",
        "special_value": ["ON", "OFF"],  // ON: Enables adaptive hash index for faster lookups; OFF: Disables to reduce memory usage
        "description": "Can improve performance for certain workloads by speeding up index lookups."
    },
    "innodb_change_buffering": {
        "enum_values": ["none", "inserts", "deletes", "changes", "purges", "all"],
        "type": "enum",
        "special_value": ["none", "inserts", "deletes", "changes", "purges", "all"],  // none: Disables change buffering; all: Buffers all operations; other options buffer specific operations
        "description": "Buffers changes to secondary indexes, impacting write performance."
    },
    "innodb_doublewrite": {
        "enum_values": ["ON", "OFF"],
        "type": "enum",
        "special_value": ["ON", "OFF"],  // ON: Provides data integrity; OFF: Disables for performance gains at the risk of data loss
        "description": "Provides data integrity but can be disabled for performance gains at the risk of data loss."
    },
    "innodb_lru_scan_depth": {
        "min": 1000,
        "max": 2048,
        "type": "integer",
        "description": "Influences the flushing algorithm, impacting buffer pool performance."
    },
    "innodb_purge_threads": {
        "min": 1,
        "max": 4,
        "type": "integer",
        "description": "Number of threads for purge operations, affecting background processing."
    },
    "innodb_page_cleaners": {
        "min": 1,
        "max": 4,
        "type": "integer",
        "description": "Number of page cleaner threads, impacting the flushing of dirty pages."
    },
    "innodb_spin_wait_delay": {
        "min": 6,
        "max": 30,
        "type": "integer",
        "description": "Affects the performance of spin locks, impacting concurrency."
    },
    "innodb_flush_log_at_timeout": {
        "min": 1,
        "max": 10,
        "type": "integer",
        "description": "Controls the frequency of log flushing, impacting durability and performance."
    },
    "innodb_adaptive_max_sleep_delay": {
        "min": 0,
        "max": 1000000,
        "type": "integer",
        "special_value": 0,  // 0: Disables adaptive sleep delay
        "description": "Allows InnoDB to adjust sleep delay based on workload, impacting performance."
    },
    "innodb_old_blocks_time": {
        "min": 0,
        "max": 1000,
        "type": "integer",
        "special_value": 0,  // 0: Disables old block protection
        "description": "Protects the buffer pool from being filled with transient data, impacting cache efficiency."
    }
}

"""

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
    # 正则表达式匹配 "key": value 模式
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
    
    # 替换带单位的数值
    json_string = re.sub(r'\d+[KMGT]B', replace_match, json_string)
    return json_string


def remove_comments(json_string):
    # 去除行尾的单行注释
    json_string = re.sub(r'//.*', '', json_string)
    # 去除多行注释
    json_string = re.sub(r'/\*.*?\*/', '', json_string, flags=re.DOTALL)
    # 移除多余的逗号
    json_string = re.sub(r',\s*}', '}', json_string)
    json_string = re.sub(r',\s*]', ']', json_string)
    return json_string

def call_open_source_llm(model, messages,filename):
    with open('./recommand/gpt4_multi',"a") as f:
        json.dump(messages, f, indent=4)
        f.close()

    client = OpenAI(
        api_key= , 
        base_url=
    )

    completion = client.chat.completions.create(
        model=model,
        messages=messages,
        temperature = 1,
        top_p = 0.98
    )

    for choice in completion.choices:
        with open('./recommand/gpt4_multi',"a") as f:
            f.write(choice.message.content)
            f.close()

        pattern = r'\{[^{}]+\}'
        match = re.search(pattern, choice.message.content, re.DOTALL)

        if match:
            json_str = match.group(0)
            json_str = replace_units(json_str)
            config_dict = extract_key_value_pairs(json_str)
            #json_str = remove_comments(json_str)
            #config_dict = json.loads(json_str)
            print(config_dict)
            if not config_dict:
                return
            config_dict = json.dumps(config_dict)
            with open(filename, 'r') as f:
                data_str = f.read()

            # Split the data into individual JSON strings
            json_strings = data_str.strip().split('\n')

            # # Prepare the final structured JSON format
            # for json_str in json_strings:
            #     d = json.loads(json_str)
            if config_dict in json_strings :
                return
            with open(filename, 'a') as f:
                print("sucess recommendation!")
                f.write('\n')
                f.write(config_dict)

        else:
            print("No JSON configuration found in the input.")



last_result = {
    "innodb_io_capacity": 1000,
    "innodb_read_io_threads": 8,
    "innodb_write_io_threads": 8,
    "innodb_max_dirty_pages_pct": 75
}

history_top5 = []
app = Flask(__name__)
request_count = 0
@app.route('/process', methods=['POST'])
def process_data():


    global request_count
    global history_top5
    request_count += 1
    filename = f'./multi_answer/history_gpt4_multi_{request_count}'
    file = open(filename, 'w')
    file.close()

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
            # 如果队列未满，直接加入
            heapq.heappush(history_top5, (throughput, item))
        else:
            # 队列已满，比较最小值，如果当前记录更大，则替换
            heapq.heappushpop(history_top5, (throughput, item))

        if throughput == 0 :
            throughput = "0, because database starting failed under current configuration"
        
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
                - Previous Configuration(input) :
                {history_knob}
                - Inner Metrics(input) :
                {history_metric}
                - Optimized Configuration(output) :
                {history_output}

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

            """.format(knob=knobs, inner_metric=inner_metrics, last_knob = last_knobs, now_inner_metric = now_inner_metrics, throughput = throughput, environment=environment, db_metric = db_metric, history_knob = history_knobs, history_metric = history_metrics, history_output = history_output )
        }
        ]

        model = "gpt-4-0125-preview"

        global last_result
        #result = call_local_llm(base_url, model, extra_body, messages)
        i = 0
        while i<5 :
            i = i+1
            call_open_source_llm(model, messages, filename)
    
    with open(filename, 'r') as f:
        data_str = f.read()
        check = data_str.strip()  # 使用 .strip() 去除空格和换行符
        if not check:  # 如果去除空格和换行符后为空
            print("File is empty")
            data_str = last_result
    
    with open(filename, 'r') as f:
        data_str = f.read()
        # Split the data into individual JSON strings
        json_strings = data_str.strip().split('\n')
    
    top_two = comparator.sort_list(now_inner_metrics, json_strings)
    


    # 将结果返回给服务器A
    return jsonify(top_two)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

