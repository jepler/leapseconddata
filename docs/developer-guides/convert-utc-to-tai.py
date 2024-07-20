from datetime import timezone, datetime

from leapseconddata import LeapSecondData

my_date = datetime(2024, 7, 18, 22, 0, 0, tzinfo=timezone.utc)
data = LeapSecondData.from_standard_source()

my_tai_date = data.to_tai(my_date)
print(my_tai_date.isoformat())
