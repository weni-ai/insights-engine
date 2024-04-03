import json

from insights.event_driven.parsers.base_parser import BaseParser
from insights.event_driven.parsers.exceptions import ParseError


class JSONParser(BaseParser):
    @staticmethod
    def parse(stream, encoding="utf-8"):
        """
        Parses the incoming bytestream as JSON and returns the resulting data.
        """

        if not stream:
            raise ParseError("JSON parse error - stream cannot be empty")

        try:
            decoded_stream = stream.decode(encoding)
            return json.loads(decoded_stream)
        except ValueError as exc:
            raise ParseError("JSON parse error - %s" % str(exc))
