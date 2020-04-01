#!/usr/bin/env python3
# rpki_ov_route_map - A RTR Substitution
#
# Copyright (C) 2016-2018 Job Snijders <job@instituut.net>
#
# This file is part of rpki_ov_route_map
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
# this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation
# and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from aggregate6 import aggregate
from ipaddress import ip_network

import argparse
import collections
import json
import pprint
import requests
import rpki_ov_route_map
import sys


def main():
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-c', dest='cache',
                        default="https://rpki.gin.ntt.net/api/export.json",
                        type=str,
                        help="""Location of the RPKI Cache in JSON format
(default: https://rpki.gin.ntt.net/api/export.json)""")

    parser.add_argument('-v', '--version', action='version',
                        version='%(prog)s ' + rpki_ov_route_map.__version__)

    args = parser.parse_args()

    if 'http' in args.cache:
        r = requests.get(args.cache, headers={'Accept': 'text/json'})
        validator_export = r.json()
    else:
        validator_export = json.load(open(args.cache, "r"))

    print("""!
ip bgp-community new-format
no ip community-list rpki-not-found
ip community-list standard rpki-not-found permit 65000:0
no ip community-list rpki-valid
ip community-list standard rpki-valid permit 65000:1
no ip community-list rpki-invalid
ip community-list standard rpki-invalid permit 65000:2
no ip community-list rpki
ip community-list expanded rpki permit 65000:[123]
!""")
    data = dict()
    data['vrps'] = load_vrp_list(validator_export)
    data['origins'] = collections.defaultdict(set)

    covered_space = set()

    for vrp in data['vrps']:
        covered_space.add(vrp['prefix'])
        if vrp['prefixlen'] == vrp['maxlen']:
            entry = vrp['prefix']
        else:
            entry = "{} le {}".format(vrp['prefix'], vrp['maxlen'])
        data['origins'][vrp['origin']].add(entry)

    print("no ip prefix-list rpki-covered-space-v4")

    for i in aggregate(covered_space):
        print("ip prefix-list rpki-covered-space-v4 permit {} le 32".format(i))
    print("!")

    for origin, prefixes in data['origins'].items():
        if origin == 0:
            continue
        print("!")
        print("no ip prefix-list rpki-origin-AS{}".format(origin))
        for prefix in prefixes:
            print("ip prefix-list rpki-origin-AS{} permit {}".format(origin,
                                                                     prefix))
        print("!")
        print("no ip as-path access-list {}".format(origin))
        print("ip as-path access-list {} permit _{}$".format(origin, origin))

    print("""!
! test whether BGP NLIR is covered by RPKI ROA or not
route-map rpki-ov permit 1
 match ip address prefix-list rpki-covered-space-v4
 set comm-list rpki delete
 continue 3
!
! BGP announcement is not covered by RPKI ROA, mark as not-found and exit
route-map rpki-ov permit 2
 set comm-list rpki delete
 set community 65000:0 additive
!
! find RPKI valids""")

    n = 3

    for origin in data['origins'].keys():
        if origin == 0:
            continue
        print("!")
        print("route-map rpki-ov permit {}".format(n))
        print(" match ip prefix-list rpki-origin-AS{}".format(origin))
        print(" match as-path {}".format(origin))
        print(" set community 65000:1")
        n += 1

    print("!")
    print("! Reject RPKI Invalid BGP announcements")
    print("route-map rpki-ov deny {}".format(n))

# phase 3 reject invalids

def load_vrp_list(export):
    """
    :param export:  the JSON blob with all ROAs
    """

    vrp_list = []

    for vrp in export['roas']:
        prefix_obj = ip_network(vrp['prefix'])
        if prefix_obj.version == 6:
            continue

        try:
            asn = int(vrp['asn'].replace("AS", ""))
            if not 0 <= asn < 4294967296:
                raise ValueError
        except ValueError:
            print("ERROR: ASN malformed", file=sys.stderr)
            print(pprint.pformat(vrp, indent=4), file=sys.stderr)
            continue

        prefix = str(prefix_obj)
        prefixlen = prefix_obj.prefixlen
        maxlength = int(vrp['maxLength'])

        vrp_list.append((prefix, prefixlen, maxlength, asn))

    vrp_list_uniq = []
    for vrp in set(vrp_list):
        vrp_list_uniq.append({'prefix': vrp[0], 'prefixlen': vrp[1],
                              'maxlen': vrp[2], 'origin': vrp[3]})

    return vrp_list_uniq
