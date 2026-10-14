@echo off
chcp 65001 > nul
title SuiviPRO - Tunnel HTTPS Sécurisé Mobile / Tablette
cls
echo ====================================================================
echo  🚀 SuiviPRO : Accès Mobile ^& Tablette avec Caméra Face ID
echo ====================================================================
echo.
echo  Ce script génère une adresse HTTPS sécurisée gratuite pour votre
echo  téléphone ou tablette d'atelier.
echo.
echo  Grâce au HTTPS, Safari (iPhone) et Chrome (Android) autorisent
echo  directement la Caméra et la reconnaissance Face ID sans blocage !
echo.
echo  Génération de l'adresse en cours...
echo ====================================================================
echo.
call npx.cmd -y localtunnel --port 8000
echo.
pause
