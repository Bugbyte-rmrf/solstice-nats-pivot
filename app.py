from uuid import uuid4
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse
from database import get_connection, initialize_database
from nats_service import (
    connect_nats,
    publish_print_request,
)

app = FastAPI(title="Solstice Event Check-In")
WEBHOOK_SECRET = "solstice-demo-secret"
nats_connection = None
jetstream = None

@app.on_event("startup")
async def startup():
    global nats_connection
    global jetstream

    initialize_database()

    nats_connection, jetstream = await connect_nats()

@app.on_event("shutdown")
async def shutdown():
    global nats_connection

    if nats_connection:
        await nats_connection.drain()

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Solstice Check-In</title>
        <style>
            body { font-family: Arial; max-width: 700px; margin: 40px auto; }
            button { padding: 12px; margin: 5px; }
            #status { margin-top: 25px; padding: 20px; border: 1px solid #ccc; }
        </style>
    </head>
    <body>
        <h1>Solstice Conference Check-In</h1>
        <button onclick="scan('A001')">Scan Alice</button>
        <button onclick="scan('A002')">Scan Brian</button>
        <button onclick="scan('A003')">Scan Carla</button>
        <div id="status">Ready for scan.</div>
        <script>
        async function scan(attendeeId) {
            const response = await fetch(`/scan/${attendeeId}`, { method: "POST" });
            const result = await response.json();
            document.getElementById("status").innerText = result.name + ": " + result.status;
            if (result.status === "PENDING") {
                waitForCompletion(attendeeId);
            }
        }
        async function waitForCompletion(attendeeId) {
            const response = await fetch(`/status/${attendeeId}`);
            const result = await response.json();
            document.getElementById("status").innerText = result.name + ": " + result.status;
            if (result.status === "PENDING") {
                setTimeout(() => waitForCompletion(attendeeId), 1000);
            }
        }
        </script>
    </body>
    </html>
    """

@app.post("/scan/{attendee_id}")
async def scan(attendee_id: str):
    connection = get_connection()
    attendee = connection.execute(
        """
        SELECT attendee_id, name, status, current_job_id
        FROM attendees
        WHERE attendee_id = ?
        """,
        (attendee_id,)
    ).fetchone()

    if attendee is None:
        connection.close()
        raise HTTPException(status_code=404, detail="Attendee not found")

    attendee_id, name, status, current_job_id = attendee

    if status == "CHECKED_IN":
        connection.close()
        return {"attendee_id": attendee_id, "name": name, "status": "ALREADY_CHECKED_IN"}

    if status == "PENDING":
        connection.close()
        return {"attendee_id": attendee_id, "name": name, "status": "PENDING"}

    job_id = str(uuid4())
    connection.execute(
        """
        UPDATE attendees
        SET status = 'PENDING', current_job_id = ?
        WHERE attendee_id = ?
        """,
        (job_id, attendee_id)
    )
    connection.commit()
    connection.close()

    await publish_print_request(jetstream, attendee_id, name, job_id)

    return {"attendee_id": attendee_id, "name": name, "status": "PENDING", "job_id": job_id}

@app.get("/status/{attendee_id}")
async def status(attendee_id: str):
    connection = get_connection()
    attendee = connection.execute(
        """
        SELECT attendee_id, name, status, current_job_id
        FROM attendees
        WHERE attendee_id = ?
        """,
        (attendee_id,)
    ).fetchone()
    connection.close()

    if attendee is None:
        raise HTTPException(status_code=404, detail="Attendee not found")

    return {"attendee_id": attendee[0], "name": attendee[1], "status": attendee[2], "job_id": attendee[3]}

@app.post("/webhook/print-complete")
async def print_complete(request: Request):
    secret = request.headers.get("X-Webhook-Secret")
    if secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    payload = await request.json()
    attendee_id = payload["attendee_id"]
    job_id = payload["job_id"]

    connection = get_connection()
    attendee = connection.execute(
        """
        SELECT status, current_job_id, completed_job_id
        FROM attendees
        WHERE attendee_id = ?
        """,
        (attendee_id,)
    ).fetchone()

    if attendee is None:
        connection.close()
        raise HTTPException(status_code=404, detail="Attendee not found")

    current_status = attendee[0]
    current_job_id = attendee[1]
    completed_job_id = attendee[2]

    if job_id != current_job_id:
        connection.close()
        return {"message": "Ignored stale or duplicate webhook"}

    if current_status == "CHECKED_IN" and completed_job_id == job_id:
        connection.close()
        return {"message": "Webhook already processed"}

    connection.execute(
        """
        UPDATE attendees
        SET status = 'CHECKED_IN', completed_job_id = ?
        WHERE attendee_id = ?
        """,
        (job_id, attendee_id)
    )
    connection.commit()
    connection.close()

    return {"message": "Check-in confirmed", "attendee_id": attendee_id, "job_id": job_id}
