# UrbanJungle Care voor Home Assistant

Brengt de sensoren uit je UrbanJungle Care-account naar Home Assistant, en stuurt metingen
van Bluetooth-plantsensoren die Home Assistant al ziet terug naar je UrbanJungle-account.

## Vereisten

- Home Assistant 2025.4 of nieuwer
- Een UrbanJungle Care-account
- De `my`-integratie, die `default_config` laadt. Home Assistant komt na het inloggen bij
  UrbanJungle terug via `my.home-assistant.io`, en die doorverwijzing heeft hem nodig. Staat
  er geen `default_config:` in je `configuration.yaml`, voeg dan `my:` toe.
- Voor het doorsturen van sensormetingen: Bluetooth in Home Assistant met de
  `xiaomi_ble`-integratie

## Installeren via HACS

1. Open HACS, dan het menu rechtsboven, dan "Custom repositories"
2. Voeg `https://github.com/koktail-nl/urbanjungle-home-assistant` toe met type Integration
3. Zoek "UrbanJungle Care" in HACS, download hem en herstart Home Assistant
4. Ga naar Instellingen, Apparaten en diensten, Integratie toevoegen, en zoek UrbanJungle Care

## Met de hand installeren

1. Download `urbanjungle_care.zip` bij de nieuwste release op
   https://github.com/koktail-nl/urbanjungle-home-assistant/releases
2. Pak hem uit in `config/custom_components/`, zodat de bestanden in
   `config/custom_components/urbanjungle_care/` staan
3. Herstart Home Assistant en voeg de integratie toe via Instellingen, Apparaten en diensten

## Koppelen

De integratie stuurt je naar je UrbanJungle-account, waar je de toegang goedkeurt. Inloggen
gaat via OAuth2 met PKCE: Home Assistant ziet je wachtwoord nooit en bewaart alleen een token
in de config entry. Home Assistant komt terug via `my.home-assistant.io` en rondt de
installatie af.

## Wat je krijgt

- Per UrbanJungle-sensorapparaat in je account een apparaat in Home Assistant, elk met vijf
  sensoren: Moisture, Light, Temperature, Conductivity (voeding) en Battery.
- Een sensor "UrbanJungle Sync Status" die de verversfrequentie toont, met attributen voor
  premiumstatus, de laatste sync en het aantal gesynchroniseerde apparaten en planten.
- De integratie maakt deze entiteiten aan voor de apparaten die er zijn bij het instellen.
  Een apparaat dat je later aan je account toevoegt, verschijnt na het herladen van de
  integratie of een herstart van Home Assistant.
- Bij elke verversing gaan de metingen van `xiaomi_ble`-plantsensoren (bodemvocht, licht,
  temperatuur, geleidbaarheid, batterij) naar je account, zodat de app en Home Assistant
  dezelfde historie delen. Een sensor die je account nog niet kent, registreert zichzelf.
- De verversfrequentie volgt je abonnement: elke 15 minuten met premium, elke 24 uur zonder.

## Verwijderen en intrekken

- Trek je de koppeling in de UrbanJungle-app in, dan vraagt Home Assistant bij de volgende
  verversing opnieuw om toestemming.
- Verwijder je de integratie in Home Assistant, dan verdwijnt de koppeling ook uit je
  UrbanJungle-account.

## Problemen

Meld problemen op https://github.com/koktail-nl/urbanjungle-home-assistant/issues
