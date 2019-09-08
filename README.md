HTTP Tunnel Proxy implementation

The script setups HTTP Tunnel Proxy and redirects all trafic according to incoming request. Tested on Mozilla Firefox.

Known issues:

Epoll sometimes still generate events for descriptors that were already unregistered.
It happens under load. 
Server displays the following message ": POLLIN event for removed fileno 48"
