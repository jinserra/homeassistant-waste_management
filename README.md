# homeassistant-waste_management

A modern, fully asynchronous Home Assistant integration to [Waste Management (wm.com)](https://www.wm.com) API to pull the next pickup dates for your services (e.g., trash, recycling, yard waste). 

This integration creates timestamp sensors in Home Assistant that update automatically, allowing you to build automations or dashboard reminders for trash day! *Note: You will need a registered account on wm.com for this to work.*

---

## 🚀 Features

This repository is a forked and modernized version of the original `homeassistant-waste_management` integration. It has been rewritten to align with modern Home Assistant standards:

* **Calendar Support**: Pickup dates are mapped directly into your Home Assistant built-in calendar. 
* **Device-Based Organization**: All individual pickup services are automatically grouped under a single, unified Waste Management device associated with your account number. 
* **UI Configuration & Options Flow**: Entirely configurable via the Home Assistant integrations dashboard. Easily add or remove monitored service streams anytime via the Configure button without reinstalling.
* **Migrated to `DataUpdateCoordinator`:** The integration now uses Home Assistant's built-in coordinator for background polling. This centralizes API requests, handles retry logic elegantly if the API goes down, and ensures your sensors properly report as "unavailable" during outages.
* **Improved API Polling:** Previously, the integration would re-authenticate with the WM API for every single sensor on every single update. The code has been rewritten to establish a single authenticated session that is shared across all sensors, drastically reducing the number of requests and preventing potential rate-limiting or account lockouts.
* **Polished Setup UI & Translations:** The configuration flow has been cleaned up. Unused legacy fields were removed, and proper English translations with step-by-step instructions were added to make setting up your account and selecting services in the UI a breeze.
* **Native HACS Support:** Added full HACS compatibility so the integration can be easily installed, updated, and tracked as a custom repository. 
* **Updated Device Classes:** Transitioned to modern Home Assistant Enums (`SensorDeviceClass.TIMESTAMP`) for better long-term compatibility.

## ⚙️ Installation

### Option 1: HACS (Recommended)
1. Go to **HACS** -> **Integrations** in Home Assistant.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Add the URL of this repository (`https://github.com/jinserra/homeassistant-waste_management`), select **Integration** as the category, and click **Add**.
4. Search for "Waste Management" in HACS, download it, and restart Home Assistant.

### Option 2: Manual Installation
1. Download the latest release from this repository.
2. Copy the `custom_components/waste_management` folder into your Home Assistant `custom_components` directory.
3. Restart Home Assistant.

## 🛠️ Configuration

1. In Home Assistant, go to **Settings** -> **Devices & Services**.
2. Click **Add Integration** and search for **Waste Management**.
3. Enter your wm.com **Username** and **Password**.
4. Select your **Account** and the **Services** (Trash, Recycling, etc.) you want to track.
