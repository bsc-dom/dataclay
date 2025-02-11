def pytest_addoption(parser):
    parser.addoption(
        "--build-legacy-deps",
        action="store_true",
        help="Build docker image with legacy dependencies",
    )
