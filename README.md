Implementation of RPKI Origin Validation in route-map
=====================================================

A substitute for the RTR protocol: generate configuration blobs for your
routers instead of using the RTR protocol to interact with RPKI.

Installation
------------

`pip3 install rpki-ov-route-map`

Use
---

Some BGP implementations don't have native support for RPKI based BGP Origin
Validation [RFC 6811](https://tools.ietf.org/html/rfc6811), this utility
attempts to offer a workaround for `route-map` oriented BGP implementations.

```
$ rpki-ov-route-map > route-map-configuration.txt
```

An example `route-map` configuration is available [here](https://raw.githubusercontent.com/job/rpki-ov-route-map/master/example-route-map-configuration.txt)

Copyright (c) 2020 Job Snijders <job@instituut.net>
