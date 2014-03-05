#!/usr/bin/env python

from argparse import ArgumentParser
import yaml
import json
from datetime import datetime

import pygal
import jinja2

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
            (timestamps[0], 
             sum(read_bytes)/len(read_bytes),
             sum(written_bytes)/len(written_bytes)))
    return partitioned_data

    
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
        
        #clean up entries
        for dataset in partitioned_data:
            while datetime.fromtimestamp(int(dataset[0][0])).date().day > 28:
                import pdb; pdb.set_trace()
                dataset.pop(0)


        chart = pygal.StackedLine(fill=True, interpolate="hermite",
                                  style=pygal.style.LightStyle,
                                  legend_at_bottom=True,
                                  show_dots=False,
                                  y_title="MByte/s",
                                  x_title="Days")
        #chart.title = host
        chart.x_labels = []
        for x in zip(range(len(partitioned_data[0])), partitioned_data[0]):
            chart.x_labels.append(datetime.fromtimestamp(int(x[1][0]))
                                  .strftime("%d"))

        for number, process in zip(range(len(partitioned_data)), partitioned_data):
            chart.add("Process %i" % number, [ float(x[1] + x[2]) / 900 / 1024**2 for x in process ])
            
        chart.render_to_file("report/graphs/%s.svg" % host)
        
        
    # calculate averages by physical host
    host_averages = {}
    for host in hosts.keys():
        process_averages = []
        for process in hosts[host]:
            process_averages.append(
                float(sum([ p[1] + p[2] for p in process ]))/900/1024**2/len(process)
            )
        host_averages[host] = round(sum(process_averages),2)
    total_average = sum([host_averages[host] for host in host_averages.keys()])
    
    # calculate accumulated traffic
    host_accumulated = {}
    for host in hosts.keys():
        process_sums = []
        for process in hosts[host]:
            process_sums.append(float(sum([ p[1] + p[2] for p in process ]))/1024**4)
        host_accumulated[host] = round(sum(process_sums),2)
    host_accumulated_total = sum([host_accumulated[host] for host in host_accumulated.keys()])

    # generate html page
    with open("templates/main.jinja.html") as f:
        template = jinja2.Template(f.read())

    with open("report/index.html", "w") as f:
        f.write(template.render(
            hosts=hosts.keys(),
            host_averages=host_averages,
            total_average=total_average,
            host_accumulated=host_accumulated,
            host_accumulated_total=host_accumulated_total
        ))
