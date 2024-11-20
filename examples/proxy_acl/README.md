## Proxy 


This example shows how the proxy works. 

We will have different clients and a whitelist which will allow each user to use specific methods.

The whitelist is set in the [proxy_config.py](https://github.com/bsc-dom/dataclay/blob/f96dcbc645a0223b8c0d291ee4e553c1f0853e58/examples/proxy_acl/proxy_config.py) file.

With the [middleware.py](https://github.com/bsc-dom/dataclay/blob/f96dcbc645a0223b8c0d291ee4e553c1f0853e58/examples/proxy_acl/middleware.py) we define a specific behavior for the proxy service. In this example we can find that the call_active_method(), get(), set() and del() methods have been defined. The workflow is the the following->

For each user in the whitelist:
- Check if the user we are currently checking is the one who requested the method.
- If it's the correct user, then we check if the user has the method in its whitelist.
- If it has it, then we check if the authorization (JWT) is correct.

If the user doesn't have the desired method in the whitelist or the authorization fails, then an exception is raised. 


For each client_XXXX.py we have the line <code>client = Client(proxy_host="127.0.0.1", username="XXXX", password="s3cret")</code> which defines the client name.

- [client_alice.py](https://github.com/bsc-dom/dataclay/blob/f96dcbc645a0223b8c0d291ee4e553c1f0853e58/examples/proxy_acl/client_alice.py): Initializes the SensorValues() class and makes it persistent. Then runs a few functions, but when it tries to do "public_data()" it fails because the whitelist doesn't allow it.
- [client_bob.py](https://github.com/bsc-dom/dataclay/blob/f96dcbc645a0223b8c0d291ee4e553c1f0853e58/examples/proxy_acl/client_bob.py): Run a few functions and then, when trying to use the "add_element(2.4)" function, it fails. 
- [client_charlie.py](https://github.com/bsc-dom/dataclay/blob/f96dcbc645a0223b8c0d291ee4e553c1f0853e58/examples/proxy_acl/client_charlie.py): As Charlie is in the whitelist, but he doesn't have any function in it, when it tries to call a function from the call_active_method, get, set or delete it fails.
- [client_owner.py](https://github.com/bsc-dom/dataclay/blob/f96dcbc645a0223b8c0d291ee4e553c1f0853e58/examples/proxy_acl/client_owner.py): When a client is not added to the whitelist then it's considered an owner and every function will be allowed.
