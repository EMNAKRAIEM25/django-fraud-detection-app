from django.utils.timezone import make_aware
import csv
from django.core.management.base import BaseCommand
from users.models import fraudTrain
import datetime
from devsearch import settings
from dateutil import parser 
from django.utils.timezone import make_aware, get_default_timezone
from django.utils import timezone


from itertools import islice

class Command(BaseCommand):
    help = 'Load data from fraudTrain file'

    def handle(self, *args, **kwargs):
        datafile = settings.BASE_DIR / 'fraudTrain.csv'

        default_timezone = get_default_timezone()

        with open(datafile, 'r') as csvfile:
            reader = csv.DictReader(islice(csvfile, 0, 1500))

            for row in reader:
                trans_date_trans_time_str = row['trans_date_trans_time']
                trans_date_trans_time = datetime.datetime.strptime(trans_date_trans_time_str, "%Y-%m-%d %H:%M:%S")
                trans_date_trans_time = make_aware(trans_date_trans_time, timezone=default_timezone)

                fraudTrain.objects.get_or_create(
                    trans_date_trans_time=trans_date_trans_time,
                    cc_num=row['cc_num'],
                    merchant=row['merchant'],
                    category=row['category'],
                    amt=row['amt'],
                    first=row['first'],
                    last=row['last'],
                    gender=row['gender'],
                    street=row['street'],
                    city=row['city'],
                    state=row['state'],
                    zip=row['zip'],
                    lat=row['lat'],
                    long=row['long'],
                    city_pop=row['city_pop'],
                    job=row['job'],
                    dob=row['dob'],
                    trans_num=row['trans_num'],
                    unix_time=row['unix_time'],
                    merch_lat=row['merch_lat'],
                    merch_long=row['merch_long'],
                    is_fraud=row['is_fraud']
                )
