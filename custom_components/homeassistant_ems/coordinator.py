"""Push updates from mapped Home Assistant states into the site data model."""

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, State, callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .site_data import SiteData, SiteDataStore

_LOGGER = logging.getLogger(__name__)


class SiteDataCoordinator(DataUpdateCoordinator[SiteData]):
    """Share the latest read-only site snapshot with integration consumers."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Initialize from current source states without scheduling polls."""
        self._store = SiteDataStore(entry.title, entry.options)
        self._store.update_sources(
            {
                entity_id: hass.states.get(entity_id)
                for entity_id in self._store.source_entity_ids
            }
        )
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=DOMAIN,
            always_update=False,
        )
        self.async_set_updated_data(self._store.snapshot)

    @property
    def snapshot(self) -> SiteData:
        """Return the current immutable snapshot."""
        return self._store.snapshot

    @property
    def source_entity_ids(self) -> tuple[str, ...]:
        """Return the mapped source IDs observed by this coordinator."""
        return self._store.source_entity_ids

    @callback
    def update_source(self, source_entity_id: str, state: State | None) -> None:
        """Update the snapshot after one mapped entity state changes."""
        self._store.update_source(source_entity_id, state)
        self.async_set_updated_data(self._store.snapshot)
