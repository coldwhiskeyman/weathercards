import peewee

database = peewee.SqliteDatabase("weather.db")


class BaseTable(peewee.Model):
    class Meta:
        database = database


class Weather(BaseTable):
    date = peewee.DateTimeField(unique=True)
    temperature = peewee.CharField()
    condition = peewee.CharField()


database.create_tables([Weather])
