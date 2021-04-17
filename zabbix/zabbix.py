#!/usr/bin/env python
# coding=utf-8

import configparser
from pyzabbix import ZabbixAPI
import time
import json


class Zabbix(object):

    def __init__(self):
        self.__get_server_config()
        self.__login()

    def __get_server_config(self):
        self.config = configparser.ConfigParser()
        self.config.read('prod.cfg')

        self.server_address = self.config.get('ZABBIX', 'SERVER')
        self.api_user = self.config.get('ZABBIX', 'API_USER')
        self.api_pass = self.config.get('ZABBIX', 'API_PASSWORD')

    def __login(self):
        self.zabbix = ZabbixAPI(self.server_address)
        self.zabbix.login(self.api_user, self.api_pass)

    def get_hostgroups(self, params=None):
        return [hostgroup for hostgroup
                in self.zabbix.hostgroup.get(output=['name', 'groupid'])]

    def get_hosts_by_hostgroup(self, hostgroup):
        return [host for host
                in self.zabbix
                .host.get(output=['name', 'hostid'],
                          groupids=['{}'
                                    .format(hostgroup[0])])]

    def get_active_triggers_by_hostgroup(self, hostgroup):
        return [trigger for trigger
                in self.zabbix
                .trigger.get(output=['hosts', 'description'],
                             only_true=1,
                             skipDependent=1,
                             monitored=1,
                             active=1,
                             selectHosts='extend',
                             expandDescription=1,
                             expandData='host',
                             group=hostgroup)]

    def get_sla(self, params=None):
        services = self.zabbix.service.get(
            output="extend", selectDependencies="extend")
        service_list = json.loads(json.dumps(services))
        response = ""
        timestampnow = time.time()

        for service in service_list:
            sla = json.loads(json.dumps(self.zabbix.service.getsla(
                serviceids=service["serviceid"],
                output="extend",
                intervals=[{"from": timestampnow -
                            2628000, "to": timestampnow}]
            )))

            sla_percentage = str(sla[service["serviceid"]]['sla'][0]['sla'])
            response += "\t\nSLA {} = ".format(
                service["name"]) + sla_percentage + "%"

        return response

    def get_events(self):
        return [trigger for trigger
                in self.zabbix
                .trigger.get(output="extend",
                             sortfield=['lastchange'],
                             sortorder="DESC",
                             withUnacknowledgedEvents=1,
                             only_true=1,
                             monitored=1,
                             active=1,
                             value=1,
                             selectHosts='extend',
                             selectLastEvent=1,
                             expandDescription=1,
                             expandData='host',
                             limit=5)]

    def set_acknowledge(self, eventid, message):
        self.zabbix.event.acknowledge(eventids=eventid, message=message)
