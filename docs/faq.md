# FAQ

## How do I debug interpolation errors?
- Use `${...}` only for values that exist at the time of resolution.
- If you see `Unknown variable` errors, check for typos or missing includes.

## Can I use yamlo with secrets managers?
- Yes! Use `!env` with environment variables populated by your secrets manager.

## How do I reference Python objects in other parts of the config?
- Use `id:` in your `!@` tags and reference with `${id}` or `${id.attr}`.

## How do I include files from a Python package?
- Use the tuple syntax: `["file.yaml", "package_name"]` in `_includes`.

## Can I use yamlo for machine learning pipelines?
- Absolutely! See the [API Reference](api.md) for a full ML pipeline example.

## How do I validate my config?
- Use `yamlo` in your CI to load and resolve all configs. If it loads, it's valid!

---

Still have questions? [Open an issue](https://github.com/your-username/yamlo/issues) or check the [API Reference](api.md).
