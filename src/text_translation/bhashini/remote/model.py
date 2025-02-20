import os
import openai
import openai_async
from cache import AsyncTTL
from .request import ModelRequest
import json

openai.api_key = os.getenv("OPENAI_API_KEY")


class Model:
    def __new__(cls, context):
        cls.context = context
        if not hasattr(cls, 'instance'):
            cls.instance = super(Model, cls).__new__(cls)
        return cls.instance

    @AsyncTTL(time_to_live=600000, maxsize=1024)
    async def inference(self, request: ModelRequest):
        augmented_text, modified_words = self.apply_dictionary(request.text, request.dictionary)
        translated_text = await self.translate_text(augmented_text, request.source_language, request.target_language)
        final_translated_text = self.replace_modified_words(translated_text, modified_words, request.dictionary)
        return {
            "translated": final_translated_text,
            "success": True
        }    
    
    async def translate_text(self, request: ModelRequest):
        url = "https://nmt-api.ai4bharat.org/translate_sentence"
        payload = json.dumps({
            "text": request.text,
            "source_language": request.source_language,
            "target_language": request.target_language
        })
        headers = {
            'authority': 'nmt-api.ai4bharat.org',
            'accept': '*/*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'content-type': 'application/json',
            'origin': 'https://models.ai4bharat.org',
            'referer': 'https://models.ai4bharat.org/',
            'sec-ch-ua': '"Not_A Brand";v="99", "Google Chrome";v="109", "Chromium";v="109"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36'
        }

        response = await self.context.client.post(url, headers=headers, data=payload)
        resp = await response.json()
        return resp["text"]
    
    def apply_dictionary(self, text, dictionary):
        words = text.split()
        modified_words = {}
        for i in range(len(words)):
            word = words[i]
            if word in dictionary:
                modified_words[i] = word
                words[i] = dictionary[word]
        augmented_text = " ".join(words)
        return augmented_text, modified_words

    def replace_modified_words(self, text, modified_words, dictionary):
        words = text.split()
        for index, word in modified_words.items():
            if index < len(words) and words[index] != word:
                words[index] = dictionary.get(word, words[index])
        final_translated_text = " ".join(words)
        return final_translated_text
