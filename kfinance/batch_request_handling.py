from concurrent.futures import ThreadPoolExecutor, as_completed
import functools
from functools import cached_property
from typing import Any, Callable, Iterable, Protocol, Type

from requests.exceptions import HTTPError

from .fetch import KFinanceApiClient


MAX_BATCH_SIZE = 10


def add_methods_of_singular_class_to_iterable_class(singular_cls: Type) -> Callable:
    """Add each method of [singular_cls] to the decorated class.

    When the method is called, the result is dictionary mapping each object in the decorated class to the result of the method called on that object.
    Requires the decorated class to be an iterable of [singular_cls].
    """

    class IterableKfinanceClass(Protocol, Iterable):
        """A protocol to represent a iterable Kfinance classes like Tickers and Companies.

        Each of these classes has a kfinance_api_client attribute.
        """

        kfinance_api_client: KFinanceApiClient

    def decorator(iterable_cls: Type[IterableKfinanceClass]) -> Type:
        def process_in_batches(
            method: Callable, self: IterableKfinanceClass, *args: Any, **kwargs: Any
        ) -> dict:
            results = {}
            kfinance_api_client = self.kfinance_api_client
            instances = list(self)
            with kfinance_api_client.batch_request_header(batch_size=len(instances)):
                for i in range(0, len(instances), MAX_BATCH_SIZE):
                    batch = instances[i : i + MAX_BATCH_SIZE]
                    with ThreadPoolExecutor() as pool:
                        future_to_obj = {
                            pool.submit(method, obj, *args, **kwargs): obj for obj in batch
                        }
                        for future in as_completed(future_to_obj):
                            obj = future_to_obj[future]
                            try:
                                result = future.result()
                                results[obj] = result
                            except HTTPError as http_err:
                                error_code = http_err.response.status_code
                                if error_code == 404:
                                    results[obj] = None
                                else:
                                    raise http_err
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
                        return process_in_batches(method, self, *args, **kwargs)

                    return method_wrapper

                setattr(iterable_cls, method_name, create_method_wrapper(method))

            elif isinstance(method, property):

                def create_prop_wrapper(method: property) -> Callable:
                    assert method.fget is not None

                    @functools.wraps(method.fget)
                    def prop_wrapper(self: IterableKfinanceClass) -> Any:
                        assert method.fget is not None
                        return process_in_batches(method.fget, self)

                    return prop_wrapper

                setattr(iterable_cls, method_name, property(create_prop_wrapper(method)))

            elif isinstance(method, cached_property):

                def create_cached_prop_wrapper(method: cached_property) -> cached_property:
                    @functools.wraps(method.func)
                    def cached_prop_wrapper(self: IterableKfinanceClass) -> Any:
                        return process_in_batches(method.func, self)

                    wrapped_cached_property = cached_property(cached_prop_wrapper)
                    wrapped_cached_property.__set_name__(iterable_cls, method_name)
                    return wrapped_cached_property

                setattr(iterable_cls, method_name, create_cached_prop_wrapper(method))

        return iterable_cls

    return decorator
