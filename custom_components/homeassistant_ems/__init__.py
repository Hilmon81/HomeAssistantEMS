"""Home Assistant EMS integration."""

from collections.abc import Callable
from dataclasses import dataclass

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.helpers.event import async_track_state_change_event

from .coordinator import SiteDataCoordinator

PLATFORMS = [Platform.SENSOR]


@dataclass
class EntryRuntimeData:
    """Runtime services for one configured site."""

    site_data: SiteDataCoordinator
    unsubscribe: Callable[[], None] | None


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up an EMS site."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    site_data = SiteDataCoordinator(hass, entry)

    @callback
    def handle_source_change(event: Event) -> None:
        """Refresh the site model when any mapped source state changes."""
        site_data.update_source(
            event.data["entity_id"],
            event.data["new_state"],
        )

    unsubscribe = (
        async_track_state_change_event(
            hass, list(site_data.source_entity_ids), handle_source_change
        )
        if site_data.source_entity_ids
        else None
    )
    entry.runtime_data = EntryRuntimeData(
        site_data=site_data,
        unsubscribe=unsubscribe,
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload an EMS site."""
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        runtime_data: EntryRuntimeData | None = entry.runtime_data
        if runtime_data is not None and runtime_data.unsubscribe is not None:
            runtime_data.unsubscribe()
        entry.runtime_data = None
    return unloaded
