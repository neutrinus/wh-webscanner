#!/usr/bin/env python

import re
import sys
import logging
import pickle

from nltk.classify import NaiveBayesClassifier


log = logging.getLogger(__name__)


class CannotRecognizeLanguage(Exception):
    pass


class TextFileTypeGuesser(object):
    MAX_BYTES = 2 * 1024 * 1024  # 2 MiB

    def __init__(self):
        """docstring for __init__"""
        self._cls = None

    def train(self, files_dict):
        '''Train classifier with sample data.
        Each ivocation train classifier from the ground.

        :param files_dict: dict where keys are files paths, and values are their
                           mime type.
        '''
        train_data = []
        for num, (file_path, orig_t) in enumerate(files_dict.iteritems()):
            print >>sys.stderr, '\r%d / %d    -   %s         ' % (num, len(files_dict), file_path),
            train_data.append((self._get_tokens(file_path), orig_t))
        print
        print 'train'
        self._cls = NaiveBayesClassifier.train(train_data)

    def guess_from_file(self, file_path):
        if not self._cls:
            raise AttributeError('Classifier is not trained!')
        cls = self._cls
        x = self._get_tokens(file_path)
        return cls.classify(x)

    def save(self, file_path):
        if not self._cls:
            raise Exception('There is no classifier to save! Please train it first.')
        pickle.dump(self._cls, open(file_path, 'w'))

    def load(self, file_path):
        self._cls = pickle.load(open(file_path))

    @staticmethod
    def normalize_dict(d):
        _max = float(max(d.itervalues()))
        return {key: value / _max for key, value in d.iteritems()}

    @classmethod
    def _get_tokens(cls, file):
        '''Make a words dict

        Read the file, separate words (using best detected lexer for language
        in file [the pytgments guesse is not very accurate but it has only to
        separate words]).

        Returns a dictionary of words (it can be used by `nltk` as featureset).
        '''
        regex = re.compile(r'\d+|\d\+.\d+')

        def valid(word):
            word = word.strip()
            if not word:  # omit white signs
                return False
            if word.isdigit():  # omit digits
                return False
            if regex.match(word):  # omit digits and floats
                return False
            return True

        data = open(file).read(cls.MAX_BYTES)
        # !!! WARNING pygments lexer hangout sometimes !!! rarely but still
        #lexer = lexers.guess_lexer(data)
        from nltk.tokenize import TreebankWordTokenizer, WordPunctTokenizer
        #tokens = TreebankWordTokenizer().tokenize(data)  # slower tokenizer
        tokens = WordPunctTokenizer().tokenize(data)  # faster tokenizer
        tokens = tokens[:300] + tokens[-100:]
        return {x: True for x in tokens if valid(x)}
