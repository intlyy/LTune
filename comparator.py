import json
import numpy as np
from keras.models import Sequential
from keras.layers import Dense
import matplotlib.pyplot as plt
import sys
from sklearn.ensemble import GradientBoostingRegressor, RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score

class comparator:
    def __init__(self, history_file):
        self.history_file = history_file
        self.gbr = None
        self.rfr = None
        self.history_x = None
        self.history_y = None

    def data_prepare(self,file):
        # 定义100个参数列表以及默认值（以MySQL5.7为准）
        parameter_list = ['tmp_table_size', 'max_heap_table_size', 'query_prealloc_size', 'innodb_thread_concurrency', 'innodb_doublewrite', 'sort_buffer_size', 'log_output', 'general_log', 'innodb_random_read_ahead', 'innodb_buffer_pool_size', 'innodb_max_dirty_pages_pct_lwm', 'innodb_purge_threads', 'table_open_cache_instances', 'innodb_compression_failure_threshold_pct', 'innodb_change_buffering', 'innodb_online_alter_log_max_size', 'innodb_purge_batch_size', 'expire_logs_days', 'innodb_lru_scan_depth', 'innodb_max_dirty_pages_pct', 'innodb_write_io_threads', 'innodb_stats_transient_sample_pages', 'div_precision_increment', 'innodb_spin_wait_delay', 'innodb_compression_pad_pct_max', 'innodb_read_ahead_threshold', 'innodb_concurrency_tickets', 'innodb_log_write_ahead_size', 'innodb_change_buffer_max_size', 'long_query_time', 'query_cache_limit', 'max_user_connections', 'key_cache_block_size', 'ngram_token_size', 'innodb_autoextend_increment', 'innodb_sort_buffer_size', 'join_buffer_size', 'host_cache_size', 'net_write_timeout', 'binlog_row_image', 'table_open_cache', 'innodb_adaptive_max_sleep_delay', 'innodb_ft_total_cache_size', 'read_buffer_size', 'eq_range_index_dive_limit', 'innodb_flush_log_at_timeout', 'key_cache_age_threshold', 'range_alloc_block_size', 'innodb_ft_sort_pll_degree', 'innodb_ft_min_token_size', 'innodb_read_io_threads', 'max_binlog_size', 'innodb_table_locks', 'innodb_ft_result_cache_limit', 'innodb_purge_rseg_truncate_frequency', 'max_binlog_stmt_cache_size', 'table_definition_cache', 'innodb_thread_sleep_delay', 'innodb_adaptive_flushing_lwm', 'max_write_lock_count', 'innodb_io_capacity_max', 'innodb_max_purge_lag', 'sync_binlog', 'optimizer_search_depth', 'session_track_schema', 'transaction_prealloc_size', 'thread_cache_size', 'query_cache_size', 'flush_time', 'low_priority_updates', 'ft_query_expansion_limit', 'max_error_count', 'binlog_group_commit_sync_no_delay_count', 'max_join_size', 'innodb_log_file_size', 'default_week_format', 'session_track_transaction_info', 'open_files_limit', 'flush', 'innodb_flush_neighbors', 'concurrent_insert', 'innodb_fill_factor', 'back_log', 'net_read_timeout', 'innodb_compression_level', 'binlog_direct_non_transactional_updates', 'session_track_state_change', 'automatic_sp_privileges', 'transaction_alloc_block_size', 'innodb_old_blocks_time', 'show_compatibility_56', 'innodb_replication_delay', 'max_sort_length', 'innodb_page_cleaners', 'innodb_sync_spin_loops', 'explicit_defaults_for_timestamp', 'ft_min_word_len', 'stored_program_cache', 'connect_timeout', 'innodb_adaptive_hash_index_parts']
        default_values = {
            "tmp_table_size": 16777216,
            "max_heap_table_size": 16777216,
            "query_prealloc_size": 8192,
            "innodb_thread_concurrency": 0,
            "innodb_doublewrite": 1,
            "sort_buffer_size": 262144,
            "log_output": "FILE",
            "general_log": 0,
            "innodb_random_read_ahead": 0,
            "innodb_buffer_pool_size": 134217728,
            "innodb_max_dirty_pages_pct_lwm": 0,
            "innodb_purge_threads": 4,
            "table_open_cache_instances": 16,
            "innodb_compression_failure_threshold_pct": 5,
            "innodb_change_buffering": "all",
            "innodb_online_alter_log_max_size": 134217728,
            "innodb_purge_batch_size": 300,
            "expire_logs_days": 0,
            "innodb_lru_scan_depth": 1024,
            "innodb_max_dirty_pages_pct": 75,
            "innodb_write_io_threads": 4,
            "innodb_stats_transient_sample_pages": 8,
            "div_precision_increment": 4,
            "innodb_spin_wait_delay": 6,
            "innodb_compression_pad_pct_max": 50,
            "innodb_read_ahead_threshold": 56,
            "innodb_concurrency_tickets": 5000,
            "innodb_log_write_ahead_size": 8192,
            "innodb_change_buffer_max_size": 25,
            "long_query_time": 10,
            "query_cache_limit": 1048576,
            "max_user_connections": 0,
            "key_cache_block_size": 1024,
            "ngram_token_size": 2,
            "innodb_autoextend_increment": 64,
            "innodb_sort_buffer_size": 1048576,
            "join_buffer_size": 262144,
            "host_cache_size": 128,
            "net_write_timeout": 60,
            "binlog_row_image": "FULL",
            "table_open_cache": 2000,
            "innodb_adaptive_max_sleep_delay": 150000,
            "innodb_ft_total_cache_size": 640000000,
            "read_buffer_size": 131072,
            "eq_range_index_dive_limit": 200,
            "innodb_flush_log_at_timeout": 1,
            "key_cache_age_threshold": 300,
            "range_alloc_block_size": 4096,
            "innodb_ft_sort_pll_degree": 2,
            "innodb_ft_min_token_size": 3,
            "innodb_read_io_threads": 4,
            "max_binlog_size": 1073741824,
            "innodb_table_locks": 1,
            "innodb_ft_result_cache_limit": 2000000000,
            "innodb_purge_rseg_truncate_frequency": 128,
            "max_binlog_stmt_cache_size": 18446744073709547520,
            "table_definition_cache": 1400,
            "innodb_thread_sleep_delay": 10000,
            "innodb_adaptive_flushing_lwm": 10,
            "max_write_lock_count": 4294967295,
            "innodb_io_capacity_max": 2000,
            "innodb_max_purge_lag": 0,
            "sync_binlog": 1,
            "optimizer_search_depth": 62,
            "session_track_schema": 1,
            "transaction_prealloc_size": 4096,
            "thread_cache_size": 9,
            "query_cache_size": 16777216,
            "flush_time": 0,
            "low_priority_updates": 0,
            "ft_query_expansion_limit": 20,
            "max_error_count": 64,
            "binlog_group_commit_sync_no_delay_count": 0,
            "max_join_size": 18446744073709551615,
            "innodb_log_file_size": 50331648,
            "default_week_format": 0,
            "session_track_transaction_info": 0,
            "open_files_limit": 5000,
            "flush": 0,
            "innodb_flush_neighbors": 1,
            "concurrent_insert": 1,
            "innodb_fill_factor": 100,
            "back_log": 80,
            "net_read_timeout": 30,
            "innodb_compression_level": 6,
            "binlog_direct_non_transactional_updates": 0,
            "session_track_state_change": 1,
            "automatic_sp_privileges": 1,
            "transaction_alloc_block_size": 8192,
            "innodb_old_blocks_time": 1000,
            "show_compatibility_56": 0,
            "innodb_replication_delay": 0,
            "max_sort_length": 1024,
            "innodb_page_cleaners": 4,
            "innodb_sync_spin_loops": 30,
            "explicit_defaults_for_timestamp": 0,
            "ft_min_word_len": 4,
            "stored_program_cache": 256,
            "connect_timeout": 10,
            "innodb_adaptive_hash_index_parts": 8,
        }


        # 初始化存储
        mertics = []
        data_x = []
        data_y = []

        # 打开文件并逐行处理
        with open(file, 'r') as f:
            lines = f.readlines()
            for line in lines[:-1]:  # 遍历除最后一行外的所有行
                try:
                    # 拆分出 knobs 和 qps+metrics
                    parts = line.split('},qps:')
                    knobs_part = parts[0].split(',')[1:]
                    qps_and_metrics = parts[1].split('metrics:')

                    # 提取 qps 值并跳过 qps 为 0 的记录
                    qps = -float(qps_and_metrics[0].strip())
                    if qps == 0:
                        continue

                    # 提取 metrics 数据
                    metrics_raw = qps_and_metrics[1].strip()[1:-1]
                    metrics = list(map(int, metrics_raw.split(',')))

                    # 提取 knobs 值
                    knobs_dict = {}
                    for i in range(0, len(knobs_part), 2):
                        param_name = knobs_part[i].strip()
                        param_value = int(knobs_part[i + 1].strip())
                        knobs_dict[param_name] = param_value

                    # 创建完整的参数列表，使用默认值填充缺失参数
                    complete_knobs = []
                    for param in parameter_list:
                        if param in knobs_dict:
                            complete_knobs.append(knobs_dict[param])
                        else:
                            complete_knobs.append(default_values[param])

                    # 存储到对应列表
                    mertics.append(metrics)
                    data_x.append(complete_knobs)
                    data_y.append(qps)
                except (IndexError, ValueError) as e:
                    print(f"跳过行，因为解析出错: {line.strip()}")
                    print(f"错误: {e}")

        # 打印结果长度检查
        print(f"成功解析行数: {len(data_x)}")


        tmpx = []
        tmpy = []

        for i in range(len(data_x)):
            for j in range(i + 1, len(data_x)):
                tmpx.append(np.array(mertics[i] + data_x[i] + data_x[j]))
                if data_y[i] < data_y[j]:
                    tmpy.append(1)
                else:
                    tmpy.append(0)
                # tmpx.append(mertics[j] + data_x[i])
                # if data_y[i] < data_y[j]:
                #     tmpy.append(0)
                # else:
                #     tmpy.append(1)

        data_x = np.array(tmpx)
        data_y = np.array(tmpy)
        print(data_x.dtype)
        print(data_y.dtype)

        mmax = data_x.max(axis=0)
        mmin = data_x.min(axis=0)

        # 最大最小归一化
        data_x = np.divide(np.subtract(data_x, mmin), np.subtract(mmax, mmin))
        print(data_x[0])
        print(data_x.dtype)
        print(data_y.dtype)

        print(data_x.shape)
        return data_x,data_y


    def offline_train_comparator(self):
        self.history_x,self.history_y = self.data_prepare(self.history_file)
        X_train, X_test, y_train, y_test = train_test_split(data_x, data_y, test_size=0.2, random_state=42)

        self.gbr = GradientBoostingRegressor(random_state=42)
        self.rfr = RandomForestRegressor(random_state=42) 
        self.gbr.fit(X_train, y_train)
        self.rfr.fit(X_train, y_train)

    def online_train_comparator(slef, file_new):
        x_new, y_new = self.data_prepare(file_new)
        #data_x,data_y = self.data_prepare(file)
        X_train = np.vstack([self.history_x, x_new])
        y_train = np.hstack([self.history_y, y_new])
        self.gbr.fit(X_train, y_train)
        self.rfr.fit(X_train, y_train)

    def compare(self, metric, k1, k2):
        tmp = np.array(mertic + k1 + k2)
        gbr_preds = gbr.predict(tmp)
        rfr_preds = rfr.predict(tmp)
        final_preds = (gbr_preds + rfr_preds) / 2
        final_class_preds = (final_preds >= 0.5).astype(int)
        return final_class_preds
    
    def sort_list(self, metric, json_str):
        json_objects = [json.loads(js) for js in json_str]
    
        # 初始化分数字典
        scores = {i: 0 for i in range(len(json_objects))}
        
        # 两两比较
        for (i, obj1), (j, obj2) in combinations(enumerate(json_objects), 2):
            # 比较规则：按照 compare_key 的值比较
            if self.compare(metric, obj1, obj2) == 0:
                scores[i] += 1  # obj1 胜
            else :
                scores[j] += 1  # obj2 胜

        # 根据得分排序，选出前两名
        sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        top_two_indices = [idx for idx, _ in sorted_scores[:2]]
        
        # 返回前两名的对象和得分
        return [(json_objects[idx]) for idx in top_two_indices]


