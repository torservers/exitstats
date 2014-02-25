#!/usr/bin/env python

from argparse import ArgumentParser
from subprocess import check_output
import yaml

def get_fingerprints(user, host, port):
    res = check_output(["/usr/bin/ssh", "%s@%s" % (user, host), "-p %i" % port,
                        "python /opt/torservers/scripts/get_fingerprints.py"])
    fingerprints = []
    for line in res.split("\n"):
        if line != "":
            fingerprints.append(line)
    return fingerprints

if __name__ == "__main__":
    aparser = ArgumentParser(description="generate fingerprints file from\
                                          ansible inventory")
    aparser.add_argument("inventory", help="ansible inventory file")
    aparser.add_argument("outfile", help="output file path")
    
    args = aparser.parse_args()
    
    # read inventory file
    try:
        with open(args.inventory) as f:
            inventory_lines = f.readlines()
    except IOError:
        print("[!] could not open inventory file.")
        sys.exit(-1)

    # extract host information
    hosts = []
    for l in inventory_lines:
        if not l.startswith("["):
            hostline_elements = l.split()
            host_dict = {}
            for e in hostline_elements:
                if e.startswith("ansible_ssh_host"):
                    host_dict['address'] = e.split("=")[1]
                elif e.startswith("ansible_ssh_user"):
                    host_dict['user'] = e.split("=")[1]
                elif e.startswith("ansible_ssh_port"):
                    host_dict['port'] = int(e.split("=")[1])
            hosts.append(host_dict)
    print("[i] found %i hosts" % len(hosts))
    
    fingerprints = {}
    for h in hosts:
        fingerprints[h['address']] = get_fingerprints(h['user'], h['address'],
                                                      h['port'])
        
    print(yaml.dump(fingerprints))
    

        
