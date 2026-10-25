from dataclasses import dataclass
from datetime import date, datetime, timedelta
@dataclass(frozen=True)
class Shift:
    name: str
    weekday: int
    start: int
    end: int
    priority: int = 0

def compile_shifts(shifts: list[Shift], holidays: dict, first: date, stop: date) -> list:
    result=[]
    while first < stop:
        for shift in shifts:
            if shift.weekday == first.weekday():
                base=datetime.combine(first,datetime.min.time())
                result.append((base+timedelta(minutes=shift.start),base+timedelta(minutes=shift.end),shift.name,shift.priority))
        first+=timedelta(days=1)
    return result
