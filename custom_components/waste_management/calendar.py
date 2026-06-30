"""Calendar platform for Waste Management Pickup."""
import datetime
import logging

from homeassistant.components.calendar import CalendarEntity, CalendarEvent
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN, CONF_ACCOUNT, CONF_SERVICES

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(hass: HomeAssistant, config, add_entities):
    """Set up the calendar platform."""
    domain_data = hass.data[DOMAIN][config.entry_id]
    coordinator = domain_data["coordinator"]
    service_names = domain_data["service_names"]
    
    config_data = config.data
    account_id = config_data[CONF_ACCOUNT]
    
    # Check for selected services in options first, fallback to data
    services = config.options.get(CONF_SERVICES, config.data.get(CONF_SERVICES, []))

    name = config.title or "Waste Management"
    
    add_entities(
        [
            WasteManagementCalendar(
                coordinator, name, account_id, service_names, services
            )
        ]
    )

class WasteManagementCalendar(CoordinatorEntity, CalendarEntity):
    """Representation of a Waste Management Calendar."""

    def __init__(self, coordinator, name, account_id, service_names, active_services):
        """Initialize the calendar."""
        super().__init__(coordinator)
        self._attr_name = name
        self._attr_unique_id = f"{account_id}_calendar"
        self.account_id = account_id
        self.service_names = service_names
        self.active_services = active_services

    @property
    def device_info(self) -> DeviceInfo:
        """Return device information to link this entity to the device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self.account_id)},
            name=f"Waste Management ({self.account_id})",
            manufacturer="Waste Management"
        )

    @property
    def event(self) -> CalendarEvent | None:
        """Return the next upcoming calendar event."""
        events = self._get_all_events()
        if not events:
            return None
            
        today = datetime.date.today()
        # Filter for events that are happening today or in the future
        future_events = [e for e in events if e.start >= today]
        
        if not future_events:
            return None
            
        # Return the event with the closest start date
        return min(future_events, key=lambda e: e.start)

    def _get_all_events(self) -> list[CalendarEvent]:
        """Generate calendar events from the coordinator data."""
        if not self.coordinator.data:
            return []
            
        events = []
        for svc_id in self.active_services:
            pickups = self.coordinator.data.get(svc_id, [])
            svc_name = self.service_names.get(svc_id, f"WM Service {svc_id}")
            
            for pickup in pickups:
                pickup_date = pickup.astimezone().date()
                events.append(
                    CalendarEvent(
                        summary=svc_name,
                        start=pickup_date,
                        # All-day events in HA require the end date to be the day after the start date
                        end=pickup_date + datetime.timedelta(days=1),
                        description=f"{svc_name} Pickup scheduled for {pickup_date.strftime('%B %d, %Y')}"
                    )
                )
        return events

    async def async_get_events(
        self,
        hass: HomeAssistant,
        start_date: datetime.datetime,
        end_date: datetime.datetime,
    ) -> list[CalendarEvent]:
        """Return calendar events within a datetime range."""
        events = self._get_all_events()
        start_filter = start_date.date()
        end_filter = end_date.date()
        
        # Return events that fall within the requested view on the calendar dashboard
        return [
            event
            for event in events
            if event.start >= start_filter and event.start <= end_filter
        ]
