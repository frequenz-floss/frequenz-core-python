# Frequenz Core Library Release Notes

## Upgrading

- If you used `enum.DeprecatedMember` directly anywhere, you should probably switch to using `enum.deprecated_member` instead, which will tag the member value with the appropriate type.

## New Features

- A new `enum.deprecated_member` function has been added to create deprecated enum members with proper typing.
