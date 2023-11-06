Compile Redis
=============

You will need internet connectivity (to download the source tarball) and a
reasonablye up-to-date ``gcc``. If everything goes smoothly, the following
should be enough:

.. code-block:: console
    
    wget https://download.redis.io/redis-stable.tar.gz
    tar -xzvf redis-stable.tar.gz
    cd redis-stable
    module load gcc/12.1.0_binutils
    make distclean
    make

If this process ends successfully, you will be able to find the Redis binary
in ``src/redis-server`` (along other useful binaries).
