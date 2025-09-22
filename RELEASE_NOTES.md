# Frequenz Core Library Release Notes

## Summary

## New Features

* `frequenz.core.enum` now provides a `@unique` decorator that is aware of deprecations, and will only check for uniqueness among non-deprecated enum members.

    For example this works:

    ```py
    >>> from frequenz.core.enum import DeprecatedMember, Enum, unique
    >>> 
    >>> @unique
    ... class Status(Enum):
    ...     ACTIVE = 1
    ...     INACTIVE = 2
    ...     PENDING = DeprecatedMember(1, "PENDING is deprecated, use ACTIVE instead")
    ... 
    >>> 
    ```

    While using the standard library's `enum.unique` decorator raises a `ValueError`:

    ```py
    >>> from enum import unique
    >>> from frequenz.core.enum import DeprecatedMember, Enum
    >>> 
    >>> @unique
    ... class Status(Enum):
    ...     ACTIVE = 1
    ...     INACTIVE = 2
    ...     PENDING = DeprecatedMember(1, "PENDING is deprecated, use ACTIVE instead")
    ... 
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/usr/lib/python3.12/enum.py", line 1617, in unique
        raise ValueError('duplicate values found in %r: %s' %
    ValueError: duplicate values found in <enum 'Status'>: PENDING -> ACTIVE
    >>> 
    ```
