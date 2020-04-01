Implementation of RPKI Origin Validation in route-map
=====================================================

A substitute for the RTR protocol: generate configuration blobs for your
routers instead of using the RTR protocol to interact with RPKI.

The generated `route-map` configuration will first check whether the BGP route
announced and passed through the `route-map` is covered by a RPKI ROA or not,
if not it will mark the route as `not-found` using the `65000:0` BGP community.

If the route _was_ covered by a RPKI ROA, the `route-map` proceeds to match
the announcement against each authorised (Prefix, Origin AS) tuple to see
if any RPKI ROA can make the BGP announcement valid. If there is no match, the
annnouncement is RPKI Invalid and will be rejected.

Example
-------

An example generated `route-map` configuration is available [here](https://raw.githubusercontent.com/job/rpki-ov-route-map/master/example-route-map-configuration.txt).

Installation
------------

```
git clone https://github.com/job/rpki-ov-route-map
cd rpki-ov-route-map
python3 -m venv .venv
. .venv/bin/activate
pip3 install -e .
```

Use
---

Some BGP implementations don't have native support for RPKI based BGP Origin
Validation [RFC 6811](https://tools.ietf.org/html/rfc6811), this utility
attempts to offer a workaround for `route-map` oriented BGP implementations.

```
$ rpki-ov-route-map > route-map-configuration.txt
```


Copyright (c) April 1st, 2020 Job Snijders <job@instituut.net>
