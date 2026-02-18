from unittest import TestCase
import meta2fdp


class ConverterTests(TestCase):
    def test_vcard_rdf(self):
        Converter = meta2fdp.parsers.hriconverter()
        # TODO Series object with dataset metadata.
        Converter.vcard_rdf()
