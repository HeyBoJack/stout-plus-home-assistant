# STOUT PLUS — Home Assistant Integration

[Русский](#русский) | [English](#english)

---

# Русский

Интеграция **STOUT PLUS** позволяет подключить электрический котёл STOUT PLUS к [Home Assistant](https://www.home-assistant.io/) по локальной сети и контролировать его работу, получать показания датчиков и управлять доступными настройками.

Интеграция использует локальный HTTP-интерфейс котла. Облачные сервисы не требуются.

## Поддерживаемое оборудование

На данный момент поддерживается модель:

- **STOUT PLUS SEB-2201-000018**
- Электрическая мощность: 18 кВт

Поддержка других моделей не заявлена.

## Возможности

### Климат и температура

- Климатическая сущность для управления температурой в режиме Room.
- Отображение текущей и целевой комнатной температуры.
- Управление целевой температурой помещения.

### Режимы работы

Интеграция позволяет выбирать режим работы котла:

- Heating — Отопление
- Weekly — Недельный
- Room — Комнатный
- Outdoor — Уличный
- Frost protection — Защита от замерзания

### Датчики

- Температура теплоносителя.
- Температура ГВС.
- Температура в помещении.
- Наружная температура.
- Текущая мощность котла.
- Давление воды.
- Режим работы.
- Ошибка котла.
- Состояние насоса.
- Состояние функции Antilegionella.

### Управление и настройки

В зависимости от возможностей котла доступны:

- Целевая температура теплоносителя.
- Целевая комнатная температура.
- Максимальная температура теплоносителя.
- Точность регулирования температуры теплоносителя.
- Управление ГВС и её целевой температурой.
- Выбор мощности ГВС.
- Выбор алгоритма отопления и ГВС.
- Настройки функции Antilegionella: температура, день недели и время запуска.
- Настройки дневной и ночной мощности.
- Время переключения дневного и ночного режимов.
- Настройка времени работы насоса после отключения.
- Управление звуковым сигналом реле.

## Требования к оборудованию

Некоторые функции котла зависят от наличия дополнительного оборудования:

**Antilegionella**

Функция встроена в котёл. Дополнительное оборудование для её работы не требуется.

**DHW (ГВС)**

Для полноценной работы ГВС необходимы бойлер косвенного нагрева и двухходовой клапан. Доступность соответствующих сущностей зависит от конфигурации и данных котла.

**Outdoor (Уличный режим)**

Для работы в этом режиме требуется соответствующее внешнее оборудование. Доступность связанных настроек зависит от текущего режима и конфигурации котла.

## Установка через Home Assistant Marketplace

[![Открыть STOUT PLUS в Home Assistant Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=HeyBoJack&repository=stout-plus-home-assistant&category=integration)

Пока интеграция не включена в общий каталог, её можно добавить по ссылке выше:

1. Откройте ссылку.
2. При необходимости подключите GitHub к Home Assistant.
3. Подтвердите добавление репозитория STOUT PLUS.
4. Откройте страницу интеграции в Marketplace и нажмите Install.
5. После установки перейдите к настройке интеграции.

## Настройка

1. Откройте **Settings → Devices & services**.
2. Нажмите **Add integration**.
3. Найдите **STOUT PLUS**.
4. Укажите IP-адрес или имя хоста котла.
5. Укажите HTTP-порт (по умолчанию `80`).

После добавления интеграции котёл появится в Home Assistant как отдельное устройство.

## Техническая информация

- Локальное подключение по HTTP.
- Облачное подключение не используется.
- Период обновления данных: 10 секунд.
- Минимальная версия Home Assistant: 2026.11.0.

## Обратная связь

Если вы обнаружили ошибку или хотите предложить улучшение, создайте [Issue на GitHub](https://github.com/HeyBoJack/stout-plus-home-assistant/issues).

---

# English

The **STOUT PLUS** integration connects a STOUT PLUS electric boiler to [Home Assistant](https://www.home-assistant.io/) over your local network. It provides boiler monitoring, temperature readings, and control of supported settings.

The integration communicates with the boiler through its local HTTP interface. No cloud services are required.

## Supported hardware

Currently supported model:

- **STOUT PLUS SEB-2201-000018**
- Electrical power: 18 kW

Other models are not currently supported.

## Features

### Climate and temperature

- Climate entity for temperature control in Room mode.
- Current and target room temperature.
- Room target temperature control.

### Operating modes

The integration supports selecting the following boiler modes:

- Heating
- Weekly
- Room
- Outdoor
- Frost protection

### Sensors

- Flow temperature.
- DHW temperature.
- Room temperature.
- Outdoor temperature.
- Current boiler power.
- Water pressure.
- Operating mode.
- Boiler error.
- Pump status.
- Antilegionella status.

### Controls and settings

Depending on the boiler capabilities, the integration provides:

- Flow temperature target.
- Room temperature target.
- Maximum flow temperature.
- Flow temperature accuracy.
- DHW control and target temperature.
- DHW power selection.
- Heating and DHW algorithm selection.
- Antilegionella settings: temperature, weekday, and start time.
- Day and night power settings.
- Day and night mode switching times.
- Pump overrun settings.
- Relay sound signal control.

## Hardware requirements

Some boiler functions depend on additional external equipment:

**Antilegionella**

This is a built-in boiler function. No additional equipment is required.

**DHW (Domestic Hot Water)**

A domestic hot water cylinder and a two-way valve are required for full DHW operation. The availability of related entities depends on the boiler configuration and reported data.

**Outdoor mode**

This mode requires compatible external equipment. The availability of related settings depends on the current operating mode and boiler configuration.

## Installation via Home Assistant Marketplace

[![Open STOUT PLUS in Home Assistant Marketplace](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/marketplace_repository/?owner=HeyBoJack&repository=stout-plus-home-assistant&category=integration)

Until the integration is included in the public catalog, you can add it using the link above:

1. Open the link.
2. Connect your GitHub account to Home Assistant if prompted.
3. Confirm adding the STOUT PLUS repository.
4. Open the integration page in the Marketplace and select Install.
5. Proceed to integration setup.

## Configuration

1. Open **Settings → Devices & services**.
2. Click **Add integration**.
3. Search for **STOUT PLUS**.
4. Enter the boiler IP address or hostname.
5. Enter the HTTP port (default: `80`).

After setup, the boiler will appear as a separate device in Home Assistant.

## Technical details

- Local HTTP connection.
- No cloud connection required.
- Data update interval: 10 seconds.
- Minimum Home Assistant version: 2026.11.0.

## Support and feedback

If you encounter a problem or have a feature request, please open an [Issue on GitHub](https://github.com/HeyBoJack/stout-plus-home-assistant/issues).
