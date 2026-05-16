from flask import Flask, jsonify, render_template
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge, Lasso
from sklearn.neighbors import KNeighborsRegressor
from sklearn.svm import SVR
from sklearn.tree import DecisionTreeRegressor, plot_tree
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import io
import base64
import warnings
warnings.filterwarnings('ignore')

app = Flask(__name__)

def load_data():
    """Cargar y preprocesar datos de viviendas"""
    df = pd.read_csv("boston_housing_esp.csv")
    
    # Limpiar nombres de columnas
    df.columns = df.columns.str.strip()
    
    # Codificar variables categóricas
    categorical_cols = ['calefaccion', 'consumo_calefacion', 'desague', 'vistas_lago', 'nueva_construccion', 'aire_acondicionado']
    
    for col in categorical_cols:
        if col in df.columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
    
    # Variable objetivo: precio
    y = df['precio'].values
    
    # Características (todas excepto precio)
    feature_cols = [col for col in df.columns if col != 'precio']
    X = df[feature_cols].values
    
    # Manejar valores nulos
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    y = np.nan_to_num(y, nan=y.mean() if len(y) > 0 else 0.0)
    
    print(f"Dataset cargado: {len(df)} registros, {len(feature_cols)} características")
    print(f"Rango de precios: ${y.min():,.0f} - ${y.max():,.0f}")
    
    return X, y, df, feature_cols

def get_regression_metrics(model, X_train, X_test, y_train, y_test, needs_scale=False):
    """Entrena modelo de regresión y devuelve métricas"""
    scaler = StandardScaler()
    if needs_scale:
        X_train_scaled = scaler.fit_transform(X_train)
        X_test_scaled = scaler.transform(X_test)
        model.fit(X_train_scaled, y_train)
        y_pred = model.predict(X_test_scaled)
    else:
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
    
    return {
        "rmse": round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
        "mae": round(mean_absolute_error(y_test, y_pred), 2),
        "r2": round(r2_score(y_test, y_pred) * 100, 2),
        "predictions": y_pred.tolist()[:10],
        "actuals": y_test.tolist()[:10]
    }

def generate_metrics_chart(metrics, model_name):
    """Gráfico de barras con métricas"""
    fig, ax = plt.subplots(figsize=(10, 6))
    fig.patch.set_facecolor('#0a0f1e')
    
    metric_names = ['R² Score (%)', 'RMSE ($)', 'MAE ($)']
    metric_values = [metrics['r2'], metrics['rmse'] / 10000, metrics['mae'] / 10000]
    colors = ['#10b981', '#00e5ff', '#f59e0b']
    
    bars = ax.bar(metric_names, metric_values, color=colors, alpha=0.8, edgecolor='white', linewidth=1)
    ax.set_ylabel('Valor (en miles de $ para RMSE/MAE)', color='#e2e8f0')
    ax.set_title(f'{model_name} - Métricas de Rendimiento', color='#00e5ff', fontweight='bold')
    ax.set_facecolor('#111827')
    ax.tick_params(colors='#e2e8f0')
    ax.spines['bottom'].set_color('#1e2d45')
    ax.spines['top'].set_color('#1e2d45')
    ax.spines['right'].set_color('#1e2d45')
    ax.spines['left'].set_color('#1e2d45')
    
    for bar, val in zip(bars, metric_values):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.5, 
                f'{val:.1f}', ha='center', va='bottom', color='#e2e8f0', fontweight='bold')
    
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', facecolor='#0a0f1e', edgecolor='none')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close()
    return img_base64

