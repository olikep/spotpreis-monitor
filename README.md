# Spotpreis-Monitor

Dashboard für die beiden Referenzindizes österreichischer Spotpreis-Tarife — **Strom**
(EPEX SPOT AT Day-Ahead, live) und **Erdgas** (CEGH VTP Austria / CEGHIX, live).
Gebaut als Vertriebswerkzeug für Produkte wie *Strom KMU Spot* und *Erdgas KMU Spot*
der Energie Klagenfurt GmbH. Ab Vertrag Version 1 | 2026 indexiert Strom auf den
**Power Spot Market AT** (Viertelstunden), nicht mehr DE-LU.

**Live-Version:** https://olikep.github.io/spotpreis-monitor/

## Funktionen

**Beide Energieträger** liegen auf eigenen Tabs, jede Zahl ist als Strom oder Erdgas beschriftet.

- **Tages-, Wochen- und Monatsmittel** per Klick; bei Strom Zeitraum von 30 Tagen bis 3 Jahren
- **Branchen-Lastprofile** (Strom): der Spotpreis wird nach der Vertragsformel
  mit dem Verbrauchsprofil der gewählten Branche gewichtet — nicht bloß als Base-Durchschnitt
- Einheit umschaltbar **EUR/MWh ↔ ct/kWh**
- **Endkundenpreis-Rechner** je Energieträger: Handlingfee, HKN bzw. CO₂-Bepreisung,
  Servicepauschale und Jahresverbrauch → Arbeitspreis nach Formel und Energiekosten gesamt
- **Heute & Morgen:** Kacheln plus **Stundenpreise des Liefertags** (Balkendiagramm + Tabelle Uhrzeit → ct/kWh), gleiche Infos wie in der WhatsApp (günstigste Fenster, Tief/Hoch/Schnitt). Handlingfee aus dem Rechner.
- Eine einzige HTML-Datei, kein Build, keine Abhängigkeiten

## Lastprofile

Der Kern: die Vertragsformel ist **lastgewichtet**, nicht Base.

```
        Σ (Spotpreis(n) × E(n))
P(n) = ─────────────────────────  + Handlingfee
             Σ E(n)
```

Wer nur den Base-Durchschnitt zeigt, nennt eine Zahl, die der Kunde nie zahlt. Diese Seite
rechnet die Formel tatsächlich durch — mit E(n) aus dem gewählten Branchenprofil.

| ID | Branche | Charakteristik |
|---|---|---|
| `base` | Referenz | ungewichtet, alle Viertelstunden gleich |
| `peak` | Referenz | Mo–Fr 08–20 Uhr |
| `G0` | Gewerbe allgemein | Mischprofil, guter Startwert |
| `G1` | Büro, Praxis, Kanzlei, Behörde | werktags 08–18, Wochenende aus — **teuerster Fall** |
| `G2` | Gastronomie, Hotel | Abendschwerpunkt |
| `G3` | Kühlhaus, Server, Tankstelle | durchlaufend, nahe Base |
| `G4` | Laden, Friseur, Einzelhandel | Mo–Sa Öffnungszeiten |
| `G5` | Bäckerei mit Backstube | Nacht-/Frühschwerpunkt — **günstigster Fall** |
| `G6` | Sport, Kino, Freizeit | Wochenend- und Abendbetrieb |
| `L0` | Landwirtschaft | zwei Spitzen, früh und spätnachmittags |
| `H0` | Haushalt | zum Vergleich |

