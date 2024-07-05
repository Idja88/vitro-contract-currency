# vitro-contract-currency

## Описание

Проект представляет собой ETL-процесс, который загружает данные с сайта национального банка РК по курсам валют в виде Excel-файла, трансформирует их под соотношение валют 1:1, и загружает их в базу данных MS SQL Server, для дальнейшего построения отчета на платформе SSRS.

## Настройка

1. В корневой папке проекта необходимо создать `config.json` со следующей структурой:

```json
{
    "begin_date": "",
    "currency_code": {
        "USD": 5,
        "EUR": 6
    },
    "connection_string": "",
    "mail_message": {
        "from_email": "your@mail.com",
        "to_emails": [
            "your@mail.com",
            "your2@email.com"
        ],
        "smtp_server": "mail.server.com",
        "smtp_port": 25
    }
}
```
* `begin_date` - параметр, обозначающий, с какой даты по текущую необходимо получить исторический курс валют. Дату необходимо указывать в формате `%d.%m.%YYYY`. Если параметр не указан и остаётся пустым, то данные загружаются за текущий день.
* `connection_string` - параметр, строка подключения к базе данных MS SQL SERVER.
* `currency_code` - параметр, обозначающий, перечисление кодов валют и их идентификаторов на сайте национального банка РК. В качестве ключа параметра используется код валюты по стандарту ISO 4217 он же CurrencyCode, а в качестве значения используется Rate, ниже приведена таблица всех валют, по которым можно получить данные подставив необходимые значения.
* `mail_message` - составной параметр, указывающий подключение к SMTP серверу, а также перечень электронных адресов, на которые должно приходить уведомление при ошибках в работе ETL.

2. Создание необходимой таблицы БД

```sql
CREATE TABLE [dbo].[currency_history](
	[ID] [bigint] IDENTITY(1,1) NOT NULL,
	[Date] [datetime] NOT NULL,
	[CurrencyCode] [nvarchar](255) NOT NULL,
	[CurrencyValue] [float] NOT NULL,
PRIMARY KEY CLUSTERED 
(
	[Date] ASC,
	[CurrencyCode] ASC
) WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]
```

##### Таблица кодов валют

| Quantity | CurrencyName                                      | CurrencyCode | Rate |
|----------|---------------------------------------------------|--------------|------|
| 1        | АВСТРАЛИЙСКИЙ ДОЛЛАР                              | AUD          | 1    |
| 1        | АЗЕРБАЙДЖАНСКИЙ МАНАТ                             | AZN          | 48   |
| 10       | АРМЯНСКИЙ ДРАМ                                    | AMD          | 51   |
| 1        | БЕЛОРУССКИЙ РУБЛЬ                                 | BYN          | 38   |
| 1        | БРАЗИЛЬСКИЙ РЕАЛ                                  | BRL          | 46   |
| 10       | ВЕНГЕРСКИХ ФОРИНТОВ                               | HUF          | 42   |
| 1        | ГОНКОНГСКИЙ ДОЛЛАР                                | HKD          | 45   |
| 1        | ГРУЗИНСКИЙ ЛАРИ                                   | GEL          | 52   |
| 1        | ДАТСКАЯ КРОНА                                     | DKK          | 3    |
| 1        | ДИРХАМ ОАЭ                                        | AED          | 4    |
| 1        | ДОЛЛАР США                                        | USD          | 5    |
| 1        | ЕВРО                                              | EUR          | 6    |
| 1        | ИНДИЙСКАЯ РУПИЯ                                   | INR          | 49   |
| 1000     | ИРАНСКИЙ РИАЛ                                     | IRR          | 53   |
| 1        | КАНАДСКИЙ ДОЛЛАР                                  | CAD          | 7    |
| 1        | КИТАЙСКИЙ ЮАНЬ                                    | CNY          | 8    |
| 1        | КУВЕЙТСКИЙ ДИНАР                                  | KWD          | 9    |
| 1        | КЫРГЫЗСКИЙ СОМ                                    | KGS          | 10   |
| 1        | МАЛАЗИЙСКИЙ РИНГГИТ                               | MYR          | 47   |
| 1        | МЕКСИКАНСКИЙ ПЕСО                                 | MXN          | 54   |
| 1        | МОЛДАВСКИЙ ЛЕЙ                                    | MDL          | 13   |
| 1        | НОРВЕЖСКАЯ КРОНА                                  | NOK          | 14   |
| 1        | ПОЛЬСКИЙ ЗЛОТЫЙ                                   | PLN          | 39   |
| 1        | РИЯЛ САУДОВСКОЙ АРАВИИ                            | SAR          | 15   |
| 1        | РОССИЙСКИЙ РУБЛЬ                                  | RUB          | 16   |
| 1        | СДР                                               | XDR          | 17   |
| 1        | СИНГАПУРСКИЙ ДОЛЛАР                               | SGD          | 18   |
| 1        | ТАДЖИКСКИЙ СОМОНИ                                 | TJS          | 44   |
| 1        | ТАЙСКИЙ БАТ                                       | THB          | 50   |
| 1        | ТУРЕЦКАЯ ЛИРА                                     | TRY          | 41   |
| 100      | УЗБЕКСКИХ СУМОВ                                   | UZS          | 20   |
| 1        | УКРАИНСКАЯ ГРИВНА                                 | UAH          | 21   |
| 1        | ФУНТ СТЕРЛИНГОВ СОЕДИНЕННОГО КОРОЛЕВСТВА          | GBP          | 2    |
| 1        | ЧЕШСКАЯ КРОНА                                     | CZK          | 43   |
| 1        | ШВЕДСКАЯ КРОНА                                    | SEK          | 22   |
| 1        | ШВЕЙЦАРСКИЙ ФРАНК                                 | CHF          | 23   |
| 1        | ЮЖНО-АФРИКАНСКИЙ РАНД                             | ZAR          | 40   |
| 100      | ЮЖНО-КОРЕЙСКИХ ВОН                                | KRW          | 25   |
| 1        | ЯПОНСКАЯ ЙЕНА                                     | JPY          | 26   |