def generate_regression_chart(X_train, y_train, model_name):
    """Gráfico característico de regresión"""
    try:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.patch.set_facecolor('#0a0f1e')
        
        # Usar primera característica para visualización
        X_simple = X_train[:, 0].reshape(-1, 1)
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X_simple)
        
        if model_name == "Regresión Lineal":
            model = LinearRegression()
        elif model_name == "KNN":
            model = KNeighborsRegressor(n_neighbors=5)
        elif model_name == "SVM":
            model = SVR(kernel='rbf')
        else:
            model = DecisionTreeRegressor(max_depth=5, random_state=42)
        
        model.fit(X_scaled, y_train)
        
        # Curva de regresión
        X_test_curve = np.linspace(X_scaled.min() - 1, X_scaled.max() + 1, 300).reshape(-1, 1)
        y_pred_curve = model.predict(X_test_curve)
        
        axes[0].scatter(X_scaled, y_train, c=y_train, cmap='viridis', edgecolors='white', s=50, alpha=0.7)
        axes[0].plot(X_test_curve, y_pred_curve, color='#00e5ff', linewidth=3, label=f'Modelo {model_name}')
        axes[0].set_xlabel('Característica 1 (Estandarizada)', color='#e2e8f0')
        axes[0].set_ylabel('Precio ($)', color='#e2e8f0')
        axes[0].set_title(f'{model_name} - Ajuste del Modelo', color='#00e5ff', fontweight='bold')
        axes[0].set_facecolor('#111827')
        axes[0].tick_params(colors='#e2e8f0')
        axes[0].legend(facecolor='#1a2235', edgecolor='#1e2d45', labelcolor='#e2e8f0')
        
        # Mapa de calor de correlaciones
        if X_train.shape[1] >= 4:
            # Calcular correlaciones con precio
            y_mean = y_train.mean()
            correlations = []
            for i in range(min(10, X_train.shape[1])):
                corr = np.corrcoef(X_train[:, i], y_train)[0, 1]
                correlations.append(corr if not np.isnan(corr) else 0)
            
            features_names = ['Caract 1', 'Caract 2', 'Caract 3', 'Caract 4', 'Caract 5', 
                            'Caract 6', 'Caract 7', 'Caract 8', 'Caract 9', 'Caract 10'][:len(correlations)]
            
            colors_corr = ['#10b981' if c > 0 else '#ef4444' for c in correlations]
            bars = axes[1].barh(features_names, correlations, color=colors_corr, alpha=0.7, edgecolor='white')
            axes[1].axvline(x=0, color='white', linestyle='-', alpha=0.3)
            axes[1].set_xlabel('Correlación con Precio', color='#e2e8f0')
            axes[1].set_title('Importancia de Características', color='#00e5ff', fontweight='bold')
            axes[1].set_facecolor('#111827')
            axes[1].tick_params(colors='#e2e8f0')
            
            for bar, val in zip(bars, correlations):
                axes[1].text(val + (0.02 if val > 0 else -0.12), bar.get_y() + bar.get_height()/2, 
                            f'{val:.2f}', va='center', color='#e2e8f0')
        
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor='#0a0f1e', edgecolor='none')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        return img_base64
    except Exception as e:
        print(f"Error en regression chart: {e}")
        return ""

def generate_tree_chart(X_train, y_train):
    """Gráfico característico de Árbol de Decisión"""
    try:
        fig, axes = plt.subplots(1, 2, figsize=(16, 8))
        fig.patch.set_facecolor('white')
        
        tree_clf = DecisionTreeRegressor(max_depth=3, random_state=42)
        tree_clf.fit(X_train, y_train)
        
        # Árbol de decisión
        plot_tree(tree_clf, 
                  feature_names=['Caract 1', 'Caract 2', 'Caract 3', 'Caract 4', 'Caract 5', 
                                'Caract 6', 'Caract 7', 'Caract 8', 'Caract 9', 'Caract 10'][:X_train.shape[1]], 
                  filled=True, 
                  fontsize=8, 
                  rounded=True,
                  ax=axes[0])
        axes[0].set_title('Árbol de Decisión - Estructura', color='black', fontweight='bold', fontsize=12)
        axes[0].set_facecolor('white')
        
        # Importancia de características
        importancias = tree_clf.feature_importances_
        indices = np.argsort(importancias)[-8:]
        
        axes[1].barh(range(len(indices)), importancias[indices], color='#00e5ff', alpha=0.7, edgecolor='black')
        axes[1].set_yticks(range(len(indices)))
        axes[1].set_yticklabels([f'Caract {i+1}' for i in indices])
        axes[1].set_xlabel('Importancia', color='black')
        axes[1].set_title('Importancia de Características', color='black', fontweight='bold')
        axes[1].set_facecolor('white')
        axes[1].spines['bottom'].set_color('black')
        axes[1].spines['top'].set_color('black')
        axes[1].spines['right'].set_color('black')
        axes[1].spines['left'].set_color('black')
        axes[1].tick_params(colors='black')
        
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor='white', edgecolor='none', dpi=150)
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        return img_base64
    except Exception as e:
        print(f"Error en tree chart: {e}")
        return ""

