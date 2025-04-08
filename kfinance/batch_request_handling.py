from concurrent.futures import ThreadPoolExecutor
import functools
from functools import cached_property
import threading
from typing import Any, Callable, Iterable, Protocol, Sized, Type, TypeVar

from requests.exceptions import HTTPError

from .fetch import KFinanceApiClient


T = TypeVar("T")

MAX_WORKERS_CAP: int = 10

throttle = threading.Semaphore(MAX_WORKERS_CAP)


def add_methods_of_singular_class_to_iterable_class(singular_cls: Type[T]) -> Callable:
    """Returns a decorator that sets each method, property, and cached_property of"""
    "[singular_cls] as an attribute of the decorated class."

    class IterableKfinanceClass(Protocol, Sized, Iterable[T]):
        """A protocol to represent a iterable Kfinance classes like Tickers and Companies.

        Each of these classes has a kfinance_api_client attribute.
        """

        kfinance_api_client: KFinanceApiClient

    def decorator(iterable_cls: Type[IterableKfinanceClass]) -> Type[IterableKfinanceClass]:
        """Decorator that adds methods, properties, and cached properties from"""
        """[singular_cls] as attributes to [iterable_cls].

        This decorator modifies the [iterable_cls] so that when an attribute
        (method, property, or cached property) added by the decorator is accessed,
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
            - If invoking an attribute results in a 400 or 500 HTTP error,
            the error is raised and bubbles up.
            - If the result is a 404 HTTP error, the corresponding value
            for that object in the dictionary will be set to None.

        Note:
            This decorator requires [iterable_cls] to be an iterable of
            instances of [singular_cls].
        """

        def process_in_thread_pool(
            executor: ThreadPoolExecutor, method: Callable, obj: T, *args: Any, **kwargs: Any
        ) -> Any:
            with throttle:
                future = executor.submit(method, obj, *args, **kwargs)
                try:
                    return future.result()
                except HTTPError as http_err:
                    error_code = http_err.response.status_code
                    if error_code == 404:
                        return None
                    else:
                        raise http_err

        def process_in_batch(
            method: Callable, self: IterableKfinanceClass, *args: Any, **kwargs: Any
        ) -> dict:
            results = {}
            kfinance_api_client = self.kfinance_api_client
            with kfinance_api_client.batch_request_header(batch_size=len(self)):
                with kfinance_api_client.thread_pool as executor:
                    results = dict(
                        zip(
                            self,
                            [
                                process_in_thread_pool(executor, method, obj, *args, **kwargs)
                                for obj in self
                            ],
                        )
                    )

            return results

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
                        return process_in_batch(method, self, *args, **kwargs)

                    return method_wrapper

                setattr(iterable_cls, method_name, create_method_wrapper(method))

            elif isinstance(method, property):

                def create_prop_wrapper(method: property) -> Callable:
                    assert method.fget is not None

                    @functools.wraps(method.fget)
                    def prop_wrapper(self: IterableKfinanceClass) -> Any:
                        assert method.fget is not None
                        return process_in_batch(method.fget, self)

                    return prop_wrapper

                setattr(iterable_cls, method_name, property(create_prop_wrapper(method)))

            elif isinstance(method, cached_property):

                def create_cached_prop_wrapper(method: cached_property) -> cached_property:
                    @functools.wraps(method.func)
                    def cached_prop_wrapper(self: IterableKfinanceClass) -> Any:
                        return process_in_batch(method.func, self)

                    wrapped_cached_property = cached_property(cached_prop_wrapper)
                    wrapped_cached_property.__set_name__(iterable_cls, method_name)
                    return wrapped_cached_property

                setattr(iterable_cls, method_name, create_cached_prop_wrapper(method))

        return iterable_cls

    return decorator
