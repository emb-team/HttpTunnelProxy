proxy_tunnel

Proxy tunnel implementation

Known issues:

Epoll sometimes still generate events for descriptors that were already unregistered.
It happens under load. Server will complain:
: POLLIN event for removed fileno 48
