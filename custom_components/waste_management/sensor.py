"""Sensor platform for Waste Management Pickup."""
import datetime
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, CONF_ACCOUNT, CONF_SERVICES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config, add_entities):
    """Set up the sensor platform."""
    domain_data = hass.data[DOMAIN][config.entry_id]
    coordinator = domain_data["coordinator"]
    service_names = domain_data["service_names"]
    
    config_data = config.data
    account_id = config_data[CONF_ACCOUNT]
    
    entities = []
    for svc_id in config_data[CONF_SERVICES]:
        # Fallback to the service ID if the name can't be found
        name = service_names.get(svc_id, f"WM Service {svc_id}")
        entities.append(
            WasteManagementSensorEntity(coordinator, name, account_id, svc_id)
        )
        
    add_entities(entities)


class WasteManagementSensorEntity(CoordinatorEntity, SensorEntity):
    """Representation of a Waste Management Sensor."""

    def __init__(self, coordinator, name, account_id, service_id):
        """Initialize the sensor."""
        # Pass coordinator to CoordinatorEntity
        super().__init__(coordinator)
        
        self._attr_has_entity_name = True
        self.account_id = account_id
        self.service_id = service_id

        self._attr_name = name
        self._attr_unique_id = f"{account_id}_{service_id}"
        self._attr_icon = "mdi:trash-can"
        # Using the modern Enum instead of the deprecated raw string
        self._attr_device_class = SensorDeviceClass.TIMESTAMP

    @property
    def native_value(self):
        """Return the state of the sensor."""
        # Extract the specific pickup list for this service_id from the coordinator data
        pickup = self.coordinator.data.get(self.service_id)
        
        if not pickup:
            return None
            
        today = datetime.date.today()
        proposed_pickup = pickup[0].astimezone()
        
        # If the first pickup date is in the past and we have upcoming ones, use the next one
        if proposed_pickup.date() < today and len(pickup) > 1:
            proposed_pickup = pickup[1].astimezone()
            
        return proposed_pickup
