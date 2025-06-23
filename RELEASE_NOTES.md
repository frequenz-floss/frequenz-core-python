# Frequenz Core Library Release Notes

## Summary

<!-- Here goes a general summary of what this release is about -->

## Upgrading

<!-- Here goes notes on how to upgrade from previous versions, including deprecations and what they should be replaced with -->

## New Features

<!-- Here goes the main new features and examples or instructions on how to use them -->

## Bug Fixes

* `BaseId` will now log instead of raising a warning when a duplicate prefix is detected. This is to fix [a problem with code examples](https://github.com/frequenz-floss/frequenz-repo-config-python/issues/421) being tested using sybil and the class being imported multiple times, which caused the exception to be raised. We first tried to use `warn()` but that complicated the building process for all downstream projects, requiring them to add an exception for exactly this warning.
