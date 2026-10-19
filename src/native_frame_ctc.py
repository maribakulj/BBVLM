"""Essai CTC : les cellules exclusivement dans le padding restent blank.

Une cellule partiellement native reste admissible : sa projection est ensuite
limitée aux pixels source par ForceCTC. Aucun caractère n'est réparti sur le
padding artificiel pour satisfaire une transcription. Sans chemin physique
possible, l'alignement reste explicitement refusé.
"""
from contextlib import contextmanager
import numpy as np


def native_frames(frames,input_width,padding,policy='intersects'):
    if frames<=0 or input_width<=2*padding or padding<0:
        raise ValueError('Dimensions de treillis/source invalides')
    edges=np.arange(frames+1,dtype=float)*input_width/frames
    if policy=='intersects':return (edges[1:]>padding)&(edges[:-1]<input_width-padding)
    if policy=='center':
        centers=(edges[1:]+edges[:-1])/2
        return (centers>=padding)&(centers<=input_width-padding)
    if policy=='contained':return (edges[:-1]>=padding)&(edges[1:]<=input_width-padding)
    raise ValueError('Politique de cellule source inconnue')


def constrain(logp,input_width,padding,policy='intersects'):
    if logp.ndim!=2 or logp.shape[1]<2:raise ValueError('Logits CTC invalides')
    valid=native_frames(len(logp),input_width,padding,policy)
    result=logp.copy();result[~valid,1:]=-1e30
    return result,valid


@contextmanager
def source_frame_alignment(forcectc,policy='intersects'):
    """Contexte isolé, séquentiel, à utiliser seulement dans le worker d'essai.

    Le tenseur fournit sa largeur exacte. Les callbacks originaux sont restaurés
    après succès ou erreur ; le modèle et le graphe imposé restent inchangés.
    """
    tensor=forcectc._ligne_tenseur;viterbi=forcectc.viterbi;context={};audit=[]
    def capture(*args,**kwargs):
        value=tensor(*args,**kwargs);context['input_width']=int(value.shape[-1])
        return value
    def solve(logp,states):
        masked,valid=constrain(logp,context['input_width'],forcectc.PAD,policy)
        required=(len(states)-1)//2+sum(states[s]==states[s-2] for s in range(3,len(states),2))
        audit.append(dict(frames=len(logp),native_frames=int(valid.sum()),required_frames=required,
                          input_width=context['input_width'],padding=forcectc.PAD,
                          policy=policy,
                          excluded_frame_ids=np.flatnonzero(~valid).tolist()))
        if required>valid.sum():return None
        return viterbi(masked,states)
    forcectc._ligne_tenseur=capture;forcectc.viterbi=solve
    try:yield audit
    finally:forcectc._ligne_tenseur=tensor;forcectc.viterbi=viterbi
