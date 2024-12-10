import requests
import json
import pymysql
import os
import sys
import time
import re

mysql_ip = 
ip_password = 
config = {
    'user': ,       # Replace with your database username
    'password': ,   # Replace with your database password
    'host': ,       # host
    'database': ,   # Replace with your database name
    'port':         # port

}
iteration_number = 100 # iteration times

def get_current_metric():

    # create a database connection
    conn = pymysql.connect(**config)
    cursor = conn.cursor()

    sql = "select name,count from information_schema.INNODB_METRICS where status = 'enabled'"
    cursor.execute(sql)
    result = cursor.fetchall() 
    knobs = {}
    for i in result:
        #print(f"\"{i[0]}\" : {i[1]},")
        knobs[i[0]] = int(i[1])
    json_data = json.dumps(knobs, indent=4)
    #print(json_data)
    return knobs

def get_current_knob():

    # create a database connection
    conn = pymysql.connect(**config)
    cursor = conn.cursor()

    knobs = {}

    parameters = [
        'tmp_table_size', 'max_heap_table_size', 'query_prealloc_size', 'innodb_thread_concurrency', 'innodb_doublewrite', 'sort_buffer_size', 'log_output', 'general_log', 'innodb_random_read_ahead', 'innodb_buffer_pool_size', 'innodb_max_dirty_pages_pct_lwm', 'innodb_purge_threads', 'table_open_cache_instances', 'innodb_compression_failure_threshold_pct', 'innodb_change_buffering', 'innodb_online_alter_log_max_size', 'innodb_purge_batch_size', 'expire_logs_days', 'innodb_lru_scan_depth', 'innodb_max_dirty_pages_pct', 'innodb_write_io_threads', 'innodb_stats_transient_sample_pages', 'div_precision_increment', 'innodb_spin_wait_delay', 'innodb_compression_pad_pct_max', 'innodb_read_ahead_threshold', 'innodb_concurrency_tickets', 'innodb_log_write_ahead_size', 'innodb_change_buffer_max_size', 'long_query_time', 'query_cache_limit', 'max_user_connections', 'key_cache_block_size', 'ngram_token_size', 'innodb_autoextend_increment', 'innodb_sort_buffer_size', 'join_buffer_size', 'host_cache_size', 'net_write_timeout', 'binlog_row_image', 'table_open_cache', 'innodb_adaptive_max_sleep_delay', 'innodb_ft_total_cache_size', 'read_buffer_size', 'eq_range_index_dive_limit', 'innodb_flush_log_at_timeout', 'key_cache_age_threshold', 'range_alloc_block_size', 'innodb_ft_sort_pll_degree', 'innodb_ft_min_token_size', 'innodb_read_io_threads', 'max_binlog_size', 'innodb_table_locks', 'innodb_ft_result_cache_limit', 'innodb_purge_rseg_truncate_frequency', 'max_binlog_stmt_cache_size', 'table_definition_cache', 'innodb_thread_sleep_delay', 'innodb_adaptive_flushing_lwm', 'max_write_lock_count', 'innodb_io_capacity_max', 'innodb_max_purge_lag', 'sync_binlog', 'optimizer_search_depth', 'session_track_schema', 'transaction_prealloc_size', 'thread_cache_size', 'query_cache_size', 'flush_time', 'low_priority_updates', 'ft_query_expansion_limit', 'max_error_count', 'binlog_group_commit_sync_no_delay_count', 'max_join_size', 'innodb_log_file_size', 'default_week_format', 'session_track_transaction_info', 'open_files_limit', 'flush', 'innodb_flush_neighbors', 'concurrent_insert', 'innodb_fill_factor', 'back_log', 'net_read_timeout', 'innodb_compression_level', 'binlog_direct_non_transactional_updates', 'session_track_state_change', 'automatic_sp_privileges', 'transaction_alloc_block_size', 'innodb_old_blocks_time', 'show_compatibility_56', 'innodb_replication_delay', 'max_sort_length', 'innodb_page_cleaners', 'innodb_sync_spin_loops', 'explicit_defaults_for_timestamp', 'ft_min_word_len', 'stored_program_cache', 'connect_timeout', 'innodb_adaptive_hash_index_parts'
    ]

    # query and print the values of each knobs
    for param in parameters:
        cursor.execute(f"SHOW VARIABLES LIKE '{param}'")
        result = cursor.fetchone()
        if result:
            try:
                # Attempt to convert to integer if it's a digit, otherwise to float
                knobs[param] = int(result[1]) if result[1].isdigit() else round(float(result[1]))
            except ValueError:
                # If conversion fails, assign the string directly (e.g., 'ON' or 'OFF')
                knobs[param] = result[1]

    json_data = json.dumps(knobs, indent=4)
    print(json_data)
    return knobs


def get_knobs_detail():
    json_file_path = os.path.join("knob", "opt_space.json")
    f = open(json_file_path, 'r')
    content = json.load(f)
    #content = set_expert_rule(content)

    result = {}
    count = 0
    for i in content.keys():
        result[i] = content[i]
        count += 1
    
    return result

