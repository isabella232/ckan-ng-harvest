# About Airflow

Airflow organices taks in DAGs. A DAG (Directed Acyclic Graph) is a collection of all the tasks you want to run, organized in a way that reflects their relationships and dependencies.  

Each task coulbe Bash, Python or others. if you need each task wait from another to start.  
You can connect the tasks in a DAG as you want (which one depends on which).
Tasks could be built from Jinja templates.
It has a nice and comfortable UI.  

You can also use _Sensors_: you can wait for certain files or database changes for activate anoter jobs. 

## Airflow code

Airflow is open, code [here](https://github.com/apache/airflow).  

### Using Airflow

```
pip install apache-airflow
airflow initdb
airflow webserver -p 8082
airflow scheduler
```

More commands: https://airflow.apache.org/cli.html
