# -*- coding: utf-8 -*-

from natasha.span import Span
from natasha.doc import DocSpan
from natasha import Doc as BaseDoc


def adapt_spans(doc, spans):
    for span in spans:
        start, stop, type = span
        fact = getattr(span, 'fact', None)
        text = doc.text[start:stop]
        yield DocSpan(start, stop, type, text, fact=fact, normal=text)


def tag_ner_doc(doc, tagger, extractors=None):
    if not doc.text.strip():
        doc.spans = []
        return
    markup = tagger(doc.text)
    spans = markup.spans
    if extractors:
        matches = []
        for extractor in extractors:
            matches.extend(list(extractor(doc.text)))
        for match in matches:
            span = Span(match.start, match.stop, match.fact.__class__.__name__.upper())
            span.fact = match.fact
            spans.append(span)
    doc.spans = list(adapt_spans(doc, spans))
    doc.envelop_span_tokens()
    doc.envelop_sent_spans()


class Doc(BaseDoc):

    def tag_ner(self, tagger, extractors=None):
        tag_ner_doc(self, tagger, extractors=extractors)

