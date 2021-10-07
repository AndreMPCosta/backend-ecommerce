# Language Helper
from dataclasses import dataclass, field
from json import load, dump, JSONDecodeError
from os.path import exists
from typing import Optional, List

from config import available_languages


@dataclass
class AppLanguage:
    prefixes: Optional[List[str]]
    languages: dict = field(default_factory=dict)

    def __post_init__(self):
        for lang in self.prefixes:
            if exists(f'languages/{lang}.json'):
                with open(f'languages/{lang}.json', 'r') as infile:
                    try:
                        read_data: dict = load(infile)
                        self.languages.update({
                            lang: read_data
                        })
                    except JSONDecodeError:
                        pass
            else:
                self.languages.update({
                    lang: {}
                })

    def update_strings(self, prefix: str, language_strings: dict):
        self.languages.get(prefix).update(language_strings)
        # if exists(f'languages/{prefix}.json'):
        with open(f'languages/{prefix}.json', 'w') as outfile:
            dump(self.languages.get(prefix), outfile, sort_keys=True, indent=4)

    def refresh_strings(self, prefix: str):
        if exists(f'languages/{prefix}.json'):
            with open(f'languages/{prefix}.json', 'r') as file:
                data: dict = load(file)
                self.languages.get(prefix).update(data)

    def get_text(self, prefix: str, text_key: str) -> str:
        return self.languages.get(prefix).get(text_key)

    def clear(self):
        for prefix in self.prefixes:
            self.languages.update({
                prefix: {}
            })


languages = AppLanguage(available_languages)
