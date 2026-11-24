"""Pytest configuration for Home Assistant integration tests."""

# Set up HA's httpx alias before the test plugin imports respx.
import homeassistant  # noqa: F401
import pytest

pytest_plugins = "pytest_homeassistant_custom_component"


@pytest.fixture(autouse=True)
def enable_custom_integrations_for_tests(enable_custom_integrations: None) -> None:
    """Make the custom integration discoverable in Home Assistant tests."""
