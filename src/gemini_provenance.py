"""Normalisation de libellé fournisseur attestée par le terminal natif.

Google est un nom de fournisseur, Gemini une famille de modèles. Le libellé
original reste dans la provenance. Aucun texte, modèle ou ID n'est corrigé.
Une autre famille OCR, un footer absent ou une requête ultérieure sont refusés.
"""
import re


def normalize_provider(value,terminal):
    if value.get('provider')!='Google':return value
    job_id=value.get('job_id','')
    if not re.fullmatch(r'[0-9a-f]{32}',job_id) or not re.match(r'^Gemini\s+[0-9]',value.get('model','')):
        raise ValueError('Libellé Google sans modèle/ID Gemini établi')
    position=terminal.rfind(job_id)
    if position<0:raise ValueError('ID absent de la preuve native')
    tail=terminal[position+len(job_id):]
    if re.search(r'(?<![0-9a-f])[0-9a-f]{32}(?![0-9a-f])',tail):
        raise ValueError('Une autre requête suit la réponse à normaliser')
    displays=re.findall(r'(Gemini\s+[\d.]+\s+(?:Flash|Pro)\s*·\s*\w+)\s*$',tail,re.MULTILINE)
    if not displays:raise ValueError('Footer natif Gemini absent après la réponse identifiée')
    out=dict(value)
    out.update(provider='gemini',provider_claim_original='Google',
        provider_normalization=dict(basis='native Gemini footer after exact job ID; model claim Gemini; vendor label only',
                                    native_model_display=displays[-1],text_changed=False))
    return out
