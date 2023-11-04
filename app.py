# Copyright 2023 Webyn
import logging
import os

from flask import Flask, request, Response, send_file
from src.ttfl import *

app = Flask(__name__)

logger = logging.getLogger()

# Test route to check if the server is running
@app.route("/", methods=["GET"])
def index() -> Response:
    args = request.args

    day = args.get("day", default=None, type=str)
    season = args.get("season", default=None, type=str)
    season_type = args.get("season_type", default=None, type=str)
    force_refresh = args.get("force_refresh", default=False, type=str)

    filename = ttlf_lab_impact_start(day=day, season=season, season_type=season_type, force_refresh=force_refresh)

    return send_file(filename, mimetype='application/ms-excel')


if __name__ == "__main__":
    logger.info('TTFF Impact flask is running')
    app.run(
        host=os.environ.get("HOST", "127.0.0.1"),
        port=os.environ.get("PORT", 8080),
        debug=True
    )
