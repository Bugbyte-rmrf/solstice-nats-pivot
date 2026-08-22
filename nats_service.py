import json
import nats

NATS_URL = "nats://localhost:4222"
STREAM_NAME = "SOLSTICE"
PRINT_SUBJECT = "solstice.print.request"

async def connect_nats():
    connection = await nats.connect(NATS_URL)
    jetstream = connection.jetstream()

    try:
        await jetstream.stream_info(STREAM_NAME)
    except Exception:
        await jetstream.add_stream(
            name=STREAM_NAME,
            subjects=["solstice.>"]
        )

    return connection, jetstream

async def publish_print_request(
    jetstream,
    attendee_id,
    name,
    job_id
):
    message = {
        "attendee_id": attendee_id,
        "name": name,
        "job_id": job_id
    }

    result = await jetstream.publish(
        PRINT_SUBJECT,
        json.dumps(message).encode()
    )

    return result
