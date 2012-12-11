"""
The classes of the forwarders.sign_direct module refer to resources in the
/sign-direct/ space. They all use a layers.SignDirect object as the backend
"""

from allocator_forwarder import AllocatorForwarder

resources = {'allocation-table': AllocatorForwarder}