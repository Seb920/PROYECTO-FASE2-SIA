# Detección de Varicela — ML con Flask

## Instalación

```bash
pip install -r requirements.txt
```

O instalar manualmente:

```bash
pip install flask scikit-learn pandas numpy
```

## Ejecutar

```bash
python app.py
```

Luego abrir en el navegador: http://127.0.0.1:5000

## Estructura

```
varicela_app/
├── app.py              ← Backend Flask + modelos ML
├── data.csv            ← Dataset CDC NNDSS 2018
├── requirements.txt    ← Librerías necesarias
└── templates/
    └── index.html      ← Interfaz web
```

## Algoritmos implementados

| Código   | Algoritmo              | Ruta API         |
|----------|------------------------|------------------|
| F2-SI-01 | Regresión Logística    | /api/regresion   |
| F2-SI-02 | K-Nearest Neighbors    | /api/knn         |
| F2-SI-03 | Support Vector Machine | /api/svm         |
| F2-SI-04 | Árbol de Decisión      | /api/arbol       |
| —        | Comparación general    | /api/comparacion |

## Dataset

NNDSS - Table II. Tetanus to Varicella (2018)  
Fuente: Centers for Disease Control and Prevention (CDC)  
Variables usadas: casos semanales, mediana 52 semanas, máximo 52 semanas, acumulado 2017/2018.

El target (variable a predecir) es si una semana representa un **brote** (casos por encima de la mediana histórica) o estado **normal**.
