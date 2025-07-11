# Domains

Domains loosely correspond to datasets and permission boundaries. 
They are used to group together related tools and models, 
for example all earnings related tools and models.

There are no hard boundaries around what constitutes a domain. If you
think it makes sense to group certain tools or models together, it probably does.

Each domain will usually have a tools file with `KfinanceTools` and a
models file with enums, pydantic models, data classes, or typed dicts 
related to the domain. We may at some point also move ORM models related
to the domain into these sub folders. Each domain should have a `tests` 
directory for tool and model tests.