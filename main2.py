# TTFL Lab Impact
#
# Entry point
import re

from src.injuries import Injuries
from src.players import Players


if __name__ == '__main__':
    injuries = Injuries()
    ir = injuries.load_injury_report()
    print(ir)
