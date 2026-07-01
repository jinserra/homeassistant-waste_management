"""Config flow for Waste Management Pickup integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.const import CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.httpx_client import get_async_client

from waste_management import WMClient

from .const import CONF_ACCOUNT, CONF_SERVICES, DOMAIN

_LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
    }
)

async def validate_input(hass: HomeAssistant, data: dict[str, Any]) -> WMClient:
    """Validate the user input allows us to connect."""
    client = WMClient(data[CONF_USERNAME], data[CONF_PASSWORD], get_async_client(hass))
    try:
        await client.async_authenticate()
        await client.async_okta_authorize()
    except Exception as ex:
        raise InvalidAuth from ex
    
    return client


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Waste Management Pickup."""

    VERSION = 1

    def __init__(self):
        """Initialize the config flow."""
        self.data: dict[str, Any] = {}
        self._client: WMClient | None = None
        self._accounts: dict[str, str] = {}
        self._services: dict[str, str] = {}

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors = {}

        if user_input is not None:
            try:
                self._client = await validate_input(self.hass, user_input)
                self.data[CONF_USERNAME] = user_input[CONF_USERNAME]
                self.data[CONF_PASSWORD] = user_input[CONF_PASSWORD]
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception as ex:  # pylint: disable=broad-except
                _LOGGER.exception("Unexpected exception %s", ex)
                errors["base"] = "unknown"
            else:
                return await self.async_step_accounts()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    async def async_step_accounts(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the accounts step."""
        errors = {}

        if user_input is not None and CONF_ACCOUNT in user_input:
            self.data[CONF_ACCOUNT] = user_input[CONF_ACCOUNT]
            return await self.async_step_services()

        try:
            accounts = await self._client.async_get_accounts()
            self._accounts = {x.id: x.name for x in accounts}
        except Exception as ex:
            _LOGGER.exception("Unexpected exception fetching accounts: %s", ex)
            errors["base"] = "unknown"
            return self.async_show_form(step_id="accounts", data_schema=vol.Schema({}), errors=errors)

        return self.async_show_form(
            step_id="accounts",
            data_schema=vol.Schema(
                {vol.Required(CONF_ACCOUNT): vol.In(self._accounts)}
            ),
            errors=errors,
        )

    async def async_step_services(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the services step."""
        errors = {}

        if user_input is not None and CONF_SERVICES in user_input:
            self.data[CONF_SERVICES] = user_input[CONF_SERVICES]

            # Use the account name as the title for the integration in the UI
            title = self._accounts.get(self.data[CONF_ACCOUNT], "Waste Management")
            return self.async_create_entry(title=title, data=self.data)

        try:
            services = await self._client.async_get_services(self.data[CONF_ACCOUNT])
            self._services = {x.id: x.name for x in services}
        except Exception as ex:
            _LOGGER.exception("Unexpected exception fetching services: %s", ex)
            errors["base"] = "unknown"
            return self.async_show_form(step_id="services", data_schema=vol.Schema({}), errors=errors)

        return self.async_show_form(
            step_id="services",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SERVICES, default=list(self._services.keys())
                    ): cv.multi_select(self._services)
                }
            ),
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: config_entries.ConfigEntry) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return WasteManagementOptionsFlowHandler(config_entry)


class WasteManagementOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Waste Management."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        # Retrieve the human-readable service names from the running integration
        try:
            service_names = self.hass.data[DOMAIN][self.config_entry.entry_id]["service_names"]
        except KeyError:
            # Fallback if integration isn't loaded properly
            current_services = self.config_entry.options.get(
                CONF_SERVICES, self.config_entry.data.get(CONF_SERVICES, [])
            )
            service_names = {svc: f"Service {svc}" for svc in current_services}

        current_selected = self.config_entry.options.get(
            CONF_SERVICES, self.config_entry.data.get(CONF_SERVICES, [])
        )

        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_SERVICES, default=current_selected
                    ): cv.multi_select(service_names)
                }
            )
        )

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
