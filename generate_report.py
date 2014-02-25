#!/usr/bin/env python

from argparse import ArgumentParser
import yaml
import json
from datetime import datetime

import pygal

def chunks(arr, chunk_size = 10):
    chunks  = [ arr[start:start+chunk_size] for start in range(0, len(arr), chunk_size)]
    return chunks

def get_rwdata(descriptors):
    rwdata = []
    for desc in descriptors:
        timestamps = [ int(desc['read_history_end']) - ( x * desc['read_history_interval'] ) for x in range(len(desc['read_history_values'])) ]
        timestamps.reverse()
        rwdata.extend(zip(timestamps, desc['read_history_values'], desc['write_history_values']))
        
    rwdata.sort(key=lambda x: x[0])
    
    deduplicated_rwdata = []

    for data in rwdata:
        if not len(filter(lambda x: x[0] == data[0], deduplicated_rwdata)) > 0:
            deduplicated_rwdata.append(data)
    
    return deduplicated_rwdata

def partition_data(dataset, chunk_size):
    partitioned_data = []
    for chunk in chunks(dataset, chunk_size):
        timestamps = [ x[0] for x in chunk ]
        read_bytes = [ x[1] for x in chunk ]
        written_bytes = [ x[2] for x in chunk ]
        partitioned_data.append(
            (timestamps[len(chunk)/2], 
             sum(read_bytes)/len(read_bytes),
             sum(written_bytes)/len(written_bytes)))
    return partitioned_data

    
def generate_host_diagram(descriptor_data):
    timestamps = descriptor_data[0][0]
    
    ## prepare diagram data
    # add up data of 12 hours
    

    # thin out timestamps
    x_axis_labels = []
    for t in map(range(len(timestamps)), timestamps):
        if t[0] % 7 == 0:
            x_axis_labels.append(datetime.fromtimestamp(t[1]).strftime("%d-%m-%Y"))
        else:
            x_axis_labels.append(None)
        
if __name__ == "__main__":
    aparser  = ArgumentParser(description="generate reports")
    aparser.add_argument("datafile")
    aparser.add_argument("hostsfile")

    args = aparser.parse_args()
    with open(args.hostsfile) as f:
        hosts = yaml.load(f.read())
    
    with open(args.datafile) as f:
        data = json.loads(f.read())

    # associate physical hosts and data
    for host in hosts.keys():
        hosts[host] = [ get_rwdata(data[fingerprint]) for fingerprint in hosts[host] ]
        

    # partition and average data
    for host in hosts.keys():
        partitioned_data = map(lambda x: partition_data(x, chunk_size=96), 
                               hosts[host])
        chart = pygal.StackedLine(fill=True, interpolate="hermite")
        chart.title = host
        chart.x_labels = []
        for x in zip(range(len(partitioned_data)), partitioned_data):
            if x[0] % 7 == 0:
                chart.x_labels.append(datetime.fromtimestamp(int(x[1][0][0])).strftime("%d-%m-%Y"))

        for number, process in zip(range(len(partitioned_data)), partitioned_data):
            chart.add("Process %i" % number, [ float(x[1] + x[2]) / 900 / 1024**2 for x in process ])
            
        chart.render_to_file("graphs/%s.svg" % host)
