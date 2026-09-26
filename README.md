# UrbanJungle Care voor Home Assistant

Brengt je UrbanJungle Care-planten en -sensoren naar Home Assistant, en stuurt metingen
van Bluetooth-sensoren die Home Assistant al ziet terug naar je UrbanJungle-account.

## Wat je krijgt

- Inloggen met je UrbanJungle-account via OAuth2 met PKCE; Home Assistant ziet je
  wachtwoord nooit en bewaart alleen een token dat je op elk moment kunt intrekken in de app.
- Sensoren per plant: bodemvocht, licht, temperatuur, voeding en batterij.
- Metingen van `xiaomi_ble`-sensoren worden doorgestuurd naar je account, zodat de app en
  Home Assistant dezelfde historie delen. Een nog onbekende sensor registreert zichzelf.
- Verversfrequentie volgt je abonnement: elke 15 minuten met premium, elke 24 uur zonder.

## Installeren

### Via HACS

1. HACS, dan Integrations, dan via het menu rechtsboven "Custom repositories"
2. Voeg `koktail-nl/urbanjungle-home-assistant` toe met categorie Integration
3. Download "UrbanJungle Care" en herstart Home Assistant
4. Instellingen, dan Apparaten en diensten, dan Integratie toevoegen, zoek UrbanJungle Care

### Met de hand

1. Pak `urbanjungle_care.zip` uit de release uit in `config/custom_components/`
2. Herstart Home Assistant en voeg de integratie toe via de interface

## Koppelen

De integratie stuurt je naar je UrbanJungle-account, waar je de toegang goedkeurt. Home
Assistant komt terug via `my.home-assistant.io` en bewaart het token in de config entry.
Trek je de koppeling later in de app in, dan vraagt Home Assistant je vanzelf opnieuw om
toestemming. Verwijder je de integratie in Home Assistant, dan verdwijnt ook de koppeling
uit je account.

## Vereisten

- Home Assistant 2024.2 of nieuwer
- Een UrbanJungle Care-account
- Voor sensormetingen: Bluetooth in Home Assistant met de `xiaomi_ble`-integratie

## Ontwikkelen

`python3 validate.py` controleert of de component compleet is en compileert. Een release
gaat via een `v*.*.*`-tag, die `.github/workflows/home-assistant-release.yml` oppakt; de
versie in `manifest.json` moet gelijk zijn aan de tag.
