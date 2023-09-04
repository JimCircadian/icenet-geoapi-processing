# Standard library
import json
import logging
import os
import pathlib
import time

# Third party
import azure.functions as func
from azure.eventgrid import EventGridPublisherClient, EventGridEvent
from azure.core.credentials import AzureKeyCredential

# Local
from .processor import Processor
from .utils import human_readable, InputBlobTriggerException


def main(event: func.EventGridEvent):
    result = json.dumps({
        'id': event.id,
        'data': event.get_json(),
        'topic': event.topic,
        'subject': event.subject,
        'event_type': event.event_type,
    })
    logging.info("Got event: {}".format(result))

    time_start = time.monotonic()
    data_filename = os.path.basename(event.subject)
    local_data_path = pathlib.Path(os.sep, "data", data_filename)

    processor = Processor(data_filename, 100000)
    try:
        processor.load(local_data_path)
        processor.update_geometries()
        processor.update_forecasts()
        processor.update_latest_forecast()
        processor.update_forecast_meta()
    except InputBlobTriggerException as exc:
        logging.error(f"{data_filename} Failed with message:\n{exc}")
    logging.info(f"{data_filename} Finished processing Azure blob: {local_data_path}")
    logging.info(
        f"{data_filename} Total time: {human_readable(time.monotonic() - time_start)}"
    )

    if "EVENTGRID_DOMAIN_KEY" in os.environ:
        domain_key = os.environ["EVENTGRID_DOMAIN_KEY"]
        domain_hostname = os.environ["EVENTGRID_DOMAIN_ENDPOINT"]
        domain_topic = os.environ["EVENTGRID_DOMAIN_TOPIC"]

        try:
            logging.info(f"Key supplied for event grid publishing, connecting to {domain_hostname}")
            credential = AzureKeyCredential(domain_key)
            client = EventGridPublisherClient(domain_hostname, credential)

            logging.info(f"Publishing icenet.forecast.processed event to {domain_topic}")
            client.send([
                EventGridEvent(
                    topic=domain_topic,
                    event_type="icenet.forecast.processed",
                    data={
                        "filename": f"{local_data_path}"
                    },
                    subject=f"{data_filename} has been processed into DB",
                    data_version="2.0"
                )
            ])
            logging.info(f"Event published")
        except Exception as ex:
            logging.exception(ex)
