
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)


Monitor the ZyXEL LTE5398 M904 modem router.
Login credentials are required.

# Compatibility

Tested with: 

- ZyXEL LTE5398-M904

Should be compatible with similar models.

# HACS version (suggested)
## Installation
- add ZyXEL LTE5398 M904 as a [custom repository](https://hacs.xyz/docs/faq/custom_repositories/)
- in HACS, search for `ZyXEL LTE5398 M904` and install the latest release
- in Home Assistant, add the `ZyXEL LTE5398 M904` integration, insert the `ip-address`, `username` and `password` and follow the instructions  

# Stand-alone version

## Installation 

To use this plugin, copy the `zyxel_lte5398_m904_stand_alone` folder into your [custom_components folder](https://developers.home-assistant.io/docs/en/creating_component_loading.html).

## Stand-alone configuration 

```yaml
# Example configuration.yaml entry
zyxel_lte5398_m904_stand_alone:  
  ip_address: !secret zyxel_lte5398_m904_stand_alone_addr
  username: !secret zyxel_lte5398_m904_stand_alone_user
  password: !secret zyxel_lte5398_m904_stand_alone_pass  
```
