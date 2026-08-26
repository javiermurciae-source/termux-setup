# Enigma Streaming Manager (v13 final)

Navegador con perfiles independientes para cuentas de streaming.

- Motor: Google
- Accesos: Netflix, Disney+, HBO Max, Prime Video, Crunchyroll, Spotify, Canva
- Sin: antidetect, proxies, IP, pánico, auto-wipe, huella

## Reinstalar
```bash
su -c "pm install -r enigma/Enigma-Streaming-FINAL.apk"
```

## Compilar cambios
Editar smali en ~/enigma-decompiled/resources/ y:
```bash
apktool b -f --aapt $(command -v aapt2) -j 4 resources -o app.apk
bash ~/enigma-decompiled/sign.sh app.apk firmado.apk
```
Keystore: NO esta en el repo (privado). Backup local: ~/enigma-decompiled/keystore/enigma-mod.jks
