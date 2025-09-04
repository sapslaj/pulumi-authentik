#!/usr/bin/env python3
import json
import os
import shutil
import subprocess
from contextlib import contextmanager


@contextmanager
def not_found_ok():
    try:
        yield
    except FileNotFoundError:
        pass


def main():
    previous_version: str = ""
    if os.path.exists("package.json"):
        old_package_json = json.load(open("package.json"))
        previous_version = old_package_json.get("version", "")

    with not_found_ok():
        shutil.rmtree("src")
        os.remove("package.json")
        os.remove("package-lock.json")

    with open("Pulumi.yaml", "w") as fp:
        json.dump(
            fp=fp,
            obj={
                "name": "pulumi-authentik",
                "runtime": {
                    "name": "nodejs",
                    "options": {
                        "packagemanager": "npm",
                    },
                },
            },
        )
    subprocess.run(
        args=[
            "pulumi",
            "package",
            "add",
            "terraform-provider",
            "goauthentik/authentik",
        ],
        check=True,
    )

    with not_found_ok():
        os.remove("Pulumi.yaml")
        os.remove("package.json")
        os.remove("package-lock.json")
        shutil.rmtree("node_modules")

    shutil.move("./sdks/authentik", "./")
    shutil.rmtree("sdks")
    shutil.move("./authentik", "./src")
    os.remove("./src/README.md")

    package_json = json.load(open("./src/package.json"))
    package_json["name"] = "@sapslaj/pulumi-authentik"
    package_json["repository"] = "https://github.com/sapslaj/pulumi-authentik"
    package_json["main"] = "dist/index.js"
    package_json["types"] = "dist/index.d.ts"
    package_json["scripts"] = {
        "build": "tsc",
    }

    new_version = package_json["version"]
    print(f"{previous_version=} {new_version=}")
    if new_version != previous_version:
        print("marking publishable")
        with open(".publish", "w") as fp:
            fp.write("\n")

    os.remove("./src/package.json")
    with open("package.json", "w") as fp:
        json.dump(fp=fp, obj=package_json, indent=2)
        fp.write("\n")

    with not_found_ok():
        os.remove("./src/tsconfig.json")
        shutil.rmtree("./src/bin")
        shutil.rmtree("./src/scripts")

    subprocess.run(
        args=[
            "sh",
            "-c",
            "sed -i 's#./package.json#../package.json#g' src/*.ts",
        ],
        check=True,
    )

    subprocess.run(
        args=[
            "npm",
            "install",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
