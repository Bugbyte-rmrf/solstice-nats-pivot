import asyncio
import json
import random
import urllib.request
import nats

NATS_URL = "nats://localhost:4222"
PRINT_SUBJECT = "solstice.print.request"
WEBHOOK_URL = "http://127.0.0.1:8000/webhook/print-complete"
WEBHOOK_SECRET = "solstice-demo-secret"

async def main():
    nc = await nats.connect(NATS_URL)
    js = nc.jetstream()
    print("Vendor simulator connected.")

    async def process_message(message):
        data = json.loads(message.data.decode())
        print(f"Received print request for {data['attendee_id']}")
        
        delay = random.randint(2, 5)
        print(f"Simulating printer delay: {delay} seconds")
        
        await asyncio.sleep(delay)
        print(f"Print complete for {data['attendee_id']}")

        payload = json.dumps(
            {
                "attendee_id": data["attendee_id"],
                "job_id": data["job_id"]
            }
        ).encode()

        request = urllib.request.Request(
            WEBHOOK_URL,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "X-Webhook-Secret": WEBHOOK_SECRET
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(request) as response:
                print("Webhook response:", response.read().decode())
            await message.ack()
        except Exception as error:
            print("Webhook failed:", error)

    # JetStream consumer.
    psub = await js.pull_subscribe(
        PRINT_SUBJECT,
        durable="solstice-vendor"
    )
    print("Vendor waiting for print jobs...")

    while True:
        try:
            messages = await psub.fetch(1, timeout=5)
            for message in messages:
                await process_message(message)
        except asyncio.TimeoutError:
            continue

if __name__ == "__main__":
    asyncio.run(main())


