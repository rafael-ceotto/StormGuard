"""
Model Training Pipeline DAG
============================
Trains Deep Learning models on processed data.
Handles hyperparameter tuning, model evaluation, and MLflow registration.

Frequency: Weekly (Sundays at 02:00 UTC)
"""

from datetime import datetime, timedelta
from airflow.decorators import dag, task
from airflow.utils.task_group import TaskGroup
import logging
import json

logger = logging.getLogger(__name__)

default_args = {
    'owner': 'stormguard-ml-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=10),
}

@dag(
    dag_id='model_training_pipeline',
    default_args=default_args,
    description='Weekly model training and evaluation pipeline',
    schedule_interval='0 2 * * 0',  # Weekly on Sundays at 02:00 UTC
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=['ml-pipeline', 'training'],
    max_active_runs=1,  # Prevent concurrent training runs
)
def model_training_pipeline():
    """
    Main model training pipeline
    """

    @task
    def prepare_training_data(**context):
        """
        Prepare training dataset from Data Lake
        - Load latest data
        - Split train/val/test (70/15/15)
        - Handle class imbalance
        """
        from data_pipeline.processors.feature_engineering import FeatureEngineer
        
        engineer = FeatureEngineer()
        execution_date = context['ds']
        
        logger.info("Preparing training data")
        
        # Load data from Delta Lake
        train_path, val_path, test_path = engineer.prepare_splits(execution_date)
        
        logger.info(f"Train: {train_path}, Val: {val_path}, Test: {test_path}")
        
        return {
            'train_path': train_path,
            'val_path': val_path,
            'test_path': test_path,
        }

    @task
    def feature_engineering(data_paths, **context):
        """
        Advanced feature engineering
        - Temporal features (lag, rolling stats)
        - Spatial features (geographical encoding)
        - Statistical features (skew, kurtosis)
        - Domain features (meteorological indices)
        """
        from data_pipeline.processors.feature_engineering import FeatureEngineer
        
        engineer = FeatureEngineer()
        
        logger.info("Running feature engineering")
        
        features_config = engineer.engineer_features(
            data_paths['train_path'],
            data_paths['val_path'],
            data_paths['test_path'],
        )
        
        logger.info(f"Generated {features_config['num_features']} features")
        
        return features_config

    @task
    def hyperparameter_tuning(features_config, **context):
        """
        Bayesian hyperparameter optimization using Optuna
        - Optimizes for ROC-AUC on validation set
        - Early stopping on plateau
        """
        from models.training.hyperparameter_optimizer import HyperparameterOptimizer
        
        optimizer = HyperparameterOptimizer()
        
        logger.info("Starting hyperparameter tuning")
        
        best_params = optimizer.optimize(
            features_config,
            n_trials=50,
            timeout=3600,  # 1 hour limit
        )
        
        logger.info(f"Best hyperparameters: {best_params}")
        
        return best_params

    @task
    def train_cnn_lstm_model(features_config, best_params, **context):
        """
        Train CNN-LSTM hybrid model
        - CNN for spatial feature extraction
        - LSTM for temporal modeling
        - Mixed precision training
        - Distributed training if available
        """
        from models.architectures.cnn_lstm_model import CNNLSTMModel
        from models.training.trainer import ModelTrainer
        
        logger.info("Training CNN-LSTM model")
        
        model = CNNLSTMModel(config=best_params)
        trainer = ModelTrainer(model)
        
        history = trainer.train(
            features_config,
            epochs=100,
            batch_size=32,
            early_stopping_patience=10,
            use_mixed_precision=True,
        )
        
        model_path = trainer.save_model('cnn_lstm_v1')
        
        logger.info(f"CNN-LSTM model saved at {model_path}")
        
        return {
            'model_type': 'cnn_lstm',
            'model_path': model_path,
            'history': history,
        }

    @task
    def train_transformer_model(features_config, best_params, **context):
        """
        Train Temporal Fusion Transformer
        - Multi-head attention for temporal patterns
        - Variable selection network
        """
        from models.architectures.transformer_model import TemporalFusionTransformer
        from models.training.trainer import ModelTrainer
        
        logger.info("Training Transformer model")
        
        model = TemporalFusionTransformer(config=best_params)
        trainer = ModelTrainer(model)
        
        history = trainer.train(
            features_config,
            epochs=100,
            batch_size=32,
            early_stopping_patience=10,
        )
        
        model_path = trainer.save_model('transformer_v1')
        
        logger.info(f"Transformer model saved at {model_path}")
        
        return {
            'model_type': 'transformer',
            'model_path': model_path,
            'history': history,
        }

    @task
    def evaluate_models(cnn_lstm_result, transformer_result, features_config, **context):
        """
        Comprehensive model evaluation
        Metrics:
        - ROC-AUC (general discrimination)
        - PR-AUC (imbalanced dataset)
        - Brier Score (calibration)
        - Expected Cost (business metric)
        - Lead Time (operational metric)
        """
        from models.training.evaluator import ModelEvaluator
        
        evaluator = ModelEvaluator()
        
        logger.info("Evaluating models on test set")
        
        cnn_lstm_metrics = evaluator.evaluate(
            cnn_lstm_result['model_path'],
            features_config['test_data'],
            model_type='cnn_lstm',
        )
        
        transformer_metrics = evaluator.evaluate(
            transformer_result['model_path'],
            features_config['test_data'],
            model_type='transformer',
        )
        
        evaluation_report = {
            'cnn_lstm': cnn_lstm_metrics,
            'transformer': transformer_metrics,
            'timestamp': context['ts'],
        }
        
        logger.info(f"Evaluation report: {json.dumps(evaluation_report, indent=2)}")
        
        return evaluation_report

    @task
    def run_backtesting(evaluation_report, **context):
        """
        Historical backtesting
        Test model performance on past disaster events
        - 2005 Hurricane Katrina
        - 2010 Pakistan Floods
        - 2011 Thailand Floods
        - 2020 Australian Bushfires
        """
        from models.training.backtester import Backtester
        
        backtester = Backtester()
        
        logger.info("Running historical backtesting")
        
        backtest_results = backtester.run_historical_backtest(
            model_paths=[
                evaluation_report['cnn_lstm']['model_path'],
                evaluation_report['transformer']['model_path'],
            ],
            historical_events=['katrina', 'pakistan_floods', 'thailand_floods', 'australian_fires'],
        )
        
        logger.info(f"Backtest results: {backtest_results}")
        
        return backtest_results

    @task
    def register_best_model(evaluation_report, backtest_results, **context):
        """
        Register best model to MLflow Model Registry
        - Compare all model candidates
        - Select best based on metrics
        - Register with version and metadata
        """
        from models.training.model_registry import ModelRegistry
        
        registry = ModelRegistry()
        
        logger.info("Registering best model to MLflow")
        
        best_model_info = registry.register_model(
            evaluation_report=evaluation_report,
            backtest_results=backtest_results,
            experiment_name='stormguard',
            run_id=context['run_id'],
        )
        
        logger.info(f"Model registered: {best_model_info}")
        
        return best_model_info

    # Task execution flow
    data = prepare_training_data()
    features = feature_engineering(data)
    best_params = hyperparameter_tuning(features)
    
    with TaskGroup("model_training") as training_group:
        cnn_lstm = train_cnn_lstm_model(features, best_params)
        transformer = train_transformer_model(features, best_params)
    
    evaluation = evaluate_models(cnn_lstm, transformer, features)
    backtest = run_backtesting(evaluation)
    registry = register_best_model(evaluation, backtest)

# Instantiate the DAG
model_training_dag = model_training_pipeline()
