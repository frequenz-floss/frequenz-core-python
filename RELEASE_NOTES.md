# Frequenz Core Library Release Notes

## Summary

You can now warn callers when they use a deprecated module constant, type variable or type alias.

## Upgrading

- Replace calls to `deprecated_aliases()` with `deprecated_symbols()`. The arguments stay the same. Calling the old function emits a deprecation warning. It will be removed in v2.0.0.

## New Features

- Use `DeprecatedSymbol` for module attributes that cannot take the `@deprecated` decorator. You can pass `DeprecatedSymbol` and `DeprecatedAlias` entries to the same `deprecated_symbols()` call. Here is how to deprecate a timeout constant:

  ```python
  from datetime import timedelta
  from typing import TYPE_CHECKING, Final

  from frequenz.core.warnings import DeprecatedSymbol, deprecated_symbols

  __all__ = ["TIMEOUT", "TIMEOUT_SECONDS"]

  TIMEOUT: Final = timedelta(seconds=30)

  _TIMEOUT_SECONDS: Final = 30.0

  if TYPE_CHECKING:
      TIMEOUT_SECONDS: Final = _TIMEOUT_SECONDS
  else:
      __getattr__ = deprecated_symbols(
          __name__,
          # Warns "mypkg.TIMEOUT_SECONDS is deprecated. Use mypkg.TIMEOUT instead."
          DeprecatedSymbol(
              "TIMEOUT_SECONDS",
              value=_TIMEOUT_SECONDS,
              replacement="mypkg.TIMEOUT",
              since="v1.5.0",
          ),
      )
  ```

  Callers still get `value` when they use the deprecated name. Set `replacement` to the fully qualified name callers should use instead. Use `since` to record the version for documentation. To customize the warning, pass a `message` template with `{old}` and, if you provide a replacement, `{new}`. Without a replacement, the default warning is `<old> is deprecated.` Give callers a message that tells them what to do next.

## Bug Fixes

<!-- Here goes notable bug fixes that are worth a special mention or explanation -->
