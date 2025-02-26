import asyncio

# Create a dedicated background event loop
bg_loop = asyncio.new_event_loop()

def start_background_loop(loop):
    import asyncio
    asyncio.set_event_loop(loop)
    loop.run_forever()
