#!/bin/python

# Import parser for process command function
from argparse import ArgumentParser

# Import libcloud libs

import libcloud
from libcloud.common.types import LibcloudError
from libcloud.dns.drivers.google import GoogleDNSDriver
from libcloud.dns.types import RecordType
from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
from libcloud.compute.drivers.dummy import DummyNodeDriver

import requests

# Import Config File
from config import Config


# Instance Parser
parser = ArgumentParser(description='Script for DDNS on GCP', prog='gcp-ddns-cmd.py')
parser.add_argument('-p', '--project', dest='dns_project_name', help='GCP CE project', metavar='GCP CE Project', required='true')
parser.add_argument('-t', '--ttl', dest='a_record_ttl_seconds', help='TTL for DNS Record', metavar='TTL', required='true')
parser.add_argument('-r', '--record', dest='a_record_name', help='DNS Record Name', metavar='GCP Record Name', required='true')
parser.add_argument('-z', '--zone', dest='a_record_zone_name', help='Record Zone Name', metavar='GCP Record Zone Name', required='true')
parser.add_argument('-i', '--instace', dest='instance_name', help='GCP Instance Name', metavar='GCP Instance Name', required='true')
parser.add_argument('-d', '--datacenter', dest='dns_dc', help='GCP Data Center Name', metavar='GCP Data Center Name', required='true')


args = parser.parse_args()

Driver = get_driver(Provider.GCE)


class GoogleDNSUpdater:
    dns_driver = None

    def __init__(self):
        self.create_dns_driver()

    def create_dns_driver(self):
        self.dns_driver = GoogleDNSDriver(Config.DNS_USER_ID, Config.DNS_KEY, args.dns_project_name)

    def list_zones(self):
        return self.dns_driver.list_zones()

    def format_record_name(self, name, zoneDomain):
        return "{}.{}".format(name, zoneDomain)

    def get_record_id_for_record_name(self, zone, name):
        for record in self.dns_driver.list_records(zone):
            if record.type != RecordType.A:
                continue
            if self.format_record_name(name, zone.domain) == record.name:
                return record.id

    def create_or_update_record(self, zone=None, record_name=None, a_record_value=None, ttl_seconds=3600):
        if None in (zone, record_name, a_record_value):
            return False

        formatted_record_name = self.format_record_name(record_name, zone.domain)

        # Try locating existing record with the same name
        dns_record = None
        try:
            record_id = self.get_record_id_for_record_name(zone, record_name)
            if record_id:
                dns_record = self.dns_driver.get_record(zone.id, record_id)
        except LibcloudError as e:
            print("Error locating record: {}".format(e.message))

        # Set record data
        record_data = {
            "ttl": ttl_seconds,
            "rrdatas": [a_record_value]
        }

        # Create or update an existing record with record_data
        if not dns_record:
            return self.dns_driver.create_record(formatted_record_name, zone, RecordType.A, record_data)
        else:
            if self.dns_driver.delete_record(dns_record):
                return self.dns_driver.create_record(formatted_record_name, zone, RecordType.A, record_data)
            else:
                return False

    def update_record_ip(self, zone_name, record_name, ip, ttl_seconds):
        for zone in self.list_zones():
            if zone.domain == zone_name:
                print("Setting A record: {}.{} to point: {}".format(record_name, zone.domain, ip))
                return gdns.create_or_update_record(zone, record_name, ip, ttl_seconds)
        return False

class GoogleGceDriver:
    gce_drive = None

    def __init__(self):
        self.create_gce_driver()

    def create_gce_driver(self):
        self.gce_driver = Driver(Config.DNS_USER_ID, Config.DNS_KEY, args.dns_dc, args.dns_project_name)

    def list_nodes(self):
        return self.gce_driver.list_nodes()

    def get_wan(self, dns_instance):
            list_instances = self.list_nodes()
            pub_ip =  str([i.public_ips for i in list_instances if i.name == dns_instance])
            pub_ip = pub_ip.translate(None, "u[] '")
            return pub_ip

if __name__ == '__main__':
    ggce = GoogleGceDriver()
    pub_ip = ggce.get_wan(args.instance_name)
    gdns = GoogleDNSUpdater()
    result = gdns.update_record_ip(args.a_record_zone_name, args.a_record_name,
                                   pub_ip, args.a_record_ttl_seconds)
    print("SUCCESS" if result else "FAILURE")
