# Runtime A83

Poids publics restaurés par restore_public_assets.py --only models/pero.zip,
hash vérifié par le runner. Base CPUa66, numpy1.26.4/opencv-headless4.8.1.78 gardés.
Installation `--no-deps` de requirements-a83.txt. Premier essai d'import a révélé
cloudpickle absent (joblib1.6) ; installé3.1.2, import réussi avant toute inférence.
Aucun échec d'inférence, aucun forward simulé. runtime-freeze.txt décrit les versions.
Pour restauration : installer requirements-a66.txt CPU puis les compléments A83
sans tirer numpy2/OpenCVGUI ; vérifier les imports et versions avant les calculs.
