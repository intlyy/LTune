# LTune
This is the source code to the paper "LTune: An Efficient and Reliable Database Tuning System via LLM-Driven Tree Search". Please refer to the paper for the experimental details.


## Environment Installation

In our experiments,  We conduct experimets on MySQL 5.7.

1. Preparations: Python == 3.7

2. Install packages

   ```shell
   pip install -r requirements.txt
   pip install .
   ```

3. Download and install MySQL 5.7 and boost

   ```shell
   wget http://sourceforge.net/projects/boost/files/boost/1.59.0/boost_1_59_0.tar.gz
   wget https://dev.mysql.com/get/Downloads/MySQL-5.7/mysql-boost-5.7.19.tar.gz
   
   sudo cmake . -DCMAKE_INSTALL_PREFIX=PATH_TO_INSTALL -DMYSQL_DATADIR=PATH_TO_DATA -DDEFAULT_CHARSET=utf8 -DDEFAULT_COLLATION=utf8_general_ci -DMYSQL_TCP_PORT=3306 -DWITH_MYISAM_STORAGE_ENGINE=1 -DWITH_INNOBASE_STORAGE_ENGINE=1 -DWITH_ARCHIVE_STORAGE_ENGINE=1 -DWITH_BLACKHOLE_STORAGE_ENGINE=1 -DWITH_MEMORY_STORAGE_ENGINE=1 -DENABLE_DOWNLOADS=1 -DDOWNLOAD_BOOST=1 -DWITH_BOOST=PATH_TO_BOOST;
   sudo make -j 16;
   sudo make install;
   ```



## Workload Preparation 

### SYSBENCH

Download and install

```shell
git clone https://github.com/akopytov/sysbench.git
./autogen.sh
./configure
make && make install
```

Load data

```shell
sysbench --db-driver=mysql --mysql-host=$HOST --mysql-socket=$SOCK --mysql-port=$MYSQL_PORT --mysql-user=root --mysql-password=$PASSWD --mysql-db=sbtest --table_size=800000 --tables=150 --events=0 --threads=32 oltp_read_write prepare > sysbench_prepare.out
```

### Join-Order-Benchmark (JOB)

Download IMDB Data Set from http://homepages.cwi.nl/~boncz/job/imdb.tgz.

Follow the instructions of https://github.com/winkyao/join-order-benchmark to load data into MySQL.

## Knob Space Optimizer

Modify  `Workload and database kernel information` in `pruning.py` and `Select.py` to match your workload and database kernel information. Then

```shell
python space_optimizer.py
```

The selected knobs will be saved in `./knob/opt_space.json` .

## Guided Tree-based Knob Recommender

1. execute tuning server
    - modify   `tuning_server.py` and fill the model you want to use and the corresponding API-Key in
    ```python
      model = ""
      client = OpenAI(
          base_url=,
          api_key="",
      )
    ```
    and select port in 
    ```python
      app.run(host='0.0.0.0', port=5000)
    ```
    
   - run
    ```shell
    nohup python -u tuning_server.py >out.log 2>&1 &
    ```

2. tuning
   - modify   `tuner.py` and fill the database information in 
    ```python
      mysql_ip = 
      ip_password = ''
      config = {
          'user': '',      
          'password': '',   
          'host': '',           
          'database': 'sysbench',   
          'port': 3306
      }
    ```
    and server url 
    ```python
     url = ''
    ```
   - tune
   ```shell
    nohup python -u tuner.py 2>&1 &
   ```