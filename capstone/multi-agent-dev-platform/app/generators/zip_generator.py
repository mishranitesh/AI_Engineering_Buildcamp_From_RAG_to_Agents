import zipfile


def create_zip(project_dir):

    zip_path = f"{project_dir}.zip"

    with zipfile.ZipFile(
        zip_path,
        "w",
        zipfile.ZIP_DEFLATED
    ) as zipf:

        for file in project_dir.rglob("*"):

            if file.is_file():

                zipf.write(
                    file,
                    file.relative_to(project_dir)
                )

    return zip_path