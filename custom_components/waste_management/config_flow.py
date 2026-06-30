"""Config flow for Waste Management Pickup integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
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

        if user_input is not None:
            self.data[CONF_ACCOUNT] = user_input[CONF_ACCOUNT]
            return await self.async_step_services()

        try:
            accounts = await self._client.async_get_accounts()
            self._accounts = {x.id: x.name for x in accounts}
        except Exception as ex:
            _LOGGER.exception("Unexpected exception fetching accounts: %s", ex)
            errors["base"] = "unknown"
            return self.async_show_form(step_id="accounts", errors=errors)

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

        if user_input is not None:
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
            return self.async_show_form(step_id="services", errors=errors)

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

class InvalidAuth(HomeAssistantError):
    """Error to indicate there is invalid auth."""
