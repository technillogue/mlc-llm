
"""Example code to turn a callback style engine into AsyncIO"""
import asyncio


# Sync API with callback
class EchoRequestState:
    def __init__(self, prompt, interval, stream_callback):
        self.prompts = prompt.split(" ")
        self.interval = interval
        self.stream_callback = stream_callback
        self.counter = 0
        self.finished = False

    def step(self):
        if self.counter % self.interval != 0:
            self.counter += 1
            return
        index = self.counter // self.interval
        if index >= len(self.prompts):
            # use none to indicate finished
            self.stream_callback(index, None)
            self.finished = True
        else:
            self.stream_callback(index, self.prompts[index])
            self.counter += 1


class EchoEngine:
    def __init__(self):
        self.active_requests = []

    def add_request(self, prompt, interval, stream_callback):
        """Add a request that echos back token at interval step"""
        self.active_requests.append(
            EchoRequestState(prompt, interval, stream_callback)
        )

    def step(self):
        new_active = []
        for req in self.active_requests:
            req.step()
            if not req.finished:
                new_active.append(req)
        self.active_requests = new_active


# Async API
class AsyncEngineDeadError(RuntimeError):
    pass

def _raise_exception_on_finish(task: asyncio.Task) -> None:
    msg = ("Task finished unexpectedly. This should never happen! "
           "Please open an issue on Github.")
    try:
        try:
            task.result()
        except asyncio.CancelledError:
            return
        except Exception as exc:
            raise AsyncEngineDeadError(
                msg + " See stack trace above for the actual cause.") from exc
        raise AsyncEngineDeadError(msg)
    except Exception as exc:
        raise exc


class AsyncStream:
    """Async output stream"""
    def __init__(self) -> None:
        self._queue = asyncio.Queue()
        self._finished = False

    def put(self, item: str) -> None:
        if self._finished:
            return
        self._queue.put_nowait(item)

    def finish(self) -> None:
        self._queue.put_nowait(StopIteration)
        self._finished = True

    @property
    def finished(self) -> bool:
        return self._finished

    def __aiter__(self):
        return self

    async def __anext__(self) -> str:
        result = await self._queue.get()
        if result is StopIteration:
            raise StopAsyncIteration
        elif isinstance(result, Exception):
            raise result
        return result


class AsyncEngine:
    def __init__(self):
        self.engine = EchoEngine()
        self.background_loop = None

    def _abort(self):
        """Customize this"""
        pass

    async def generate(self, prompt, interval, request_id) -> str:
        # pass from outside or generate from engine
        stream = AsyncStream()
        try:
            def stream_callback(index, value):
                if value is None:
                    stream.finish()
                else:
                    stream.put(value)

            self.engine.add_request(
                prompt, interval, stream_callback
            )
            async for output in stream:
                    yield output
        except (Exception, asyncio.CancelledError) as e:
            self._abort(request_id)

    async def _engine_loop(self):
        engine_step = 0
        while True:
            self.engine.step()
            await asyncio.sleep(0)
            engine_step += 1
            print(f"engine_step={engine_step}")

    def _engine_done_callback(self):
        pass

    @property
    def is_running(self) -> bool:
        return (self.background_loop is not None
                and not self.background_loop.done())

    def start_background_loop(self) -> None:
        """Start the background loop."""
        if self.is_running:
            raise RuntimeError("Background loop is already running.")

        # start with avent loop that drives the engine
        # use create_task so we do not have to await it
        self._background_loop_unshielded = asyncio.get_event_loop(
        ).create_task(self._engine_loop())
        # when we are done
        self._background_loop_unshielded.add_done_callback(_raise_exception_on_finish)
        self.background_loop = asyncio.shield(self._background_loop_unshielded)


async def generate_task(async_engine, prompt, interval):
    async for token in async_engine.generate(
        prompt, interval, request_id="dummpy"
    ):
        print(token)

async def main():
    print("start with ")
    engine = AsyncEngine()
    engine.start_background_loop()

    def create(prompt, interval):
        return asyncio.create_task(generate_task(engine, prompt, interval))
    tasks = [
        create("hello world", interval=1),
        create("you are so cool", interval=2),
        create("good job guy", interval=3)
    ]
    await asyncio.gather(*tasks)
    print("All finished")

asyncio.run(main())
