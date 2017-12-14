import yaml
import random
from influxdb import InfluxDBClient
from influxdb.client import InfluxDBClientError
from datetime import datetime, timedelta


class MetricsHandler(object):
    def __init__(self, logger):
        self.logger = logger
        self.influxDbClient = self.get_influxdb_client('winty/influxdb.yaml')


    def get_influxdb_client(self, filepath):
        try:
            stream = open(filepath, "r")
            config = yaml.load(stream)
            config = config['configuration']
            client = InfluxDBClient(config['host'], config['port'], config['username'], config['password'], config['dbname'])
            return client
        except InfluxDBClientError:
            logger.error("Failed to connect to InfluxDB", exc_info=True)
        except Exception as e:
            logger.error('Failed to open file', exc_info=True)
        

    def write_metric(self, metric_name, values_dict, tags_dict, time=None):
        metric = {}

        json_body = [
            {
                "measurement": metric_name,
                "tags": tags_dict,
                "time": datetime.utcnow().isoformat() if time is None else time,
                "fields": values_dict
            }
        ]

        metric['measurement'] = metric_name
        metric['tags'] = tags_dict
        metric['time'] = datetime.utcnow().isoformat()
        metric['fields'] = values_dict
        if not self.influxDbClient.write_points(json_body):
            logger.error("Failed to write data to db", exc_info=True)
        

if __name__ == '__main__':
    # w = MetricsHandler(None)
    # if w.influxDbClient is not None:
    #     nb_day = 15  # number of day to generate time series
    #     timeinterval_min = 5  # create an event every x minutes
    #     total_minutes = 1440 * nb_day
    #     total_records = int(total_minutes / timeinterval_min)
    #     now = datetime.utcnow()
    #     metric = "balance"
    #     series = []

    #     for i in range(0, total_records):
    #         past_date = now - timedelta(minutes=i * timeinterval_min)
    #         value = random.random()

    #         tags = {}
    #         values = {}

    #         values['value'] = value
    #         tags['format'] = '24H' if value < .5 else 'Current'
    #         w.write_metric('balance', values, tags, past_date.isoformat())


    #     result = w.influxDbClient.query('select value from balance;')
    #     if result is not None:
    #         print (result)
    pass