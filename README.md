# SL Förseningsövervakare (Telegram + GitHub Actions)

Det här projektet kollar valda rutter i SL-trafiken *var 5:e minut* via **GitHub Actions** och skickar automatiskt ett Telegram-meddelande till din telefon om det finns förseningar på mer än 20 minuter (som berättigar till förseningsersättning).

## Instruktioner för Uppsättning

### 1. Skapa en Telegram-Bot
1. Ladda ner Telegram och sök efter `@BotFather`.
2. Skriv `/newbot` och följ instruktionerna för att namnge din bot (t.ex. `SL_Försening_Bot`).
3. Kopiera **API-token** som BotFather ger dig. Denna token är din `TELEGRAM_BOT_TOKEN`.
4. Sök sedan upp din bot i chatten och klicka på "Start". Skriv ett random meddelande, t.ex. "hello".
5. Sök efter `@userinfobot` i Telegram, klicka "Start" och kopiera ditt **Chat ID** (ett nummer, t.ex. `12345678`). Detta är din `TELEGRAM_CHAT_ID`.

### 2. Skaffa API-nyckel från Trafiklab
1. Skapa ett gratiskonto på [Trafiklab](https://www.trafiklab.se/).
2. Skapa ett nytt projekt och lägg till API:et **SL Reseplanerare 3.1** eller **SL Stopp-Tider** (se Python-koden för exakt länk).
3. Kopiera din API-nyckel. Detta är din `SL_API_KEY`.

### 3. Konfigurera GitHub-repot
1. Logga in på GitHub och skapa ett nytt kod-repo (t.ex. `sl-overvakare`).
2. Gå till fliken **Settings** -> **Secrets and variables** -> **Actions**.
3. Klicka på **"New repository secret"** och lägg till tre stycken:
   - `SL_API_KEY` = Din Trafiklab nyckel
   - `TELEGRAM_BOT_TOKEN` = Din Telegram-bot token
   - `TELEGRAM_CHAT_ID` = Ditt Telegram Chat-ID
4. Ladda upp/pusha kodfilerna från din dator till detta GitHub-repo (inklusive mappen `.github`).

### Nu rullar det!
När detta är uppladdat till GitHub kommer filen `.github/workflows/scraper.yml` se till att köra skriptet automatiskt **var 5:e minut**, helt gratis. Springer en resa iväg 20+ minuter så plingar mobilen till direkt!

[Läs mer om förseningsersättning hos SL här](https://sl.se/kundservice/forseningsersattning).
