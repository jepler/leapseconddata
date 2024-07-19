from datetime import datetime

from leapseconddata import LeapSecondData, tai

my_date = datetime(2024, 7, 18, 22, 0, 37, tzinfo=tai)
data = LeapSecondData.from_standard_source()

my_tai_date = data.tai_to_utc(my_date)
print(my_tai_date.isoformat())
