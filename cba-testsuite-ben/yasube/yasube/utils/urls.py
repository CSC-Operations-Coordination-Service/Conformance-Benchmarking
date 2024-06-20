from urllib.parse import urlparse

from requests import Response


def urlfilename(response: Response) -> str:
    """
    Extracts the file name from the given response.
    It is expected to have a content-disposition header with
    the filename in it.
    """
    try:
        cd = response.headers["content-disposition"]
        # Content-Disposition is something like:
        # 'attachment; filename="MyFile.zip"'
        # or
        # 'attachment; filename="MyFile.zip"; creation-date="Wed, 07 Sep 2022 15";'
        # Sometime the double quote is missing.
        substring = "filename="
        start = cd.find(substring) + len(substring)
        end = cd.find(";", cd.find(substring))
        filename = cd[start : end > 0 and end or None]
        if filename.startswith('"'):
            filename = filename[1:]
        if filename.endswith('"'):
            filename = filename[:-1]
        return filename
    except KeyError:
        return urlparse(response.url).path.split("/")[-1]
