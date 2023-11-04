# TTFL Lab Impact
#
# Entry point
import re

from src.ttfl import *
import sys
import getopt


def print_help():
    print('main.py -d <day_to_generate> -f <force_refresh> -s <season> -t <season_type>')
    print('\t<day_to_generate> mm/dd/yyyy (default: today)')
    print('\t<force_refresh> True or False (default: False)')
    print('\t<season> yyyy-yy (default: 2023-24)')
    print('\t<season_type> RegularSeason, PlayOff (default: RegularSeason)')


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hd:f:s:t:",
                                   ["help", "day=", "force-refresh=", "season=", "season-type="])
    except getopt.GetoptError:
        print_help()
        sys.exit(2)

    arg_force_refresh = False
    arg_day = None
    arg_season = None
    arg_season_type = None

    for opt, arg in opts:
        if opt in ("-d", "--day"):
            arg_day = arg
        elif opt in ("-f", "--force-refresh"):
            arg_force_refresh = bool(arg)
        elif opt in ("-s", "--season"):
            arg_season = arg
        elif opt in ("-t", "--season-type"):
            arg_season_type = arg
        else:
            print_help()
            sys.exit()

    ttlf_lab_impact_start(day=arg_day, season=arg_season, season_type=arg_season_type, force_refresh=arg_force_refresh)
