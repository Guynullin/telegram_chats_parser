# Telegram Chats & Channels Parser

**English** | [Русский](#Русский)

## Description

A Python-based data collection tool that systematically archives messages from specified Telegram chats and channels. Using the Telethon library and a user account, it saves all extracted data into structured JSON files, one per chat/channel. The tool is designed for incremental updates, appending new messages to the existing history upon subsequent runs.

## Key Functionalities

*   **Targeted Data Extraction:** Connects to and parses messages from a predefined list of Telegram chats and channels.
*   **Structured JSON Storage:** Saves all messages, metadata, and media information into well-organized JSON files, maintaining a separate file for each source.
*   **Incremental Archiving:** On each run, the script efficiently fetches only new messages that appeared since the last collection, prepending them to the existing JSON file to maintain chronological order.
*   **Session Management:** Uses a Telegram user account (via MTProto API) for authentication, providing a stable and reliable connection.

## Tech Stack

*   Python
*   Telethon (MTProto API client)
*   JSON

## Project Context & Development Notes

This parser was developed to create a centralized and searchable archive of communications from relevant Telegram communities for the client. The primary requirement was to build a historical record and keep it updated with minimal manual intervention.

The choice of Telethon and a user account (as opposed to a bot) was crucial, as it provides access to a wider range of chats and channels, including those where a bot might not be added. The incremental update mechanism is a core feature that makes the tool efficient for long-term monitoring, as it avoids re-downloading the entire message history every time, saving bandwidth and time.

The output JSON files serve as a raw data source that can be easily imported into databases, fed into analytics pipelines, or used for further processing.

## Why It's Here

This repository demonstrates my ability to:

*   Leverage the Telegram MTProto API (via Telethon) for robust data collection from real-time communication platforms.
*   Design efficient ETL (Extract, Transform, Load) processes that perform incremental updates to avoid redundant work.
*   Create reliable, long-running data-gathering tools that require minimal configuration after the initial setup.
*   Structure and persist unstructured social data into a structured, machine-readable format (JSON) for downstream applications.

---

# Русский

## Описание

Инструмент для сбора данных на Python, который систематически архивирует сообщения из указанных чатов и каналов Telegram. Используя библиотеку Telethon и пользовательский аккаунт, он сохраняет все извлеченные данные в структурированные JSON-файлы, по одному файлу на каждый чат или канал. Инструмент предназначен для инкрементальных обновлений, добавляя новые сообщения в существующую историю при последующих запусках.

## Ключевые функции

*   **Целевой сбор данных:** Подключается и парсит сообщения из заранее заданного списка чатов и каналов Telegram.
*   **Структурированное хранение в JSON:** Сохраняет все сообщения, метаданные и информацию о медиафайлах в хорошо организованные JSON-файлы, ведя отдельный файл для каждого источника.
*   **Инкрементальное архивирование:** При каждом запуске скрипт эффективно загружает только новые сообщения, появившиеся с момента последнего сбора, и добавляет их в начало существующего JSON-файла для сохранения хронологического порядка.
*   **Управление сессией:** Использует пользовательский аккаунт Telegram (через MTProto API) для аутентификации, обеспечивая стабильное и надежное соединение.

## Стек технологий

*   Python
*   Telethon (MTProto API client)
*   JSON

## Контекст проекта и заметки о разработке

Данный парсер был разработан для создания централизованного и доступного для поиска архива коммуникаций из релевантных Telegram-сообществ для клиента. Основным требованием было построение исторической записи и ее поддержание в актуальном состоянии с минимальным ручным вмешательством.

Выбор Telethon и пользовательского аккаунта (в отличие от бота) был ключевым, так как это обеспечивает доступ к более широкому кругу чатов и каналов, включая те, куда бота, возможно, не добавили. Механизм инкрементального обновления является основной особенностью, которая делает инструмент эффективным для долгосрочного мониторинга, поскольку он позволяет избежать повторной загрузки всей истории сообщений каждый раз, экономя трафик и время.

Выходные JSON-файлы служат источником сырых данных, которые можно легко импортировать в базы данных, передавать в аналитические пайплайны или использовать для дальнейшей обработки.

## Почему этот проект здесь

Этот репозиторий демонстрирует мои способности:

*   Эффективно использовать Telegram MTProto API (через Telethon) для надежного сбора данных из платформ реального времени.
*   Проектировать эффективные ETL (Extract, Transform, Load) процессы, которые выполняют инкрементальные обновления для избежания избыточной работы.
*   Создавать надежные, долгосрочные инструменты для сбора данных, требующие минимальной настройки после первоначального развертывания.
*   Структурировать и сохранять неструктурированные социальные данные в структурированный, машиночитаемый формат (JSON) для последующих приложений.