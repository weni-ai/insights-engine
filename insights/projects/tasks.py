import logging
from insights.celery import app


logger = logging.getLogger(__name__)


@app.task
def test(arg):
    print(arg)
    logger.info(arg)
