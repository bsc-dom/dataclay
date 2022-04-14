# dataClay

dataClay is a distributed data store that enables applications to store and access objects in the same format they have in memory, and executes object methods within the data store. These two main features accelerate both the development of applications and their execution.

## Dependencies

- openjdk <8|11>
- Git
- Maven
- Python3

### Debian/Ubuntu

```bash
apt install openjdk-8-jdk git maven python3-pip
```

## Step-by-step installation

1. Make sure the above listed dependencies are available on your machine.
2. Clone dataClay repository: `git clone --recurse-submodules https://github.com/bsc-dom/dataclay`
3. Package *javaclay* source code into a *jar* file: `mvn -f javaclay/pom.xml package`
4. [optional] Install *dataClay* in Python. We recommend to use a virtual environment.
   - From the *pyclay* folder: `python setup.py install`.
   - Alternatively, you can install it using *pip*: `pip install dataclay`.

## Deploy dataClay

The architecture of dataClay is composed by two main components: the *Logic Module* and the *Data Service*. The *Logic Module* is a central repository that handles object metadata and management information. The *Data Service* is a distributed object store that handles object persistence and execution requests.

In order to deploy dataClay on a cluster of N nodes, one possible setup is to assign 1 node for the *Logic Module* and N-1 nodes for *Data Service* backends. You can easy extrapolete this scenario to more complex ones. For example, adding a backend to the *Logic Module* node, or sharing one node for multiple backends.

Considering our simple setup, the deployment would be as follows:

Deploy the ***Logic Module*** in one node:

1. Define the necessary environment variables (you may want to change the default values):
   - `export LOGICMODULE_PORT_TCP=11034`
   - `export LOGICMODULE_HOST=127.0.0.1`
   - `export DATACLAY_ADMIN_USER=admin`
   - `export DATACLAY_ADMIN_PASSWORD=admin`
   <!-- - export DATACLAY_HOME=. -->
   <!-- - `export STORAGE_METADATA_PATH=./dataclay/metadata` -->
   <!-- - `export STORAGE_PATH=./dataclay/storage` -->
2. Deploy the *Logic Module*: `java -cp <jar_path> es.bsc.dataclay.logic.server.LogicModuleSrv`

In the rest of the nodes deploy a ***Data Service*** backend:

1. Define the necessary environment variables (you may want to change the default values):
   - `export DATASERVICE_NAME=DS1`
   - `export DATASERVICE_JAVA_PORT_TCP=2127`
   - `export LOGICMODULE_PORT_TCP=11034`
   - `export LOGICMODULE_HOST=127.0.0.1`
   <!-- - export DATACLAY_HOME=. -->
   <!-- - `export STORAGE_METADATA_PATH=./dataclay/metadata` -->
   <!-- - `export STORAGE_PATH=./dataclay/storage` -->
   <!-- - export DEPLOY_PATH_SRC=. -->
   <!-- - export DEPLOY_PATH=. -->
2. Deploy the *Storage Location* and the Java *Execution Environment*: `java -cp <jar_path> es.bsc.dataclay.dataservice.server.DataServiceSrv`
3. Deploy the Python *Execution Environment*: `python -m dataclay.executionenv.server --service`

The Python *Execution Environment* do not have to be deployed if the client is not running Python applications.

## Client libraries

In order to connect your applications with dataClay services you need a client library for your preferred programming language. If you are developing a Java application, you can add the following dependency into your *pom* file to install the Java client library for dataClay version 2.6:

```xml
<dependency>
    <groupId>es.bsc.dataclay</groupId>
    <artifactId>dataclay</artifactId>
    <version>2.6.1</version>
</dependency>
```

In case you are developing a Python application, you can easily install the Python module with `pip` command (if you have not done it yet):

```bash
pip install dataClay
```

## Configuration files

The basic client configuration for an application is the minimum information required to initialize a session with dataClay. To  this end two different files are required: the *session.properties* file and the *client.properties* file.

### Session properties

This file contains the basic info to initialize a session with dataClay. It is automatically loaded during the initialization process (*DataClay.init()* in Java or *api.init()* in Python) and its default path is ***./cfgfiles/session.properties***. This path can be overridden by setting a different path through the environment variable DATACLAYSESSIONCONFIG.

Here is an example:

```Properties
Account=user
Password=s3ecret
StubsClasspath=./stubs
DataSets=myDataset,OtherDataSet
DataSetForStore=myDataset
LocalBackends=DS1
DataClayClientConfig=./cfgfiles/client.properties
```

**Account** and **Password** properties are used to specify user’s credentials.  
**StubsClasspath** defines a path where the stub classes can be located. That is, the path where the dataClay command line utility saved our stub classes after calling GetStubs operation.  
**DataSetForStore** specifies which dataset the application will use in case a makePersistent request is produced to store a new object in the system, and **DataSets** provide information about the datasets the application will access (normally it includes the DataSetForStore).  
**LocalBackend** defines the default backend that the application will access when using either DataClay.LOCAL in Java or api.LOCAL in Python.

### Client properties

This file contains the minimum service info to connect applications with dataClay. It is also loaded automatically during the initialization process and its default path is ***./cfgfiles/client.properties***, which can be overriden by setting the environment variable DATACLAYCLIENTCONFIG.

```Properties
HOST=127.0.0.1
TCPPORT=11034
```

As you can see, it only requires two properties to be defined: HOST and TCPPORT; comprising the full address to be resolved in order to initialize a session with dataClay from your application.

## Application cycle

Before executing our application in Java or Python, some steps need to be done in order for the application to run using dataClay and store its data in a persistent state. For that matter, we are going to use ***dataclaycmd***, the dataClay command line utility intended to be used for management operations such as accounting, class registering, or contract creation.

Here is an example:

```bash
# To begin with, create an account
dataclaycmd NewAccount user s3ecret

# Create a dataset (with granted access)
# to register stored objects on it
dataclaycmd NewDataContract user s3ecret myDataset user

# Register the class moddel in a certain namespace
# Assuming Person.class or person.py is in ./modelClassDirPath
dataclaycmd NewModel user s3ecret myNamespace ./modelClassDirPath <java | python>

# Download the corresponding stubs for your application
dataclaycmd GetStubs user s3ecret myNamespace ./stubs
```

You can check all the options with `dataclaycmd --help`

### Build and run the application

To run a dataClay application, we just need i) to make sure that it is using the stubs instead of
the original class files and ii) to create two configuration files that specify our account, datasets,
stubs path and connection info.

You can find several sample applications in [dataclay-examples](https://github.com/bsc-dom/dataclay-examples) and [dataclay-demos](https://github.com/bsc-dom/dataclay-demos).

<!-- ## Tracing -->

<!-- ## Federation -->

## Documentation

- [dataClay Python documentation](https://pyclay.readthedocs.io/en/latest/)
- [BSC official dataClay webpage](https://www.bsc.es/research-and-development/software-and-apps/software-list/dataclay/documentation)
