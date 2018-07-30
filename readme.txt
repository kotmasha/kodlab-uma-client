####HOW TO RUN UMA CLIENT####
0 in your cmd, run setEnv.bat(sh), so you get the UMA environment variable
1 run client through bin/launcher.py <test_yml>
2 run plotter through bin/plotter.py <test_name>
3 cluster/cluster.yml contains instance num, host and port to connect to
4 cluster/pool.yml contains pool size settings
5 every test_yml file should contains:
    script: the test script to run, should be in you $PATHONPATH(without .py)
    fun:    functions to run, should be in the test script
    iter:   number of iterations to run the test
    params: the parameters needed in the fun
        name field is necessary to make the script work
