# Cisco SPA Sensor Support for Home Assistant

Sensor for Cisco SPA devices  
### Setup


Example configuration.yaml entry

```
sensor:
  - platform: ciscospa
    host: 192.168.1.6
    monitored_variables:
      - registration_state
      - hook_state
      - last_called_number
      - last_caller_number
      - call_state
      - call_peer_name
      - call_peer_phone
      - call_type
      - call_duration
```