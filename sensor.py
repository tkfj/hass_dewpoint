from __future__ import annotations
from math import log

from homeassistant.core import HomeAssistant, callback, State
from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature, ATTR_UNIT_OF_MEASUREMENT
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import DOMAIN, CONF_NAME, CONF_TEMP_ENTITY, CONF_HUM_ENTITY, CONF_PRECISION

PLATFORM = "sensor"

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    async_add_entities([DewPointSensor(hass, entry)], update_before_add=True)

class DewPointSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_device_class = "temperature"
    _attr_state_class = "measurement"
    _attr_should_poll = False
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry):
        self.hass = hass
        self.entry = entry
        self._temp_ent: str = (entry.options.get(CONF_TEMP_ENTITY)
                               or entry.data[CONF_TEMP_ENTITY])
        self._hum_ent: str = (entry.options.get(CONF_HUM_ENTITY)
                              or entry.data[CONF_HUM_ENTITY])
        self._precision: int = int(entry.options.get(CONF_PRECISION,
                                  entry.data.get(CONF_PRECISION, 1)))
        name = (entry.options.get(CONF_NAME) or entry.data.get(CONF_NAME) or "Dew Point")
        self._attr_name = name
        self._attr_unique_id = f"{entry.entry_id}_dewpoint"
        self._unsub = None

    async def async_added_to_hass(self) -> None:
        @callback
        def _state_change(event):
            self._recalc_and_write()

        self._unsub = async_track_state_change_event(
            self.hass, [self._temp_ent, self._hum_ent], _state_change
        )
        # 初回計算
        self._recalc_and_write()

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

    @callback
    def _recalc_and_write(self):
        t_state: State | None = self.hass.states.get(self._temp_ent)
        h_state: State | None = self.hass.states.get(self._hum_ent)

        if not t_state or not h_state:
            self._attr_available = False
            self.async_write_ha_state()
            return

        try:
            t = float(t_state.state)
            # 温度単位が華氏ならCに変換
            t_unit = t_state.attributes.get(ATTR_UNIT_OF_MEASUREMENT)
            if t_unit == UnitOfTemperature.FAHRENHEIT:
                t = (t - 32.0) * 5.0 / 9.0

            h = float(h_state.state)
        except (ValueError, TypeError):
            self._attr_available = False
            self.async_write_ha_state()
            return

        # 湿度の妥当域チェック
        if not (0.0 < h <= 100.0):
            self._attr_available = False
            self.async_write_ha_state()
            return

        # ── Magnus式で露点（℃）
        # alpha = (a * T)/(b + T) + ln(RH/100)
        a = 17.27
        b = 237.7
        alpha = ((a * t) / (b + t)) + log(h / 100.0)
        dew = (b * alpha) / (a - alpha)

        self._attr_native_value = round(dew, self._precision)
        self._attr_available = True
        self.async_write_ha_state()
