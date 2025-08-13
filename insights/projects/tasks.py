from insights.celery import app


@app.task
def test(arg):
    print(arg)
