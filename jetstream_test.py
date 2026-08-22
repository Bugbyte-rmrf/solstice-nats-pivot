import asyncio
import nats

STREAM_NAME = "SOLSTICE"

async def main():
    nc = await nats.connect("nats://localhost:4222")

    js = nc.jetstream()

    try:
        await js.delete_stream(STREAM_NAME)
    except Exception:
        pass

    await js.add_stream(
        name=STREAM_NAME,
        subjects=["solstice.>"]
    )

    print("JetStream stream created.")

    ack = await js.publish(
        "solstice.test",
        b"Hello from JetStream"
    )

    print("Message stored:", ack)

    await nc.close()

if __name__ == "__main__":
    asyncio.run(main())
