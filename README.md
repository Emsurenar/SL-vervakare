# SL Public Transport Delay Monitor (SL-övervakare)

This project monitors specific routes in the SL (Stockholm Public Transport) system every 5 minutes using GitHub Actions. If severe delays or interruptions are detected, it sends an automated Telegram notification directly to your phone. 

The primary use case is documenting and obtaining proof of delays exceeding 20 minutes to claim the [SL Delay Compensation](https://sl.se/kundservice/forseningsersattning).

The script utilizes the **ResRobot v2.1 - Reseplanerare** API from Trafiklab. This API provides exact scheduled and real-time (`rtTime`) departures to accurately calculate minute-by-minute delays for specific trips.

## Configured Routes
The script currently checks upcoming trips between:
- Tekniska högskolan -> Enskede gård T-bana
- Tekniska högskolan -> Medborgarplatsen T-bana
- Tekniska högskolan -> Nytorgsgatan (Stockholm)

*You can easily modify this by changing the `ROUTES` array in `sl_monitor.py`.*

## Features

### Fast Delay Compensation Proof
The Telegram message includes the official timestamp and the internal SL journey ID directly from their system. This information can be directly included in your delay compensation request for fast, undeniable processing.

### Anti-Spam Mechanism
To prevent spamming the user with repeated notifications for the same ongoing delayed trip, the script maintains a state file (`sent_deviations.txt`). Each time a new event triggers an alarm, its unique ID is stored here, and the file is automatically pushed back to the GitHub repository. This guarantees exactly **one** notification per specific delayed trip.