> **Wichtig:** Diese Profile sind **Näherungen**, an die Charakteristik der Standardlastprofile
> angelehnt — nicht die amtlichen Koeffizienten. Für verbindliche Zahlen die echten Profile von
> [APCS](https://www.apcs.at/de/clearing/technisches-clearing/lastprofile) (Österreich) oder
> [BDEW](https://www.bdew.de/energie/standardlastprofile-strom/) (Deutschland) herunterladen und
> die Arrays im `PROFILES`-Block in `index.html` ersetzen: je Profil `wd` (24 Werte Werktag),
> `sa` und `so` (Faktor oder eigenes 24er-Array). Nur relative Verhältnisse zählen, keine Normierung nötig.

## Datenquellen

| Energieträger | Index | Quelle | Live? |
|---|---|---|---|
| Strom | EPEX SPOT AT Day-Ahead | [energy-charts.info API](https://api.energy-charts.info/) `bzn=AT` (Fraunhofer ISE, CC BY 4.0) | ja |
| Strom (Fallback) | EPEX SPOT AT | [aWATTar AT API](https://api.awattar.at/v1/marketdata) | ja |
| Erdgas | CEGHIX (CEGH VTP Austria) | [CEGH Day-Ahead-Export](https://www.cegh.at/en/direct-download-links/) über `https://api.angebote.xolvix.ai/api/ext/ceghix` | ja |

**Warum Strom auf AT läuft:** der Liefervertrag *Strom KMU Spot* (EKG, Version 1 | 2026)
nennt ausdrücklich **EPEX AT SPOT** — „Viertelstundenpreise des Power Spot Market AT“.
Formel: Energiepreis = Börseneinkaufspreis + Handlingfee (ct/kWh) + HKN 0,42 ct/kWh
+ Servicepauschale 3,99 €/Monat je Zählpunkt.

### Gaspreise

CEGHIX kommt live aus dem öffentlichen Day-Ahead-CSV von CEGH (Spalte `CEGHIX`,
zugeordnet zum Lieferstag des DA-Kontrakts). Der Browser holt das über den
Xolvix-Proxy `/api/ext/ceghix` (CEGH selbst sendet kein CORS).
`data/ceghix.csv` bleibt Fallback und wächst per GitHub Action mit.

Manuell im Gas-Tab einfügen wirkt sofort, wird aber nicht gespeichert.

## Nutzung

```bash
git clone https://github.com/olikep/spotpreis-monitor.git
cd spotpreis-monitor
python3 -m http.server 8000     # dann http://localhost:8000 öffnen
```

Ein lokaler Server ist nötig, damit `data/ceghix.csv` geladen werden kann — beim Öffnen per
Doppelklick (`file://`) blockiert der Browser das. Strom funktioniert auch ohne Server, sofern
keine Firewall den API-Abruf blockiert.

### GitHub Pages

Repo-Einstellungen → **Pages** → Source: *Deploy from a branch* → Branch `main`, Ordner `/docs`.
`docs/` ist eine Kopie von `index.html` und `data/`; nach Änderungen mitziehen:

```bash
cp index.html docs/index.html && cp -r data docs/
```

## Voreinstellungen anpassen

| Feld | ID | Vorbelegung | Bedeutung |
|---|---|---|---|
| Handlingfee Strom | `inHF` | `15` | **Platzhalter** — der echte Wert steht im Energieliefervertrag |
| Stromqualität HKN | `inHKN` | `0.82` | ct/kWh, Preisblatt August 2026 |
| Servicepauschale | `inService` | `3.99` | EUR/Monat je Zählpunkt |
| Jahresverbrauch | `inUse` | `40000` | kWh/Jahr |
| Handlingfee Gas | `gHF` | `15` | **Platzhalter** |
| CO₂-Bepreisung | `gCO2` | `0` | ct/kWh nach NEHG |

Farbpalette und Dark-Mode-Tokens liegen als CSS Custom Properties im `:root`-Block.

## Grenzen

- Die Lastprofile sind Näherungen (siehe oben), keine amtlichen SLP-Koeffizienten.
- Der CEGHIX ist ein **Tagesindex** — eine Lastgewichtung nach Stunden gibt es beim Gas nicht.
- Alle Werte netto: ohne Netzentgelte, Elektrizitäts- bzw. Erdgasabgabe, Ökostrompauschalen und USt.
- Zeitzone Europe/Vienna.
- Richtwerte, keine Angebotsgrundlage. Maßgeblich ist die Abrechnung des Lieferanten.

## Lizenz

MIT — siehe [LICENSE](LICENSE). Die abgerufenen Marktdaten stehen unter CC BY 4.0
(Fraunhofer ISE / Bundesnetzagentur) und sind nicht Teil dieser Lizenz.
