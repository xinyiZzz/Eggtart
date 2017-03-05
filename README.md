## May 30 2016 8:44 PM

# Eggtart

* * *


## Introduction/框架介绍

### 目录结构

-     config 引擎配置文件模版，yaml格式，系统运行自动加载
-     engine_test_data 引擎测试用任务文件，json格式
-     eggtart 源代码
          server_base：引擎框架基类
          test_engine：测试引擎——模版Demo
          client.py：客户端，用于向指定引擎发送任务
          main_control: 主控引擎
          business_handle: 业务处理引擎
-     client.sh 客户端脚本，调用client.py，用于单引擎测试时命令行调用
-     client_cmd 引擎测试用客户端指令
-     setup.sh：引擎启动脚本

### 单个引擎功能

    新建引擎可仿照/eggtart/test_engine中调用方式，重写TestEngine.py文件中read_config、init_object、handle_task这三个函数来自定义引擎，主要功能包括：
    1) 以守护进程的方式启动引擎，输出日志写入/log目录下，启动时调用init_object函数初始化引擎具体操作类
    2) 读取/config目录下引擎指定的配置文件，其中server、beanstalkc、mysql三个配置部分会自动读取，其它自定义的配置文件需要重写read_config函数读取
    3) 实现引擎心跳，写入mysql中server_live表中
    4) 循环监听beanstalk中指定的任务开始队列，当接收到任务时自动调用handle_task函数进行处理
    5) 任务执行结果回写，将handle_task函数return返回的结果输出，包括本地文件、beanstalk任务结果队列两种输出方式

- - -

## 运行方法


- 单引擎调试运行方法

    注：若Mysql和beanstalk没安装在本机，需修改/config目录下对应引擎配置文件的queue_ip，mysql_host字段，若MySQL库不使用Test命名，需修改mysql_db字段。每个引擎对应/eggtart 目录下的一个子目录，/phishing_spark/test_engine目录为引擎模版，下面以其为例介绍
    
    1.  进入/Eggtart根目录，启动指令如下。

        ```
        python TestEngine.py start 启动引擎

        python TestEngine.py stop关闭引擎。

        python TestEngine.py reset 重启引擎。
        ```

    2. 查看/eggtart/test_engine/log下启动状态
    
    3. 在项目根目录下运行./client.sh -c test_engine_conf.yaml -cmd SINGLE_ENGINE_TEST -ti engine_test_data/test_task.json 指令(查看客户端详细参数可在根目录下运行 python client.py -cmd HELP 查看)
    
    4. (可选)用beanstalk_console查看beanstalk的任务启动队列中运行结果(/config/test_engine_conf.yaml的queue_start_name字段指定，注意当任务结束时，该队列中任务将删除并添加到结果队列中，即queue_result_name字段指定队列)
    
    5. 查看local_result中运行结果，查看/log目录下运行日志
    
    6. (可选)用beanstalk_console查看beanstalk的结果队列中运行结果(/config/test_engine_conf.yaml的queue_result_name字段指定)

    
- 框架启动方法(即启动全部引擎)：

    运行根目录下的setup.sh文件

    ```
    ./setup.sh  start  all       ：启动所有引擎

    ./setup.sh  start 引擎名称  ：启动指令引擎

    ./setup.sh stop all         ：关闭所有引擎

    ./setup.sh stop 引擎名称    ：关闭指令引擎

    ./setup.sh restart all     ：重启所有引擎

    ./setup reset 引擎名称      ：重启对应引擎

- 其他测试用指令 :    

    结果写入本地目录：
        ./client.sh -c test_engine_conf.yaml -cmd SINGLE_ENGINE_TEST -ti engine_test_data/test_task.json 
    结果写入结果队列：
    ./client.sh -c test_engine_conf.yaml -cmd SINGLE_ENGINE_TEST -ti engine_test_data/test_task.json -gn 1 -o queue 
    # 
    ./client.sh -c test_engine_conf.yaml -cmd SINGLE_ENGINE_TEST -ti engine_test_data/test_task.json -gn 1 -o /home/ 
    # 结果写入指定目录
    ./client.sh -c test_engine_conf.yaml -cmd SINGLE_ENGINE_TEST -ti engine_test_data/test_task.json -gn 1 
    # 分组发送任务
        
    客户端参数解析:
        '-c/--config': "config.yaml that in ./config dir, contains a) server info; b) beanstalkc connection string;", # 调用引擎的配置文件，对应config目录下配置文件
        '-cmd/--command': "the cmd you want to run, e.g., \"BATCH_GRAYS_CHECK\"", #调用指令，单引擎测试时用SINGLE_ENGINE_TEST指令
        '-ti/--task_info_list': "the location of the json file for task info", # 任务列表，对应engine_test_data目录下任务文件，任务文件为json格式，内容任意
        '-gn/--group_num': "the num of the group for task info or url list, default None", # 没个任务最大包含子任务数量，若单任务数量太大，则分组发送给引擎
        '-o/--output': "the location of the output json file for task result, default None" # 输出文件目录，默认引擎目录下local_result目录，文件名为时间戳；当为queue时，写入config中定义的beanstalk结果队列；否则写入指定目录
```

- - -

## contact/联系方式

609610350@qq.com









