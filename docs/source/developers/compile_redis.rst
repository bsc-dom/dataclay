Compile Redis in MN4
====================

Use login0 to download redis.

.. code-block:: console
    
    wget https://download.redis.io/redis-stable.tar.gz
    tar -xzvf redis-stable.tar.gz
    cd redis-stable
    module load gcc/12.1.0_binutils
    make distclean
    make
