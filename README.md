SignServer
==========

An HTTP server for the sign board.

Implementation Notes:
---------------------

The two packages layers and forwarders do the bulk of the work. The layers
package contains the actual backend classes- they are responsible for taking
parsed data and using it to interact with the sign. The forwarders package
contains the forwarder classes, that act as the glue between the HTTP server
and the layers. The forwarders package has a dict, `layers`, that specifies all
of the layers that can be used. Each layer is itself a package with a dict
called resources that maps each resource to the appropriate handler class.