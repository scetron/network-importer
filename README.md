# Network Importer

The network importer is a tool/library to analyze and/or synchronize an existing network with a Network Source of Truth (SOT), it's designed to be idempotent and by default it's only showing the difference between the running network and the remote SOT. 

The main use cases for the network importer: 
 - Import an existing network into a SOT (Netbox) as a first step to automate a brownfield network
 - Check the differences between the running network and the Source of Truth

## Getting Started

### Install

The Network Importer can be installed from pypi or from a wheel

```
# NOT PUBLISHED YET
pip install network-importer
```

### Pre-requisite

To operate, the Network Importer is dependents on the following items:
- A device inventory (defined in NetBox for now)
- Batfish 
- A valid configuration file

#### Inventory

A device inventory must be already available in NetBox, if you don't have your devices in NetBox yet you can use the [onboarding plugin for NetBox](https://github.com/networktocode/ntc-netbox-plugin-onboarding/) to easily import your devices. 

To be able to connect to the device the following information needs to be defined in NetBox:
- Primary ip address
- Platform (must be a valid netmiko driver or have a valid napalm driver defined)
> Connecting to the device is not mandatory but some features depends on it: configuration update, mostly cabling and potentially vlan update.

#### Bafish

The Network Importer requires to have access to a working batfish environment, you can easily start one using docker or use a Batfish Enterprise instance.

You can start a local batfish instance with the following command : `docker run -d -p 9997:9997 -p 9996:9996 batfish/batfish:2020.10.08.667`

#### Configuration file

The information to connect to NetBox must be provided either via environment variables or via the configuration file.
The configuration file below present the most standard options that can be provided to control the behavior of the Network Importer.

```toml
[main]
# import_ips = true 
# import_prefixes = false
# import_cabling = "lldp"       # Valid options are ["lldp", "cdp", "config", false]
# import_transceivers = false 
# import_intf_status = true     # If set as False, interface status will be ignore all together
# import_vlans="config"         # Valid options are ["cli", "config", true, false]
# excluded_platforms_cabling = ["cisco_asa"]

# Directory where the configurations can be find, organized in Batfish format
# configs_directory= "configs"

[inventory]
# Limit the scope of the inventory to a subset of devices
# Accept any parameters supported by NetBox devices API
# filter = "site=nyc,role=router"
# filter = ""

# Define a list of supported platform, 
# if defined all devices without platform or with a different platforms will be removed from the inventory
# supported_platforms = [ "cisco_ios", "cisco_nxos" ]

[netbox]
# The information to connect to netbox needs to be provided, either in the config file or as environment variables
address = "http://localhost:8080"                   # Alternative Env Variable : NETBOX_ADDRESS
token = "113954578a441fbe487e359805cd2cb6e9c7d317"  # Alternative Env Variable : NETBOX_TOKEN
verify_ssl = true                                   # Alternative Env Variable : NETBOX_VERIFY_SSL

[network]
# To be able to pull live information from the devices, the credential information needs to be provided
# either in the configuration file or as environment variables ( & NETWORK_DEVICE_PWD)
login = "username"      # Alternative Env Variable : NETWORK_DEVICE_LOGIN
password = "password"   # Alternative Env Variable : NETWORK_DEVICE_PWD

[batfish]
address= "localhost"   # Alternative Env Variable : BATFISH_ADDRESS
# api_key = "XXXX"      # Alternative Env Variable : BATFISH_API_KEY
# use_ssl = false

[logs]
# Define log level, curently the logs are printed on the screen
# level = "info" # "debug", "info", "warning"
```

### Execute

The network importer can run either in `check` mode or in `apply` mode. 
 - In `check` mode, no modification will be made to the SOT, the differences will be printed on the screen
 - in `apply` mode, the SOT will be updated will all interfaces, IPs, vlans etc

#### Check Mode

In check mode the Network Importer is working in read-only mode.

The first time, it's encouraged to run the Network Importer in `--check` mode to garantee that no change will be made to the SOT.

```
network-importer --check --diff [--update-configs] [--limit="site=nyc"]
```
This command will print on the screen a list of all changes that have been detected between the Network and the SOT.

#### Apply Mode

If you are confident with the changes reported in check mode, you can run the Network Importer in apply mode to update your SOT to align with your network. The network importer will attempt to create/update or delete all elements in the SOT that do not match what has been observed in the network.

```
network-importer --apply [--update-configs] [--limit="site=nyc"]
```

> Running in Apply mode may result in loss of data in your SOT, as the network importer will attempt to delete all Interfaces and Ip addresses that are not present in the network. 
> Before running in Apply mode, it's highly encouraged to do a backup of your database.

## How does it work

The Network Importer is using different tools to collect information from the network devices: 
- [batfish](https://github.com/batfish/batfish) to parse the configurations and extract a vendor neutral data model. 
- [nornir], [napalm], [netmiko] and [ntc-templates] to extract some information from the device cli if available


## Development
In addition to the supplied Makefile you can also use `docker-compose` to bring up the required service stack. Like so:
```
sudo docker-compose up -d
sudo docker-compose exec network-importer bash
sudo docker-compose down
```
