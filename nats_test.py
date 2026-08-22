import asyncio
import nats

async def main():
    nc = await nats.connect("nats://localhost:4222")

    print("Connected to NATS!")

    await nc.publish(
        "solstice.test",
        b"Hello from Solstice"
    )

    await nc.flush()

    print("Message published.")

    await nc.close()

if __name__ == "__main__":
    asyncio.run(main())
