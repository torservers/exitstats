# exitstats #

Generate statistics for tor exit relays.

## how to use ##

### Prerequisites ###

In order to run the script you need the following things:

* Python installation
* `python-yaml`
* [stem](https://stem.torproject.org/)

### 0. Acquire hosts.yaml ###

See `hosts.yaml.example` for an example. If you use ansible, you also may use the
script in `tools/get_fingerprints.py` for acquiring all your fingerprints

### 1. Acquire Extra-Info descriptors ###

Get them at <http://metrics.torproject.org/data.html>

### 2. Extract relevant data ###

`extract_data.py hosts.yaml <descriptor_package>`

where `<descriptor_package>` obviously is the absolute or relative (from your working
directory) path to the descriptor file (or folders, unpacking the descriptor archives
makes sifting through them way faster).

### 3. Paint nice graphs ###

`generate_report.py hosts.yaml data.json`

your graphs are now in the graphs directory.
