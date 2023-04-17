Main Concepts
=============


What is dataClay
----------------

dataClay [MARTI2017129, MartiFraiz2017] is a distributed object store that enables programmers to handle object persistence using the same model they use in their object-oriented applications, thus avoiding time consuming transformation between persistent and non persistent models. In other words, dataClay enables applications to store objects in the same format they have in memory. This can be done either using the standard GET/PUT/UPDATE methods of standard object stores, or by just calling the makePersistent method on an object that will enable applications to access it, in the same way, regardless of whether it is loaded in memory or persisted in disk (you just follow the object reference). In addition, dataClay simplifies and optimizes the idea of moving computation close to data (see Section 1.3) by enabling the execution of methods in the same node where a given object is located. dataClay also optimizes the idea of sharing data and models (set of classes) between different users by means of storing the class (including method definition) together with the object.


Basic terminology
-----------------

In this section we present a brief terminology that is used throughout the manual:

- **Object**, as in object oriented programming, refers to a particular instance of a class.
- **dataClay application** is any application that uses dataClay to handle its persistent data.
- **Backend** is a node in the system that is able to handle persistent objects and execution requests. These nodes need to be running the dataClay platform on them. We can have as many as we need either for capacity or parallelism reasons.
- **Clients** are the machines where dataClay applications run. These nodes can be very thin. They only need to be able to run Java or Python code and to have the dataClay lib installed.
- **dataClay object** is any object stored in dataClay.
- **Objects with alias** are objects that have been explicitly named (much in the same way we give names to files). Not all dataClay objects need to have an alias (a name). If an object has an alias, we can access it by using its name. On the other hand, objects without an alias can only be accessed by a reference from another object.
- **Dataset** is an abstraction where many objects are grouped. It is indented to simplify the task of sharing objects with other users.

Execution model
---------------

As we have mentioned, one of the key features of dataClay is to offer a mechanism to bring computation closer to data. For this reason, all methods of a dataClay object will not be executed in the client (application address space) but on the backend where dataClay stored the object. Thus, searching for an object in a collection will not imply sending all objects in the collection to the client, but only the final result because the search method will be executed in the backend. If the collection is distributed among different backends, any sub-method required to check whether objects match certain conditions or not, will be executed on the involved backends. It is important to notice that this execution model does not prevent developers to use the standard object store model by using GET/PUT/UPDATE methods. In particular, a GET method (as CLONE in dataClay to match with object oriented terminology), will bring the object to the application address space and thus all methods will be executed locally. At this point, any application object either retrieved (CLONED) from dataClay or created by the application itself, can be either PUT into the system to save it or can be used to UPDATE an existing stored object.


Tasks and roles
---------------

In order to rationalize the different roles that take part in data-centric applications, such as the ones
supported by dataClay, we assume two different roles.

- **Model providers** design and implement class models to define the elements of data (data structure), their relationships, and methods (API) that applications can use to access and process it.
- **Application developers** use classes developed by the model provider in order to build applications. These applications can either create and store new objects or access data previously created.

Although dataClay encourages these roles in the cycle of applications, they do not have to be
declared as such and, of course, they can be assumed by a single person.

Memory Management and Garbage Collection
----------------------------------------

Every backend in dataClay maintains a daemon process that checks if memory usage has reached a certain threshold and, if this is the case, it flushes those objects that are not referenced into the underlying storage. On the other hand, dataClay also performs background garbage collection to remove those objects that are no longer accessible. More specifically, dataClay deploys a distributed garbage collection service, involving all the backends, to periodically collect any object meeting the following conditions:

1. The object is not pointed by any other object.
2. The object has no aliases.
3. There is no user application referencing the object.
4. There is no backend accessing the object from a running execution method.


Federation
----------

In some scenarios, such as edge-to-cloud deployments, part of the data stored in a dataClay instance has to be shared with another dataClay instance running in a different device. An example can be found in the context of smart cities where, for instance, part of the data residing in a car is temporarily shared with the city the car is traversing. This partial, and possibly temporal, integration of data between independent dataClay instances is implemented by means of dataClay’s federation mechanism. More precisely, federation consists in replicating an object (either simple or complex, such as a collection of objects) in an independent dataClay instance so that the recipient dataClay can access the object without the need to contact the owner dataClay. This provides immediate access to the object, avoiding communications when the object is requested and overcoming the possible unavailability of the data source.
