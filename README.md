# ProxyCheckerTgBot

Этот бот представляет собой мощный и эффективный чекер прокси, разработанный для обеспечения безопасности и надежности вашего интернет-соединения. С его помощью вы легко и быстро можете проверить работоспособность прокси-серверов, гарантируя стабильность вашего интернет-трафика.

<img src="img\Telegram_Mogs5CGuT0.png">

## Описание

Бот предоставляет пользователю возможность проверять прокси на их валидность. Прокси могут быть введены в текстовом формате или загружены с использованием документа.

## Использование

1. Отправьте боту текстовое сообщение с прокси или загрузите файл .txt с прокси.
2. Бот запустит проверку каждого прокси и сообщит вам о результатах.
3. Получите отчет о валидных и невалидных прокси.

## Запуск

Прежде чем запустить бота, убедитесь, что у вас установлены все необходимые библиотеки. Вы можете установить их, выполнив следующую команду:

```bash
pip install -r requirements.txt
```

Далее требуется настроить файл конфигурации `config.py`

```python
bot_token = '' # Токен бота

# Настройка платёжки
crystal_pay_status = True
crystal_pay_login = ''
crystal_pay_secret = ''
crystal_pay_salt = ''
```

После этого запустите бота
```
python main.py
```

## Выдача админа

Зайдите в `bot/database/db.json` найдите свой `user_id` и в нём уже задайте параметры `is_admin` и `is_super` как `true`


Script by <a href='https://github.com/reques6e' style='display: block; text-align: center;'>Requeste Project<img src='https://github.com/reques6e/reques6e/blob/main/assets/images.png?v=1' alt='Мой баннер' width='20' height='20' style='float: right;'></a>
