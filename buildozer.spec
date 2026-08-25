[app]
title = E-Motors
package.name = emotors
package.domain = org.bastler
source.dir = .
source.include_exts = py,png,kv
version = 0.1

requirements = python3,kivy,requests,plyer

orientation = portrait
fullscreen = 0

# Android-Konfiguration
android.api = 33
android.minapi = 24
android.sdk = 33
android.ndk = 25.2.9519653
android.private_storage = True
android.permissions = INTERNET,VIBRATE

# Icon festlegen
icon.filename = %(source.dir)s/logo.png

# Wichtige System-Bibliotheken (Verhindert Absturz am Ende)
android.archs = arm64-v8a, armeabi-v7a
android.allow_gpl = True
android.skip_update = False
android.accept_sdk_license = True

[buildozer]
log_level = 2
warn_on_root = 1
