"""The Waste Management Pickup integration."""
from __future__ import annotations

from datetime import timedelta
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform, CONF_USERNAME, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.helpers.httpx_client import get_async_client
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from waste_management import WMClient

from .const import DOMAIN, CONF_ACCOUNT, CONF_SERVICES

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR]
UPDATE_INTERVAL = timedelta(hours=6)

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Waste Management Pickup from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    username = entry.data[CONF_USERNAME]
    password = entry.data[CONF_PASSWORD]
    account_id = entry.data[CONF_ACCOUNT]
    services = entry.data[CONF_SERVICES]

    # Initialize the client once to be reused by the coordinator
    client = WMClient(username, password, get_async_client(hass))

    async def async_update_data():
        """Fetch data from API endpoint."""
        try:
            # We re-authenticate here before fetching pickups, as the session might expire
            # over the 6-hour polling interval.
            await client.async_authenticate()
            await client.async_okta_authorize()
            
            pickups = {}
            for svc_id in services:
                pickups[svc_id] = await client.async_get_service_pickup(account_id, svc_id)
            return pickups
        except Exception as err:
            raise UpdateFailed(f"Error communicating with Waste Management API: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=DOMAIN,
        update_method=async_update_data,
        update_interval=UPDATE_INTERVAL,
    )

    # Do a one-time fetch of the service names so we can assign them to the sensors
    # without having to re-authenticate inside the sensor platform.
    try:
        await client.async_authenticate()
        await client.async_okta_authorize()
        wm_services = await client.async_get_services(account_id)
        service_names = {svc.id: svc.name for svc in wm_services}
    except Exception as err:
        _LOGGER.error("Failed to initialize Waste Management client during setup: %s", err)
        return False

    # Fetch initial data so we have state when entities are added
    await coordinator.async_config_entry_first_refresh()

    # Store both the coordinator and the service names in hass.data
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "service_names": service_names
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
