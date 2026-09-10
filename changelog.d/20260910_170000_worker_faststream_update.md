### Other changes

- Update to faststream 0.7.5 and faststream-fastapi 1.3.1. faststream-fastapi 1.3.1 also now starts the broker inside the application lifespan rather than around it, so nothing in Squarebot's startup may rely on a connected broker (nothing did).
