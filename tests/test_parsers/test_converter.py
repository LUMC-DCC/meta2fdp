from unittest import TestCase
from .context import samplenavigator2fdp


class ConverterTests(TestCase):

    def test_vcard_rdf():
        Converter = samplenavigator2fdp.parsers.hriconverter()
        #TODO Series object with dataset metadata.
        Converter.vcard_rdf()

