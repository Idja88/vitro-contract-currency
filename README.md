# vitro-contract-currency

## Описание

Проект представляет собой ETL-процесс на языке Python, который получает и трансформирует данные сайта национального банка по курсам валют в виде Excel-файла в базу данных MS SQL Server, для дальнейшего построения отчета на платформе SSRS.

## Настройка

1. В корневой папке проекта необходимо создать `config.json` со следующей структурой:

```json
{   
    "currency_code": {"USD": 5, "EUR": 6},
    "connection_string" : ""
}
```
`currency_code` - параметр, с перечислением кодов валют и их идентификаторов на сайте национального банка.
`connection_string` - параметр подключения к базе данных MS SQL SERVER.

2. Создание необходиой таблицы БД

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