def generate_prediction_chart(y_test, y_pred, model_name):
    """Gráfico de predicciones vs reales"""
    try:
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        fig.patch.set_facecolor('#0a0f1e')
        
        # Scatter plot: Predicciones vs Reales
        axes[0].scatter(y_test, y_pred, alpha=0.6, c='#00e5ff', edgecolors='white')
        axes[0].plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--', lw=2, label='Predicción Perfecta')
        axes[0].set_xlabel('Precio Real ($)', color='#e2e8f0')
        axes[0].set_ylabel('Precio Predicho ($)', color='#e2e8f0')
        axes[0].set_title(f'{model_name} - Predicciones vs Reales', color='#00e5ff', fontweight='bold')
        axes[0].set_facecolor('#111827')
        axes[0].tick_params(colors='#e2e8f0')
        axes[0].legend(facecolor='#1a2235', edgecolor='#1e2d45', labelcolor='#e2e8f0')
        
        # Histograma de errores
        errores = np.array(y_test) - np.array(y_pred)
        axes[1].hist(errores, bins=30, color='#f59e0b', alpha=0.7, edgecolor='white')
        axes[1].axvline(x=0, color='#10b981', linestyle='--', linewidth=2, label='Error Cero')
        axes[1].set_xlabel('Error de Predicción ($)', color='#e2e8f0')
        axes[1].set_ylabel('Frecuencia', color='#e2e8f0')
        axes[1].set_title('Distribución de Errores', color='#00e5ff', fontweight='bold')
        axes[1].set_facecolor('#111827')
        axes[1].tick_params(colors='#e2e8f0')
        axes[1].legend(facecolor='#1a2235', edgecolor='#1e2d45', labelcolor='#e2e8f0')
        
        plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', facecolor='#0a0f1e', edgecolor='none')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close()
        return img_base64
    except Exception as e:
        print(f"Error en prediction chart: {e}")
        return ""

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/regresion_lineal")
def regresion_lineal():
    try:
        X, y, df, feature_cols = load_data()
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = LinearRegression()
        result = get_regression_metrics(model, X_train, X_test, y_train, y_test, needs_scale=True)
        
        metrics_chart = generate_metrics_chart(result, "Regresión Lineal")
        regression_chart = generate_regression_chart(X_train, y_train, "Regresión Lineal")
        prediction_chart = generate_prediction_chart(y_test, result['predictions'], "Regresión Lineal")
        
        result['metrics_chart'] = metrics_chart
        result['regression_chart'] = regression_chart
        result['prediction_chart'] = prediction_chart
        result['model_name'] = "Regresión Lineal"
        return jsonify(result)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/knn")
def knn():
    try:
        X, y, df, feature_cols = load_data()
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = KNeighborsRegressor(n_neighbors=5)
        result = get_regression_metrics(model, X_train, X_test, y_train, y_test, needs_scale=True)
        
        metrics_chart = generate_metrics_chart(result, "KNN Regressor")
        regression_chart = generate_regression_chart(X_train, y_train, "KNN")
        prediction_chart = generate_prediction_chart(y_test, result['predictions'], "KNN")
        
        result['metrics_chart'] = metrics_chart
        result['regression_chart'] = regression_chart
        result['prediction_chart'] = prediction_chart
        result['model_name'] = "K-Nearest Neighbors (k=5)"
        return jsonify(result)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/svm")
def svm():
    try:
        X, y, df, feature_cols = load_data()
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = SVR(kernel='rbf', C=100, gamma='auto')
        result = get_regression_metrics(model, X_train, X_test, y_train, y_test, needs_scale=True)
        
        metrics_chart = generate_metrics_chart(result, "SVM Regressor")
        regression_chart = generate_regression_chart(X_train, y_train, "SVM")
        prediction_chart = generate_prediction_chart(y_test, result['predictions'], "SVM")
        
        result['metrics_chart'] = metrics_chart
        result['regression_chart'] = regression_chart
        result['prediction_chart'] = prediction_chart
        result['model_name'] = "Support Vector Machine (RBF)"
        return jsonify(result)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/arbol")
def arbol():
    try:
        X, y, df, feature_cols = load_data()
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        
        model = DecisionTreeRegressor(max_depth=10, random_state=42)
        result = get_regression_metrics(model, X_train, X_test, y_train, y_test, needs_scale=False)
        
        metrics_chart = generate_metrics_chart(result, "Árbol de Decisión")
        tree_chart = generate_tree_chart(X_train, y_train)
        prediction_chart = generate_prediction_chart(y_test, result['predictions'], "Árbol de Decisión")
        
        result['metrics_chart'] = metrics_chart
        result['regression_chart'] = tree_chart
        result['prediction_chart'] = prediction_chart
        result['model_name'] = "Árbol de Decisión"
        return jsonify(result)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/comparacion")
def comparacion():
    try:
        X, y, df, feature_cols = load_data()
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)

        modelos = {
            "Regresión Lineal": LinearRegression(),
            "KNN (k=5)": KNeighborsRegressor(n_neighbors=5),
            "SVM (RBF)": SVR(kernel='rbf', C=100, gamma='auto'),
            "Árbol Decisión": DecisionTreeRegressor(max_depth=10, random_state=42)
        }

        resultado = []
        for nombre, modelo in modelos.items():
            if nombre == "Árbol Decisión":
                modelo.fit(X_train, y_train)
                y_pred = modelo.predict(X_test)
            else:
                modelo.fit(X_train_s, y_train)
                y_pred = modelo.predict(X_test_s)
            resultado.append({
                "nombre": nombre,
                "r2": round(r2_score(y_test, y_pred) * 100, 2),
                "rmse": round(np.sqrt(mean_squared_error(y_test, y_pred)), 2),
                "mae": round(mean_absolute_error(y_test, y_pred), 2)
            })
        return jsonify(resultado)
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)