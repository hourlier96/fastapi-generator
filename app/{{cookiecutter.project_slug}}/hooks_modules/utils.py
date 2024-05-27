import os
import re


def remove_reference_from_project(pattern):
    """
    Iterate on all files to find a matching
    pattern & remove all lines containing it
    """
    for root, subdirs, files in os.walk("."):
        # print("--\nroot = " + root)
        # for subdir in subdirs:
        # print("\t- subdirectory " + subdir)
        for filename in files:
            file_path = os.path.join(root, filename)
            # print("\t- file %s (full path: %s)" % (filename, file_path))
            with open(file_path, "rb") as f:
                f_content = f.read()
                if re.search(bytes(pattern, encoding="utf-8"), f_content):
                    # print(f"Found {pattern} in file: " + file_path)
                    # print("Removing...")
                    with open(file_path, "w") as f:
                        f.write(
                            re.sub(
                                f"\r?\n.*{pattern}.*",
                                "",
                                f_content.decode("utf-8", errors="ignore"),
                            )
                        )


def remove_decorated_function(file_path, decorator):
    # Read the content of the file
    with open(file_path, "r") as file:
        content = file.read()

    # Define the regex pattern to match a function
    # decorated with the specified decorator
    pattern = r"@{}\s*\n(?:async\s+)?def\s+\w+\([^)]*\)\s*:.*?\n\n".format(decorator)

    matches = re.findall(pattern, content, flags=re.DOTALL)
    if matches:
        # Remove each matched function from the content
        for match in matches:
            content = content.replace(match, "")
        # Write the modified content back to the file
        with open(file_path, "w") as file:
            file.write(content)
