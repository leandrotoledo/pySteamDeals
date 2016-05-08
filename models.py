from peewee import *

db = SqliteDatabase('deals.db')


class Deals(Model):
    id = PrimaryKeyField(unique=True)
    title = CharField()
    link = CharField()
    discount = IntegerField()
    original_price = FloatField()
    discounted_price = FloatField()


def create_tables():
    db.connect()
    db.create_tables([Deals,])


if __name__ == '__main__':
    create_tables()