def test_by_JOB(self,log_file):

    temp_config = {}
    knobs_detail = get_knobs_detail()
    for key in knobs_detail.keys():
        if key in knob.keys():
            if knobs_detail[key]['type'] == 'integer':
                temp_config[key] = knob.get(key) 
            elif knobs_detail[key]['type'] == 'enum':
                temp_config[key] = knobs_detail[key]['enum_values'][knob.get(key)]
    
    #set knobs and restart databases
    set_knobs_command = '\cp {} {};'.format('/etc/my.cnf.bak' , '/etc/my.cnf')
    for knobs in temp_config:
        set_knobs_command += 'echo "{}"={} >> {};'.format(knobs,temp_config[knobs],'/etc/my.cnf')
    
    head_command = 'sshpass -p {} ssh {} '.format(ip_password, mysql_ip)
    set_knobs_command = head_command + '"' + set_knobs_command + '"' 
    state = os.system(set_knobs_command)

    time.sleep(10)

    print("success set knobs")
    #exit()

    restart_knobs_command = head_command + '"service mysqld restart"' 
    state = os.system(restart_knobs_command)

    if state == 0:
        print('database has been restarted')
        conn = pymysql.connect(host=config.get('host'),
                    user=config.get('mysql_user'),
                    passwd=config.get('mysql_password'),
                    db=config.get('database'),
                    port=config.get('port'))
        cursor = conn.cursor()
        # query file directory
        query_dir = '/home/JOB'
        query_files = [os.path.join(query_dir, f) for f in os.listdir(query_dir) if f.endswith('.sql')]
        total_time = 0
        i = 0 
        for i in range(1):
            i = i+1
            for query_file in query_files:
                print(f"Running {query_file}")
                elapsed_time = self.run_benchmark(query_file, cursor)
                print(f"Time taken: {elapsed_time:.2f} seconds")
                total_time += elapsed_time
        
        print(f"Total time for 5 runs: {total_time:.2f} seconds")

        cursor.close()
        conn.close()
        return total_time
    else:
        print('database restarting failed')
        return -1    

def test_by_sysbench(knob):

    #load knobs
    temp_config = {}
    knobs_detail = get_knobs_detail()
    for key in knobs_detail.keys():
        if key in knob.keys():
            if knobs_detail[key]['type'] == 'integer':
                temp_config[key] = knob.get(key) 
            elif knobs_detail[key]['type'] == 'enum':
                value = str(knob.get(key))
                if value in knobs_detail[key]['enum_values']:
                    temp_config[key] = value
                else:
                    # Handle case where value is not in the enum_values list
                    print(f"Warning: {value} not found in enum values for {key}")
    
    #set knobs and restart databases
    set_knobs_command = '\cp {} {};'.format('/etc/my.cnf.bak' , '/etc/my.cnf')
    for knobs in temp_config:
        set_knobs_command += 'echo "{}"={} >> {};'.format(knobs,temp_config[knobs],'/etc/my.cnf')
    
    head_command = 'sshpass -p {} ssh {} '.format(ip_password, mysql_ip)
    set_knobs_command = head_command + '"' + set_knobs_command + '"' 
    state = os.system(set_knobs_command)

    time.sleep(10)

    print("success set knobs")
    #exit()

    restart_knobs_command = head_command + '"service mysqld restart"' 
    state = os.system(restart_knobs_command)

    if state == 0:
        print('database has been restarted')
        log_file = './log/' + '{}.log'.format(int(time.time()))
        command_run = 'sysbench --db-driver=mysql --threads=32 --mysql-host={} --mysql-port={} --mysql-user={} --mysql-password={} --mysql-db={} --tables=50 --table-size=1000000 --time=120 --report-interval=60 oltp_read_write run'.format(
                            config.get('host'),
                            config.get('port'),
                            config.get('user'),
                            config.get('password'),
                            config.get('database')
                            )
        
        os.system(command_run + ' > {} '.format(log_file))
        
        qps = sum([float(line.split()[8]) for line in open(log_file,'r').readlines() if 'qps' in line][-int(120/60):]) / (int(120/60))
        tps = float(qps/20.0)
        return tps
    else:
        print('database restarting failed')
        return 0

if __name__ == "__main__":

    # Obtain the initial configuration and test the performance
    knob = get_current_knob()
    throughput = test_by_sysbench(knob)
    metric = get_current_metric()
    data = {
        "knob": knob,
        "throughput": throughput,
        "metric": metric
    }
    # The address and port of tuning server.
    url = 
    # Send data to tuning server
    response = requests.post(url, json=data)

    # Retrieve and print the return result
    result = response.json()
    print(result)
    
    iteration = 0
    best_knob = []
    best_metric = []
    best_throughput = 0
    while iteration < iteration_number:
        json_strings = result.strip().split('\n')
        data_list = []
        for knobs in json_strings:
            if not knobs.strip():
                continue
            knob = json.loads(knobs)
            throughput =  test_by_sysbench(knob)
            if(throughput == 0):
                metric = []
            else:
                metric = get_current_metric()
            data = {
                "knob": knob,
                "throughput": throughput,
                "metric": metric
            }
            data_list.append(data)
            with open('record/history',"a") as f:
                json.dump(data, f, indent=4)
                f.close()
            if throughput>best_throughput:
                best_knob = knob
                best_metric = metric
                best_throughput = throughput
            
            
        url =  # The address and port of tuning server.
        response = requests.post(url, json=data_list)
        result = response.json()
        iteration = iteration+1
