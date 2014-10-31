#!/usr/bin/env python
#-*- coding:utf-8 -*-

import xml.etree.ElementTree as ET

class Verse():

    def __init__(self, book_name, chapter_num, verse_num, xml, highlights=set()):
        self.book_name = book_name
        self.chapter_num = chapter_num
        self.verse_num = verse_num
        self.xml = xml
        self.highlights = highlights
        self.words = []

    def to_string(self):
        return "{}\n{}".format(self.citation_ref(), self.text)

    def citation_ref(self):
        return "{} {}:{}".format(self.book_name.replace('_', ' '), self.chapter_num, self.verse_num)

    def chapter_link(self):
        return (self.book_name, self.chapter_num)

    def get_words(self):
        if (len(self.words) is 0):
            root = ET.fromstring(u'<verse>{}</verse>'.format(self.xml).encode('utf-8'))
            for child in root:
                monad_id = int(child.attrib['m'])
                focus = monad_id in self.highlights
                text = '' if child.text is None else child.text
                trailer = child.get('t', '')
                word = Word(monad_id, text, trailer, focus=focus)
                self.words.append(word)
        return self.words


class Word():

    def __init__(self, monad_id, text, trailer, focus=False):
        self.monad_id = monad_id
        self.text = text
        self.trailer = trailer
        self.focus = focus

    def to_string(self):
        return "id:" + str(self.monad_id) + " focus:" + str(self.focus) + " text:" + self.text + " trailer:" + self.trailer

