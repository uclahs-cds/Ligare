import argparse


def parse_args():
    parser = argparse.ArgumentParser(
        description="BL_Python Web Project Scaffolding Tool"
    )
    _ = parser.add_argument(
        "-n",
        metavar="name",
        dest="name",
        required=True,
        type=str,
        help="The name of the application.",
    )
    template_types = ["basic", "openapi"]
    _ = parser.add_argument(
        "-t",
        choices=template_types,
        type=str,
        default="basic",
        help="The type of template to scaffold.",
    )
    modules = ["database"]
    _ = parser.add_argument(
        "-m",
        choices=modules,
        action="append",
        type=str,
        help="Optional modules to include in the application.",
    )

    return vars(parser.parse_args())


def scaffold():
    args = parse_args()
    print(args)
