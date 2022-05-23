import dateutil.parser
from datetime import datetime, timezone

def UTCStr_to_LocalDate(UTC_str):
	"""
		switch UTC time to local timezone
		input: iso utc time string, ("2020-02-26T08:23:57.862296")
		output: iso time string (local timezone)
	"""
	utc_date = dateutil.parser.parse(UTC_str)
	local_date = utc_date.replace(tzinfo=timezone.utc).astimezone(tz=None)
	local_str = local_date.strftime("%Y-%m-%d %H:%M:%S.%f")
	return dateutil.parser.parse(local_str)



