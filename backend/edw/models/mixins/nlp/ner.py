# -*- coding: utf-8 -*-


from jsonfield.fields import JSONField
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
from celery.utils.log import get_logger

from django.utils.translation import ugettext_lazy as _

from edw.models.mixins import ModelMixin
from edw.models.mixins.nlp import Doc
from edw.tasks import extract_ner_data


class NERMixin(ModelMixin):
    """
    Миксин для работы с NER. Добавляет в модель методы получения списка именованных сущностей, а также прочие методы,
    необходимые для работы с ними
    """

    EXTRACTED_TYPES = [PER, LOC, ORG, 'DATE', 'MONEY']

    NO_INDEX_TYPES = [PER, LOC, 'DATE', 'MONEY']

    REPLACERS = [
        ('&nbsp;|&ensp;|&emsp;', ' '),
        ('&quot;|«|&laquo;|»|&raquo;', '\"'),
        ('&ndash;|&mdash;', '-'),
        ('&gt;', '>'),
        ('&lt;', '<'),
    ]

    TASK_WAIT_EXECUTION_INTERVAL = 3

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
    def get_no_index_types(cls):
        return cls.NO_INDEX_TYPES

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
    def get_embedding(cls):
        embedding = getattr(cls, "_embedding", None)
        if not embedding:
            embedding = NewsEmbedding()
            cls._embedding = embedding
        return embedding

    @classmethod
    def get_morph_tagger(cls):
        morph_tagger = getattr(cls, "_morph_tagger", None)
        if not morph_tagger:
            embedding = cls.get_embedding()
            morph_tagger = NewsMorphTagger(embedding)
            cls._morph_tagger = morph_tagger
        return morph_tagger

    @classmethod
    def get_syntax_parser(cls):
        syntax_parser = getattr(cls, "_syntax_parser", None)
        if not syntax_parser:
            embedding = cls.get_embedding()
            syntax_parser = NewsSyntaxParser(embedding)
            cls._syntax_parser = syntax_parser
        return syntax_parser

    @classmethod
    def get_ner_tagger(cls):
        ner_tagger = getattr(cls, "_ner_tagger", None)
        if not ner_tagger:
            embedding = cls.get_embedding()
            ner_tagger = NewsNERTagger(embedding)
            cls._ner_tagger = ner_tagger
        return ner_tagger

    @classmethod
    def _extract_ner(cls, doc, morph_tagger, morph_vocab, syntax_parser, ner_tagger, extractors, extracted_types):
        # Apply morph
        doc.tag_morph(morph_tagger)
        # Lemmatize
        for token in doc.tokens:
            token.lemmatize(morph_vocab)
        # Parse syntax
        doc.parse_syntax(syntax_parser)
        # NER extract
        doc.tag_ner(ner_tagger, extractors=extractors)
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
        for _ in doc.spans:
            span_type = _.type
            if span_type in extracted_types:
                if not span_type in result:
                    result.update({span_type: []})
                data = _.as_json
                result[span_type].append(data)

        return result

    def extract_ner(self):
        '''
        Данный метод вызывать только через task`и! Если его вызывать из инстанции объекта то это приведет к перерасходу
        памяти из-за того, что для каждого запущеного потока сервера будет создана копия данных нужных для извлечения
        именованных сущностей. Каждая копия использует 250-350 мегабайт оперативной памяти, на боевом сервере создается
        практически столько потоков сколько есть процессорных ядер, у сервером с большим количеством ядер это приведет
        к тому что память будет использоваться крайне неэффективно.
        '''
        doc = Doc(self.get_ner_source())
        doc.segment(self.get_segmenter())

        morph_tagger = self.get_morph_tagger()
        morph_vocab = self.get_morph_vocab()
        syntax_parser = self.get_syntax_parser()
        ner_tagger = self.get_ner_tagger()
        extractors = self.get_extractors()
        extracted_types = self.get_extracted_types()

        return self._extract_ner(doc, morph_tagger, morph_vocab, syntax_parser,
                                          ner_tagger, extractors, extracted_types)

    def extract_ner_by_task(self):
        ner_data = {}
        try:
            result = extract_ner_data.apply_async(
                kwargs={
                    "obj_id": self.id,
                    "obj_model": self.__class__.__name__.lower()
                },
                expires=self.TASK_WAIT_EXECUTION_INTERVAL,
                retry=False,
            )
        except extract_ner_data.OperationalError as exc:
            logger = get_logger('logfile_error')
            logger.exception('Sending task raised: %r', exc)
        else:
            try:
                ner_data = result.get(
                    interval=self.TASK_WAIT_EXECUTION_INTERVAL,
                    propagate=False,
                )
            except Exception:
                pass
        self.ner_data = ner_data

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

    def cleaned_text_for_index(self):
        # Получаем данные для индексации тем же методом, что и при распознавании.
        text = self.get_ner_source()
        # Цикл по всем имеющимся в объекте типам данных NER
        for span_type in self.ner_data.keys():
            # Цикл по всем данным определенного типа
            for ner_data_by_type in self.ner_data[span_type]:
                # Если данные включены в список исключаемого к индексации - удаляем их
                if ner_data_by_type['type'] in self.NO_INDEX_TYPES:
                    text = text.replace(ner_data_by_type['text'], ' ')
        return text
