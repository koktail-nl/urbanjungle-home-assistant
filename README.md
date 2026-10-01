# UrbanJungle Care for Home Assistant

Brings the sensors of your UrbanJungle Care account into Home Assistant, and sends the
readings of Bluetooth plant sensors that Home Assistant already sees back to your
UrbanJungle account.

## Requirements

- Home Assistant 2025.4 or newer
- An UrbanJungle Care account
- The `my` integration, which `default_config` loads. Home Assistant returns from the
  UrbanJungle sign-in through `my.home-assistant.io`, and that redirect needs it. If your
  `configuration.yaml` has no `default_config:`, add `my:`.
- For forwarding sensor readings: Bluetooth in Home Assistant with the `xiaomi_ble`
  integration

## Install through HACS

1. Open HACS, then the menu at the top right, then "Custom repositories"
2. Add `https://github.com/koktail-nl/urbanjungle-home-assistant` with type Integration
3. Search for "UrbanJungle Care" in HACS, download it and restart Home Assistant
4. Go to Settings, Devices & services, Add integration, and search for UrbanJungle Care

## Install by hand

1. Download `urbanjungle_care.zip` from the latest release on
   https://github.com/koktail-nl/urbanjungle-home-assistant/releases
2. Unpack it into `config/custom_components/`, so the files end up in
   `config/custom_components/urbanjungle_care/`
3. Restart Home Assistant and add the integration through Settings, Devices & services

## Connecting

The integration sends you to your UrbanJungle account, where you approve the access. Sign-in
uses OAuth2 with PKCE: Home Assistant never sees your password and only stores a token in its
config entry. Home Assistant comes back through `my.home-assistant.io` and finishes the setup.

## What you get

- One Home Assistant device per UrbanJungle sensor device in your account, each with five
  sensors: Moisture, Light, Temperature, Conductivity (nutrition) and Battery.
- One "UrbanJungle Sync Status" sensor that shows the refresh frequency, with attributes for
  premium status, the last sync and the number of synced devices and plants.
- The integration creates these entities for the devices that exist when it is set up. A
  device added to your account later appears after you reload the integration or restart
  Home Assistant.
- On each refresh cycle the readings of `xiaomi_ble` plant sensors (moisture, light,
  temperature, conductivity, battery) are sent to your account, so the app and Home
  Assistant share the same history. A sensor your account does not know yet registers
  itself.
- The refresh cycle follows your subscription: every 15 minutes with premium, every 24 hours
  without.

## Removing and revoking

- Revoke the link in the UrbanJungle app and Home Assistant asks you to approve the access
  again on its next refresh.
- Remove the integration in Home Assistant and the link disappears from your UrbanJungle
  account as well.

## Issues

Report problems at https://github.com/koktail-nl/urbanjungle-home-assistant/issues
