import os
import re
import urllib.parse
from datetime import datetime
from random import choice, randint

import geopandas
from dateutil.relativedelta import relativedelta

from yasube.data.product_types import PRODUCT_TYPES, PRODUCT_TYPES_PATTERN

PATTERNS = {
    "date": re.compile("{{\s*NOW\s*((?P<action>(\+|-))\s*(?P<amount>[\d]+)(?P<unit>(d|D|m|M|y|Y))){0,1}\s*}}"),
    "product_type": re.compile("{{\s*PRODUCT\s*(?P<sat>(S1|S2|S3))?\s*(?P<level>(L0|L1|L2|AUX))?\s*}}"),
    "geo": re.compile("{{\s*GEO\s*(?P<preset>(RANDOM|EUR|MED))\s*}}"),
}


class ShapeHelper:

    SHAPES_FILE = "../data/borders/TM_WORLD_BORDERS-0.3.shp"
    EUR = "Polygon((31.6 71.2,20.7 71.2,-10.8 56.6,-10.5 34.8,31.6 34.8,31.6 71.2))"
    MED = "Polygon((-9.84 27.99,48.87 27.99,48.87 48.46,-9.84 48.46,-9.84 27.99))"
    ISO2 = [
        "BA",
        "BG",
        "DK",
        "IE",
        "AT",
        "CZ",
        "FI",
        "FR",
        "DE",
        "GR",
        "HR",
        "HU",
        "IS",
        "IT",
        "BE",
        "LU",
        "NL",
        "NO",
        "PL",
        "PT",
        "ES",
        "SE",
        "CH",
        "TR",
        "GB",
        "UA",
    ]
    POINT_PATTERN = re.compile("[\d]+.[\d]+")

    def __init__(self):
        shapes_file = os.path.join(os.path.dirname(__file__), self.SHAPES_FILE)
        self.shapes = geopandas.read_file(shapes_file)

    def adapt_polygon(self, polygon: str) -> str:
        """Returns the polygon string in a format compatible with the API."""
        points = self.POINT_PATTERN.findall(polygon)
        for point in points:
            polygon = polygon.replace(point, str(round(float(point), 6)))

        return polygon.replace("POLYGON ", "Polygon").replace(", ", ",")

    def get_random_country(self) -> str:
        iso2 = choice(self.ISO2)
        return self.adapt_polygon(self.get_iso_polygon(iso2))

    def get_iso_polygon(self, iso2: str) -> str:
        shape = self.shapes[self.shapes.ISO2 == iso2]
        simplified_shape = shape.geometry.simplify(0.5).convex_hull
        for geometry in simplified_shape.to_dict().values():
            # Should be only one, haven't find a better way
            polygon = str(geometry)
        return polygon


class Template:
    @staticmethod
    def _date(value: str, match: re.Match, pattern: re.Pattern) -> str:
        """Replaces a date template with an iso formatted date string.
        Templates are expected to be in the following format:
        {{ NOW [+|-] XY }}
        where Y can be 'd' or 'D' for days, 'm' or 'M' for months and 'y' or 'Y'
        for years and X the amount of those.
        """
        action = match.groupdict()["action"]
        amount = int(match.groupdict()["amount"])
        unit = match.groupdict()["unit"]

        if unit in "dD":
            delta = relativedelta(days=amount)
        elif unit in "mM":
            delta = relativedelta(months=amount)
        elif unit in "yY":
            delta = relativedelta(years=amount)

        if action == "+":
            out = datetime.now() + delta
        else:
            out = datetime.now() - delta

        return re.sub(pattern, f"{out.isoformat(timespec='seconds')}Z", value)

    @staticmethod
    def _product_type(value: str, match: re.Match, pattern: re.Pattern) -> str:
        """Replaces a product type template with a random product type.
        See the docstring for the PRODUCT_TYPES constant.
        """
        sat = match.groupdict().get("sat")
        level = match.groupdict().get("level")
        if sat is not None and level is not None:
            rules = PRODUCT_TYPES.get(sat, {}).get(level, [])
        elif sat is not None and level is None:
            rules = [t for i in PRODUCT_TYPES.get(sat, {}).values() for t in i]
        elif sat is None and level is not None:
            rules = []
            # There must be a more pythonic way, but at list is half-readable...
            types = [PRODUCT_TYPES[k] for k in PRODUCT_TYPES.keys()]
            for type_ in types:
                rules.extend([types_ for level_, types_ in type_.items() if level_ == level])

            rules = [rule for i in rules for rule in i]

        rule = choice(rules)
        matches = PRODUCT_TYPES_PATTERN.finditer(rule)
        for match in matches:
            pattern_ = match.groupdict()["pattern"]
            if "|" in pattern_:
                choices = pattern_.split("|")
                rule = rule.replace(pattern_, choice(choices))
            elif ".." in pattern_:
                start, end = map(int, pattern_.split(".."))
                rule = rule.replace(pattern_, str(randint(start, end)))
        rule = rule.replace("[", "").replace("]", "")
        return re.sub(pattern, rule, value)

    @staticmethod
    def _geo(value: str, match: re.Match, pattern: re.Pattern) -> str:
        """Replaces a geo template with one of the provided preset.
        It can be:
        - MED: It will return an approximated polygon for the Mediterranean sea.
        - EUR: It will return an approximated polygon for EC.
        - RANDOM: It will return a convex_hull for a random European country.
        """
        shape_helper = ShapeHelper()
        preset = match.groupdict()["preset"]
        if preset == "MED":
            polygon = shape_helper.MED
        elif preset == "EUR":
            polygon = shape_helper.EUR
        else:
            polygon = shape_helper.get_random_country()
        return re.sub(pattern, polygon, value)

    @staticmethod
    def replace(value: str) -> str:
        """Entry point. It handles all preconfigured templates and
        replaces them with actual values.

        If no match is found within the value passed in, it will
        return it as it is.

        Refer to the PATTERNS constant for the available options.
        """
        for method_name, pattern in PATTERNS.items():
            match = pattern.search(value)
            if match is not None:
                method = getattr(Template, f"_{method_name}")
                return method(value, match, pattern)

        return value


class UrlHelper:
    @staticmethod
    def build(root_uri: str, path: str, query: str = None) -> str:
        url = urllib.parse.urljoin(root_uri, path)
        if query is not None:
            query = Template.replace(query)
            return f"{url}?{query}"
        return url
