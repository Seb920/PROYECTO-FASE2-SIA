# Predicción de Precios de Viviendas — ML con Flask

Sistema de aprendizaje supervisado (regresión) para estimar precios de viviendas usando cuatro algoritmos de Machine Learning con interfaz web interactiva.

## Dataset

- **Archivo:** `boston_housing_esp.csv`
- **Registros:** 1,728 propiedades
- **Variable objetivo:** `precio` (valor de la vivienda en USD)
- **Características:** 15 variables (metros habitables, antigüedad, dormitorios, baños, calefacción, desagüe, vistas al lago, etc.)

## Algoritmos implementados

| Algoritmo              | Ruta API              | Escalado |
|------------------------|-----------------------|----------|
| Regresión Lineal       | `/api/regresion_lineal` | Sí (StandardScaler) |
| K-Nearest Neighbors    | `/api/knn`            | Sí |
| Support Vector Machine | `/api/svm`            | Sí |
| Árbol de Decisión      | `/api/arbol`          | No |
| Comparación general    | `/api/comparacion`    | — |
| **Predicción nueva casa** | **`POST /api/predecir`** | Automático |
| Info del dataset       | `/api/dataset_info`   | — |

## Instalación

```bash
pip install -r requirements.txt
```

## Ejecutar

```bash
cd proyecto_viviendas
python app.py
```

Abrir en el navegador: http://127.0.0.1:5000

## Estructura

```
proyecto_viviendas/
├── app.py                  ← Backend Flask + modelos ML + validaciones
├── boston_housing_esp.csv  ← Dataset (1,728 registros)
├── requirements.txt        ← Dependencias
└── templates/
    └── index.html          ← Interfaz web con formulario de predicción
```

## Funcionalidades

- **Pestaña "Modelos ML":** Ejecuta cada algoritmo y visualiza métricas (R², RMSE, MAE) + gráficos de predicciones vs reales y diagrama característico.
- **Pestaña "Predecir Casa":** Formulario con validación completa para ingresar datos de una propiedad y obtener el precio estimado de los 4 algoritmos.
- **Comparación:** Tabla comparativa de los 4 modelos en el mismo conjunto de prueba.

## Validaciones implementadas

- Campos requeridos (front-end y back-end)
- Rangos numéricos por campo (metros, años, precio, dormitorios, etc.)
- Opciones válidas para campos categóricos (calefacción, desagüe, etc.)
- Regla de negocio: habitaciones totales ≥ dormitorios
