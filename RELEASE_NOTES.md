# Frequenz Core Library Release Notes

## Summary

This release introduces a better way to deprecate enum members.

## Upgrading

Even when this is a minor release, it ships with 2 potential breaking changes for users of `DeprecatedAlias` and `DeprecatedMember`:

- The standard warning of a `DeprecatedAlias` with `since` no longer includes the version: it is now `<old> is deprecated. Use <new> instead.` `since` is only used for the documentation now, following the Frequenz deprecation guide. Update tests matching the old wording.
- `DeprecatedMember.message` is now `str | None`, since a member declared with only `new_name` has its warning generated when the enum class is created. `DeprecatedMember` is not meant to be used directly, `deprecated_member()` is.

## New Features

- `DeprecatedAlias` now accepts `since` and `message` together, or neither: `since` is only for the documentation, and `message` only replaces the warning. This lets an alias with a custom warning still say since which version it is deprecated in its documentation.
- `deprecated_member()` takes the replacement and version as structured, keyword-only arguments, like `DeprecatedAlias`: `new_name`, the member to use instead in the same enum, and `since`, the version it is deprecated since, for the documentation only. With `new_name` the `message` can be omitted, and the warning is generated with fully qualified names:

  ```python
  class TaskStatus(Enum):
      OPEN = 1
      # Warns "mypkg.TaskStatus.PENDING is deprecated. Use mypkg.TaskStatus.OPEN instead."
      PENDING = deprecated_member(1, new_name="OPEN", since="v1.2.0")
  ```

  The enum class checks that `new_name` is one of its members and is not deprecated itself. Existing calls passing a `message` keep working unchanged.

  [`griffe-frequenz-core`](https://github.com/frequenz-floss/griffe-frequenz-core) will read `since` and `new_name` to generate the documentation notice of these members.

## Bug Fixes

- Docstrings now use absolute cross-references to public paths instead of relative ones. Relative cross-references are expanded from the module where an object is defined since mkdocstrings-python 2.0.9, which broke some links, and projects rendering docstrings inherited from this library needed `relative_crossrefs: true` for them to work at all. See [frequenz-repo-config-python#655](https://github.com/frequenz-floss/frequenz-repo-config-python/issues/655) for details.
