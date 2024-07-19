from datetime import date, timedelta

from leapseconddata import LeapSecondData

my_date = date(2015, 12, 31)
data = LeapSecondData.from_standard_source()

for leap in data.leap_seconds:
    time = leap.start - timedelta(seconds=1)
    if my_date.year == time.year and my_date.month == time.month and my_date.day == time.day:
        print(f"{my_date} has a leap second!")
        break
else:
    print(f"{my_date} does not have a leap second.")
