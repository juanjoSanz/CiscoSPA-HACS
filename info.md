# Cisco SPA Sensor Support for Home Assistant

Sensor for Cisco SPA devices  
### Setup


Example configuration.yaml entry

```
sensor:
    - platform: cisco_spa
      host: 10.0.1.2
      username: !secret ciscospa_user
      password: !secret ciscospa_password
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

