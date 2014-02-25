#!/usr/bin/env python

import sys
import os
from argparse import ArgumentParser
import json
import yaml

from stem.descriptor.reader import DescriptorReader

if __name__ == "__main__":
    aparser = ArgumentParser(description="Generate monthly reports for exit\
                                          relays")

    aparser.add_argument("hosts", help="yaml file containing addresses and \
                                        fingerprints")
    aparser.add_argument("descriptors", help="descriptor dir containing the \
                                             base data")
    
    args = aparser.parse_args()

    try:
        with open(args.hosts) as f:
            hosts = yaml.load(f.read())
    except IOError:
        print("[!] Could not read hosts file.")
        sys.exit(-1)
    except yaml.ReaderError:
        print("[!] Error parsing YAML file.")
        sys.exit(-1)
        
    fingerprints = []
    for hostname in hosts:
        fingerprints.extend(hosts[hostname])
        
    print("[i] %i fingerprints found." % len(fingerprints))
        
    descriptors = {}
    with DescriptorReader(args.descriptors) as reader:
        for descriptor in reader:
            if descriptor.fingerprint in fingerprints:
                try:
                    descriptor_data = {
                        'nickname': descriptor.nickname,
                        'read_history_end': descriptor.read_history_end.strftime("%s"),
                        'read_history_interval': descriptor.read_history_interval,
                        'read_history_values': descriptor.read_history_values, 
                        'write_history_end': descriptor.write_history_end.strftime("%s"),
                        'write_history_interval': descriptor.write_history_interval,
                        'write_history_values': descriptor.write_history_values,
                    }

                    if descriptor.fingerprint not in descriptors.keys():
                        descriptors[descriptor.fingerprint] = [ descriptor_data ]
                    else:
                        descriptors[descriptor.fingerprint].append(descriptor_data)
                    print("[i] found descriptor for fingerprint %s (%i/%i)" % 
                          (descriptor.fingerprint, len(descriptors), len(fingerprints)))
                except AttributeError:
                    print("[i] found descriptor without traffic history")
                    
    with open("data.json", "w") as f:
        f.write(json.dumps(descriptors))
