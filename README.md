## Link Shortener

### Features

The project allows generating a short link for a given URL. Accessing the short link redirects users to the original URL. Additionally, there is an endpoint that provides link details, including the creator's IP address, user agent, and a visit counter showing how many times the short link has been accessed. All the endpoints are documented at http://localhost:8008/docs.

### Running

Project runs through Docker. Here are some useful commands:

- `make up` - Starts all services. The application will be available at http://localhost:8008.
- `make test` - Runs all tests.
