=======
Logging
=======

DataClay offers logging to allow code debugging and information collection. 

When dataclay is imported, the logging is first initialized with a basic configuration in the config.py file:

.. code-block:: python
    :caption: config.py

    ...

    class Settings(BaseSettings):

    ...

        loglevel: Annotated[str, StringConstraints(strip_whitespace=True, to_upper=True)] = "INFO"

    ...

    settings = Settings()

    ...


    def logger_config(**kwargs):
        logging.basicConfig(**kwargs)


    logger_config(level=settings.loglevel)



If the user wants to configure its own logging, it can be done by importing the logging library and modifying 
the basicConfig. When client.start() function is called, then logger_config() is executed again, and if the argument
"force" is True then the logging configuration is overwritten.

.. warning::
    When modifying the basicConfig remember that the **force=True** parameter is mandatory. Otherwise, this new 
    configuration will be obviated.

An example is available in `GitHub <https://github.com/bsc-dom/dataclay/tree/main/examples/client-logger-config>`_
