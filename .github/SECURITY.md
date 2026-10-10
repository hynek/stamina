# Security Policy

## Supported Versions

We're following [Calendar Versioning](https://calver.org) with generous backwards-compatibility guarantees.
Therefore, we only support the latest version.

That said, you shouldn't be afraid to upgrade if you only use our documented public APIs and pay attention to `DeprecationWarning`s.
Whenever there is a need to break compatibility, it is announced in the changelog and raises a `DeprecationWarning` for a year (if possible) before it's finally really broken.

> [!CAUTION]
> Do **not** use Tenacity's features through *stamina*.
> We cannot and do not guarantee that such leaking behavior will keep working in future releases.
> If you're missing a Tenacity feature that would be a good fit for *stamina*, please [open an issue](https://github.com/hynek/stamina/issues).


## Security Contact Information

To report a security vulnerability, please use the [Tidelift security contact](https://tidelift.com/security).
Tidelift will coordinate the fix and disclosure.
