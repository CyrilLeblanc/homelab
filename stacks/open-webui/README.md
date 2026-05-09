En résumé, les étapes qui auraient dû être faites dès le début :

Ne pas utiliser rhasspy/piper-voices — ce n'est pas supporté par Speaches v0.8+. Il faut les modèles du registry Speaches (speaches-ai/piper-*).
Télécharger le modèle via huggingface-cli dans le container :

```bash
docker exec speaches huggingface-cli download speaches-ai/piper-fr_FR-siwis-medium
```

Config LiteLLM correcte :

yaml- model_name: piper
  litellm_params:
    model: openai/speaches-ai/piper-fr_FR-siwis-medium
    api_base: http://speaches:8000
    api_key: dummy-key
  model_info:
    mode: audio_speech

OpenWebUI : TTS Model = piper, TTS Voice = fr_FR-siwis-medium

Le reste (volume, endpoints, mode: text_to_speech vs audio_speech) c'était des fausses pistes. Le vrai bloquant était juste le mauvais nom de modèle.