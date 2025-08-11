from concurrent.futures import Future
from dataclasses import dataclass, field
import functools
import threading
from typing import Any, Callable, Hashable, Iterable, Protocol, Sized, Type, TypeVar

from requests.exceptions import HTTPError

from kfinance.client.fetch import KFinanceApiClient


T = TypeVar("T")

MAX_WORKERS_CAP: int = 10

throttle = threading.Semaphore(MAX_WORKERS_CAP)


def add_methods_of_singular_class_to_iterable_class(singular_cls: Type[T]) -> Callable:
    """Returns a decorator that adds methods and properties from a singular to a plural class."""
    "[singular_cls] as an attribute of the decorated class."

    class IterableKfinanceClass(Protocol, Sized, Iterable[T]):
        """A protocol to represent a iterable Kfinance classes like Tickers and Companies.

        Each of these classes has a kfinance_api_client attribute.
        """

        kfinance_api_client: KFinanceApiClient

    def decorator(iterable_cls: Type[IterableKfinanceClass]) -> Type[IterableKfinanceClass]:
        """Adds functions from a singular class to an iterable class.

        This decorator modifies the [iterable_cls] so that when an attribute
        (method or property) added by the decorator is accessed,
        it returns a dictionary. This dictionary maps each object in [iterable_cls]
        to the result of invoking the attribute on that specific object.

        For example, consider a `Company` class with a `city` property and a
        `Companies` class that is an iterable of `Company` instances. When the
        `Companies` class is decorated, it gains a `city` property. Accessing this
        property will yield a dictionary where each key is a `Company` instance
        and the corresponding value is the city of that instance. The resulting
        dictionary might look like:

            {<kfinance.kfinance.Company object>: 'Some City'}

        Error Handling:
            - If the result is a 404 HTTP error, the corresponding value
            for that object in the dictionary will be set to None.
            - For any other HTTP error, the error is raised and bubbles up.

        Note:
            This decorator requires [iterable_cls] to be an iterable of
            instances of [singular_cls].
        """

        for method_name in dir(singular_cls):
            method = getattr(singular_cls, method_name)
            if method_name.startswith("__") or method_name.startswith("set_"):
                continue
            if callable(method):

                def create_method_wrapper(method: Callable) -> Callable:
                    @functools.wraps(method)
                    def method_wrapper(
                        self: IterableKfinanceClass, *args: Any, **kwargs: Any
                    ) -> dict:
                        return process_tasks_in_thread_pool_executor(
                            api_client=self.kfinance_api_client,
                            tasks=[
                                Task(func=method, args=(obj, *args), kwargs=kwargs, result_key=obj)
                                for obj in self
                            ],
                        )

                    return method_wrapper

                setattr(iterable_cls, method_name, create_method_wrapper(method))

            elif isinstance(method, property):

                def create_prop_wrapper(method: property) -> Callable:
                    assert method.fget is not None

                    @functools.wraps(method.fget)
                    def prop_wrapper(self: IterableKfinanceClass) -> Any:
                        assert method.fget is not None
                        return process_tasks_in_thread_pool_executor(
                            api_client=self.kfinance_api_client,
                            tasks=[
                                Task(func=method.fget, args=(obj,), result_key=obj) for obj in self
                            ],
                        )

                    return prop_wrapper

                setattr(iterable_cls, method_name, property(create_prop_wrapper(method)))

        return iterable_cls

    return decorator


@dataclass(kw_only=True)
class Task:
    """A task for batch processing.

    - args and kwargs are intended to be passed into the func as func(*args, **kwargs)
    - results from batch processing are returned as dicts. The result_key is usually
        something that either is an id (e.g. company_id) or has an id (e.g. Company
        or CompanyIdentifier), used to map from that key to the corresponding result.
    - The future is used to store the batch processing future. It should not be modified
        directly outside of process_tasks_in_thread_pool_executor.
    """

    func: Callable
    args: Any = field(default_factory=tuple)
    kwargs: Any = field(default_factory=dict)
    result_key: Hashable
    future: Future | None = field(init=False, default=None)


def process_tasks_in_thread_pool_executor(api_client: KFinanceApiClient, tasks: list[Task]) -> dict:
    """Execute a list of tasks in the api client's thread pool executor and return the results.

    Returns a dict mapping from each task's key to the corresponding result.
    """

    # Update access if necessary before submitting batch job.
    # If the batch job starts without a valid token, each thread may try to refresh it.
    assert api_client.access_token
    with api_client.batch_request_header(batch_size=len(tasks)):
        for task in tasks:
            # Acquire throttle before submitting the task
            throttle.acquire()
            future = api_client.thread_pool.submit(task.func, *task.args, **task.kwargs)
            # On success or failure, release the throttle.
            # This releases the throttle before the
            # `resolve_future_with_error_handling` call.
            future.add_done_callback(lambda f: throttle.release())
            task.future = future

        results = {}
        for task in tasks:
            assert task.future
            results[task.result_key] = resolve_future_with_error_handling(task.future)

    return results


def resolve_future_with_error_handling(future: Future) -> Any:
    """Return the result of a future with error handling for non-200 status codes.

    If request returned a 404, return None. Otherwise, raise the error.
    """
    try:
        return future.result()
    except HTTPError as http_err:
        error_code = http_err.response.status_code
        if error_code == 404:
            return None
        else:
            raise http_err
