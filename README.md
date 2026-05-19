# PROYECTO FASE 2 — SIA: Predicción de Precios de Viviendas

Sistema de Información con aprendizaje supervisado (regresión) para predecir precios de viviendas. Implementado en Python (Flask + scikit-learn) con interfaz web interactiva.

## Tema elegido

**Predicción de Precios de Viviendas**

## Algoritmos implementados

1. Regresión Lineal
2. K-Nearest Neighbors (KNN, k=5)
3. Support Vector Machine (SVM kernel RBF)
4. Árbol de Decisión (max_depth=10)

## Instalación y ejecución

```bash
cd proyecto_viviendas
pip install -r requirements.txt
python app.py
```

Abrir: http://127.0.0.1:5000

## Estructura del proyecto

```
PROYECTO-FASE2-SIA/
└── proyecto_viviendas/
    ├── app.py                  ← Backend Flask + modelos + validaciones
    ├── boston_housing_esp.csv  ← Dataset (1,728 registros)
    ├── requirements.txt
    └── templates/
        └── index.html          ← Interfaz web
```
