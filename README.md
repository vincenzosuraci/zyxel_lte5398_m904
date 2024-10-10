
[![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg?style=for-the-badge)](https://github.com/hacs/integration)


Monitor the ZyXEL LTE5398 M904 router.
Login credentials are required.

# Compatibility

Tested with: 

- ZyXEL LTE5398-M904

Should be compatible with similar models.

# HACS version

# Stand-alone version

## Installation 

To use this plugin, copy the `zyxel_lte5398_m904` folder into your [custom_components folder](https://developers.home-assistant.io/docs/en/creating_component_loading.html).

## Stand-alone configuration 

```yaml
# Example configuration.yaml entry
zyxel_lte5398_m904:  
  ip_address: !secret zyxel_lte5398_m904_addr
  username: !secret zyxel_lte5398_m904_user
  password: !secret zyxel_lte5398_m904_pass  
```
