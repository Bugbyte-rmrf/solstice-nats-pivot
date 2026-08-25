# Solstice Event Check-In: Asynchronous Architecture Pivot

## Overview
This project is an event-driven conference check-in system built with Python, FastAPI, SQLite, and NATS JetStream. It demonstrates a pivot from a synchronous REST architecture (which blocks the UI while waiting for a physical printer) to a fully asynchronous, event-driven architecture using message queues and webhooks.

## Architecture & Data Flow
1. **Kiosk (Browser):** User clicks to scan an attendee badge.
2. **FastAPI (`app.py`):** Saves the attendee state as `PENDING`, generates a unique `job_id`, and publishes a print request to NATS JetStream.
3. **NATS JetStream:** Persists the message in the `SOLSTICE` stream.
4. **Vendor Simulator (`vendor_simulator.py`):** A standalone worker that pulls the job from the queue, simulates a physical printing delay, and fires a webhook.
5. **Webhook Endpoint:** Receives the completion event, validates the payload and security headers, and updates the database state to `CHECKED_IN`.

## Infrastructure Pivot (The NATS Server)
Initially, this project intended to use Docker for containerization (`compose.yaml`). Due to local WSL2/Docker socket virtualization blockers (`Cannot connect to the Docker daemon`), the infrastructure was successfully pivoted to run a pre-compiled native Linux NATS binary (`nats-server`) in the background.

## Project Structure
* **`.gitignore` & `requirements.txt`:** Environment and dependency management.
* **`compose.yaml`:** Original Docker configuration (pre-pivot).
* **`nats_test.py` & `jetstreams_test.py`:** Initial pub/sub proof-of-concept scripts.
* **`database.py`:** SQLite setup, schema creation, and initialization of test attendees (Alice, Brian, Carla).
* **`nats_service.py`:** Core NATS connection and JetStream publishing logic.
* **`app.py`:** The main FastAPI web server and webhook receiver.
* **`vendor_simulator.py`:** Asynchronous consumer acting as the external printer.
* **`SCOPE_DELTA.md`:** Documentation of the architectural pivot and trade-offs.
* **`TEST_RESULTS.md`:** Regression testing results for the end-to-end flow.
* **`TIME_LOG.md`:** Planned vs. actual time tracking.

## How to Run

### **1. Start the NATS Server**
Run the native binary in the background with JetStream enabled:
```bash
./nats-server -js -m 8222 &
```

### **2. Start the FastAPI Application**
Activate your virtual environment and start the web server:
```bash
source .venv/bin/activate
fastapi dev app.py
```
*The UI is available at `http://127.0.0.1:8000` and docs at `/docs`.*

### **3. Start the Vendor Simulator**
In a separate terminal, activate the environment and start the consumer:
```bash
source .venv/bin/activate
python3 vendor_simulator.py
```

## **Key Resiliency Features**
* **Duplicate Scan Protection:** If an attendee is scanned multiple times while PENDING, the system ignores the subsequent requests without creating duplicate print jobs.
* **Webhook Authentication:** The webhook endpoint requires a valid `X-Webhook-Secret` header, returning a `401 Unauthorized` if validation fails.
* **Stale Webhook Rejection:** Completion events are tied to a specific `job_id`, not just the attendee. If a delayed webhook arrives for an old print job, it is safely ignored, preventing outdated events from overwriting the current state.
