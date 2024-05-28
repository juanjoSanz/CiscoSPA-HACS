"""
Support for Cisco ATAs for VOIP systems

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/sensor.ciscospa/
"""
from __future__ import annotations
from pyciscospa import CiscoClient
from pyciscospa.client import PyCiscoSPAError

import datetime
import logging
from datetime import timedelta

import requests
import voluptuous as vol


from homeassistant.components.sensor import (
    PLATFORM_SCHEMA,
    SensorEntity,
)

from homeassistant.helpers.entity import Entity
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import Throttle
from homeassistant.const import (
    CONF_USERNAME, CONF_PASSWORD,
    CONF_NAME, CONF_MONITORED_VARIABLES, CONF_HOST)
import homeassistant.helpers.config_validation as cv


REQUIREMENTS = ['pyciscospa==0.1.4']


_LOGGER = logging.getLogger(__name__)

SENSOR_TYPES = {
    'registration_state': ['Registration state', '', 'mdi:phone'],
    'hook_state': ['Hook state', '', 'mdi:phone'],
    'last_called_number': ['Last called number', '', 'mdi:phone'],
    'last_caller_number': ['Last caller number', '', 'mdi:phone'],
    'call_state': ['Call state', '', 'mdi:phone'],
    'call_duration': ['Call duration', '', 'mdi:phone'],
    'call_type': ['Call type', '', 'mdi:phone'],
    'call_peer_phone': ['Call peer phone', '', 'mdi:phone'],
    'call_peer_name': ['Call peer name', '', 'mdi:phone'],

}

DEFAULT_NAME = 'Phone'

SCAN_INTERVAL = datetime.timedelta(seconds=10)



PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_MONITORED_VARIABLES):
        vol.All(cv.ensure_list, [vol.In(SENSOR_TYPES)]),
    vol.Required(CONF_HOST): cv.string,
    vol.Optional(CONF_USERNAME, default='admin'): cv.string,
    vol.Optional(CONF_PASSWORD, default='admin'): cv.string,
    vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string
})


def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None=None,
) -> None:    
    """Set up the Cisco SPA sensor."""

    hostname = config.get(CONF_HOST)
    username = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    name = config.get(CONF_NAME)

    try:
        cisco_data = CiscoData(hostname, username, password)
        cisco_data.update()
    except requests.exceptions.HTTPError as error:
        _LOGGER.error("Failed login: %s", error)
        return False
    
    sensors = []
    for line in cisco_data.client.phones():
        for variable in config[CONF_MONITORED_VARIABLES]:
            sensors.append(CiscoSPASensor(cisco_data, variable, name,
                                          line['line']))

    _LOGGER.info("Loading sensors %s", sensors)
    add_entities(sensors, update_before_add=True)
    


class CiscoSPASensor(SensorEntity):
    """Representation of a Sensor."""

    def __init__(self, cisco_data, sensor_type, name, line):
        """Initialize the sensor."""
        self.client_name = name
        self._line = line
        self.type = sensor_type
        self._name = SENSOR_TYPES[sensor_type][0]
        self._unit_of_measurement = SENSOR_TYPES[sensor_type][1]
        self._icon = SENSOR_TYPES[sensor_type][2]
        self.cisco_data = cisco_data
        self._state = None

    @property
    def name(self):
        """Return the name of the sensor."""
        return '{} {} {}'.format(self.client_name, self._line, self._name)

    @property
    def state(self):
        """Return the state of the sensor."""
        return self._state

    @property
    def unit_of_measurement(self):
        """Return the unit of measurement of this entity, if any."""
        return self._unit_of_measurement

    @property
    def icon(self):
        """Icon to use in the frontend, if any."""
        return self._icon

    @property
    def device_state_attributes(self):
        """Return the state attributes of the sensor."""
        return {
            'line': self._line,
        }

    def update(self):
        """Get the latest data from Cisco SPA and update the state."""
        _LOGGER.info("Updating sensor %s", self._name)
        self.cisco_data.update()
        if self.type in self.cisco_data.data[self._line-1]:
            self._state = self.cisco_data.data[self._line-1][self.type]


class CiscoData(object):
    """Get data from Cisco."""

    def __init__(self, hostname, username, password):
        """Initialize the data object."""
        self.client = CiscoClient(hostname, username, password)
        self.data = {}
        
        # Apply throttling to methods using configured interval
        self.update = Throttle(SCAN_INTERVAL)(self._update)

        
    def _update(self):
        """Get the latest data from Cisco SPA."""
        try:
            self.client.phones()
        except PyCiscoSPAError as err:
            _LOGGER.error("Error on receive last Cisco SPA data: %s", err)
            return
        # Update data
        self.data = self.client.phones()
