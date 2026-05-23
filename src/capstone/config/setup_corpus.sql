-- Copyright 2026 Matthew Marshall
--
-- Licensed under the Apache License, Version 2.0 (the "License");
-- you may not use this file except in compliance with the License.
-- You may obtain a copy of the License at
--
--     http://www.apache.org/licenses/LICENSE-2.0
--
-- Unless required by applicable law or agreed to in writing, software
-- distributed under the License is distributed on an "AS IS" BASIS,
-- WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
-- See the License for the specific language governing permissions and
-- limitations under the License.

CREATE TABLE IF NOT EXISTS articles(
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    subject TEXT NOT NULL,
    date TEXT NOT NULL,
    is_true BOOLEAN NOT NULL,
    negativity REAL, -- sentiment neg
    neutrality REAL, -- sentiment neu
    positivity REAL, -- sentiment pos
    compound_sentiment REAL, -- sentiment compound
    sentence_count INTEGER -- sentiment n_sentences
);

CREATE TABLE IF NOT EXISTS tokens_true(
    id INTEGER PRIMARY KEY,
    article_id INT NOT NULL,
    orth TEXT NOT NULL, -- text/orth_
    lemma TEXT NOT NULL, -- lemma_
    pos TEXT NOT NULL, -- pos_
    tag TEXT NOT NULL, -- tag_
    dep TEXT NOT NULL, -- dep_
    head TEXT NOT NULL,
    prefix TEXT NOT NULL, -- prefix_
    suffix TEXT NOT NULL, -- suffix_
    FOREIGN KEY (article_id) REFERENCES articles(id)
);

CREATE TABLE IF NOT EXISTS tokens_fake(
    id INTEGER PRIMARY KEY,
    article_id INT NOT NULL,
    orth TEXT NOT NULL, -- text/orth_
    lemma TEXT NOT NULL, -- lemma_
    pos TEXT NOT NULL, -- pos_
    tag TEXT NOT NULL, -- tag_
    dep TEXT NOT NULL, -- dep_
    head TEXT NOT NULL,
    prefix TEXT NOT NULL, -- prefix_
    suffix TEXT NOT NULL, -- suffix_
    FOREIGN KEY (article_id) REFERENCES articles(id)
);
