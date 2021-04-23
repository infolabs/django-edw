# -*- coding: utf-8 -*-

from jsonfield.fields import JSONField

from django.utils.translation import ugettext_lazy as _

from natasha import (
    Segmenter,
    MorphVocab,

    DatesExtractor,
    MoneyExtractor,
    NamesExtractor,

    NewsEmbedding,
    NewsMorphTagger,
    NewsSyntaxParser,
    NewsNERTagger,

    PER,
    LOC,
    ORG
)

from edw.models.mixins import ModelMixin
from edw.models.mixins.entity.nlp import Doc


class NERMixin(ModelMixin):
    """
    Миксин для работы с NER. Добавляет в модель методы получения списка именованных сущностей, а также прочие методы,
    необходимые для работы с ними
    """

    EXTRACTED_TYPES = [PER, LOC, ORG, 'DATE', 'MONEY']

    ner_data = JSONField(verbose_name=_("NER data"), default={},
        help_text=_("Data obtained after recognition of named entities for the given text"))

    def get_ner_source(self):
        '''
        Метод для получения исходных данных для получения именованных сущностей. Требуется перекрыть в модели где осуществляется
        примешивание
        :return:
        '''
        return self.entity_name

    @classmethod
    def get_extracted_types(cls):
        return cls.EXTRACTED_TYPES

    @classmethod
    def get_segmenter(cls):
        segmenter = getattr(cls, "_segmenter", None)
        if not segmenter:
            segmenter = Segmenter()
            cls._segmenter = segmenter
        return segmenter

    @classmethod
    def get_morph_vocab(cls):
        morph_vocab = getattr(cls, "_morph_vocab", None)
        if not morph_vocab:
            morph_vocab = MorphVocab()
            cls._morph_vocab = morph_vocab
        return morph_vocab

    @classmethod
    def get_extractors(cls):
        extractors = getattr(cls, "_extractors", None)
        if not extractors:
            morph_vocab = cls.get_morph_vocab()
            extractors = [DatesExtractor(morph_vocab), MoneyExtractor(morph_vocab)]
            cls._extractors = extractors
        return extractors

    @classmethod
    def init_pipeline_methods(cls):
        embedding = NewsEmbedding()
        cls.morph_tagger = NewsMorphTagger(embedding)
        cls.syntax_parser = NewsSyntaxParser(embedding)
        cls.ner_tagger = NewsNERTagger(embedding)

    @property
    def doc(self):
        _doc = Doc(self.get_ner_source())
        _doc.segment(self.get_segmenter())
        return _doc

    def _extract_ner(self):
        # Init doc object
        doc = self.doc

        # Get morph vocabulary
        morph_vocab = self.get_morph_vocab()

        # Init taggers and syntax parsers
        self.init_pipeline_methods()

        # Apply morph
        doc.tag_morph(self.morph_tagger)

        # Lemmatize
        for token in doc.tokens:
            token.lemmatize(morph_vocab)

        # Parse syntax
        doc.parse_syntax(self.syntax_parser)

        # NER extract
        doc.tag_ner(self.ner_tagger, extractors=self.get_extractors())

        # Normalize data
        if doc.spans:
            for span in doc.spans:
                span.normalize(morph_vocab)

        # Extend person data
        if doc.spans:
            names_extractor = NamesExtractor(morph_vocab)
            for span in doc.spans:
                if span.type == PER:
                    span.extract_fact(names_extractor)

        # Get result
        result = {}
        extracted_types = self.get_extracted_types()
        for _ in doc.spans:
            span_type = _.type
            if span_type in extracted_types:
                if not span_type in result:
                    result.update({span_type: []})
                data = _.as_json
                result[span_type].append(data)

        return result

    def extract_ner(self):
        self.ner_data = self._extract_ner()
        self.save()

    @property
    def highlighter_context(self):
        result = []
        _already_append = []
        for span_type in self.ner_data.keys():
            for ner_data_by_type in self.ner_data[span_type]:
                text = ner_data_by_type['text']
                if not text in _already_append:
                    _already_append.append(text)
                    result.append({
                        'text': text,
                        'type': span_type.lower(),
                    })
        return result